# Kubernetes Deployment

Deploy the Board Game Night Planner to Kubernetes with an **external PostgreSQL** database.

## Prerequisites

- `kubectl` configured for your cluster
- Docker image built and pushed to your registry (see DEVELOPMENT_PLAN 3.1)
- External PostgreSQL database (URL and credentials)

## Setup

### 1. Create the secret with your database URL

```bash
kubectl create secret generic cal-db-secret \
  --from-literal=DATABASE_URL='postgresql://user:password@your-db-host:5432/cal' \
  -n cal
```

Or edit `secret.yaml`, replace the placeholder, then:

```bash
kubectl apply -f secret.yaml
```

### 2. Update the deployment image

Edit `deployment.yaml` and replace `your-registry/cal:latest` with your actual image (e.g. `ghcr.io/your-org/cal:latest`).

### 3. Apply all manifests

```bash
kubectl apply -f k8s/
```

Or apply individually:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml   # optional, for external access
```

### 4. Access the app

- **ClusterIP (default)**: Use port-forward: `kubectl port-forward svc/cal-app 8501:8501 -n cal`
- **Ingress**: If you applied `ingress.yaml`, access via the configured host (requires ingress controller)
- **LoadBalancer**: Change `service.yaml` to `type: LoadBalancer` for a cloud load balancer

## Migrations

Migrations run automatically on container startup (`alembic upgrade head` in the Dockerfile).
