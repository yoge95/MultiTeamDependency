# Architecture Documentation

## System Overview

The Multi-team Knowledge Assistant is a bounded internal knowledge platform designed to answer questions about team ownership, service dependencies, stakeholder routing, onboarding guidance, runbooks, and governance processes using approved enterprise sources. The system implements a retrieval-augmented answering approach with explicit limitation handling, citation-backed responses, and access-aware filtering.

## System Components

### 1. Backend Service (Python + FastAPI)

**Purpose**: Orchestrates question intake, retrieval, answer composition, and governance workflows.

**Key Modules**:
- **API Layer** (`app/api/`): REST endpoints for questions, answers, citations, feedback, governance
- **Service Layer** (`app/services/`): Business logic for question intake, retrieval orchestration, answer composition, citation generation, confidence scoring, access control, feedback capture, source governance
- **Integration Layer** (`app/integrations/`): Client adapters for Auth API, User Service, OpenSearch, Neo4j
- **Data Layer** (`app/models/`): SQLAlchemy ORM models across five schemas (org, knowledge, interaction, governance, ops)

**Technologies**:
- FastAPI 0.115+ for REST API framework
- SQLAlchemy 2.0+ (sync) for ORM
- Pydantic 2.10+ for request/response validation
- Alembic for database migrations
- httpx for HTTP client integrations
- Redis for access scope caching (15-minute TTL)

### 2. Frontend Application (React + TypeScript + Vite)

**Purpose**: Provides user interface for question submission, answer display with citations, feedback capture, and source governance workflows.

**Key Components**:
- **Pages** (`src/pages/`): QuestionPage, AnswerPage, LoginPage
- **Components** (`src/components/`): CitationPanel, ConfidenceBadge, FreshnessWarning, LimitationMessage, FeedbackForm, RequireAuth (route guard)
- **Context** (`src/context/`): AuthContext for authentication state management
- **Services** (`src/services/`): Centralized API client with Bearer token attachment and 401 handling

**Technologies**:
- React 18 with TypeScript
- Vite for build tooling and dev server
- React Router for client-side routing
- Tailwind CSS for styling

### 3. Data Stores

#### PostgreSQL 15.2 (Authoritative Transactional Store)

**Purpose**: System of record for all canonical identifiers and governance state.

**Schemas**:
- **org**: Teams, stakeholders, team memberships, services, service dependencies
- **knowledge**: Knowledge domains, source records, source versions, source chunks, domain assignments
- **interaction**: Question sessions, question turns, answer records, citation references, feedback records
- **governance**: Access policies, access policy bindings, escalation routes
- **ops**: Audit events, ingestion runs, privacy request links, graph sync batches

**Key Design Decisions**:
- UUID primary keys for all business entities (team_id, stakeholder_id, source_record_id, etc.)
- Canonical identifiers generated and stored in PostgreSQL, propagated to projection stores
- 365-day audit retention for compliance
- 90-day operational telemetry online retention
- SQLite default for local development (zero-config startup)

#### OpenSearch (Searchable Projections)

**Purpose**: Semantic vector search and filtered retrieval over source chunks.

**Projections**:
- Chunk documents with semantic embeddings
- Domain-aware chunking with lineage to source_record_id and source_version_id
- Filtered search attributes: domain_id, access_tags, freshness_date

**Implementation Status**: Client interfaces defined, stub implementation (production would use opensearch-py library)

#### Neo4j (Traversable Relationship Projections)

**Purpose**: Graph traversal for team ownership, stakeholder routing, escalation paths, service dependencies.

**Graph Model**:
- Team ownership relationships
- Stakeholder routing and escalation paths
- Service dependency graphs (DEPENDS_ON relationships)
- Knowledge domain connections
- All nodes carry canonical UUIDs from PostgreSQL for traceability

**Implementation Status**: Client interfaces defined with Cypher query methods, stub implementation (production would use neo4j-driver library)

## Data Flow

### Question Answering Flow

```
User → Frontend (QuestionPage)
  → API Client: POST /api/v1/questions
    → Backend: QuestionIntakeService
      → Intent Classification (ownership/dependency/routing/runbook/onboarding/governance)
      → Ambiguity Detection (too_vague, unclear_reference, multiple_intents)
      → SessionContextService: Create or continue session
      → Store QuestionSession + QuestionTurn in PostgreSQL
      ← Return: question_id, session_id, turn_id, status, optional clarification_prompt

User → Frontend: Poll status via GET /api/v1/questions/{question_id}
  → Backend: RetrievalOrchestrationService (when status=processing)
    → OpenSearch: Semantic search with domain/access/freshness filters
    → AccessControlService: Filter by user's access_scope (roles, domains, source-scope)
    → PostgreSQL: Enrich with governance metadata (approval_state, last_reviewed_at)
    → RankingService: Combine retrieval scores with governance metadata
    → Neo4j: Relationship traversal based on intent (ownership paths, dependencies, escalation routes)
    → EvidenceBundle assembled: chunks + relationships + metadata

  → AnswerCompositionService
    → Synthesize answer_text from evidence bundle
    → Detect limitations: low_confidence, stale_source, conflicting_evidence, restricted_access, missing_knowledge

  → CitationService
    → Extract substantive claims from answer_text
    → Match claims to evidence chunks via word overlap
    → Generate claim-level citations with lineage (chunk_id → source_version_id → source_record_id)
    → Validate citation coverage (≥90% threshold)

  → ConfidenceScoringService
    → Calculate multi-dimensional score:
      - evidence_quality (40%): retrieval scores + approval state
      - freshness (25%): last_reviewed_at, 90-day stale threshold
      - consistency (20%): variance in chunk scores
      - citation_coverage (15%): percentage of claims cited
    → Determine confidence_band: high (≥0.80), medium (0.60-0.79), low (0.40-0.59), insufficient (<0.40)
    → Identify confidence_flags: low_evidence, stale_sources, conflicting_claims, low_citation_coverage, restricted_access

  → EscalationRoutingService (if confidence low or evidence insufficient)
    → Neo4j traversal: identify domain stewards, platform admins, fallback contacts

  → Store AnswerRecord + CitationReferences in PostgreSQL
  ← Return: answer_id, answer_text, citations, confidence_score, limitations, escalation_contacts

User → Frontend (AnswerPage)
  → Display answer with inline citation markers, expandable citations panel, confidence badge, freshness warnings, limitation messages
```

### Feedback Capture Flow

```
User → Frontend (FeedbackForm)
  → API Client: POST /api/v1/feedback
    → Backend: FeedbackCaptureService
      → Validate: feedback_type (helpful/incomplete/stale/unclear/incorrect/other), ≤2000 chars, no HTML/script tags
      → Verify answer ownership (answer must belong to authenticated user's session)
      → Store FeedbackRecord with triage_status=pending
      → Set steward_action_required flag for negative feedback types
      ← Return: feedback_id, confirmation

Knowledge Steward → Backend: Query pending feedback
  → GET /api/v1/feedback?triage_status=pending (filtered by steward's domains)
  → Review feedback, investigate source quality issues
```

### Source Governance Flow

```
Knowledge Steward → Backend: Register new source
  → POST /api/v1/sources
    → SourceGovernanceService
      → Validate: domain exists, no duplicate source_key
      → Create SourceRecord with approval_state=pending
      ← Return: source_record_id

Knowledge Steward → Backend: Approve source
  → POST /api/v1/sources/{source_id}/approve
    → SourceGovernanceService
      → Verify steward is assigned to source's domain
      → Record SourceReview with review_decision (approved/rejected/exception_granted/archived)
      → Update SourceRecord: approval_state, next_review_due_on
      ← Return: confirmation

Knowledge Steward → Backend: Grant freshness exception
  → POST /api/v1/sources/{source_id}/freshness-exception
    → SourceGovernanceService
      → Verify steward permissions
      → Create SourceReview with freshness_exception_granted=true, exception_until (max 180 days)
      ← Return: confirmation
```

## Technology Stack

### Backend
- **Language**: Python 3.10+
- **Framework**: FastAPI 0.115+
- **ORM**: SQLAlchemy 2.0+ (sync, not async)
- **Validation**: Pydantic 2.10+
- **Database**: PostgreSQL 15.2 (production), SQLite (development default)
- **Migrations**: Alembic 1.13+
- **HTTP Client**: httpx 0.27+
- **Cache**: Redis (access scope caching, 15-minute TTL)
- **Testing**: pytest

### Frontend
- **Language**: TypeScript 5+
- **Framework**: React 18
- **Build Tool**: Vite 5+
- **Routing**: React Router 6
- **Styling**: Tailwind CSS 3+
- **Testing**: Vitest

### Infrastructure
- **Orchestration**: Kubernetes 1.28
- **Cloud Platform**: AWS (us-west-2, multi-AZ)
- **GitOps**: ArgoCD for deployment automation
- **CI/CD**: GitHub Actions
- **Monitoring**: CloudWatch + Grafana
- **Observability**: OpenTelemetry instrumentation

## Design Decisions

### ADR-001: Bounded Retrieval-Augmented Model (Not Autonomous Multi-Agent)

**Decision**: Use LangGraph-style stateful workflow patterns for retrieval-augmented answering, avoiding unconstrained autonomous multi-agent models.

**Rationale**: 
- Predictable behavior with explicit control flow
- Clear audit trail for compliance requirements
- Deterministic citation and evidence lineage
- No uncontrolled tool use or external API calls

### ADR-002: OpenSearch for Semantic Search

**Decision**: Use OpenSearch for semantic vector search and filtered retrieval.

**Rationale**:
- Native vector search capabilities with k-NN plugin
- Flexible filtering on domain_id, access_tags, freshness_date
- Strong integration with AWS ecosystem
- Mature open-source community

### ADR-003: Three-Store Governed Pattern

**Decision**: PostgreSQL as authoritative store, OpenSearch and Neo4j as projections.

**Rationale**:
- PostgreSQL provides ACID guarantees for governance state
- Canonical UUIDs generated in PostgreSQL propagate to projections
- Projection lag observable via synchronization control metadata
- Clear separation between system of record and search/graph capabilities

### ADR-004: Multi-Dimensional Confidence Scoring

**Decision**: Calculate confidence from evidence_quality (40%), freshness (25%), consistency (20%), citation_coverage (15%).

**Rationale**:
- Evidence quality reflects retrieval relevance and approval state
- Freshness addresses staleness concerns for time-sensitive content
- Consistency detects conflicting information across sources
- Citation coverage ensures grounded answers with provenance

### ADR-005: Claim-Level Citations

**Decision**: Generate citations at claim granularity (substantive assertions ≥20 chars) rather than paragraph or document level.

**Rationale**:
- Enables verification of specific facts
- Supports partial answer scenarios where some claims lack evidence
- Facilitates feedback on specific citation quality
- Aligns with governance requirement for inspectable provenance

### ADR-006: Access-Aware Filtering

**Decision**: Filter retrieved content by user's access_scope including domain filtering, role-based access levels, and source-scope restrictions.

**Rationale**:
- Enforces least-privilege access to confidential/restricted sources
- Role-aware filtering: end_user sees public/internal, knowledge_steward adds confidential, admin adds restricted
- Source-scope exclusions prevent exposure of embargoed content
- Access clarity score penalizes answers with restricted evidence

### ADR-007: 365-Day Audit Retention

**Decision**: Retain immutable audit records for privileged/admin/governance actions for 365 days.

**Rationale**:
- Meets SOC2 Type II compliance requirements
- Supports security investigations and access reviews
- Enables post-incident analysis of configuration changes
- Satisfies regulatory expectations for audit trail

### ADR-008: Stewardship Review Paths

**Decision**: Negative feedback (incomplete/stale/unclear/incorrect) triggers steward_action_required flag and triage workflow.

**Rationale**:
- Continuous improvement loop for source quality
- Stewards notified of quality issues in their domains
- Feedback routing via domain assignment relationships
- Prevents stale sources from degrading answer quality

### ADR-009: Canonical UUID Strategy

**Decision**: Every business entity uses canonical UUID generated in PostgreSQL, propagated to OpenSearch documents and Neo4j nodes.

**Rationale**:
- Deterministic citation linking across data stores
- Graph traversal traceability to authoritative records
- Audit evidence correlation via stable identifiers
- Simplifies projection synchronization logic

### ADR-010: Neo4j for Relationship Traversal

**Decision**: Use Neo4j graph database for ownership paths, service dependencies, and escalation routing.

**Rationale**:
- Efficient multi-hop traversal for team ownership chains
- Natural modeling of service dependency graphs
- Flexible schema for evolving relationship types
- Strong Cypher query language for path finding

### ADR-011: Conservative Spring Boot Integration

**Decision**: Synchronous REST/HTTP integration with Auth API, User Service, Payment API rather than event-driven or gRPC.

**Rationale**:
- Conservative integration with existing Spring Boot services
- OAuth 2.1 token validation through Auth API
- Circuit breaker pattern mitigates known Auth API single-point-of-failure risk
- TLS-secured internal service-to-service traffic

### ADR-013: OpenTelemetry Observability

**Decision**: Unified observability instrumentation using OpenTelemetry across Python orchestration and Spring Boot services.

**Rationale**:
- Vendor-neutral instrumentation standard
- Consistent trace, metric, and log collection
- Integration with CloudWatch and Grafana
- Future-proof for multi-vendor observability backends

## Integration Patterns

### Authentication & Authorization

**Auth API (svc-001) Integration**:
- OAuth 2.1 token validation via introspection endpoint
- Circuit breaker pattern: 5-failure threshold, 30-second recovery timeout
- Access scope caching in Redis with 15-minute TTL
- Graceful degradation: cache fallback when circuit breaker open

**User Service (svc-003) Integration**:
- User profile retrieval for enriching session context
- Circuit breaker pattern for resilience
- Minimal scope from token when User Service unavailable

**Role-Based Authorization**:
- Four roles: end_user, knowledge_steward, governance_reviewer, platform_administrator
- Role-aware access filtering at retrieval layer
- Require_role factory for endpoint-level authorization

### External Service Communication

**Synchronous REST/HTTP**:
- All integration clients use httpx with timeout configuration
- TLS-secured internal traffic
- Outbound egress restricted to explicitly allowed enterprise services and AWS APIs

**Circuit Breaker Pattern**:
- Applied to Auth API and User Service clients
- 5-failure threshold before opening circuit
- 30-second recovery timeout before half-open state
- Fail-fast behavior prevents cascade failures

### Data Store Synchronization

**PostgreSQL → OpenSearch Projection**:
- Chunk ingestion writes to PostgreSQL first (SourceChunk records)
- Background job projects to OpenSearch with semantic embeddings
- Synchronization control metadata tracks projection lag

**PostgreSQL → Neo4j Projection**:
- Team, stakeholder, service entities written to PostgreSQL first
- Background job projects relationships to Neo4j graph
- GraphSyncBatch records track synchronization status

## Security Architecture

### Authentication
- OAuth 2.1 bearer tokens via Auth API integration
- Token validation on every protected endpoint
- 401 responses trigger frontend redirect to login

### Authorization
- Role-based access control (RBAC) with four roles
- Access scope filtering at retrieval layer
- Domain-based content filtering (stewards see only their domains)
- Source-scope restrictions (exclusions, whitelists)

### Data Protection
- Secrets from environment variables only (never hardcoded)
- Password hashing with bcrypt (cost factor ≥12)
- JWT tokens include expiry claim (no infinite tokens)
- TLS for all internal service-to-service communication

### Input Validation
- Pydantic validation on all API endpoints
- Character limits: question_text (1-2000), feedback_text (≤2000)
- HTML/script tag blocking in user-submitted text
- Parameterized queries via SQLAlchemy ORM (SQL injection prevention)

### CORS Configuration
- Explicit allowed origins (no wildcard in production)
- Configured from CORS_ORIGINS environment variable
- Standard methods and Authorization header allowed

### Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Strict-Transport-Security (HSTS)

### Audit Logging
- Immutable audit records for privileged/admin/governance actions
- 365-day retention for compliance
- Audit events stored in PostgreSQL ops.audit_event table
- Captured fields: actor_stakeholder_id, action_type, target_resource, timestamp, outcome

## Deployment Architecture

### Environment Topology

**Four-Environment Model**:
1. **Development**: Feature development, synthetic data, continuous deployment
2. **Test**: Functional/integration/security/performance verification, synthetic/masked data
3. **Staging**: Production-like rehearsal with masked data, high stability target
4. **Production**: Live operations in AWS us-west-2 multi-AZ, 99.9%+ availability target

### Kubernetes Configuration

**Namespace Separation**: Separate namespaces per environment with isolated service accounts, secrets, network policies

**Resource Limits**:
- Backend: 250m CPU, 512Mi memory (base), 1000m CPU, 2Gi memory (limits)
- Frontend: 100m CPU, 256Mi memory (base), 500m CPU, 512Mi memory (limits)

**High Availability** (Production):
- Backend: 3 replicas with pod anti-affinity for zone spreading
- Frontend: 3 replicas with pod anti-affinity for zone spreading
- Health checks on /api/v1/health (backend), / (frontend)

**Ingress Configuration**:
- TLS termination with cert-manager integration
- Routes: /api → backend (port 9000), / → frontend (port 80)

### GitOps Deployment

**ArgoCD Applications**:
- Development: auto-sync enabled with self-heal
- Test: auto-sync enabled, no self-heal
- Staging: manual sync
- Production: manual sync with rollback protection

**CI/CD Pipeline** (GitHub Actions):
- CI: lint (ruff, eslint) → type-check (mypy, tsc) → test (pytest, vitest) → security scan (bandit, pip-audit, npm audit) → Docker build → manifest validation
- CD Staging: triggers on push to main, syncs via ArgoCD
- CD Production: triggers on release tags (v*), includes smoke tests and automatic rollback

## Scalability Considerations

### Horizontal Scaling
- Stateless backend services enable horizontal pod autoscaling
- Session state stored in PostgreSQL (not in-memory)
- Access scope cache in Redis (shared across pods)

### Database Optimization
- UUID primary keys with btree indexes
- Foreign key indexes for join performance
- Partial indexes on approval_state, freshness_status
- Connection pooling via SQLAlchemy

### Caching Strategy
- Access scope caching in Redis (15-minute TTL)
- Idempotency key caching (24-hour window)
- Future: OpenSearch result caching for frequently asked questions

### Observability for Performance
- OpenTelemetry traces for request latency
- CloudWatch metrics for service health
- Grafana dashboards for operational visibility
- 90-day online operational telemetry retention

## Future Enhancements

### Planned Improvements
- OpenSearch and Neo4j production integration (currently stub implementations)
- Real-time notification service for steward triage alerts
- Advanced analytics dashboard for knowledge gap identification
- Bulk source import/export workflows
- Multi-language support for internationalization
- Enhanced clarification dialog with interactive refinement

### Known Limitations
- Single-point-of-failure risk with Auth API (mitigated by circuit breaker + cache)
- Projection lag between PostgreSQL and OpenSearch/Neo4j (observable via sync metadata)
- OpenSearch and Neo4j clients currently stub implementations (interfaces defined for production replacement)

---

**Document Version**: 1.0  
**Last Updated**: 2026-08-25  
**Maintained By**: Platform Engineering Team
