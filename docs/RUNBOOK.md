# Operational Runbook

## Service Overview

The Multi-team Knowledge Assistant consists of two primary services:
- **Backend Service**: Python FastAPI application (port 9000)
- **Frontend Service**: React application served via Vite dev server (port 5173 in dev) or nginx (port 80 in production)

## Service Startup and Shutdown

### Local Development

#### Starting Services

```bash
cd /path/to/multiteamdependency

# Start entire stack (recommended)
./start.sh

# Services will start on:
# - Backend: http://localhost:9000
# - Frontend: http://localhost:5173
# - API Docs: http://localhost:9000/docs
```

The startup script automatically:
1. Checks prerequisites (Python 3.10+, Node.js 18+)
2. Detects available ports
3. Creates Python virtual environment
4. Installs dependencies
5. Runs database migrations
6. Seeds database with default credentials
7. Starts backend and frontend services
8. Displays service URLs and credentials

#### Stopping Services

```bash
cd /path/to/multiteamdependency

# Stop all services
./stop.sh
```

The shutdown script:
1. Reads PIDs from `.pids` file
2. Sends SIGTERM to each process
3. Cleans up PID file

### Production (Kubernetes)

#### Starting Services

```bash
# Check current status
kubectl get pods -n knowledge-assistant-prod

# If pods are stopped, scale up
kubectl scale deployment backend --replicas=3 -n knowledge-assistant-prod
kubectl scale deployment frontend --replicas=3 -n knowledge-assistant-prod

# Verify pods are running
kubectl get pods -n knowledge-assistant-prod -w
```

#### Stopping Services

```bash
# Scale down to zero (emergency stop)
kubectl scale deployment backend --replicas=0 -n knowledge-assistant-prod
kubectl scale deployment frontend --replicas=0 -n knowledge-assistant-prod

# Verify pods terminated
kubectl get pods -n knowledge-assistant-prod
```

#### Restarting Services

```bash
# Rolling restart (zero-downtime)
kubectl rollout restart deployment/backend -n knowledge-assistant-prod
kubectl rollout restart deployment/frontend -n knowledge-assistant-prod

# Monitor restart progress
kubectl rollout status deployment/backend -n knowledge-assistant-prod
kubectl rollout status deployment/frontend -n knowledge-assistant-prod
```

## Health Checks

### Backend Health

#### Local Development

```bash
# Basic health check
curl -s http://localhost:9000/api/v1/health

# Expected response:
# {"status":"healthy"}

# With verbose output
curl -v http://localhost:9000/api/v1/health

# Check if backend is listening
lsof -i :9000
```

#### Production

```bash
# Health check via ingress
curl -f https://knowledge-assistant.example.com/api/v1/health

# Health check directly to pod
kubectl exec -n knowledge-assistant-prod deployment/backend -- \
  curl -f http://localhost:9000/api/v1/health

# Check all backend pods
for pod in $(kubectl get pods -n knowledge-assistant-prod -l app=backend -o name); do
  echo "Checking $pod"
  kubectl exec -n knowledge-assistant-prod $pod -- curl -f http://localhost:9000/api/v1/health
done
```

### Frontend Health

#### Local Development

```bash
# Check frontend is serving
curl -s http://localhost:5173 | head -20

# Should see HTML with <div id="root">
```

#### Production

```bash
# Health check via ingress
curl -f https://knowledge-assistant.example.com/

# Check frontend pods
kubectl get pods -n knowledge-assistant-prod -l app=frontend
```

### Database Health

#### Local Development (SQLite)

```bash
# Check database file exists
ls -lh storage/app.db

# Check database size
du -h storage/app.db

# Query database
sqlite3 storage/app.db "SELECT COUNT(*) as stakeholder_count FROM stakeholder;"
```

#### Production (PostgreSQL)

```bash
# Connect to database via backend pod
kubectl exec -it -n knowledge-assistant-prod deployment/backend -- \
  psql $DATABASE_URL -c "SELECT version();"

# Check connection count
kubectl exec -it -n knowledge-assistant-prod deployment/backend -- \
  psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Check table sizes
kubectl exec -it -n knowledge-assistant-prod deployment/backend -- \
  psql $DATABASE_URL -c "
    SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
    FROM pg_tables 
    WHERE schemaname IN ('org', 'knowledge', 'interaction', 'governance', 'ops')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC 
    LIMIT 20;
  "
```

## Common Issues and Resolutions

### Authentication Failures

**Symptom**: Users see "401 Unauthorized" or "Invalid token" errors.

**Diagnosis**:
```bash
# Check backend logs for auth errors
kubectl logs -n knowledge-assistant-prod -l app=backend --tail=100 | grep -i "auth\|401"

# Check Auth API integration
kubectl exec -n knowledge-assistant-prod deployment/backend -- \
  curl -v $AUTH_API_URL/health

# Check circuit breaker status (look for "circuit breaker open" in logs)
kubectl logs -n knowledge-assistant-prod -l app=backend --tail=500 | grep -i "circuit"
```

**Resolution**:
1. **Auth API unavailable**: Circuit breaker will open. Check Auth API service status.
   ```bash
   # Check Auth API pods
   kubectl get pods -n auth-api-prod
   
   # If Auth API is down, backend will use cached access scopes
   # Wait for Auth API recovery or restart backend to retry
   ```

2. **Expired tokens**: Users need to re-login.
   ```bash
   # Clear frontend localStorage (user action)
   # Or reduce ACCESS_TOKEN_EXPIRE_MINUTES in backend config
   ```

3. **Redis cache unavailable**: Backend will fallback to Auth API for every request.
   ```bash
   # Check Redis connection
   kubectl exec -n knowledge-assistant-prod deployment/backend -- \
     redis-cli -u $REDIS_URL ping
   
   # Expected: PONG
   ```

**Escalation**: If Auth API circuit breaker remains open for >10 minutes, escalate to Auth API team.

### Database Connection Errors

**Symptom**: Backend returns "500 Internal Server Error" with "connection refused" or "no pg_hba.conf entry" in logs.

**Diagnosis**:
```bash
# Check backend logs
kubectl logs -n knowledge-assistant-prod -l app=backend --tail=100 | grep -i "database\|connection"

# Test database connection from backend pod
kubectl exec -it -n knowledge-assistant-prod deployment/backend -- \
  psql $DATABASE_URL -c "SELECT 1;"

# Check database secret exists
kubectl get secret db-credentials -n knowledge-assistant-prod

# Verify DATABASE_URL format
kubectl get secret db-credentials -n knowledge-assistant-prod -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

**Resolution**:
1. **Incorrect credentials**: Update db-credentials secret and restart backend.
   ```bash
   kubectl create secret generic db-credentials \
     --from-literal=DATABASE_URL="postgresql://correct-user:correct-pass@host:5432/db" \
     --namespace=knowledge-assistant-prod \
     --dry-run=client -o yaml | kubectl apply -f -
   
   kubectl rollout restart deployment/backend -n knowledge-assistant-prod
   ```

2. **Database server down**: Check RDS instance status in AWS console or contact DBA team.

3. **Connection pool exhausted**: Restart backend pods to reset connections.
   ```bash
   kubectl rollout restart deployment/backend -n knowledge-assistant-prod
   ```

4. **Network connectivity**: Check security groups and network policies.
   ```bash
   kubectl exec -it -n knowledge-assistant-prod deployment/backend -- \
     nc -zv <database-host> 5432
   ```

**Escalation**: If database is unreachable for >5 minutes, escalate to database operations team.

### Port Conflicts (Local Development)

**Symptom**: `start.sh` reports "Port 9000 in use" or backend fails to start with "Address already in use".

**Diagnosis**:
```bash
# Find process using port
lsof -ti:9000

# Get details about the process
lsof -i:9000

# Or on Linux
netstat -tulpn | grep 9000
```

**Resolution**:
1. **Kill conflicting process**:
   ```bash
   kill $(lsof -ti:9000)
   ```

2. **Use different port**:
   ```bash
   # Edit shared_config.json to use different port
   # Or let start.sh auto-detect (it will try 9001, 9002, etc.)
   ./start.sh
   ```

3. **Stop services properly**:
   ```bash
   # Always use stop.sh instead of Ctrl+C
   ./stop.sh
   ```

### High Memory Usage

**Symptom**: Backend pods restarting due to OOMKilled, or local backend process consuming excessive memory.

**Diagnosis**:
```bash
# Check pod memory usage (production)
kubectl top pods -n knowledge-assistant-prod

# Check memory limits
kubectl describe pod -n knowledge-assistant-prod -l app=backend | grep -A5 "Limits:"

# Check for memory leak indicators in logs
kubectl logs -n knowledge-assistant-prod -l app=backend --tail=500 | grep -i "memory\|oom"

# Local development - check process memory
ps aux | grep uvicorn
```

**Resolution**:
1. **Increase memory limits** (if legitimately needed):
   ```bash
   # Edit infrastructure/kubernetes/overlays/production/patches/backend-resources.yaml
   # Increase memory limits from 2Gi to 4Gi
   # Commit, push, and sync via ArgoCD
   ```

2. **Investigate memory leak**:
   ```bash
   # Enable memory profiling (dev environment)
   pip install memory-profiler
   python -m memory_profiler app/main.py
   ```

3. **Restart pods to free memory** (temporary fix):
   ```bash
   kubectl rollout restart deployment/backend -n knowledge-assistant-prod
   ```

**Escalation**: If memory usage grows unbounded, escalate to development team with memory profiling data.

### Frontend Not Loading

**Symptom**: Blank page, "Failed to fetch" errors, or 404 on frontend routes.

**Diagnosis**:
```bash
# Check frontend logs (production)
kubectl logs -n knowledge-assistant-prod -l app=frontend --tail=100

# Check ingress configuration
kubectl get ingress -n knowledge-assistant-prod -o yaml

# Test frontend directly (bypass ingress)
kubectl port-forward -n knowledge-assistant-prod deployment/frontend 8080:80
curl http://localhost:8080/

# Check if frontend can reach backend
kubectl exec -n knowledge-assistant-prod deployment/frontend -- \
  curl -f http://backend-service:9000/api/v1/health
```

**Resolution**:
1. **Frontend build failed**: Check frontend container logs for build errors.
   ```bash
   kubectl describe pod -n knowledge-assistant-prod -l app=frontend
   ```

2. **Incorrect VITE_API_URL**: Update frontend configmap and restart.
   ```bash
   kubectl get configmap -n knowledge-assistant-prod app-config -o yaml
   # Should contain VITE_API_URL pointing to backend
   ```

3. **CORS errors**: Check browser console, verify CORS_ORIGINS in backend includes frontend origin.
   ```bash
   # Check backend CORS configuration
   kubectl exec -n knowledge-assistant-prod deployment/backend -- \
     printenv CORS_ORIGINS
   ```

4. **React Router 404s on refresh**: Ensure nginx.conf has `try_files` fallback to index.html.

**Escalation**: If frontend consistently fails to load, escalate to frontend team with browser console logs.

### Slow Query Performance

**Symptom**: API requests taking >2 seconds, timeout errors, high database CPU.

**Diagnosis**:
```bash
# Check backend response times
kubectl logs -n knowledge-assistant-prod -l app=backend --tail=100 | grep "duration"

# Check database slow queries (PostgreSQL)
kubectl exec -it -n knowledge-assistant-prod deployment/backend -- \
  psql $DATABASE_URL -c "
    SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
    FROM pg_stat_activity 
    WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '2 seconds';
  "

# Check for missing indexes
kubectl exec -it -n knowledge-assistant-prod deployment/backend -- \
  psql $DATABASE_URL -c "
    SELECT schemaname, tablename, attname, n_distinct, correlation
    FROM pg_stats
    WHERE schemaname IN ('org', 'knowledge', 'interaction')
    AND n_distinct > 100
    ORDER BY abs(correlation) DESC
    LIMIT 20;
  "
```

**Resolution**:
1. **Add missing indexes**: Create migration to add index on frequently queried columns.
   ```python
   # In new Alembic migration
   op.create_index('idx_source_record_approval_state', 'source_record', ['approval_state'])
   ```

2. **Optimize query**: Review SQLAlchemy query, add `joinedload()` for eager loading.

3. **Scale database**: Increase RDS instance size (requires downtime, coordinate with DBA).

4. **Add caching**: Cache frequently accessed data in Redis.

**Escalation**: If slow queries persist, escalate to database team with query execution plans.

### Circuit Breaker Open

**Symptom**: Logs show "Circuit breaker open" for Auth API or User Service, degraded functionality.

**Diagnosis**:
```bash
# Check circuit breaker status in logs
kubectl logs -n knowledge-assistant-prod -l app=backend --tail=500 | grep -i "circuit"

# Check external service health
kubectl exec -n knowledge-assistant-prod deployment/backend -- \
  curl -v $AUTH_API_URL/health

kubectl exec -n knowledge-assistant-prod deployment/backend -- \
  curl -v $USER_SERVICE_URL/health

# Check circuit breaker configuration (5 failures, 30s timeout)
grep -r "CircuitBreaker" backend/app/integrations/
```

**Resolution**:
1. **Auth API circuit breaker open**:
   - Backend will use cached access scopes (15-minute TTL)
   - Users with cached scopes can continue working
   - New logins may fail
   - Wait for Auth API recovery (circuit breaker will auto-recover after 30s)

2. **User Service circuit breaker open**:
   - Backend will use minimal scope from token
   - User profile enrichment unavailable
   - Core functionality continues
   - Wait for User Service recovery

3. **Manual circuit breaker reset**: Restart backend pods (circuit breaker state is in-memory).
   ```bash
   kubectl rollout restart deployment/backend -n knowledge-assistant-prod
   ```

**Escalation**: If circuit breaker remains open >10 minutes, escalate to owning service team (Auth API or User Service).

## Log Locations

### Local Development

**Backend logs**:
```bash
# Stdout (if started with ./start.sh or uvicorn directly)
# No file logging in development

# View backend logs
tail -f backend/logs/app.log  # If file logging enabled
```

**Frontend logs**:
```bash
# Vite dev server stdout
# Browser console (F12 → Console tab)
```

**Database logs**:
```bash
# SQLite has no separate log file
# Query errors appear in backend logs
```

### Production (Kubernetes)

**Backend logs**:
```bash
# Recent logs
kubectl logs -n knowledge-assistant-prod -l app=backend --tail=100

# Follow logs (real-time)
kubectl logs -n knowledge-assistant-prod -l app=backend -f

# Logs from specific pod
kubectl logs -n knowledge-assistant-prod <pod-name>

# Previous container logs (if pod restarted)
kubectl logs -n knowledge-assistant-prod <pod-name> --previous

# All backend pods
kubectl logs -n knowledge-assistant-prod -l app=backend --all-containers=true
```

**Frontend logs**:
```bash
# Frontend container logs (nginx access logs)
kubectl logs -n knowledge-assistant-prod -l app=frontend --tail=100

# Follow logs
kubectl logs -n knowledge-assistant-prod -l app=frontend -f
```

**CloudWatch Logs** (if configured):
- Log Group: `/aws/kubernetes/knowledge-assistant-prod`
- Backend stream: `backend-{pod-name}`
- Frontend stream: `frontend-{pod-name}`

**Access via AWS Console**:
1. Navigate to CloudWatch → Log Groups
2. Select `/aws/kubernetes/knowledge-assistant-prod`
3. Filter by pod name or search for specific errors

## Monitoring and Alerts

### Key Metrics to Monitor

**Application Health**:
- Health endpoint response time (target: <100ms)
- Error rate (target: <1%)
- Request throughput (baseline varies by usage)

**System Resources**:
- CPU usage (alert: >80% sustained for 5 min)
- Memory usage (alert: >85% sustained for 5 min)
- Disk usage (alert: >90%)

**Business Metrics**:
- Question submission rate
- Answer success rate (target: >95%)
- Average confidence score (target: >0.70)
- Citation coverage percentage (target: >90%)

### Grafana Dashboards

Production dashboards available at: https://grafana.example.com

**Key Dashboards**:
1. **Knowledge Assistant - Application Health**
   - Request rate, error rate, latency percentiles
   - Health check status
   - API endpoint performance

2. **Knowledge Assistant - Infrastructure**
   - CPU, memory, disk usage per pod
   - Network I/O
   - Container restart count

3. **Knowledge Assistant - Business Metrics**
   - Questions per hour
   - Answer confidence distribution
   - Feedback sentiment
   - Source freshness warnings

### CloudWatch Alarms

Critical alarms (PagerDuty integration):
- `HighErrorRate` - Error rate >5% for 5 minutes
- `HighLatency` - P95 latency >500ms for 5 minutes
- `PodCrashLooping` - Any pod crash-looping
- `DatabaseConnectionFailure` - DB connection failures

Warning alarms (email only):
- `ElevatedLatency` - P95 latency >300ms for 10 minutes
- `HighMemoryUsage` - Memory >80% for 10 minutes
- `LowConfidenceRate` - >30% low-confidence answers for 15 minutes

## Escalation Paths

### On-Call Rotation

Primary on-call: Check PagerDuty schedule
Secondary on-call: Check PagerDuty schedule

### Escalation Contacts

| Issue Type | Team | Contact | Response SLA |
|------------|------|---------|--------------|
| Backend application errors | Platform Engineering | #team-platform-eng | 30 min |
| Frontend issues | Frontend Team | #team-frontend | 30 min |
| Database issues | Database Operations | #team-dba | 15 min |
| Auth API failures | Auth Team | #team-auth | 15 min |
| Infrastructure/Kubernetes | Cloud Operations | #team-cloud-ops | 15 min |
| Security incidents | Security Team | #team-security | Immediate |

### Escalation Procedure

1. **Acknowledge alert** in PagerDuty
2. **Triage** using this runbook
3. **Attempt resolution** using documented procedures
4. **Escalate if**:
   - Issue persists >15 minutes
   - Root cause unclear
   - Requires permissions you don't have
   - Involves external dependencies
5. **Document** incident in incident management system
6. **Post-mortem** for severity 1-2 incidents

### Emergency Contacts

- **Severity 1 (service down)**: Page on-call engineer immediately via PagerDuty
- **Severity 2 (degraded)**: Post in #team-platform-eng, tag @oncall
- **Severity 3 (minor)**: Create ticket, post in #team-platform-eng
- **Security incident**: Page security on-call + post in #security-incidents

## Backup and Recovery

### Database Backups

**Automated backups** (production):
- Daily automated RDS snapshots (35-day retention)
- Transaction logs backed up every 5 minutes
- Point-in-time recovery available for last 35 days

**Manual backup**:
```bash
# Create manual snapshot via backend pod
kubectl exec -n knowledge-assistant-prod deployment/backend -- \
  pg_dump $DATABASE_URL | gzip > backup-$(date +%Y%m%d-%H%M%S).sql.gz

# Upload to S3
aws s3 cp backup-*.sql.gz s3://knowledge-assistant-backups/manual/
```

**Restore from backup**:
See DEPLOYMENT.md "Disaster Recovery" section.

### Configuration Backups

All configuration is in Git:
- Kubernetes manifests: `infrastructure/kubernetes/`
- ArgoCD applications: `infrastructure/argocd/`
- Application code: Full Git history

To restore configuration:
```bash
git checkout <commit-hash>
argocd app sync knowledge-assistant-prod
```

## Maintenance Windows

### Scheduled Maintenance

Production maintenance windows:
- **When**: Tuesday-Thursday, 10am-2pm PT
- **Frequency**: As needed (typically bi-weekly for releases)
- **Notification**: 48 hours advance notice to #announcements
- **Expected downtime**: <5 minutes for rolling updates

### Pre-Maintenance Checklist

- [ ] Announce maintenance window 48 hours in advance
- [ ] Verify staging environment matches production
- [ ] Test upgrade procedure in staging
- [ ] Prepare rollback plan
- [ ] Identify on-call engineer
- [ ] Schedule maintenance window in PagerDuty (suppress non-critical alerts)

### During Maintenance

1. Post start notification in #announcements
2. Execute deployment procedure (see DEPLOYMENT.md)
3. Monitor metrics and logs for 30 minutes
4. Run smoke tests
5. Post completion notification

### Post-Maintenance

- [ ] Verify all health checks passing
- [ ] Check error rates returned to baseline
- [ ] Review monitoring dashboards
- [ ] Close maintenance ticket
- [ ] Document any issues encountered

---

**Document Version**: 1.0  
**Last Updated**: 2026-08-25  
**Maintained By**: Operations Team  
**On-Call Schedule**: https://pagerduty.example.com/schedules/knowledge-assistant
