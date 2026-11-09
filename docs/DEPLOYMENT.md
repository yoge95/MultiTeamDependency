# Deployment Guide

## Overview

This document describes deployment procedures for the Multi-team Knowledge Assistant across development, test, staging, and production environments using GitOps practices with ArgoCD.

## Environment Topology

### Development Environment
- **Purpose**: Feature development and rapid iteration
- **Data**: Synthetic/scrubbed test data
- **Deployment**: Continuous deployment from approved development branches
- **Namespace**: `knowledge-assistant-dev`
- **Sync Policy**: Auto-sync enabled with self-heal
- **Access**: Developer SSH access for debugging

### Test Environment
- **Purpose**: Functional, integration, security, and performance verification
- **Data**: Synthetic/masked non-production data
- **Deployment**: Automated promotion after CI gates (lint, type-check, test, security scan)
- **Namespace**: `knowledge-assistant-test`
- **Sync Policy**: Auto-sync enabled, no self-heal
- **Access**: QA team and automated test runners

### Staging Environment
- **Purpose**: Production-like rehearsal with masked data
- **Data**: Production-like masked data (real structure, scrubbed PII)
- **Deployment**: GitOps promotion from tested release candidate manifests
- **Namespace**: `knowledge-assistant-staging`
- **Sync Policy**: Manual sync (no auto-sync)
- **Access**: Operations team and release managers
- **Stability Target**: High stability during release windows

### Production Environment
- **Purpose**: Live operations serving internal users
- **Data**: Real production data with full security controls
- **Deployment**: Controlled ArgoCD sync from approved mainline manifests
- **Namespace**: `knowledge-assistant-prod`
- **Cluster**: prod-k8s-cluster-us-west (AWS us-west-2, multi-AZ)
- **Sync Policy**: Manual sync with rollback protection
- **Availability Target**: 99.9%+ monthly during business hours
- **Access**: Restricted to operations team, no direct developer access

## Prerequisites

### Required Tools
- `kubectl` 1.28+ configured for target cluster
- `argocd` CLI 2.8+ for GitOps operations
- `git` for repository access
- `docker` for local image builds (optional)
- `kustomize` 5.0+ for manifest customization

### Required Access
- Git repository read access (all environments)
- Git repository write access (for promoting changes)
- Kubernetes cluster access (environment-specific RBAC)
- ArgoCD UI/API access with environment-specific permissions
- AWS credentials for ECR image registry (production only)

### Required Secrets (Per Environment)

Create Kubernetes secrets before first deployment:

```bash
# Database credentials
kubectl create secret generic db-credentials \
  --from-literal=DATABASE_URL="postgresql://user:password@postgres-host:5432/knowledge_assistant" \
  --namespace=knowledge-assistant-<env>

# Application secrets
kubectl create secret generic app-secrets \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=AUTH_API_URL="http://auth-api:8080" \
  --from-literal=USER_SERVICE_URL="http://user-service:8081" \
  --namespace=knowledge-assistant-<env>

# Redis connection
kubectl create secret generic redis-credentials \
  --from-literal=REDIS_URL="redis://redis-service:6379/0" \
  --namespace=knowledge-assistant-<env>

# OpenSearch credentials (production)
kubectl create secret generic opensearch-credentials \
  --from-literal=OPENSEARCH_HOST="opensearch-cluster.example.com" \
  --from-literal=OPENSEARCH_PORT="9200" \
  --from-literal=OPENSEARCH_USER="app_user" \
  --from-literal=OPENSEARCH_PASSWORD="$(openssl rand -base64 24)" \
  --namespace=knowledge-assistant-prod

# Neo4j credentials (production)
kubectl create secret generic neo4j-credentials \
  --from-literal=NEO4J_URI="bolt://neo4j-cluster:7687" \
  --from-literal=NEO4J_USER="app_user" \
  --from-literal=NEO4J_PASSWORD="$(openssl rand -base64 24)" \
  --namespace=knowledge-assistant-prod
```

## Deployment Procedures

### Development Environment Deployment

Development deployments trigger automatically on push to `develop` branch:

```bash
# Verify current development state
argocd app get knowledge-assistant-dev

# Manual sync (if auto-sync disabled)
argocd app sync knowledge-assistant-dev

# View sync progress
argocd app wait knowledge-assistant-dev --timeout 300

# Check deployed pods
kubectl get pods -n knowledge-assistant-dev
```

### Test Environment Deployment

Test deployments trigger automatically after CI pipeline passes on `main` branch:

```bash
# Verify CI pipeline passed
gh run list --workflow=ci.yml --branch=main --limit=1

# Check ArgoCD application status
argocd app get knowledge-assistant-test

# Wait for sync completion
argocd app wait knowledge-assistant-test --timeout 600

# Verify deployment health
kubectl get all -n knowledge-assistant-test
kubectl describe deployment backend -n knowledge-assistant-test
kubectl describe deployment frontend -n knowledge-assistant-test

# Check application logs
kubectl logs -n knowledge-assistant-test -l app=backend --tail=100
kubectl logs -n knowledge-assistant-test -l app=frontend --tail=100
```

### Staging Environment Deployment

Staging requires manual promotion from test:

```bash
# 1. Verify test environment is stable
argocd app get knowledge-assistant-test
kubectl get pods -n knowledge-assistant-test --no-headers | grep -v "Running\|Completed"

# 2. Tag release candidate
git checkout main
git pull origin main
git tag -a v1.2.0-rc1 -m "Release candidate 1.2.0"
git push origin v1.2.0-rc1

# 3. Update staging ArgoCD application to use RC tag
argocd app set knowledge-assistant-staging --revision v1.2.0-rc1

# 4. Sync staging environment
argocd app sync knowledge-assistant-staging

# 5. Wait for sync and health checks
argocd app wait knowledge-assistant-staging --timeout 900 --health

# 6. Verify staging deployment
kubectl get pods -n knowledge-assistant-staging
kubectl get ingress -n knowledge-assistant-staging

# 7. Run smoke tests
curl -f https://staging.knowledge-assistant.example.com/api/v1/health
# (Full staging verification in RUNBOOK.md)

# 8. Monitor for 1 hour before production promotion
kubectl logs -n knowledge-assistant-staging -l app=backend --tail=100 -f
```

### Production Environment Deployment

Production deployments require formal approval and controlled rollout:

#### Pre-Deployment Checklist

- [ ] Staging verification completed (minimum 1 hour stable)
- [ ] Release notes reviewed and approved
- [ ] Rollback plan documented
- [ ] Maintenance window scheduled (if required)
- [ ] On-call engineer identified
- [ ] Stakeholders notified

#### Production Deployment Steps

```bash
# 1. Verify staging is healthy
argocd app get knowledge-assistant-staging --show-operation

# 2. Create production release tag
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Release 1.2.0 - Description of changes"
git push origin v1.2.0

# 3. Update production ArgoCD application
argocd app set knowledge-assistant-prod --revision v1.2.0

# 4. Sync production (manual, no auto-sync)
argocd app sync knowledge-assistant-prod --prune

# 5. Monitor sync progress
argocd app wait knowledge-assistant-prod --timeout 900 --health

# 6. Verify pod rollout
kubectl rollout status deployment/backend -n knowledge-assistant-prod
kubectl rollout status deployment/frontend -n knowledge-assistant-prod

# 7. Check pod health
kubectl get pods -n knowledge-assistant-prod
kubectl describe pods -n knowledge-assistant-prod -l app=backend
kubectl describe pods -n knowledge-assistant-prod -l app=frontend

# 8. Verify ingress and service
kubectl get ingress -n knowledge-assistant-prod
kubectl get svc -n knowledge-assistant-prod

# 9. Run production smoke tests
curl -f https://knowledge-assistant.example.com/api/v1/health
# (Full production verification in RUNBOOK.md)

# 10. Monitor application metrics
# - Check Grafana dashboards for latency, error rate, throughput
# - Verify CloudWatch logs for errors
# - Monitor user-facing health indicators

# 11. Monitor for 30 minutes post-deployment
kubectl logs -n knowledge-assistant-prod -l app=backend --tail=500 -f
```

#### Post-Deployment Verification

Wait 30 minutes, then verify:
- Health endpoint returns 200 OK
- User login succeeds
- Question submission and answer retrieval work end-to-end
- No elevated error rates in CloudWatch
- Grafana dashboards show normal latency and throughput
- No alerts firing in monitoring system

## Rollback Procedures

### Staging/Production Rollback

If critical issues detected post-deployment:

```bash
# 1. Identify previous stable version
argocd app history knowledge-assistant-prod

# 2. Rollback to previous revision
argocd app rollback knowledge-assistant-prod <REVISION_NUMBER>

# OR rollback to specific tag
argocd app set knowledge-assistant-prod --revision v1.1.9
argocd app sync knowledge-assistant-prod

# 3. Verify rollback completion
argocd app wait knowledge-assistant-prod --timeout 600 --health
kubectl rollout status deployment/backend -n knowledge-assistant-prod
kubectl rollout status deployment/frontend -n knowledge-assistant-prod

# 4. Verify service restoration
curl -f https://knowledge-assistant.example.com/api/v1/health

# 5. Notify stakeholders of rollback
# Document rollback reason and create incident ticket
```

### Database Migration Rollback

If deployment includes database migrations:

```bash
# 1. Connect to backend pod
kubectl exec -it -n knowledge-assistant-prod deployment/backend -- /bin/bash

# 2. Check current migration version
alembic current

# 3. Rollback migration (if safe)
alembic downgrade -1

# 4. Verify database state
alembic current
psql $DATABASE_URL -c "SELECT version_num FROM alembic_version;"

# 5. Exit pod and rollback application
exit
argocd app rollback knowledge-assistant-prod <REVISION_NUMBER>
```

**WARNING**: Not all migrations are reversible. Review migration scripts before rollback.

### Emergency Rollback (Circuit Breaker)

If severe production impact detected:

```bash
# Immediate scale-down to stop traffic
kubectl scale deployment backend --replicas=0 -n knowledge-assistant-prod
kubectl scale deployment frontend --replicas=0 -n knowledge-assistant-prod

# Rollback to last known good version
argocd app set knowledge-assistant-prod --revision v1.1.9
argocd app sync knowledge-assistant-prod

# Scale back up
kubectl scale deployment backend --replicas=3 -n knowledge-assistant-prod
kubectl scale deployment frontend --replicas=3 -n knowledge-assistant-prod

# Monitor recovery
kubectl get pods -n knowledge-assistant-prod -w
```

## Configuration Management

### Environment-Specific Configuration

Configuration managed via Kustomize overlays:

```
infrastructure/kubernetes/
├── base/                    # Base manifests
│   ├── namespace.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── kustomization.yaml
└── overlays/
    ├── development/         # Dev overrides
    │   ├── kustomization.yaml
    │   └── patches/
    ├── test/                # Test overrides
    │   ├── kustomization.yaml
    │   └── patches/
    ├── staging/             # Staging overrides
    │   ├── kustomization.yaml
    │   └── patches/
    └── production/          # Prod overrides
        ├── kustomization.yaml
        └── patches/
```

### Updating Configuration

```bash
# 1. Edit configuration in Git repository
vim infrastructure/kubernetes/overlays/production/patches/backend-env.yaml

# 2. Validate changes locally
kustomize build infrastructure/kubernetes/overlays/production

# 3. Commit and push
git add infrastructure/
git commit -m "Update production backend environment variables"
git push origin main

# 4. Sync ArgoCD
argocd app sync knowledge-assistant-prod

# 5. Verify configuration applied
kubectl get configmap -n knowledge-assistant-prod -o yaml
kubectl describe deployment backend -n knowledge-assistant-prod
```

## Secrets Management

### Rotating Secrets

Secrets should be rotated quarterly (minimum) or immediately if compromised:

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# 2. Update secret in Kubernetes
kubectl create secret generic app-secrets \
  --from-literal=SECRET_KEY="$NEW_SECRET" \
  --namespace=knowledge-assistant-prod \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart pods to pick up new secret
kubectl rollout restart deployment/backend -n knowledge-assistant-prod

# 4. Verify pods restarted successfully
kubectl rollout status deployment/backend -n knowledge-assistant-prod

# 5. Document secret rotation in audit log
echo "$(date): Rotated SECRET_KEY in production" >> secrets-audit.log
```

### Secret Backup

**CRITICAL**: Secrets are not stored in Git. Back up secrets to secure vault:

```bash
# Export secrets to secure location (encrypted)
kubectl get secret -n knowledge-assistant-prod -o yaml > secrets-backup.yaml
gpg --encrypt --recipient ops-team@example.com secrets-backup.yaml
mv secrets-backup.yaml.gpg /secure/vault/knowledge-assistant-prod-secrets-$(date +%Y%m%d).yaml.gpg
rm secrets-backup.yaml
```

## Monitoring Post-Deployment

### Key Metrics to Monitor

**Application Health**:
- Health endpoint response time (<100ms target)
- Error rate (<1% target)
- Request throughput (establish baseline)

**Resource Utilization**:
- CPU usage (<70% sustained)
- Memory usage (<80% sustained)
- Pod restart count (0 restarts)

**Business Metrics**:
- Question submission rate
- Answer success rate
- Average confidence score
- Citation coverage percentage

### CloudWatch Alarms

Monitor these CloudWatch alarms post-deployment:
- `HighErrorRate` - backend error rate >5% for 5 minutes
- `HighLatency` - P95 latency >500ms for 5 minutes
- `PodCrashLooping` - any pod crash-looping
- `DatabaseConnectionFailure` - DB connection failures
- `LowConfidenceRate` - >30% low-confidence answers for 15 minutes

### Grafana Dashboards

Review these dashboards post-deployment:
- `Knowledge Assistant - Application Health`
- `Knowledge Assistant - Request Latency`
- `Knowledge Assistant - Business Metrics`
- `Knowledge Assistant - Infrastructure`

## Disaster Recovery

### Database Backup

Automated daily backups via AWS RDS:
- Daily automated snapshots (35-day retention)
- Transaction log backup every 5 minutes
- Point-in-time recovery available

### Manual Backup (if needed)

```bash
# Create manual database snapshot
kubectl exec -n knowledge-assistant-prod deployment/backend -- \
  pg_dump $DATABASE_URL > backup-$(date +%Y%m%d-%H%M%S).sql

# Upload to S3
aws s3 cp backup-*.sql s3://knowledge-assistant-backups/manual/
```

### Restore from Backup

```bash
# 1. Scale down application
kubectl scale deployment backend --replicas=0 -n knowledge-assistant-prod

# 2. Restore database from snapshot
# (Use AWS RDS console or CLI to restore snapshot)

# 3. Update DATABASE_URL secret to point to restored database
kubectl create secret generic db-credentials \
  --from-literal=DATABASE_URL="postgresql://user:password@restored-host:5432/knowledge_assistant" \
  --namespace=knowledge-assistant-prod \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Scale application back up
kubectl scale deployment backend --replicas=3 -n knowledge-assistant-prod

# 5. Verify data integrity
kubectl exec -n knowledge-assistant-prod deployment/backend -- \
  python -c "from app.database import SessionLocal; from app.models.org import Stakeholder; db = SessionLocal(); print(f'Stakeholders: {db.query(Stakeholder).count()}'); db.close()"
```

## GitOps Workflow

### Standard Development Flow

```
Developer → Feature branch → PR → Code review → Merge to develop
  → CI pipeline (lint, test, build) → Auto-deploy to development
  → QA verification → Merge to main → Auto-deploy to test
  → Test verification → Tag release candidate → Manual deploy to staging
  → Staging soak test (1+ hour) → Tag release → Manual deploy to production
  → Production monitoring → Success or rollback
```

### Hotfix Flow

```
Incident detected → Create hotfix branch from production tag
  → Implement fix → Emergency PR review → Merge to main
  → Tag hotfix release (e.g., v1.2.1) → Deploy to staging
  → Expedited staging verification (30 min minimum) → Deploy to production
  → Monitor production → Backport fix to develop
```

## Compliance & Audit

### Deployment Audit Trail

All deployments are auditable via:
- Git commit history with signed commits
- ArgoCD deployment history (retained 90 days)
- Kubernetes audit logs (retained 365 days)
- CloudWatch deployment events (retained 90 days)

### Required Approvals

| Environment | Required Approvals | Review Time |
|-------------|-------------------|-------------|
| Development | None (auto-deploy) | N/A |
| Test | CI pipeline pass | Automated |
| Staging | Release manager | 1 business day |
| Production | Release manager + Operations lead | 2 business days |

### Change Windows

| Environment | Change Window | Freeze Periods |
|-------------|---------------|----------------|
| Development | 24/7 | None |
| Test | Business hours | None |
| Staging | Business hours | Week before major release |
| Production | Tuesday-Thursday, 10am-2pm PT | End-of-quarter, major holidays |

---

**Document Version**: 1.0  
**Last Updated**: 2026-08-25  
**Maintained By**: Operations Team
