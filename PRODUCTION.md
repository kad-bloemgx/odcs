# Production Deployment Guide for ODCS

This guide covers best practices for deploying ODCS to production Kubernetes clusters.

## Pre-Deployment Security Checklist

- [ ] PostgreSQL password is changed from default (`postgres`)
- [ ] PostgREST role password is changed from default (`postgrest`)
- [ ] Kubernetes secrets are used instead of plain-text passwords in values
- [ ] Network Policies are defined to restrict traffic between pods
- [ ] RBAC roles are configured with minimal necessary permissions
- [ ] TLS/SSL certificate is configured for Ingress
- [ ] Image pull secrets are configured if using private registries
- [ ] Container images are scanned for vulnerabilities

## 1. Secrets Management

### Option A: Kubernetes Secrets

Create a secret for database credentials:

```bash
kubectl create secret generic odcs-db-credentials \
  --from-literal=postgres-password=YourSecurePassword123 \
  --from-literal=postgrest-password=PostgREST123 \
  -n odcs
```

Update `values.yaml` to reference the secret:

```yaml
postgres:
  password: ""  # Leave empty; use secret instead
  existingSecret: odcs-db-credentials
  existingSecretPasswordKey: postgres-password
```

### Option B: Sealed Secrets (GitOps)

Install Sealed Secrets controller:

```bash
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml
```

Create and seal a secret:

```bash
echo -n mypassword | kubectl create secret generic my-secret \
  --dry-run=client \
  --from-file=password=/dev/stdin \
  -o yaml | kubeseal -o yaml > my-sealed-secret.yaml

kubectl apply -f my-sealed-secret.yaml
```

### Option C: External Secrets Operator

For cloud-native secret management (AWS Secrets Manager, Azure Key Vault, etc.):

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

Create SecretStore:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets
  namespace: odcs
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
```

## 2. Networking & Ingress

### Setup Nginx Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
```

### Configure SSL/TLS with Let's Encrypt

Install Cert-Manager:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.11.0/cert-manager.yaml
```

Create ClusterIssuer:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

Create Ingress with TLS:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: odcs-ingress
  namespace: odcs
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - odcs.example.com
      secretName: odcs-tls
  rules:
    - host: odcs.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: odcs-swagger
                port:
                  number: 8080
```

## 3. Storage Configuration

### For AWS (EBS)

```bash
# Create storage class for EBS
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
allowVolumeExpansion: true
EOF

# Deploy with EBS storage
helm install odcs ./helm -n odcs --create-namespace \
  --set postgres.storage.storageClass=ebs-gp3 \
  --set postgres.storage.size=100Gi
```

### For Azure (AzureDisk)

```bash
# Create storage class for Azure
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-managed-disk
provisioner: disk.csi.azure.com
parameters:
  skuname: Premium_LRS
  replication-type: None
allowVolumeExpansion: true
EOF

helm install odcs ./helm -n odcs --create-namespace \
  --set postgres.storage.storageClass=azure-managed-disk
```

### For GCP (Persistent Disk)

```bash
# GCP uses default storage classes
helm install odcs ./helm -n odcs --create-namespace \
  --set postgres.storage.storageClass=standard-rwo
```

## 4. Resource Limits & Requests

For a production deployment, set appropriate resource limits:

```yaml
postgres:
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"

postgrest:
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "1000m"

swagger:
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "500m"
```

Deploy with custom resources:

```bash
helm install odcs ./helm -n odcs --create-namespace -f values-prod.yaml
```

## 5. High Availability

### Multi-replica PostgREST

Enable horizontal scaling for PostgREST:

```bash
helm install odcs ./helm -n odcs --create-namespace \
  --set replicaCount=3
```

This scales PostgREST and Swagger UI to 3 replicas.

### Database Backup Strategy

Implement regular PostgreSQL backups:

```bash
# Create a backup cronjob
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: odcs
spec:
  schedule: "0 2 * * *"  # Run at 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              BACKUP_FILE="/backups/postgres_backup_\$(date +%Y%m%d_%H%M%S).sql"
              pg_dump -h odcs-postgres -U postgres -d postgres > \$BACKUP_FILE
              echo "Backup created: \$BACKUP_FILE"
            env:
            - name: PGPASSWORD
              value: YOUR_PASSWORD_HERE
            volumeMounts:
            - name: backup-volume
              mountPath: /backups
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: postgres-backup-pvc
          restartPolicy: OnFailure
EOF
```

## 6. Monitoring & Observability

### Prometheus & Grafana

Install Prometheus Operator:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

Enable ServiceMonitor in Helm values:

```yaml
serviceMonitor:
  enabled: true
```

### ELK Stack for Logs

Deploy Elasticsearch, Logstash, Kibana:

```bash
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch -n logging --create-namespace
helm install kibana elastic/kibana -n logging
```

Configure Fluent Bit to collect container logs:

```bash
helm repo add fluent https://fluent.github.io/helm-charts
helm install fluent-bit fluent/fluent-bit -n logging
```

### Key Metrics to Monitor

- **PostgreSQL**
  - Connection count
  - Query latency
  - Transaction rollback rate
  - Disk space usage

- **PostgREST**
  - Request count
  - Response time
  - Error rate
  - Active connections

- **Kubernetes**
  - Pod CPU/Memory usage
  - Network I/O
  - PVC usage
  - Pod restart count

## 7. Network Policies

Restrict traffic between pods:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: odcs-network-policy
  namespace: odcs
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  - from:
    - podSelector:
        matchLabels:
          app: odcs-postgrest
  egress:
  - to:
    - podSelector: {}
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

## 8. RBAC Configuration

Create minimal role for service account:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: odcs-reader
  namespace: odcs
rules:
- apiGroups: [""]
  resources: ["pods", "pods/logs"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get"]
```

## 9. Security Hardening

### Pod Security Policy / Pod Security Standards

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'MustRunAs'
  supplementalGroups:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: false
```

## 10. Scaling Checklist for Production

- [ ] Set appropriate resource requests/limits
- [ ] Configure HorizontalPodAutoscaler for PostgREST
- [ ] Enable cluster autoscaling (if using managed K8s)
- [ ] Increase PostgreSQL `max_connections` if needed
- [ ] Configure connection pooling (PgBouncer/pgpool)
- [ ] Set up load balancing via Ingress
- [ ] Monitor and alert on resource usage
- [ ] Plan for backup and disaster recovery

## Before Going Live

1. **Test failover scenarios**
   - Kill a pod, verify automatic restart
   - Delete a node, verify pod rescheduling

2. **Load testing**
   ```bash
   # Example with Apache Bench
   ab -n 10000 -c 100 http://odcs.example.com/personen
   ```

3. **Backup verification**
   - Perform test restore from backup

4. **Disaster recovery plan**
   - Document RTO (Recovery Time Objective)
   - Document RPO (Recovery Point Objective)
   - Practice recovery procedures

5. **Documentation**
   - Document all custom configurations
   - Create runbooks for common operations
   - Document emergency contacts

## Useful Production Commands

```bash
# Check cluster health
kubectl get nodes
kubectl describe nodes

# Monitor pod logs
kubectl logs -n odcs -l app=odcs-postgrest -f --all-containers=true

# Scale deployment
kubectl scale deployment -n odcs odcs-postgrest --replicas=5

# Update image
kubectl set image -n odcs deployment/odcs-postgrest \
  postgrest=postgrest/postgrest:v11.0.0 --record

# Check resource usage
kubectl top nodes
kubectl top pods -n odcs --containers

# Export configuration
kubectl get all -n odcs -o yaml > backup.yaml

# Apply resource quotas
kubectl create quota odcs-quota --hard=requests.cpu=10,limits.memory=20Gi -n odcs
```

## Support & Resources

For issues, consult:
- Kubernetes documentation: https://kubernetes.io/docs/
- Helm best practices: https://helm.sh/docs/chart_best_practices/
- PostgreSQL performance tuning: https://wiki.postgresql.org/wiki/Performance_Optimization
- PostgREST docs: https://postgrest.org/

