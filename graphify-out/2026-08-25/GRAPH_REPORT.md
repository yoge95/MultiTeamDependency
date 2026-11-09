# Graph Report - multiteamdependency  (2026-08-25)

## Corpus Check
- 101 files · ~42,980 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1273 nodes · 2224 edges · 88 communities (69 shown, 19 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 200 edges (avg confidence: 0.94)
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
- ops.py
- EscalationRoutingService
- dependencies
- SessionContextService
- compilerOptions
- app/__init__.py
- multiteamdependency-backend
- user_service_client.py
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
- AnswerRecord
- OpenSearchClient
- RankingService
- services/__init__.py
- api/governance.py
- CurrentUser
- FeedbackSubmissionRequest
- RetrievedChunk
- patch
- ConfidenceScoringService
- test_api_governance_unit.py
- CitationService
- CircuitBreaker
- submit_feedback
- SourceApprovalRequest
- test_citation_service.py
- knowledge.py
- services/api.ts
- datetime
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
- confidence_scoring_service.py
- app/auth.py
- schemas/governance.py
- retrieval_orchestration_service.py
- UserProfile
- interaction.py
- start.sh
- AuthAPIClient
- .__init__
- ._synthesize_answer_text
- .__init__
- { login, health, submitQuestion, getQuestionStatus, getAnswer, getCitation, submitFeedback }
- stop.sh
- test_answer_composition.py

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

## Communities (88 total, 19 thin omitted)

### Community 0 - "devDependencies"
Cohesion: 0.12
Nodes (17): eslint, eslint-plugin-react-hooks, devDependencies, eslint, eslint-plugin-react-hooks, happy-dom, jsdom, postcss (+9 more)

### Community 1 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution (+16 more)

### Community 2 - "asyncio"
Cohesion: 0.12
Nodes (17): asyncio, Test that retrieve_evidence filters chunks by access control., Test that chunks are enriched with PostgreSQL metadata., Test OpenSearch client search_chunks interface., Test OpenSearch client health check., Test Neo4j client get_ownership_path interface., Test Neo4j client get_dependencies interface., Test Neo4j client get_escalation_route interface. (+9 more)

### Community 3 - "test_api_governance.py"
Cohesion: 0.07
Nodes (32): Team entity representing organizational teams., Team, mock_domain(), mock_source(), fixture, Tests for source governance API endpoints., Test that listing sources requires knowledge_steward or governance_reviewer…, Test successful source registration. (+24 more)

### Community 4 - "api/answers.py"
Cohesion: 0.17
Nodes (16): get_answer(), get, Session, UUID, Answer API endpoints., Retrieve answer with citations, confidence score, freshness warnings, and…, AnswerLimitationResponse, AnswerResponse (+8 more)

### Community 5 - "Multi-team Knowledge Assistant"
Cohesion: 0.06
Nodes (33): Accessing the Application, API Documentation, Architecture Overview, Backend Environment Variables, Backend Setup, Configuration, Contributing, Database (+25 more)

### Community 6 - "AccessScope"
Cohesion: 0.13
Nodes (15): Factory for role-based authorization dependencies. Creates a FastAPI dependency…, require_role(), AccessScope, Access scope for a user session., Filter chunks based on user's access scope. Enforces access control by: 1.…, Check if a single chunk is accessible to the user. Args: chunk: Chunk to check…, Tests for authentication and authorization., Tests for require_auth dependency. (+7 more)

### Community 7 - "ops.py"
Cohesion: 0.11
Nodes (19): Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online(), SQLAlchemy ORM models for all database schemas., AuditEvent, get_table_args(), GraphSyncBatch (+11 more)

### Community 8 - "EscalationRoutingService"
Cohesion: 0.19
Nodes (10): EscalationRoutingService, Session, UUID, Get platform administrator contacts., Get fallback contacts when no specific route is found., Retrieve predefined escalation route by ID. Args: route_id: Escalation route ID…, Service for identifying escalation routes when confidence is low., Identify next-step contacts via Neo4j traversal. Args: intent_classification:… (+2 more)

### Community 9 - "dependencies"
Cohesion: 0.15
Nodes (13): clsx, dependencies, clsx, react, react-dom, react-router-dom, tailwind-merge, @tanstack/react-query (+5 more)

### Community 10 - "SessionContextService"
Cohesion: 0.18
Nodes (9): Session, UUID, Session context service for managing conversation sessions., Service for managing question sessions and context., Initialize session context service., Create a new question session. Args: user_id: UUID of the authenticated user…, Get an existing session if it belongs to the user. Args: session_id: UUID of…, Update session last activity timestamp. Args: session_id: UUID of the session (+1 more)

### Community 11 - "compilerOptions"
Cohesion: 0.20
Nodes (9): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, strict, include (+1 more)

### Community 19 - "user_service_client.py"
Cohesion: 0.18
Nodes (9): CircuitBreaker, CircuitBreakerOpen, Exception, User Service client with circuit breaker pattern., Exception raised when circuit breaker is open., Circuit breaker implementation for external service calls., Execute function with circuit breaker protection., Record a failure and potentially open the circuit. (+1 more)

### Community 20 - "test_retrieval_orchestration.py"
Cohesion: 0.09
Nodes (28): AccessControlService, UUID, Access control service for filtering retrieved content by user's access scope., Check if user can access a specific source. Args: source_record_id: Source…, Service for enforcing access-aware retrieval filtering., Get list of domains the user can access. Args: access_scope: User's access…, mock_db(), fixture (+20 more)

### Community 23 - "test_api_questions.py"
Cohesion: 0.06
Nodes (44): QuestionTurn, Question turn within a session., client(), db_session(), mock_current_user(), fixture, Tests for question submission and status endpoints., Test submitting a follow-up question to an existing session. (+36 more)

### Community 24 - "TASK-3 Implementation: Core API Routes and Question Intake"
Cohesion: 0.07
Nodes (27): 1. FastAPI Application (`app/main.py`), 2. Health Endpoint (`app/api/health.py`), 3. Question Submission Endpoint (`app/api/questions.py`), 4. Question Status Endpoint (`app/api/questions.py`), 5. Intent Classification (`app/services/question_intake_service.py`), 6. Session Management (`app/services/session_context_service.py`), 7. Request/Response Validation (`app/schemas/questions.py`), 8. Database Integration (+19 more)

### Community 25 - "test_api_answers.py"
Cohesion: 0.07
Nodes (33): CitationReference, Citation reference linking answers to source chunks., client(), db_session(), mock_auth(), fixture, Tests for answer API endpoints., Test successful answer retrieval. (+25 more)

### Community 26 - "QuestionIntakeService"
Cohesion: 0.12
Nodes (15): UUID, QuestionIntakeService, Classify question intent based on keywords and context. This is a simple rule-…, Determine candidate knowledge domains based on intent and question., Detect ambiguity flags in the question., Generate a clarification prompt based on ambiguity flags., Service for handling question intake and intent classification., Get the status of a submitted question. Args: question_id: UUID of the question… (+7 more)

### Community 27 - "verify_task3.py"
Cohesion: 0.17
Nodes (14): IntentClassification, BaseModel, field_validator, QuestionStatusResponse, QuestionSubmissionRequest, QuestionSubmissionResponse, Pydantic schemas for question submission and status., Request schema for question submission. (+6 more)

### Community 28 - "PaginatedResponse"
Cohesion: 0.15
Nodes (11): ErrorResponse, PaginatedResponse, BaseModel, Common Pydantic schemas used across modules., Mixin for created_at and updated_at timestamps., Standard paginated response wrapper., Calculate total number of pages., Check if there are more pages. (+3 more)

### Community 29 - "Infrastructure as Code"
Cohesion: 0.05
Nodes (41): Additional Resources, ArgoCD Rollback, Backend Deployment, Backend Image, Backend Secrets, Base Manifests, CD Production Pipeline (.github/workflows/cd-production.yml), CD Staging Pipeline (.github/workflows/cd-staging.yml) (+33 more)

### Community 30 - "Neo4jClient"
Cohesion: 0.11
Nodes (17): Neo4jClient, UUID, Neo4j client for relationship graph traversal., Client for Neo4j relationship graph operations. In a production implementation,…, Find shortest path between two entities. Args: source_id: Source entity UUID…, Check Neo4j connection health. Returns: True if connection is healthy, Initialize Neo4j client. Args: uri: Neo4j connection URI (from environment)…, Establish connection to Neo4j. (+9 more)

### Community 31 - "api/questions.py"
Cohesion: 0.14
Nodes (15): _apply_rate_limit(), get_question_intake_service(), get_question_status(), get, post, Request, Session, UUID (+7 more)

### Community 32 - "RetrievalOrchestrationService"
Cohesion: 0.11
Nodes (16): UUID, Retrieve chunks from OpenSearch with semantic search and filters. Args:…, Enrich chunks with PostgreSQL governance metadata. Args: chunks: List of chunks…, Retrieve relationship paths from Neo4j based on intent. Args: request: Original…, Retrieve ownership relationships for entities mentioned in chunks., Service for orchestrating multi-source retrieval from OpenSearch, Neo4j, and…, Retrieve service dependency relationships., Retrieve escalation routes for domains in chunks. (+8 more)

### Community 33 - "AnswerRecord"
Cohesion: 0.15
Nodes (16): AnswerLimitation, AnswerRecord, Answer limitation tracking., Answer record with confidence and citations., ConfidenceScoreDetail, Detailed confidence scoring breakdown., AnswerCompositionService, UUID (+8 more)

### Community 34 - "OpenSearchClient"
Cohesion: 0.09
Nodes (14): OpenSearchClient, UUID, OpenSearch client for semantic chunk retrieval., Index a chunk document in OpenSearch. Args: chunk_data: Chunk document with all…, Client for OpenSearch chunk index operations. In a production implementation,…, Delete a chunk from the index. Args: chunk_id: Chunk UUID to delete Returns:…, Check OpenSearch cluster health. Returns: True if cluster is healthy, Initialize OpenSearch client. Args: endpoint: OpenSearch endpoint URL (from… (+6 more)

### Community 35 - "RankingService"
Cohesion: 0.10
Nodes (17): Session, RankingService, Calculate freshness score based on review recency. Args: last_reviewed_at:…, Service for ranking retrieved chunks by combined relevance., Calculate approval score based on source state. Args: approval_state: Approval…, Initialize ranking service. Args: db: Database session for fetching governance…, Calculate access score based on access clarity. Args: access_scope_tag: Access…, Rank chunks combining retrieval scores with governance metadata. Scoring… (+9 more)

### Community 37 - "api/governance.py"
Cohesion: 0.23
Nodes (13): approve_source(), grant_freshness_exception(), list_sources(), get, post, Session, UUID, Source governance API endpoints. (+5 more)

### Community 38 - "CurrentUser"
Cohesion: 0.21
Nodes (10): CurrentUser, Current authenticated user context., UUID, Source governance service for steward workflows., Approve or review a source. Args: source_id: Source record ID request: Approval…, Service for source governance workflows., Grant freshness exception for a source. Args: source_id: Source record ID…, List sources filtered by user's steward domains. Args: current_user:… (+2 more)

### Community 39 - "FeedbackSubmissionRequest"
Cohesion: 0.11
Nodes (22): FeedbackSubmissionRequest, field_validator, Request model for feedback submission., Validate feedback type., Validate feedback text does not contain HTML/script tags., Unit tests for feedback API endpoints (schema validation only)., Test valid feedback submission request., Test feedback submission with invalid feedback_type. (+14 more)

### Community 40 - "RetrievedChunk"
Cohesion: 0.07
Nodes (32): Single retrieved chunk from OpenSearch., RetrievedChunk, Test freshness status determination., test_determine_freshness_status(), confidence_service(), fixture, Tests for confidence scoring service., Test confidence scoring with low citation coverage. (+24 more)

### Community 41 - "patch"
Cohesion: 0.17
Nodes (19): get_current_user(), FastAPI dependency for authenticated user context. Validates OAuth 2.1 bearer…, CircuitBreakerOpen, Exception, Exception raised when circuit breaker is open., Response from Auth API token validation., TokenValidationResponse, Test answer retrieval without authentication. (+11 more)

### Community 42 - "ConfidenceScoringService"
Cohesion: 0.14
Nodes (10): Session, ConfidenceScoringService, Service for calculating multi-dimensional confidence scores., Score freshness based on review dates and staleness state. Args: chunks:…, Score consistency across retrieved chunks (simplified heuristic). Args: chunks:…, Determine confidence band from overall score., Identify confidence flags based on dimension scores., Generate human-readable explanation of confidence score. (+2 more)

### Community 43 - "test_api_governance_unit.py"
Cohesion: 0.15
Nodes (17): FreshnessExceptionRequest, Request model for source registration., Request model for freshness exception., SourceRegistrationRequest, Unit tests for governance API endpoints (schema validation only)., Test valid source registration request., Test source registration with invalid sensitivity classification., Test valid freshness exception request. (+9 more)

### Community 44 - "CitationService"
Cohesion: 0.08
Nodes (27): get_citation(), get, Session, UUID, Citation API endpoints., Retrieve citation details with source context. Returns citation with full…, CitationCoverageReport, CitationDetail (+19 more)

### Community 45 - "CircuitBreaker"
Cohesion: 0.17
Nodes (9): CircuitBreaker, Circuit breaker implementation for external service calls., Execute function with circuit breaker protection., Record a failure and potentially open the circuit., Reset the circuit breaker to closed state., Tests for circuit breaker functionality., Test circuit breaker opens after failure threshold., Test circuit breaker transitions to half-open after recovery timeout. (+1 more)

### Community 46 - "submit_feedback"
Cohesion: 0.16
Nodes (13): FeedbackSubmissionRequest, post, Session, Submit feedback for an answer. Args: request: Feedback submission request…, submit_feedback(), CitationFeedbackItem, FeedbackListResponse, FeedbackSubmissionResponse (+5 more)

### Community 47 - "SourceApprovalRequest"
Cohesion: 0.25
Nodes (8): Request model for source approval., SourceApprovalRequest, Test all valid review decisions., Test valid source approval request., Test source approval with invalid review decision., test_review_decisions(), test_source_approval_invalid_decision(), test_source_approval_request_valid()

### Community 48 - "test_citation_service.py"
Cohesion: 0.09
Nodes (22): citation_service(), db_session(), fixture, Tests for citation service., Test claim extraction from answer text., Test that meta sentences are filtered out., Test matching a claim to relevant chunk., Test matching with no relevant chunks. (+14 more)

### Community 49 - "knowledge.py"
Cohesion: 0.13
Nodes (24): ChunkRelationshipAssertion, get_table_args(), KnowledgeDomain, KnowledgeDomainAssignment, Base, Knowledge governance models (knowledge schema)., Source version tracking., Source review records. (+16 more)

### Community 50 - "services/api.ts"
Cohesion: 0.05
Nodes (46): App(), RequireAuth(), CitationPanel(), CitationPanelProps, ConfidenceBadge(), ConfidenceBadgeProps, ErrorBoundary, ErrorBoundaryProps (+38 more)

### Community 51 - "datetime"
Cohesion: 0.18
Nodes (13): AccessPolicy, AccessPolicyBinding, EscalationRoute, EscalationRouteStep, get_table_args(), Base, Governance models for access policies and escalation routes (governance schema)., Get table args with optional schema based on database type. (+5 more)

### Community 52 - "main.py"
Cohesion: 0.06
Nodes (38): Feedback API endpoints., health_check(), get, Health check endpoint., Health check endpoint (unauthenticated). Returns: dict: Health status, FastAPI dependency enforcing authentication. This is an explicit authentication…, require_auth(), get_db() (+30 more)

### Community 53 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, build, dev, lint, preview, test, test:watch, typecheck

### Community 54 - "org.py"
Cohesion: 0.18
Nodes (13): get_table_args(), Base, Organizational and Stakeholder models (org schema)., Service dependency relationships., Get table args with optional schema based on database type., Stakeholder entity representing individuals in the organization., Team membership association between stakeholders and teams., Service entity representing organizational services. (+5 more)

### Community 55 - ".validate_exception_date"
Cohesion: 0.25
Nodes (5): field_validator, Validate exception date is not more than 180 days in future., Validate sensitivity classification., Validate review decision., date

### Community 56 - "package.json"
Cohesion: 0.50
Nodes (3): name, type, version

### Community 57 - "test_api_feedback.py"
Cohesion: 0.08
Nodes (26): mock_answer(), mock_session(), mock_turn(), fixture, Tests for feedback API endpoints., Test feedback submission with text exceeding 2000 chars., Create a mock question session., Test feedback submission with HTML/script tags is blocked. (+18 more)

### Community 74 - "confidence_scoring_service.py"
Cohesion: 0.33
Nodes (5): ConfidenceDimensions, Confidence score dimensions., Confidence scoring service calculating multi-dimensional answer confidence., Test response type determination., test_determine_response_type()

### Community 75 - "app/auth.py"
Cohesion: 0.16
Nodes (10): get_redis_client(), Authentication and authorization middleware for FastAPI., Get Redis client for access scope caching., Application configuration settings., Parse CORS origins string into list., Application settings loaded from environment variables., Settings, Auth API client with circuit breaker pattern. (+2 more)

### Community 76 - "schemas/governance.py"
Cohesion: 0.21
Nodes (12): FreshnessExceptionResponse, BaseModel, Source governance schemas for steward workflows., Source list item for governance views., Response model for freshness exception., Paginated source list response., Response model for source registration., Response model for source approval. (+4 more)

### Community 77 - "retrieval_orchestration_service.py"
Cohesion: 0.18
Nodes (13): EvidenceBundle, BaseModel, RankedChunk, Retrieval schemas for evidence assembly., Complete evidence bundle for answer composition., Request for evidence retrieval., Chunk with combined relevance ranking., RetrievalRequest (+5 more)

### Community 78 - "UserProfile"
Cohesion: 0.22
Nodes (7): Client for User Service integration with circuit breaker., Retrieve user profile from User Service. Args: user_id: User identifier…, UserServiceClient, BaseModel, Authentication and authorization schemas., User profile from User Service., UserProfile

### Community 79 - "interaction.py"
Cohesion: 0.11
Nodes (20): FeedbackRecord, FeedbackReview, get_table_args(), Base, QuestionSession, Interaction models for questions, answers, and feedback (interaction schema)., Get table args with optional schema based on database type., Feedback review by stewards. (+12 more)

### Community 80 - "start.sh"
Cohesion: 0.43
Nodes (6): check_prerequisites(), CORS_ORIGINS, DATABASE_URL, find_available_port(), portable_sed(), start.sh script

### Community 81 - "AuthAPIClient"
Cohesion: 0.40
Nodes (3): AuthAPIClient, Client for Auth API integration with circuit breaker., Validate OAuth 2.1 bearer token via Auth API. Args: token: Bearer token to…

### Community 83 - "._synthesize_answer_text"
Cohesion: 0.33
Nodes (3): Synthesize answer text from evidence chunks. Args: question_text: Original…, Generate intent-specific introduction., Append relationship context to answer.

### Community 87 - "test_answer_composition.py"
Cohesion: 0.09
Nodes (22): answer_composition_service(), db_session(), fixture, Tests for answer composition service., Test answer composition with no evidence., Test answer text synthesis for ownership intent., Test answer text synthesis for dependency intent., Test intro generation for different intents. (+14 more)

## Knowledge Gaps
- **166 isolated node(s):** `multiteamdependency-backend`, `MockDB`, `name`, `version`, `type` (+161 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RetrievedChunk` connect `RetrievedChunk` to `RetrievalOrchestrationService`, `AnswerRecord`, `OpenSearchClient`, `RankingService`, `AccessScope`, `confidence_scoring_service.py`, `ConfidenceScoringService`, `CitationService`, `retrieval_orchestration_service.py`, `test_citation_service.py`, `knowledge.py`, `._synthesize_answer_text`, `test_retrieval_orchestration.py`, `test_answer_composition.py`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `AccessScope` connect `AccessScope` to `RetrievalOrchestrationService`, `patch`, `SessionContextService`, `app/auth.py`, `retrieval_orchestration_service.py`, `UserProfile`, `test_retrieval_orchestration.py`, `test_api_questions.py`, `QuestionIntakeService`, `verify_task3.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `QuestionIntakeService` connect `QuestionIntakeService` to `AnswerRecord`, `AccessScope`, `SessionContextService`, `interaction.py`, `.__init__`, `test_api_questions.py`, `verify_task3.py`, `api/questions.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `RetrievedChunk` (e.g. with `OpenSearchClient` and `AccessControlService`) actually correct?**
  _`RetrievedChunk` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `CurrentUser` (e.g. with `get_answer()` and `get_citation()`) actually correct?**
  _`CurrentUser` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `AccessScope` (e.g. with `AccessControlService` and `QuestionIntakeService`) actually correct?**
  _`AccessScope` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Neo4jClient` (e.g. with `get_answer()` and `RelationshipPath`) actually correct?**
  _`Neo4jClient` has 14 INFERRED edges - model-reasoned connections that need verification._