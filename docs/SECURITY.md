# Security Documentation

## Security Overview

The Multi-team Knowledge Assistant handles internal organizational knowledge with varying sensitivity levels (public, internal, confidential, restricted). This document outlines security policies, controls, and procedures.

## Security Architecture

### Defense in Depth

Multiple security layers protect the application:

1. **Network Layer**: VPC segmentation, security groups, network policies
2. **Transport Layer**: TLS 1.3 for all traffic, mutual TLS for service-to-service
3. **Application Layer**: OAuth 2.1 authentication, role-based authorization, input validation
4. **Data Layer**: Encryption at rest, column-level access control, audit logging
5. **Infrastructure Layer**: Pod security policies, secrets management, container scanning

### Trust Boundaries

```
Internet → Ingress (TLS termination) → Application Pods → Database/Cache
         └─> CloudFlare WAF           └─> mTLS           └─> Encrypted at rest
```

**External Trust Boundary**: Internet-facing ingress with TLS, rate limiting, WAF
**Internal Trust Boundary**: Service-to-service mTLS, network policies
**Data Trust Boundary**: Encrypted database connections, access control filtering

## Authentication and Authorization

### Authentication Flow

1. **User initiates login** via frontend (email + password)
2. **Frontend sends credentials** to backend POST `/api/v1/auth/login`
3. **Backend validates** via Auth API OAuth 2.1 integration
4. **Auth API returns JWT** with user_id, roles, access scope
5. **Backend caches access scope** in Redis (15-minute TTL)
6. **Frontend stores token** in localStorage
7. **All subsequent requests** include `Authorization: Bearer {token}` header
8. **Backend validates token** on every protected endpoint

### Authorization Model

**Four Roles**:
- `end_user`: Read access to public and internal sources
- `knowledge_steward`: Read/write access to confidential sources, source governance
- `governance_reviewer`: Read access to all sources, audit access
- `platform_administrator`: Full access including privileged actions

**Access Levels by Role**:

| Access Tag | end_user | knowledge_steward | governance_reviewer | platform_administrator |
|------------|----------|-------------------|---------------------|------------------------|
| public     | ✓        | ✓                 | ✓                   | ✓                      |
| internal   | ✓        | ✓                 | ✓                   | ✓                      |
| confidential | ✗      | ✓                 | ✓                   | ✓                      |
| restricted | ✗        | ✗                 | ✓                   | ✓                      |

**Domain-Based Filtering**:
- Knowledge stewards see only sources in their assigned domains
- End users filtered by domain context from access scope
- Platform admins see all domains

**Source-Scope Restrictions**:
- Exclusion lists: specific sources blocked for user/role
- Whitelist-only mode: only explicitly allowed sources visible

### Token Management

**Token Lifecycle**:
- **Expiry**: 60 minutes (configurable via ACCESS_TOKEN_EXPIRE_MINUTES)
- **Refresh**: Not implemented (user must re-login after expiry)
- **Revocation**: Clear token from localStorage, invalidate in Auth API
- **Storage**: Browser localStorage (frontend), Redis cache (backend access scope)

**Token Security**:
- JWT signed with HS256 algorithm
- SECRET_KEY rotation quarterly (documented procedure)
- No infinite-lived tokens (expiry required)
- Token includes: user_id, roles, issued_at, expires_at

### Session Security

**Session Management**:
- Sessions stored in PostgreSQL, not in-memory
- Session timeout: 24 hours of inactivity
- Concurrent sessions: Allowed (multiple browsers/devices)
- Session fixation protection: New session on login

**CSRF Protection**:
- Not required for JWT bearer tokens (no cookie-based auth)
- State-changing operations require authentication
- Idempotency-Key header for duplicate prevention

## Data Protection

### Encryption at Rest

**Database**:
- PostgreSQL: AWS RDS encryption enabled (AES-256)
- SQLite (dev): File-level encryption not enabled (development only)
- Encryption keys managed by AWS KMS

**Secrets**:
- Kubernetes secrets encrypted at rest in etcd
- Environment variables never logged
- Secrets rotation: quarterly minimum

**Backups**:
- RDS snapshots encrypted with same key as database
- Manual backups encrypted before upload to S3

### Encryption in Transit

**External Traffic**:
- TLS 1.3 for ingress (TLS 1.2 minimum)
- Certificate managed by cert-manager + Let's Encrypt
- HSTS header enforces HTTPS
- No HTTP allowed (automatic redirect to HTTPS in production)

**Internal Traffic**:
- mTLS for service-to-service communication
- PostgreSQL connections use TLS
- Redis connections use TLS (production)

### Sensitive Data Handling

**Passwords**:
- Hashed with bcrypt (cost factor 12)
- Never stored in plaintext
- Never logged or included in error messages
- Password reset tokens: 1-hour expiry, single-use

**Personal Identifiable Information (PII)**:
- User names, emails stored in org.stakeholder table
- Audit events reference stakeholder_id (UUID), not email
- Privacy request handling: 30-day SLA for restriction/export/deletion
- Data minimization: only collect what's needed

**Audit Logging**:
- Immutable audit records (no UPDATE, only INSERT)
- 365-day retention for compliance
- Includes: actor, action, target, timestamp, outcome
- No sensitive data in audit records (use references)

## Input Validation and Output Encoding

### Input Validation

**All API endpoints** validate input via Pydantic schemas:

```python
# Example: Question submission validation
class QuestionSubmissionRequest(BaseModel):
    question_text: str = Field(min_length=1, max_length=2000)
    session_id: Optional[UUID] = None
    
    @validator('question_text')
    def validate_no_html(cls, v):
        if '<script' in v.lower() or '<iframe' in v.lower():
            raise ValueError("HTML tags not allowed")
        return v
```

**Character Limits**:
- Question text: 1-2000 characters
- Feedback text: ≤2000 characters
- Source title: ≤500 characters
- All text fields have explicit max length

**HTML/Script Filtering**:
- Block: `<script>`, `<iframe>`, `javascript:`, `onerror=`, `onclick=`
- Feedback text and user-submitted content sanitized
- No raw HTML rendering in frontend (React escapes by default)

**File Upload Validation** (if implemented):
- Whitelist allowed file types (.pdf, .md, .txt)
- Max file size: 10MB
- Virus scanning before processing
- Files stored outside web root

### SQL Injection Prevention

**Parameterized Queries Only**:
```python
# Good - SQLAlchemy ORM (parameterized)
db.query(Stakeholder).filter_by(email=email).first()

# Bad - Never use raw SQL with string interpolation
db.execute(f"SELECT * FROM stakeholder WHERE email='{email}'")
```

All database queries use SQLAlchemy ORM or parameterized raw SQL.

### Cross-Site Scripting (XSS) Prevention

**React Auto-Escaping**:
- React escapes content by default
- No `dangerouslySetInnerHTML` used in codebase
- User-generated content displayed as text, not HTML

**Content Security Policy** (CSP):
```
Content-Security-Policy: 
  default-src 'self'; 
  script-src 'self'; 
  style-src 'self' 'unsafe-inline'; 
  img-src 'self' data:; 
  connect-src 'self' https://knowledge-assistant.example.com;
```

### Cross-Site Request Forgery (CSRF)

**Not Applicable**: Application uses JWT bearer tokens (not cookies), so CSRF not relevant.

For future cookie-based auth: implement CSRF tokens via Django middleware or equivalent.

## API Security

### Rate Limiting

**Per-User Limits** (enforced by slowapi library):
- 100 requests per minute per user
- 1000 requests per hour per user
- 429 status code when exceeded
- Retry-After header included in response

**Global Limits** (enforced at ingress):
- 10,000 requests per minute per IP (CloudFlare WAF)
- Burst protection for DDoS mitigation

### CORS Configuration

**Development**:
```python
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
```

**Production**:
```python
CORS_ORIGINS = ["https://knowledge-assistant.example.com"]
```

**Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS
**Allowed Headers**: Authorization, Content-Type, Idempotency-Key
**Credentials**: Not allowed (bearer token used instead)

### Security Headers

**Response Headers** (all environments):
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: (see CSP section above)
```

Implemented in:
- Backend: FastAPI middleware
- Frontend: nginx.conf

### API Authentication

**Public Endpoints** (no authentication):
- `GET /api/v1/health`
- `POST /api/v1/auth/login`

**Protected Endpoints** (authentication required):
- All other endpoints require `Authorization: Bearer {token}` header
- 401 response if token missing or invalid
- 403 response if token valid but insufficient permissions

## Secrets Management

### Secret Types

**Application Secrets**:
- `SECRET_KEY`: JWT signing key (rotate quarterly)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `AUTH_API_URL`, `USER_SERVICE_URL`: Integration endpoints

**Infrastructure Secrets**:
- Database credentials
- AWS access keys (for S3, CloudWatch)
- TLS certificates (managed by cert-manager)
- Service account keys

### Secret Storage

**Production**:
- Kubernetes secrets (encrypted at rest in etcd)
- AWS Secrets Manager (for RDS credentials)
- Never in Git, environment variables, or logs

**Development**:
- `.env` files (gitignored)
- `.env.example` committed (no real secrets)

### Secret Rotation Procedure

**Quarterly Rotation** (SECRET_KEY example):
```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# 2. Update Kubernetes secret
kubectl create secret generic app-secrets \
  --from-literal=SECRET_KEY="$NEW_SECRET" \
  --namespace=knowledge-assistant-prod \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Rolling restart pods
kubectl rollout restart deployment/backend -n knowledge-assistant-prod

# 4. Verify pods running
kubectl rollout status deployment/backend -n knowledge-assistant-prod

# 5. Document rotation
echo "$(date): Rotated SECRET_KEY" >> /secure/audit/secrets-rotation.log
```

**Emergency Rotation** (if secret compromised):
Same procedure but execute immediately, notify security team.

## Vulnerability Management

### Dependency Scanning

**CI Pipeline** (automated on every commit):
```bash
# Python dependencies
pip-audit --requirement requirements.txt

# Node dependencies
npm audit

# Fail build if critical vulnerabilities found
```

**Container Scanning**:
- Trivy scans Docker images in CI
- Critical/High vulnerabilities block deployment

**Scheduled Scans**:
- Weekly dependency scan via GitHub Dependabot
- Monthly container image rescan

### Patch Management

**Critical Vulnerabilities** (CVE with CVSS ≥9.0):
- Emergency patch within 24 hours
- Deploy to production after expedited staging verification

**High Vulnerabilities** (CVSS 7.0-8.9):
- Patch within 7 days
- Include in next scheduled release

**Medium/Low Vulnerabilities**:
- Patch within 30 days
- Batch with regular releases

### Security Updates

**Python Dependencies**:
```bash
cd backend
pip list --outdated
pip install --upgrade <package>
pip freeze > requirements.txt
```

**Node Dependencies**:
```bash
cd frontend
npm outdated
npm update <package>
```

Test thoroughly after updates (unit tests, integration tests, staging verification).

## Incident Response

### Security Incident Classification

**Severity 1** (Critical):
- Data breach (PII/confidential data exposed)
- Unauthorized admin access
- Service compromise (RCE, privilege escalation)
- Active attack in progress

**Severity 2** (High):
- Successful unauthorized access to restricted data
- XSS/injection vulnerability discovered in production
- Secret leak (API keys, credentials)

**Severity 3** (Medium):
- Attempted unauthorized access (blocked)
- Vulnerability discovered (not exploited)
- Security misconfiguration

**Severity 4** (Low):
- Policy violation (no security impact)
- Suspicious activity (false positive)

### Incident Response Procedure

**Detection** → **Triage** → **Containment** → **Investigation** → **Remediation** → **Recovery** → **Post-Mortem**

#### 1. Detection
- Security alerts in CloudWatch/Grafana
- Unusual activity in audit logs
- User report
- External security researcher report

#### 2. Triage (within 15 minutes)
- Classify severity
- Page security on-call
- Create incident ticket
- Notify stakeholders if Sev 1-2

#### 3. Containment (within 1 hour for Sev 1)
- Isolate affected systems
- Revoke compromised credentials
- Block malicious IP addresses
- Scale down affected pods if necessary

#### 4. Investigation
- Collect logs, audit events
- Identify attack vector
- Determine scope of compromise
- Preserve evidence for forensics

#### 5. Remediation
- Patch vulnerability
- Rotate secrets if compromised
- Update security controls
- Deploy fix to production

#### 6. Recovery
- Verify fix effectiveness
- Restore normal operations
- Monitor for recurrence

#### 7. Post-Mortem (within 5 business days)
- Document timeline
- Root cause analysis
- Action items to prevent recurrence
- Share lessons learned

### Incident Contacts

- **Security Team (Sev 1-2)**: Page via PagerDuty + post #security-incidents
- **Legal Team (data breach)**: security-legal@example.com
- **Communications (public disclosure)**: pr@example.com
- **Affected Users**: Notify via email within 72 hours (GDPR requirement)

## Compliance

### Regulatory Requirements

**SOC 2 Type II**:
- Audit logging (365-day retention)
- Access control enforcement
- Encryption at rest and in transit
- Quarterly access reviews
- Annual penetration testing

**GDPR** (Data Protection):
- Data minimization
- Right to erasure (30-day SLA)
- Right to data portability (export functionality)
- Privacy by design
- Consent tracking
- Data breach notification (72 hours)

**Internal Policies**:
- Least-privilege access
- Separation of duties (no single person has full production access)
- Code review required (2 approvals for security-sensitive changes)
- No direct production database access (via backend pod only)

### Audit Procedures

**Quarterly Access Review**:
1. Export list of privileged accounts (platform_administrator role)
2. Verify each account has business justification
3. Remove accounts for departed employees
4. Document review in compliance system

**Annual Penetration Test**:
1. Engage external security firm (Q4 each year)
2. Provide test environment (staging)
3. Remediate findings within 30 days
4. Retest critical findings

**Continuous Audit Logging**:
```sql
-- Audit events query (governance_reviewer role required)
SELECT 
  actor_stakeholder_id,
  action_type,
  target_resource,
  outcome,
  occurred_at
FROM ops.audit_event
WHERE occurred_at > NOW() - INTERVAL '30 days'
ORDER BY occurred_at DESC;
```

## Security Best Practices for Developers

### Code Review Checklist

- [ ] Input validation on all API endpoints
- [ ] Parameterized queries (no string interpolation in SQL)
- [ ] Authentication required for protected endpoints
- [ ] Authorization checks before data access
- [ ] No secrets in code (use environment variables)
- [ ] Error messages don't leak sensitive information
- [ ] Audit logging for privileged actions
- [ ] Unit tests include security test cases

### Common Pitfalls to Avoid

**Don't**:
- Hardcode secrets or credentials
- Log sensitive data (passwords, tokens, PII)
- Use raw SQL with f-strings
- Trust user input without validation
- Return detailed error messages to users
- Grant overly broad permissions
- Skip authentication checks
- Use `eval()` or `exec()` on user input

**Do**:
- Validate all input
- Use parameterized queries
- Apply least-privilege principle
- Log security events
- Rotate secrets regularly
- Keep dependencies updated
- Write security tests

## Vulnerability Reporting

### Responsible Disclosure Policy

We encourage security researchers to report vulnerabilities responsibly.

**How to Report**:
1. Email: security@example.com
2. PGP key: https://example.com/pgp-key.asc
3. Include: vulnerability description, steps to reproduce, impact assessment

**What to Expect**:
- Acknowledgment within 24 hours
- Triage and severity classification within 72 hours
- Regular updates on remediation progress
- Credit in security advisory (if desired)
- Coordinated disclosure after fix deployed

**Bug Bounty** (if applicable):
- Critical vulnerabilities: $500-$2000
- High vulnerabilities: $200-$500
- Medium vulnerabilities: $50-$200

**Out of Scope**:
- Development/test environments
- Social engineering attacks
- Physical attacks
- DoS/DDoS attacks
- Spam or brute force attempts

### Hall of Fame

We publicly acknowledge security researchers who have responsibly disclosed vulnerabilities:
- (List will be maintained at https://example.com/security/hall-of-fame)

## Security Training

### Required Training

**All Developers**:
- Secure coding practices (annual)
- OWASP Top 10 (annual)
- Authentication and authorization patterns
- Input validation and output encoding

**Platform Team**:
- Kubernetes security (annual)
- Secrets management
- Incident response procedures

**On-Call Engineers**:
- Security incident handling
- Log analysis for security events
- Escalation procedures

### Resources

- OWASP Cheat Sheets: https://cheatsheetseries.owasp.org/
- Internal security wiki: https://wiki.example.com/security
- Security training portal: https://training.example.com/security

---

**Document Version**: 1.0  
**Last Updated**: 2026-08-25  
**Maintained By**: Security Team  
**Contact**: security@example.com  
**Next Review**: 2026-11-25
