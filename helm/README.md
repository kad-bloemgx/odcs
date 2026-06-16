# ODCS Helm Chart

Complete Kubernetes deployment for Open Data Contract Service (PostgreSQL + PostgREST + Swagger UI).

## Prerequisites

- Kubernetes 1.20+
- Helm 3.0+
- A storage class available in your cluster (default: `standard`)

## Installation

### 1. Add the chart to your Helm repository (if using a repo)

```bash
# If using a local chart:
helm install odcs ./helm -n default --create-namespace
```

### 2. Install with custom values

```bash
# Using custom values file
helm install odcs ./helm -f values-custom.yaml -n odcs --create-namespace

# Using inline values
helm install odcs ./helm \
  --set postgres.password=mySecurePassword \
  --set postgres.storage.size=20Gi \
  -n odcs --create-namespace
```

### 3. Verify installation

```bash
# Check pods
kubectl get pods -n odcs

# Check services
kubectl get svc -n odcs

# Check persistent volumes
kubectl get pvc -n odcs

# View logs
kubectl logs -n odcs -l app=odcs-postgres
kubectl logs -n odcs -l app=odcs-postgrest
kubectl logs -n odcs -l app=odcs-swagger
```

## Accessing the Services

### Inside the Cluster

- **PostgreSQL**: `odcs-postgres:5432`
- **PostgREST API**: `http://odcs-postgrest:3000`
- **Swagger UI**: `http://odcs-swagger:8080`
- **OpenAPI Server**: `http://odcs-openapi-server:80`

### Outside the Cluster (Port Forwarding)

```bash
# Forward PostgreSQL
kubectl port-forward -n odcs svc/odcs-postgres 5432:5432 &

# Forward PostgREST API
kubectl port-forward -n odcs svc/odcs-postgrest 3000:3000 &

# Forward Swagger UI
kubectl port-forward -n odcs svc/odcs-swagger 8080:8080 &

# Then access:
# - PostgreSQL: localhost:5432
# - API: http://localhost:3000
# - Swagger UI: http://localhost:8080
```

### Using Ingress (if enabled)

Enable ingress by modifying `values.yaml`:

```yaml
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: odcs.example.com
      paths:
        - path: /
          pathType: Prefix
```

Then install/upgrade:

```bash
helm upgrade odcs ./helm -n odcs
```

Access: `http://odcs.example.com`

## Configuration

### Common Configuration Options

Edit `values.yaml` or override during install:

```bash
helm install odcs ./helm \
  --set postgres.password=YOUR_PASSWORD \
  --set postgres.storage.size=20Gi \
  --set postgrest.image.tag=v11.0.0 \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=odcs.example.com \
  -n odcs --create-namespace
```

### Database Storage Class

```bash
helm install odcs ./helm \
  --set postgres.storage.storageClass=fast-ssd \
  -n odcs --create-namespace
```

### Resource Limits

Adjust resource requests/limits in `values.yaml`:

```yaml
postgres:
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "1000m"
```

## Usage

### Test the API

Once deployed, test the `/personen` endpoint:

```bash
# Get all personen
curl http://localhost:3000/personen

# Filter by id (using PostgREST syntax)
curl 'http://localhost:3000/personen?id=eq.123456'

# Filter by name (pattern matching)
curl 'http://localhost:3000/personen?naam=like.*Jan*'
```

### Use Swagger UI

Open `http://localhost:8080` in your browser to:
- Explore the API documentation
- Test endpoints interactively
- View request/response examples

## Upgrading the Chart

```bash
# Upgrade to new values
helm upgrade odcs ./helm -n odcs -f values-custom.yaml

# Rollback if needed
helm rollback odcs 1 -n odcs
```

## Uninstalling the Chart

```bash
# Delete the release (includes all resources)
helm uninstall odcs -n odcs

# Clean up the namespace if desired
kubectl delete namespace odcs
```

**Warning**: By default, the PersistentVolumeClaim will not be deleted. To delete it:

```bash
kubectl delete pvc -n odcs odcs-postgres-pvc-0
```

## Troubleshooting

### PostgreSQL not starting

```bash
# Check logs
kubectl logs -n odcs -l app=odcs-postgres -f

# Check PVC
kubectl get pvc -n odcs

# Verify storage class exists
kubectl get storageclass
```

### PostgREST can't connect to database

```bash
# Check PostgREST logs
kubectl logs -n odcs -l app=odcs-postgrest -f

# Test database connectivity from PostgREST pod
kubectl exec -it -n odcs deployment/odcs-postgrest -- sh
# Inside pod:
# psql -h odcs-postgres -U postgrest -d postgres
```

### Swagger UI not loading API spec

```bash
# Test if OpenAPI server is running
kubectl logs -n odcs -l app=odcs-openapi-server -f

# Verify service is accessible
kubectl exec -it -n odcs deployment/odcs-swagger -- sh
# curl http://odcs-openapi-server/openapi.yaml
```

### Can't access from outside cluster

1. Check Service type (should be ClusterIP for port-forward, LoadBalancer for external access)
2. Check Ingress configuration if enabled
3. Verify firewall/security group rules allow traffic
4. Use port-forward for testing: `kubectl port-forward -n odcs svc/odcs-swagger 8080:8080`

## Files Structure

```
helm/
├── Chart.yaml                 # Chart metadata
├── values.yaml                # Default configuration values
└── templates/
    ├── namespace.yaml
    ├── configmap-init-sql.yaml      # PostgreSQL init script
    ├── configmap-postgrest.yaml     # PostgREST configuration
    ├── configmap-openapi.yaml       # OpenAPI specification
    ├── pvc-postgres.yaml            # Persistent volume claim
    ├── statefulset-postgres.yaml    # PostgreSQL StatefulSet
    ├── deployment-postgrest.yaml    # PostgREST Deployment
    ├── deployment-swagger.yaml      # Swagger UI Deployment
    ├── deployment-openapi.yaml      # OpenAPI server Deployment
    ├── service-postgres.yaml        # PostgreSQL Service
    ├── service-postgrest.yaml       # PostgREST Service
    ├── service-swagger.yaml         # Swagger UI Service
    ├── service-openapi.yaml         # OpenAPI server Service
    └── ingress.yaml                 # Ingress configuration (optional)
```

## Best Practices for Production

1. **Secrets Management**: Use Kubernetes Secrets for passwords instead of storing in values.yaml:
   ```bash
   kubectl create secret generic odcs-db-credentials \
     --from-literal=postgres-password=YOUR_SECURE_PASSWORD \
     -n odcs
   ```

2. **Storage**: Use a production-grade StorageClass (e.g., `fast-ssd`, EBS, GCP Persistent Disk)

3. **Resource Limits**: Set appropriate CPU and memory limits

4. **High Availability**: Set `replicaCount: 2+` for PostgREST and Swagger UI (PostgreSQL should remain 1 with StatefulSet)

5. **Monitoring**: Enable ServiceMonitor for Prometheus integration if available

6. **Backup**: Implement PostgreSQL backup strategy for PersistentVolumes

7. **Security**: 
   - Use strong passwords
   - Enable TLS/SSL for Ingress
   - Use RBAC for Kubernetes access
   - Scan container images for vulnerabilities

## Support

For issues or questions, refer to:
- [PostgREST Documentation](https://postgrest.org)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Swagger UI Documentation](https://github.com/swagger-api/swagger-ui)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

