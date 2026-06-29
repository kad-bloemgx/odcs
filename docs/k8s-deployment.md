# ODCS Kubernetes Deployment Guide

This guide walks you through deploying ODCS (PostgreSQL + PostgREST + Swagger UI) to Kubernetes using Helm.

## Prerequisites

- **Kubernetes Cluster** (1.20+) - local or cloud-based
  - Minikube, Kind, or cloud provider K8s (AKS, EKS, GKE)
- **Helm** (3.0+) - [Install Helm](https://helm.sh/docs/intro/install/)
- **kubectl** - [Install kubectl](https://kubernetes.io/docs/tasks/tools/)
- **Storage Class** - at least one available (check with `kubectl get storageclass`)

## Quick Start (5 minutes)

### 1. Deploy using the quick start script

```bash
cd /path/to/odcs
bash helm/quickstart.sh odcs odcs
```

This will:
- Check prerequisites
- Lint the Helm chart
- Create the namespace
- Install the release

### 2. Wait for pods to be ready

```bash
kubectl get pods -n odcs -w
```

All pods should reach `Running` and `Ready 1/1` status.

### 3. Access the services via port forwarding

**Terminal 1 - Swagger UI:**
```bash
kubectl port-forward -n odcs svc/odcs-swagger 8080:8080
```
Then open: http://localhost:8080

**Terminal 2 - PostgREST API:**
```bash
kubectl port-forward -n odcs svc/odcs-postgrest 3000:3000
```

**Terminal 3 - PostgreSQL (optional):**
```bash
kubectl port-forward -n odcs svc/odcs-postgres 5432:5432
```

### 4. Test the API

```bash
# List all personen
curl http://localhost:3000/personen

# Get specific persoon
curl 'http://localhost:3000/personen?id=eq.123456'
```

## Detailed Deployment

### Option A: Using Docker Desktop Kubernetes

1. **Enable Kubernetes in Docker Desktop**
   - Settings → Kubernetes → Enable Kubernetes
   - Wait for cluster to start (~2 minutes)

2. **Deploy ODCS**
   ```bash
   cd /path/to/odcs
   helm install odcs ./helm -n odcs --create-namespace
   ```

3. **Verify installation**
   ```bash
   kubectl get all -n odcs
   ```

### Option B: Using Minikube

1. **Start Minikube**
   ```bash
   minikube start --cpus 4 --memory 4096
   ```

2. **Deploy ODCS**
   ```bash
   cd /path/to/odcs
   helm install odcs ./helm -n odcs --create-namespace
   ```

3. **Get the Minikube IP**
   ```bash
   minikube ip
   ```

4. **Access via Minikube service**
   ```bash
   minikube service -n odcs odcs-swagger
   ```

### Option C: Using Kind (Kubernetes in Docker)

1. **Create a Kind cluster**
   ```bash
   kind create cluster --name odcs --image kindest/node:v1.24.0
   ```

2. **Deploy ODCS**
   ```bash
   cd /path/to/odcs
   helm install odcs ./helm -n odcs --create-namespace
   ```

3. **Port forward to access**
   ```bash
   kubectl port-forward -n odcs svc/odcs-swagger 8080:8080 &
   kubectl port-forward -n odcs svc/odcs-postgrest 3000:3000 &
   ```

### Option D: Cloud Kubernetes (AKS, EKS, GKE)

1. **Connect to your cluster**
   ```bash
   # AKS example
   az aks get-credentials --resource-group myGroup --name myCluster
   
   # EKS example
   aws eks update-kubeconfig --name myCluster --region us-east-1
   
   # GKE example
   gcloud container clusters get-credentials myCluster --zone us-east1-b
   ```

2. **Deploy ODCS**
   ```bash
   cd /path/to/odcs
   helm install odcs ./helm -n odcs --create-namespace
   ```

3. **Create Ingress for external access**
   ```bash
   helm upgrade odcs ./helm -n odcs \
     --set ingress.enabled=true \
     --set ingress.hosts[0].host=odcs.example.com
   ```

4. **Get the external IP**
   ```bash
   kubectl get ingress -n odcs
   # Update your DNS to point odcs.example.com to the external IP
   ```

## Custom Configuration

### Change PostgreSQL password

```bash
helm install odcs ./helm -n odcs --create-namespace \
  --set postgres.password=YourSecurePassword123
```

### Use a specific PostgreSQL version

```bash
helm install odcs ./helm -n odcs --create-namespace \
  --set postgres.image.tag=14
```

### Increase storage size

```bash
helm install odcs ./helm -n odcs --create-namespace \
  --set postgres.storage.size=50Gi
```

### Use a custom storage class

```bash
helm install odcs ./helm -n odcs --create-namespace \
  --set postgres.storage.storageClass=fast-ssd
```

### Enable external access via Ingress

Create `values-prod.yaml`:

```yaml
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: odcs.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: odcs-tls
      hosts:
        - odcs.yourdomain.com
```

Deploy:

```bash
helm install odcs ./helm -n odcs --create-namespace -f values-prod.yaml
```

## Monitoring & Troubleshooting

### View logs

```bash
# PostgreSQL
kubectl logs -n odcs -l app=odcs-postgres -f

# PostgREST
kubectl logs -n odcs -l app=odcs-postgrest -f

# Swagger UI
kubectl logs -n odcs -l app=odcs-swagger -f

# OpenAPI Server
kubectl logs -n odcs -l app=odcs-openapi-server -f
```

### Check resource usage

```bash
kubectl top nodes
kubectl top pods -n odcs
```

### Connect to PostgreSQL pod

```bash
kubectl exec -it -n odcs statefulset/odcs-postgres -- psql -U postgres -d postgres
```

### Run a test query inside the cluster

```bash
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n odcs -- \
  curl http://odcs-postgrest:3000/personen
```

## Scaling

### Scale PostgREST replicas

```bash
kubectl scale deployment -n odcs odcs-postgrest --replicas=3
```

### Scale Swagger UI replicas

```bash
kubectl scale deployment -n odcs odcs-swagger --replicas=2
```

Note: PostgreSQL is a StatefulSet with 1 replica. Do not scale it.

## Upgrading

### Upgrade the Helm release

```bash
helm upgrade odcs ./helm -n odcs
```

### Rollback to previous version

```bash
# See history
helm history odcs -n odcs

# Rollback to previous revision
helm rollback odcs 1 -n odcs
```

## Uninstallation

### Delete the release

```bash
helm uninstall odcs -n odcs
```

### Delete the namespace

```bash
kubectl delete namespace odcs
```

### Delete the persistent volume (data loss!)

```bash
kubectl delete pvc -n odcs odcs-postgres-pvc-0
```

## Production Considerations

1. **Secrets Management**
   - Use Kubernetes Secrets for passwords
   - Use Sealed Secrets or External Secrets Operator for GitOps

2. **Resource Limits**
   - Set appropriate CPU/memory requests and limits
   - Monitor actual usage and adjust

3. **Networking**
   - Use Network Policies to restrict traffic
   - Enable TLS/SSL for all external traffic

4. **Storage**
   - Use production-grade storage class
   - Implement backup strategy for PostgreSQL

5. **Monitoring & Logging**
   - Integrate with Prometheus for metrics
   - Use ELK Stack or similar for logs
   - Set up alerts for critical metrics

6. **High Availability**
   - ReplicaSet > 1 for PostgREST
   - Multi-AZ storage for PostgreSQL
   - Load balancer for external traffic

7. **Security**
   - Use RBAC for Kubernetes access
   - Scan container images for vulnerabilities
   - Apply Pod Security Policies
   - Use Network Policies for traffic control

## Useful Commands

```bash
# Get all resources
kubectl get all -n odcs

# Get detailed resource info
kubectl describe pod -n odcs odcs-postgres-0

# Stream logs of multiple pods
kubectl logs -n odcs -l app=odcs-postgrest -f

# Execute command in pod
kubectl exec -n odcs pod/odcs-postgres-0 -- ls -la

# Port forward
kubectl port-forward -n odcs svc/odcs-postgrest 3000:3000

# Get service endpoints
kubectl get endpoints -n odcs

# Check persistent volumes
kubectl get pv
kubectl get pvc -n odcs

# Test DNS resolution inside cluster
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -n odcs -- \
  nslookup odcs-postgres.odcs.svc.cluster.local
```

## Support & Documentation

- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [PostgREST Documentation](https://postgrest.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Swagger UI Documentation](https://github.com/swagger-api/swagger-ui)

For issues specific to ODCS, see `helm/README.md`.

