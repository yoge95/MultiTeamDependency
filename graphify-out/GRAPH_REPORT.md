# Graph Report - multiteamdependency  (2026-08-25)

## Corpus Check
- 106 files · ~54,314 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1515 nodes · 2461 edges · 110 communities (93 shown, 17 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 200 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9f18b1e9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- devDependencies
- compilerOptions
- asyncio
- test_api_governance.py
- api/answers.py
- Multi-team Knowledge Assistant
- AccessScope
- database.py
- EscalationRoutingService
- dependencies
- SessionContextService
- compilerOptions
- app/__init__.py
- multiteamdependency-backend
- CircuitBreaker
- test_retrieval_orchestration.py
- integrations/__init__.py
- test_api_questions.py
- TASK-3 Implementation: Core API Routes and Question Intake
- test_api_answers.py
- QuestionIntakeService
- verify_task3.py
- PaginatedResponse
- Infrastructure as Code
- Neo4jClient
- api/questions.py
- RetrievalOrchestrationService
- test_answer_composition.py
- OpenSearchClient
- RankingService
- services/__init__.py
- api/governance.py
- SourceGovernanceService
- FeedbackSubmissionRequest
- RetrievedChunk
- patch
- Operational Runbook
- test_api_governance_unit.py
- CitationService
- CircuitBreaker
- Deployment Guide
- Development Guide
- test_citation_service.py
- datetime
- services/api.ts
- Base
- main.py
- scripts
- org.py
- .validate_exception_date
- package.json
- test_api_feedback.py
- types/api.ts
- autoprefixer
- eslint-plugin-react-refresh
- tailwindcss
- @testing-library/jest-dom
- @types/react-dom
- typescript
- @typescript-eslint/eslint-plugin
- @typescript-eslint/parser
- @vitejs/plugin-react
- vitest
- CurrentUser
- app/auth.py
- schemas/governance.py
- retrieval.py
- UserProfile
- QuestionSession
- start.sh
- Design Decisions
- conftest.py
- Base
- Team
- { login, health, submitQuestion, getQuestionStatus, getAnswer, getCitation, submitFeedback }
- stop.sh
- CitationCoverageReport
- Incident Response Procedure
- SourceRegistrationRequest
- Security Documentation
- client
- Security Architecture
- 3. Data Stores
- Architecture Documentation
- Settings
- Scalability Considerations
- API Security
- Authentication and Authorization
- Input Validation and Output Encoding
- Integration Patterns
- Technology Stack
- Data Flow
- Deployment Architecture
- Data Protection
- Vulnerability Management
- Secrets Management
- Compliance
- Security Best Practices for Developers
- Security Training

## God Nodes (most connected - your core abstractions)
1. `RetrievedChunk` - 54 edges
2. `CurrentUser` - 41 edges
3. `AccessScope` - 37 edges
4. `Neo4jClient` - 32 edges
5. `RetrievalOrchestrationService` - 30 edges
6. `CitationService` - 26 edges
7. `QuestionSession` - 25 edges
8. `QuestionIntakeService` - 25 edges
9. `OpenSearchClient` - 22 edges
10. `AnswerRecord` - 22 edges

## Surprising Connections (you probably didn't know these)
- `get_answer()` --uses--> `Neo4jClient`  [INFERRED]
  backend/app/api/answers.py → backend/app/integrations/neo4j_client.py
- `get_answer()` --uses--> `AnswerLimitation`  [INFERRED]
  backend/app/api/answers.py → backend/app/models/interaction.py
- `get_answer()` --uses--> `AnswerRecord`  [INFERRED]
  backend/app/api/answers.py → backend/app/models/interaction.py
- `get_answer()` --uses--> `CitationReference`  [INFERRED]
  backend/app/api/answers.py → backend/app/models/interaction.py
- `get_answer()` --uses--> `QuestionSession`  [INFERRED]
  backend/app/api/answers.py → backend/app/models/interaction.py

## Import Cycles
- None detected.

## Communities (110 total, 17 thin omitted)

### Community 0 - "devDependencies"
Cohesion: 0.12
Nodes (17): eslint, eslint-plugin-react-hooks, devDependencies, eslint, eslint-plugin-react-hooks, happy-dom, jsdom, postcss (+9 more)

### Community 1 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution (+16 more)

### Community 2 - "asyncio"
Cohesion: 0.12
Nodes (17): asyncio, Test that retrieve_evidence returns complete evidence bundle., Test graceful handling of OpenSearch errors., Test OpenSearch client search_chunks interface., Test OpenSearch client health check., Test Neo4j client get_ownership_path interface., Test Neo4j client get_dependencies interface., Test Neo4j client get_escalation_route interface. (+9 more)

### Community 3 - "test_api_governance.py"
Cohesion: 0.09
Nodes (21): Tests for source governance API endpoints., Test that listing sources requires knowledge_steward or governance_reviewer…, Test successful source approval., Test approving non-existent source., Test approving source in domain user is not steward for., Test successful freshness exception grant., Test freshness exception exceeding 180 days is rejected., Test that governance endpoints require authentication. (+13 more)

### Community 4 - "api/answers.py"
Cohesion: 0.17
Nodes (16): get_answer(), get, Session, UUID, Answer API endpoints., Retrieve answer with citations, confidence score, freshness warnings, and…, AnswerLimitationResponse, AnswerResponse (+8 more)

### Community 5 - "Multi-team Knowledge Assistant"
Cohesion: 0.06
Nodes (33): Accessing the Application, API Documentation, Architecture Overview, Backend Environment Variables, Backend Setup, Configuration, Contributing, Database (+25 more)

### Community 6 - "AccessScope"
Cohesion: 0.16
Nodes (11): FastAPI dependency enforcing authentication. This is an explicit authentication…, require_auth(), AccessScope, Authentication and authorization schemas., Access scope for a user session., Filter chunks based on user's access scope. Enforces access control by: 1.…, Check if a single chunk is accessible to the user. Args: chunk: Chunk to check…, Tests for authentication and authorization. (+3 more)

### Community 7 - "database.py"
Cohesion: 0.15
Nodes (12): Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online(), Database configuration and session management., get_table_args(), Governance models for access policies and escalation routes (governance schema)., Get table args with optional schema based on database type. (+4 more)

### Community 8 - "EscalationRoutingService"
Cohesion: 0.19
Nodes (10): EscalationRoutingService, Session, UUID, Get platform administrator contacts., Get fallback contacts when no specific route is found., Retrieve predefined escalation route by ID. Args: route_id: Escalation route ID…, Service for identifying escalation routes when confidence is low., Identify next-step contacts via Neo4j traversal. Args: intent_classification:… (+2 more)

### Community 9 - "dependencies"
Cohesion: 0.15
Nodes (13): clsx, dependencies, clsx, react, react-dom, react-router-dom, tailwind-merge, @tanstack/react-query (+5 more)

### Community 10 - "SessionContextService"
Cohesion: 0.12
Nodes (13): get_question_intake_service(), Session, Dependency injection for QuestionIntakeService., Session, Initialize question intake service., Session, UUID, Service for managing question sessions and context. (+5 more)

### Community 11 - "compilerOptions"
Cohesion: 0.20
Nodes (9): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, strict, include (+1 more)

### Community 19 - "CircuitBreaker"
Cohesion: 0.20
Nodes (8): CircuitBreaker, CircuitBreakerOpen, Exception, Exception raised when circuit breaker is open., Circuit breaker implementation for external service calls., Execute function with circuit breaker protection., Record a failure and potentially open the circuit., Reset the circuit breaker to closed state.

### Community 20 - "test_retrieval_orchestration.py"
Cohesion: 0.09
Nodes (28): AccessControlService, UUID, Access control service for filtering retrieved content by user's access scope., Check if user can access a specific source. Args: source_record_id: Source…, Service for enforcing access-aware retrieval filtering., Get list of domains the user can access. Args: access_scope: User's access…, mock_db(), fixture (+20 more)

### Community 23 - "test_api_questions.py"
Cohesion: 0.06
Nodes (34): client(), db_session(), mock_current_user(), fixture, Tests for question submission and status endpoints., Test question validation rejects empty questions., Test question validation rejects questions over 2000 characters., Test intent classification for ownership questions. (+26 more)

### Community 24 - "TASK-3 Implementation: Core API Routes and Question Intake"
Cohesion: 0.07
Nodes (27): 1. FastAPI Application (`app/main.py`), 2. Health Endpoint (`app/api/health.py`), 3. Question Submission Endpoint (`app/api/questions.py`), 4. Question Status Endpoint (`app/api/questions.py`), 5. Intent Classification (`app/services/question_intake_service.py`), 6. Session Management (`app/services/session_context_service.py`), 7. Request/Response Validation (`app/schemas/questions.py`), 8. Database Integration (+19 more)

### Community 25 - "test_api_answers.py"
Cohesion: 0.07
Nodes (32): CitationReference, FeedbackReview, Base, QuestionTurn, Citation reference linking answers to source chunks., Feedback review by stewards., Session access scope cache., Question turn within a session. (+24 more)

### Community 26 - "QuestionIntakeService"
Cohesion: 0.12
Nodes (15): UUID, QuestionIntakeService, Classify question intent based on keywords and context. This is a simple rule-…, Determine candidate knowledge domains based on intent and question., Detect ambiguity flags in the question., Generate a clarification prompt based on ambiguity flags., Service for handling question intake and intent classification., Get the status of a submitted question. Args: question_id: UUID of the question… (+7 more)

### Community 27 - "verify_task3.py"
Cohesion: 0.14
Nodes (15): IntentClassification, BaseModel, field_validator, QuestionStatusResponse, QuestionSubmissionRequest, QuestionSubmissionResponse, Pydantic schemas for question submission and status., Request schema for question submission. (+7 more)

### Community 28 - "PaginatedResponse"
Cohesion: 0.15
Nodes (11): ErrorResponse, PaginatedResponse, BaseModel, Common Pydantic schemas used across modules., Mixin for created_at and updated_at timestamps., Standard paginated response wrapper., Calculate total number of pages., Check if there are more pages. (+3 more)

### Community 29 - "Infrastructure as Code"
Cohesion: 0.05
Nodes (41): Additional Resources, ArgoCD Rollback, Backend Deployment, Backend Image, Backend Secrets, Base Manifests, CD Production Pipeline (.github/workflows/cd-production.yml), CD Staging Pipeline (.github/workflows/cd-staging.yml) (+33 more)

### Community 30 - "Neo4jClient"
Cohesion: 0.12
Nodes (15): Neo4jClient, UUID, Neo4j client for relationship graph traversal., Client for Neo4j relationship graph operations. In a production implementation,…, Find shortest path between two entities. Args: source_id: Source entity UUID…, Check Neo4j connection health. Returns: True if connection is healthy, Initialize Neo4j client. Args: uri: Neo4j connection URI (from environment)…, Establish connection to Neo4j. (+7 more)

### Community 31 - "api/questions.py"
Cohesion: 0.18
Nodes (12): _apply_rate_limit(), get_question_status(), get, post, Request, UUID, Question submission and status endpoints., Get the status of a submitted question. User must own the question (via session… (+4 more)

### Community 32 - "RetrievalOrchestrationService"
Cohesion: 0.08
Nodes (25): Request for evidence retrieval., RetrievalRequest, UUID, Retrieval orchestration service coordinating multi-source evidence retrieval., Retrieve chunks from OpenSearch with semantic search and filters. Args:…, Enrich chunks with PostgreSQL governance metadata. Args: chunks: List of chunks…, Retrieve relationship paths from Neo4j based on intent. Args: request: Original…, Retrieve ownership relationships for entities mentioned in chunks. (+17 more)

### Community 33 - "test_answer_composition.py"
Cohesion: 0.05
Nodes (49): AnswerLimitation, AnswerRecord, get_table_args(), Interaction models for questions, answers, and feedback (interaction schema)., Answer limitation tracking., Get table args with optional schema based on database type., Answer record with confidence and citations., ConfidenceDimensions (+41 more)

### Community 34 - "OpenSearchClient"
Cohesion: 0.10
Nodes (13): OpenSearchClient, UUID, OpenSearch client for semantic chunk retrieval., Index a chunk document in OpenSearch. Args: chunk_data: Chunk document with all…, Client for OpenSearch chunk index operations. In a production implementation,…, Delete a chunk from the index. Args: chunk_id: Chunk UUID to delete Returns:…, Check OpenSearch cluster health. Returns: True if cluster is healthy, Initialize OpenSearch client. Args: endpoint: OpenSearch endpoint URL (from… (+5 more)

### Community 35 - "RankingService"
Cohesion: 0.10
Nodes (17): Session, RankingService, Calculate freshness score based on review recency. Args: last_reviewed_at:…, Service for ranking retrieved chunks by combined relevance., Calculate approval score based on source state. Args: approval_state: Approval…, Initialize ranking service. Args: db: Database session for fetching governance…, Calculate access score based on access clarity. Args: access_scope_tag: Access…, Rank chunks combining retrieval scores with governance metadata. Scoring… (+9 more)

### Community 37 - "api/governance.py"
Cohesion: 0.20
Nodes (15): approve_source(), grant_freshness_exception(), list_sources(), get, post, Session, UUID, Source governance API endpoints. (+7 more)

### Community 38 - "SourceGovernanceService"
Cohesion: 0.17
Nodes (11): Source review records., SourceReview, Session, UUID, Source governance service for steward workflows., Approve or review a source. Args: source_id: Source record ID request: Approval…, Service for source governance workflows., Initialize source governance service. Args: db: Database session (+3 more)

### Community 39 - "FeedbackSubmissionRequest"
Cohesion: 0.05
Nodes (45): FeedbackSubmissionRequest, post, Session, Submit feedback for an answer. Args: request: Feedback submission request…, submit_feedback(), FeedbackRecord, CitationFeedbackItem, FeedbackListResponse (+37 more)

### Community 40 - "RetrievedChunk"
Cohesion: 0.06
Nodes (39): Single retrieved chunk from OpenSearch., RetrievedChunk, ConfidenceScoringService, Service for calculating multi-dimensional confidence scores., Score freshness based on review dates and staleness state. Args: chunks:…, Score consistency across retrieved chunks (simplified heuristic). Args: chunks:…, Determine confidence band from overall score., Identify confidence flags based on dimension scores. (+31 more)

### Community 41 - "patch"
Cohesion: 0.17
Nodes (19): get_current_user(), FastAPI dependency for authenticated user context. Validates OAuth 2.1 bearer…, CircuitBreakerOpen, Exception, Exception raised when circuit breaker is open., Response from Auth API token validation., TokenValidationResponse, Test answer retrieval without authentication. (+11 more)

### Community 42 - "Operational Runbook"
Cohesion: 0.04
Nodes (48): Authentication Failures, Backend Health, Backup and Recovery, Circuit Breaker Open, CloudWatch Alarms, Common Issues and Resolutions, Configuration Backups, Database Backups (+40 more)

### Community 43 - "test_api_governance_unit.py"
Cohesion: 0.15
Nodes (17): FreshnessExceptionRequest, Request model for source approval., Request model for freshness exception., SourceApprovalRequest, Unit tests for governance API endpoints (schema validation only)., Test all valid review decisions., Test valid source approval request., Test source approval with invalid review decision. (+9 more)

### Community 44 - "CitationService"
Cohesion: 0.13
Nodes (13): Session, CitationService, Session, UUID, Retrieve detailed citation with full source context. Args: citation_id:…, Extract substantive claims from answer text. Args: text: Answer text to analyze…, Service for generating claim-level citations with provenance tracking., Match a claim to the most relevant evidence chunk. Args: claim: Claim text to… (+5 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.17
Nodes (9): CircuitBreaker, Circuit breaker implementation for external service calls., Execute function with circuit breaker protection., Record a failure and potentially open the circuit., Reset the circuit breaker to closed state., Tests for circuit breaker functionality., Test circuit breaker opens after failure threshold., Test circuit breaker transitions to half-open after recovery timeout. (+1 more)

### Community 46 - "Deployment Guide"
Cohesion: 0.04
Nodes (44): Change Windows, CloudWatch Alarms, Compliance & Audit, Configuration Management, Database Backup, Database Migration Rollback, Deployment Audit Trail, Deployment Guide (+36 more)

### Community 47 - "Development Guide"
Cohesion: 0.05
Nodes (36): Adding a New API Endpoint, Adding a New Frontend Page, Authentication failures, Backend Debugging, Backend Development, Building for Production, Code Conventions, Common Development Tasks (+28 more)

### Community 48 - "test_citation_service.py"
Cohesion: 0.07
Nodes (28): citation_service(), db_session(), fixture, Tests for citation service., Test claim extraction from answer text., Test that meta sentences are filtered out., Test matching a claim to relevant chunk., Test matching with no relevant chunks. (+20 more)

### Community 49 - "datetime"
Cohesion: 0.11
Nodes (27): init_db(), Initialize database by creating all tables., Search chunks using semantic vector search with filters. Args: query_text:…, ChunkRelationshipAssertion, get_table_args(), KnowledgeDomain, KnowledgeDomainAssignment, Base (+19 more)

### Community 50 - "services/api.ts"
Cohesion: 0.05
Nodes (46): App(), RequireAuth(), CitationPanel(), CitationPanelProps, ConfidenceBadge(), ConfidenceBadgeProps, ErrorBoundary, ErrorBoundaryProps (+38 more)

### Community 51 - "Base"
Cohesion: 0.29
Nodes (7): AccessPolicy, AccessPolicyBinding, EscalationRouteStep, Base, Access policy definitions., Access policy bindings to principals., Escalation route step.

### Community 52 - "main.py"
Cohesion: 0.11
Nodes (21): Feedback API endpoints., health_check(), get, Health check endpoint., Health check endpoint (unauthenticated). Returns: dict: Health status, get_limiter_key(), global_exception_handler(), lifespan() (+13 more)

### Community 53 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, build, dev, lint, preview, test, test:watch, typecheck

### Community 54 - "org.py"
Cohesion: 0.15
Nodes (15): EscalationRoute, Escalation route definitions., get_table_args(), Base, Organizational and Stakeholder models (org schema)., Service dependency relationships., Get table args with optional schema based on database type., Stakeholder entity representing individuals in the organization. (+7 more)

### Community 55 - ".validate_exception_date"
Cohesion: 0.25
Nodes (5): field_validator, Validate exception date is not more than 180 days in future., Validate sensitivity classification., Validate review decision., date

### Community 56 - "package.json"
Cohesion: 0.50
Nodes (3): name, type, version

### Community 57 - "test_api_feedback.py"
Cohesion: 0.08
Nodes (26): mock_answer(), mock_session(), mock_turn(), fixture, Tests for feedback API endpoints., Test feedback submission with text exceeding 2000 chars., Create a mock question session., Test feedback submission with HTML/script tags is blocked. (+18 more)

### Community 74 - "CurrentUser"
Cohesion: 0.15
Nodes (15): get_citation(), get, Session, UUID, Citation API endpoints., Retrieve citation details with source context. Returns citation with full…, Factory for role-based authorization dependencies. Creates a FastAPI dependency…, require_role() (+7 more)

### Community 75 - "app/auth.py"
Cohesion: 0.16
Nodes (9): get_redis_client(), Authentication and authorization middleware for FastAPI., Get Redis client for access scope caching., Application configuration settings., AuthAPIClient, Auth API client with circuit breaker pattern., Client for Auth API integration with circuit breaker., Validate OAuth 2.1 bearer token via Auth API. Args: token: Bearer token to… (+1 more)

### Community 76 - "schemas/governance.py"
Cohesion: 0.24
Nodes (10): FreshnessExceptionResponse, BaseModel, Source governance schemas for steward workflows., Source list item for governance views., Response model for freshness exception., Paginated source list response., Response model for source registration., SourceListItem (+2 more)

### Community 77 - "retrieval.py"
Cohesion: 0.40
Nodes (4): BaseModel, RankedChunk, Retrieval schemas for evidence assembly., Chunk with combined relevance ranking.

### Community 78 - "UserProfile"
Cohesion: 0.24
Nodes (7): User Service client with circuit breaker pattern., Client for User Service integration with circuit breaker., Retrieve user profile from User Service. Args: user_id: User identifier…, UserServiceClient, BaseModel, User profile from User Service., UserProfile

### Community 79 - "QuestionSession"
Cohesion: 0.25
Nodes (8): QuestionSession, Question session tracking user conversations., Test submitting a follow-up question to an existing session., Test getting status of an existing question., Test user cannot access another user's question., test_get_question_status_found(), test_get_question_status_wrong_user(), test_submit_question_existing_session()

### Community 80 - "start.sh"
Cohesion: 0.43
Nodes (6): check_prerequisites(), CORS_ORIGINS, DATABASE_URL, find_available_port(), portable_sed(), start.sh script

### Community 81 - "Design Decisions"
Cohesion: 0.15
Nodes (13): ADR-001: Bounded Retrieval-Augmented Model (Not Autonomous Multi-Agent), ADR-002: OpenSearch for Semantic Search, ADR-003: Three-Store Governed Pattern, ADR-004: Multi-Dimensional Confidence Scoring, ADR-005: Claim-Level Citations, ADR-006: Access-Aware Filtering, ADR-007: 365-Day Audit Retention, ADR-008: Stewardship Review Paths (+5 more)

### Community 82 - "conftest.py"
Cohesion: 0.22
Nodes (10): get_db(), Get database session., client(), db_session(), mock_auth_user(), fixture, Pytest configuration and shared fixtures., Create a fresh database session for each test. (+2 more)

### Community 83 - "Base"
Cohesion: 0.18
Nodes (11): AuditEvent, GraphSyncBatch, IngestionRun, IngestionRunItem, PrivacyRequestLink, Base, Graph sync batch tracking., Ingestion run tracking. (+3 more)

### Community 84 - "Team"
Cohesion: 0.20
Nodes (11): Team entity representing organizational teams., Team, mock_domain(), mock_source(), fixture, Test successful source registration., Create a mock knowledge domain., Test source registration with duplicate source_key. (+3 more)

### Community 87 - "CitationCoverageReport"
Cohesion: 0.22
Nodes (10): CitationCoverageReport, CitationDetail, BaseModel, Citation schemas for source attribution., Detailed citation with full source context., Citation coverage analysis., Source metadata for citation enrichment., SourceMetadata (+2 more)

### Community 88 - "Incident Response Procedure"
Cohesion: 0.18
Nodes (11): 1. Detection, 2. Triage (within 15 minutes), 3. Containment (within 1 hour for Sev 1), 4. Investigation, 5. Remediation, 6. Recovery, 7. Post-Mortem (within 5 business days), Incident Contacts (+3 more)

### Community 89 - "SourceRegistrationRequest"
Cohesion: 0.20
Nodes (9): Request model for source registration., SourceRegistrationRequest, Register a new source for governance. Args: request: Source registration…, Test valid source registration request., Test source registration with invalid sensitivity classification., Test all valid sensitivity classifications., test_sensitivity_classifications(), test_source_registration_invalid_sensitivity() (+1 more)

### Community 90 - "Security Documentation"
Cohesion: 0.22
Nodes (8): Defense in Depth, Hall of Fame, Responsible Disclosure Policy, Security Architecture, Security Documentation, Security Overview, Trust Boundaries, Vulnerability Reporting

### Community 91 - "client"
Cohesion: 0.25
Nodes (8): client(), db_session(), mock_auth(), fixture, Create test database session., Create test client with database override., override_get_db(), Override database dependency for testing.

### Community 92 - "Security Architecture"
Cohesion: 0.25
Nodes (8): Audit Logging, Authentication, Authorization, CORS Configuration, Data Protection, Input Validation, Security Architecture, Security Headers

### Community 93 - "3. Data Stores"
Cohesion: 0.29
Nodes (7): 1. Backend Service (Python + FastAPI), 2. Frontend Application (React + TypeScript + Vite), 3. Data Stores, Neo4j (Traversable Relationship Projections), OpenSearch (Searchable Projections), PostgreSQL 15.2 (Authoritative Transactional Store), System Components

### Community 94 - "Architecture Documentation"
Cohesion: 0.33
Nodes (5): Architecture Documentation, Future Enhancements, Known Limitations, Planned Improvements, System Overview

### Community 95 - "Settings"
Cohesion: 0.40
Nodes (4): Parse CORS origins string into list., Application settings loaded from environment variables., Settings, BaseSettings

### Community 96 - "Scalability Considerations"
Cohesion: 0.40
Nodes (5): Caching Strategy, Database Optimization, Horizontal Scaling, Observability for Performance, Scalability Considerations

### Community 97 - "API Security"
Cohesion: 0.40
Nodes (5): API Authentication, API Security, CORS Configuration, Rate Limiting, Security Headers

### Community 98 - "Authentication and Authorization"
Cohesion: 0.40
Nodes (5): Authentication and Authorization, Authentication Flow, Authorization Model, Session Security, Token Management

### Community 99 - "Input Validation and Output Encoding"
Cohesion: 0.40
Nodes (5): Cross-Site Request Forgery (CSRF), Cross-Site Scripting (XSS) Prevention, Input Validation, Input Validation and Output Encoding, SQL Injection Prevention

### Community 100 - "Integration Patterns"
Cohesion: 0.50
Nodes (4): Authentication & Authorization, Data Store Synchronization, External Service Communication, Integration Patterns

### Community 101 - "Technology Stack"
Cohesion: 0.50
Nodes (4): Backend, Frontend, Infrastructure, Technology Stack

### Community 102 - "Data Flow"
Cohesion: 0.50
Nodes (4): Data Flow, Feedback Capture Flow, Question Answering Flow, Source Governance Flow

### Community 103 - "Deployment Architecture"
Cohesion: 0.50
Nodes (4): Deployment Architecture, Environment Topology, GitOps Deployment, Kubernetes Configuration

### Community 104 - "Data Protection"
Cohesion: 0.50
Nodes (4): Data Protection, Encryption at Rest, Encryption in Transit, Sensitive Data Handling

### Community 105 - "Vulnerability Management"
Cohesion: 0.50
Nodes (4): Dependency Scanning, Patch Management, Security Updates, Vulnerability Management

### Community 106 - "Secrets Management"
Cohesion: 0.50
Nodes (4): Secret Rotation Procedure, Secret Storage, Secret Types, Secrets Management

### Community 107 - "Compliance"
Cohesion: 0.67
Nodes (3): Audit Procedures, Compliance, Regulatory Requirements

### Community 108 - "Security Best Practices for Developers"
Cohesion: 0.67
Nodes (3): Code Review Checklist, Common Pitfalls to Avoid, Security Best Practices for Developers

### Community 109 - "Security Training"
Cohesion: 0.67
Nodes (3): Required Training, Resources, Security Training

## Knowledge Gaps
- **343 isolated node(s):** `multiteamdependency-backend`, `MockDB`, `name`, `version`, `type` (+338 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RetrievedChunk` connect `RetrievedChunk` to `RetrievalOrchestrationService`, `test_answer_composition.py`, `OpenSearchClient`, `RankingService`, `AccessScope`, `CitationService`, `retrieval.py`, `test_citation_service.py`, `datetime`, `test_retrieval_orchestration.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `AccessScope` connect `AccessScope` to `RetrievalOrchestrationService`, `patch`, `SessionContextService`, `app/auth.py`, `CurrentUser`, `UserProfile`, `test_retrieval_orchestration.py`, `test_api_questions.py`, `QuestionIntakeService`, `verify_task3.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `api/answers.py`, `api/governance.py`, `AccessScope`, `FeedbackSubmissionRequest`, `SourceGovernanceService`, `patch`, `app/auth.py`, `UserProfile`, `conftest.py`, `main.py`, `test_api_questions.py`, `SourceRegistrationRequest`, `api/questions.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `RetrievedChunk` (e.g. with `OpenSearchClient` and `AccessControlService`) actually correct?**
  _`RetrievedChunk` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `CurrentUser` (e.g. with `get_answer()` and `get_citation()`) actually correct?**
  _`CurrentUser` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `AccessScope` (e.g. with `AccessControlService` and `QuestionIntakeService`) actually correct?**
  _`AccessScope` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Neo4jClient` (e.g. with `get_answer()` and `RelationshipPath`) actually correct?**
  _`Neo4jClient` has 14 INFERRED edges - model-reasoned connections that need verification._