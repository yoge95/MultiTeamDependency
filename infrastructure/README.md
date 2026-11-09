# Infrastructure as Code

This directory contains Kubernetes manifests, Kustomize overlays, ArgoCD applications, and CI/CD pipelines for the Multi-team Knowledge Assistant.

## Directory Structure

```
infrastructure/
├── kubernetes/
│   ├── base/                           # Base Kubernetes manifests
│   │   ├── namespace.yaml             # Namespaces for runtime and admin
│   │   ├── configmap.yaml             # Shared configuration
│   │   ├── backend-deployment.yaml    # Backend deployment with resource limits
│   │   ├── backend-service.yaml       # Backend ClusterIP service
│   │   ├── frontend-deployment.yaml   # Frontend deployment with resource limits
│   │   ├── frontend-service.yaml      # Frontend ClusterIP service
│   │   ├── ingress.yaml               # Ingress with TLS configuration
│   │   └── kustomization.yaml         # Base kustomization
│   └── overlays/                       # Environment-specific overlays
│       ├── development/                # Development environment (1 replica, reduced resources)
│       ├── test/                       # Test environment (1 replica)
│       ├── staging/                    # Staging environment (2 replicas)
│       └── production/                 # Production environment (3 replicas, high availability)
├── argocd/                             # ArgoCD Application manifests
│   ├── application-development.yaml
│   ├── application-test.yaml
│   ├── application-staging.yaml
│   └── application-production.yaml
└── README.md                           # This file

.github/workflows/                      # GitHub Actions CI/CD workflows
├── ci.yml                              # Continuous Integration pipeline
├── cd-staging.yml                      # Staging deployment
└── cd-production.yml                   # Production deployment
```

## Environment Configuration

### Development
- **Namespace**: `knowledge-assistant-dev`
- **Replicas**: Backend 1, Frontend 1
- **Resources**: Minimal (100m CPU, 256Mi memory for backend)
- **Git Branch**: `develop`
- **Auto-sync**: Enabled with self-heal
- **Purpose**: Feature development and integration testing

### Test
- **Namespace**: `knowledge-assistant-test`
- **Replicas**: Backend 1, Frontend 1
- **Resources**: Standard (250m CPU, 512Mi memory for backend)
- **Git Branch**: `test`
- **Auto-sync**: Enabled, no self-heal
- **Purpose**: Automated testing and QA validation

### Staging
- **Namespace**: `knowledge-assistant-staging`
- **Replicas**: Backend 2, Frontend 2
- **Resources**: Production-like (250m CPU, 512Mi memory for backend)
- **Git Branch**: `main`
- **Auto-sync**: Disabled (manual approval)
- **Purpose**: Production rehearsal and release validation

### Production
- **Namespace**: `knowledge-assistant-production`
- **Replicas**: Backend 3, Frontend 3 (high availability)
- **Resources**: High (500m CPU, 1Gi memory for backend)
- **Git Tag**: Release tags (e.g., `v1.0.0`)
- **Auto-sync**: Disabled (manual approval with rollback protection)
- **Purpose**: Live production environment

## Base Manifests

### Backend Deployment
- **Image**: `knowledge-assistant-backend:latest`
- **Port**: 9000
- **Health Check**: `/api/v1/health`
- **Environment Variables**:
  - `DATABASE_URL` (from secret)
  - `SECRET_KEY` (from secret)
  - `AUTH_API_URL` (from configmap)
  - `USER_SERVICE_URL` (from configmap)
  - `CORS_ORIGINS` (from configmap)
  - `LOG_LEVEL`, `DEBUG`
- **Resource Limits**: CPU 1000m, Memory 2Gi (base)
- **Pod Anti-Affinity**: Spreads replicas across availability zones

### Frontend Deployment
- **Image**: `knowledge-assistant-frontend:latest`
- **Port**: 80 (nginx)
- **Health Check**: `/`
- **Environment Variables**:
  - `VITE_API_URL` (from configmap)
- **Resource Limits**: CPU 500m, Memory 512Mi (base)
- **Pod Anti-Affinity**: Spreads replicas across availability zones

### Ingress
- **TLS**: Enabled with cert-manager
- **Host**: `knowledge-assistant.example.com` (environment-specific)
- **Routes**:
  - `/api` → backend service (port 9000)
  - `/` → frontend service (port 80)

## CI/CD Pipelines

### CI Pipeline (.github/workflows/ci.yml)
Triggers on push to `main`, `develop`, `feature/**` branches and pull requests.

**Stages**:
1. **Backend Lint**: ruff code quality checks
2. **Backend Type Check**: mypy static type checking
3. **Backend Tests**: pytest with coverage reporting
4. **Backend Security**: bandit + pip-audit vulnerability scanning
5. **Frontend Lint**: ESLint code quality checks
6. **Frontend Type Check**: TypeScript compiler
7. **Frontend Tests**: Vitest with coverage reporting
8. **Frontend Security**: npm audit vulnerability scanning
9. **Build Docker Images**: Backend and frontend containers
10. **Validate Manifests**: kubectl dry-run for all overlays

**Quality Gates**:
- All lint and type checks must pass
- All tests must pass
- No critical security vulnerabilities allowed
- Manifest validation must succeed

### CD Staging Pipeline (.github/workflows/cd-staging.yml)
Triggers on push to `main` branch.

**Steps**:
1. Install ArgoCD CLI
2. Login to ArgoCD
3. Update application to sync from new commit SHA
4. Trigger sync with prune
5. Wait for application health (10 minute timeout)
6. Report deployment status

### CD Production Pipeline (.github/workflows/cd-production.yml)
Triggers on release tags (`v*`) or manual workflow dispatch.

**Steps**:
1. Validate tag format (vX.Y.Z)
2. Install ArgoCD CLI
3. Login to ArgoCD
4. Update application to sync from release tag
5. Trigger sync with prune
6. Wait for application health (15 minute timeout)
7. Run smoke tests (health check)
8. Rollback automatically on failure

## Deployment Instructions

### Prerequisites
- Kubernetes 1.28+ cluster
- kubectl configured with cluster access
- ArgoCD installed and configured
- Docker registry access for pushing images
- GitHub Actions secrets configured:
  - `ARGOCD_AUTH_TOKEN`: ArgoCD authentication token

### Manual Deployment with Kustomize

```bash
# Apply base manifests
cd infrastructure/kubernetes/base
kubectl apply -k .

# Apply environment-specific overlay
cd ../overlays/production
kubectl apply -k .
```

### GitOps Deployment with ArgoCD

```bash
# Apply ArgoCD Application for production
kubectl apply -f infrastructure/argocd/application-production.yaml

# Sync application
argocd app sync knowledge-assistant-production

# Check application status
argocd app get knowledge-assistant-production
```

### Local Testing with Kustomize

```bash
# Preview manifests without applying
cd infrastructure/kubernetes/overlays/development
kubectl kustomize .

# Validate manifests
kubectl apply --dry-run=client -k .
```

## Docker Image Build

### Backend Image
```bash
cd backend
docker build -t knowledge-assistant-backend:latest .
docker push your-registry/knowledge-assistant-backend:latest
```

### Frontend Image
```bash
cd frontend
docker build -t knowledge-assistant-frontend:latest .
docker push your-registry/knowledge-assistant-frontend:latest
```

## Secrets Management

Secrets are managed separately and must be created before deploying:

### Backend Secrets
```bash
kubectl create secret generic backend-secrets \
  --namespace=knowledge-assistant-runtime \
  --from-literal=database-url='postgresql://user:pass@host:5432/db' \
  --from-literal=secret-key='your-secret-key'
```

### Environment ConfigMaps
Created automatically by Kustomize overlays using `configMapGenerator`.

## Monitoring and Observability

- **Logs**: Application logs are sent to stdout/stderr and collected by cluster logging
- **Metrics**: Prometheus-compatible metrics exposed on `/metrics` endpoint
- **Health Checks**: Liveness and readiness probes configured for both services
- **Distributed Tracing**: OpenTelemetry instrumentation in application code

## High Availability

Production configuration ensures high availability through:
- **Multi-replica deployment**: 3 replicas for backend and frontend
- **Pod anti-affinity**: Spreads replicas across availability zones
- **Resource limits**: Prevents resource contention
- **Readiness probes**: Prevents traffic to unhealthy pods
- **Liveness probes**: Restarts unhealthy pods automatically
- **Horizontal Pod Autoscaling**: Can be added based on CPU/memory metrics

## Security

- **TLS**: All external traffic encrypted with TLS 1.2+
- **Non-root containers**: Both backend and frontend run as non-root users
- **Secret management**: Sensitive data stored in Kubernetes secrets
- **Network policies**: Can be added to restrict pod-to-pod communication
- **Security scanning**: Automated vulnerability scanning in CI pipeline
- **Image scanning**: Container images scanned before deployment

## Troubleshooting

### Check deployment status
```bash
kubectl get deployments -n knowledge-assistant-runtime
kubectl get pods -n knowledge-assistant-runtime
```

### View logs
```bash
kubectl logs -n knowledge-assistant-runtime deployment/backend
kubectl logs -n knowledge-assistant-runtime deployment/frontend
```

### Describe resources
```bash
kubectl describe deployment backend -n knowledge-assistant-runtime
kubectl describe pod <pod-name> -n knowledge-assistant-runtime
```

### Port forward for local testing
```bash
# Forward backend
kubectl port-forward -n knowledge-assistant-runtime deployment/backend 9000:9000

# Forward frontend
kubectl port-forward -n knowledge-assistant-runtime deployment/frontend 8080:80
```

### Restart deployment
```bash
kubectl rollout restart deployment/backend -n knowledge-assistant-runtime
kubectl rollout restart deployment/frontend -n knowledge-assistant-runtime
```

## Updating the Infrastructure

1. Make changes to base manifests or overlays
2. Test locally with `kubectl apply --dry-run=client -k .`
3. Commit changes to Git
4. Open pull request for review
5. CI pipeline validates changes
6. Merge to target branch
7. ArgoCD syncs changes automatically (dev/test) or on approval (staging/prod)

## Rollback Procedures

### ArgoCD Rollback
```bash
argocd app rollback knowledge-assistant-production
```

### Kubectl Rollback
```bash
kubectl rollout undo deployment/backend -n knowledge-assistant-production
kubectl rollout undo deployment/frontend -n knowledge-assistant-production
```

### Manual Rollback
1. Revert Git commit containing the problematic change
2. ArgoCD will sync to previous state
3. Or manually sync to previous commit SHA

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
