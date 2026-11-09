# Development Guide

## Local Development Setup

### Prerequisites

Ensure these tools are installed before starting:

- **Python 3.10+** (required)
  ```bash
  python3 --version  # Should show 3.10 or higher
  ```

- **Node.js 18+** (required)
  ```bash
  node --version  # Should show v18 or higher
  ```

- **pip** (Python package installer)
  ```bash
  python3 -m pip --version
  ```

- **npm** (Node package manager)
  ```bash
  npm --version
  ```

- **Git** (version control)
  ```bash
  git --version
  ```

### Quick Start

The fastest way to start development:

```bash
# Clone repository
git clone https://github.com/your-org/multiteamdependency.git
cd multiteamdependency

# Start entire stack
./start.sh

# Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:9000
# API Docs: http://localhost:9000/docs

# Login with default credentials
# Email: admin@example.com
# Password: admin123

# Stop services when done
./stop.sh
```

## Backend Development

### Initial Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (use . not -e for editable mode)
pip install .

# Install development dependencies
pip install pytest pytest-cov ruff mypy
```

### Environment Configuration

Create `backend/.env` file:

```bash
# Database (SQLite for local dev, PostgreSQL for production)
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# External Services (for local dev, use mock/stub implementations)
AUTH_API_URL=http://localhost:8080
USER_SERVICE_URL=http://localhost:8081
REDIS_URL=redis://localhost:6379/0

# OpenSearch (optional - stub implementation in dev)
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USE_SSL=false

# Neo4j (optional - stub implementation in dev)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Application
DEBUG=true
LOG_LEVEL=INFO
API_BASE_PATH=/api/v1
```

### Database Management

#### Running Migrations

```bash
cd backend
source .venv/bin/activate

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current

# View migration history
alembic history
```

#### Creating New Migrations

```bash
cd backend
source .venv/bin/activate

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column to users table"

# Create empty migration (for data migrations or manual DDL)
alembic revision -m "Migrate legacy data"

# Edit generated migration file in backend/alembic/versions/
# Then apply it
alembic upgrade head
```

#### Seeding Development Data

```bash
cd backend
source .venv/bin/activate

# Run seed script (idempotent - safe to run multiple times)
python app/seed.py

# Verify seed data
python -c "
from app.database import SessionLocal
from app.models.org import Stakeholder
db = SessionLocal()
admin = db.query(Stakeholder).filter_by(email='admin@example.com').first()
print(f'Admin: {admin.display_name if admin else \"Not found\"}')
db.close()
"
```

### Running the Backend

```bash
cd backend
source .venv/bin/activate

# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000

# Or without reload (production-like)
uvicorn app.main:app --host 0.0.0.0 --port 9000

# With custom log level
uvicorn app.main:app --reload --log-level debug
```

Access points:
- API: http://localhost:9000
- Swagger UI: http://localhost:9000/docs
- ReDoc: http://localhost:9000/redoc
- OpenAPI JSON: http://localhost:9000/openapi.json

### Running Backend Tests

```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_valid_token_with_profile

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # On macOS
# Or: xdg-open htmlcov/index.html  # On Linux
```

### Linting and Type Checking

```bash
cd backend
source .venv/bin/activate

# Run ruff linter
ruff check app/

# Auto-fix issues
ruff check app/ --fix

# Type checking with mypy
mypy app/

# Check specific module
mypy app/services/question_intake_service.py
```

## Frontend Development

### Initial Setup

```bash
cd frontend

# Install dependencies
npm install

# Install development tools globally (optional)
npm install -g typescript eslint
```

### Environment Configuration

Create `frontend/.env` file:

```bash
# Backend API URL
VITE_API_URL=http://localhost:9000
```

### Running the Frontend

```bash
cd frontend

# Development server with hot reload
npm run dev

# Specify custom port
npm run dev -- --port 5173

# Open browser automatically
npm run dev -- --open
```

Access frontend at: http://localhost:5173

### Building for Production

```bash
cd frontend

# Create production build
npm run build

# Preview production build locally
npm run preview
```

Build output appears in `frontend/dist/`.

### Running Frontend Tests

```bash
cd frontend

# Run tests once
npm test

# Or with explicit vitest command
npx vitest run

# Run tests in watch mode (for development)
npx vitest

# Run with coverage
npx vitest run --coverage

# Run specific test file
npx vitest run tests/utils.test.ts

# Run tests matching pattern
npx vitest run --grep "authentication"
```

### Linting and Type Checking

```bash
cd frontend

# Run ESLint
npm run lint

# Auto-fix ESLint issues
npm run lint -- --fix

# Type check with TypeScript (no emit)
npx tsc --noEmit

# Watch mode for type checking
npx tsc --noEmit --watch
```

## Code Conventions

### Python Backend Conventions (PEP 8)

**Naming Conventions**:
- `lowercase_with_underscores` for variables, functions, methods, config fields
- `UPPERCASE_WITH_UNDERSCORES` for constants only
- `PascalCase` for class names
- `_leading_underscore` for internal/private functions

**Example**:
```python
# Good
database_url: str = "sqlite:///./app.db"
MAX_RETRIES: int = 3

class QuestionIntakeService:
    def process_question(self, question_text: str) -> dict:
        return self._classify_intent(question_text)
    
    def _classify_intent(self, text: str) -> str:
        # Internal helper
        pass

# Bad
DATABASE_URL: str = "..."  # Config field should be lowercase
databaseUrl: str = "..."    # No camelCase in Python
```

**Import Organization**:
```python
# Standard library imports
import os
from datetime import datetime

# Third-party imports
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Local imports
from app.database import get_db
from app.models.org import Team
from app.services.question_intake_service import QuestionIntakeService
```

**Docstrings**:
```python
def retrieve_evidence(question: str, access_scope: dict) -> dict:
    """Retrieve evidence bundle from multiple data sources.
    
    Args:
        question: User's question text
        access_scope: User's access permissions and domain context
    
    Returns:
        Evidence bundle with chunks, relationships, and metadata
    """
    pass
```

### TypeScript Frontend Conventions

**Naming Conventions**:
- `camelCase` for variables, functions, parameters
- `PascalCase` for components, classes, types, interfaces
- `UPPER_SNAKE_CASE` for constants
- Avoid `I` prefix for interfaces (use `type` or plain interface names)

**Example**:
```typescript
// Good
const apiBaseUrl = import.meta.env.VITE_API_URL;
const MAX_RETRIES = 3;

interface User {
  id: number;
  email: string;
}

function fetchUserProfile(userId: number): Promise<User> {
  // ...
}

// Bad
const APIBaseURL = "...";        // Should be camelCase
interface IUser { /* ... */ }    // Avoid I prefix
function FetchUserProfile() {}   // Should be camelCase
```

**Component Structure**:
```typescript
// Imports
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Types
interface QuestionPageProps {
  sessionId?: string;
}

// Component
export function QuestionPage({ sessionId }: QuestionPageProps) {
  // State hooks
  const [question, setQuestion] = useState('');
  
  // Other hooks
  const navigate = useNavigate();
  
  // Event handlers
  const handleSubmit = async (e: React.FormEvent) => {
    // ...
  };
  
  // Render
  return (
    <div>
      {/* JSX */}
    </div>
  );
}
```

**File Organization**:
```
src/
├── pages/           # Page components (one route = one page)
├── components/      # Reusable components
├── context/         # React context providers
├── services/        # API clients and business logic
├── types/           # TypeScript type definitions
├── lib/             # Utilities and helpers
└── styles/          # Global styles (if any)
```

## Debugging Tips

### Backend Debugging

**Enable Debug Logging**:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload
```

**Interactive Python Debugger**:
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint() in Python 3.7+
breakpoint()
```

**View SQLAlchemy Queries**:
```python
# In app/database.py
engine = create_engine(
    settings.database_url,
    echo=True  # Logs all SQL queries
)
```

**Check Database State**:
```bash
# SQLite
sqlite3 app.db "SELECT * FROM org.stakeholder WHERE email='admin@example.com';"

# PostgreSQL
psql $DATABASE_URL -c "SELECT * FROM org.stakeholder WHERE email='admin@example.com';"
```

### Frontend Debugging

**React DevTools**:
- Install React Developer Tools browser extension
- Inspect component state and props
- Profile component renders

**Network Debugging**:
```typescript
// Enable request logging in api.ts
export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  console.log('API Request:', endpoint, options);  // Add this
  const response = await fetch(url, config);
  console.log('API Response:', response.status, await response.clone().json());  // Add this
  // ...
}
```

**Browser DevTools**:
- Network tab: inspect API calls, check request/response payloads
- Console tab: view logs and errors
- Application tab: inspect localStorage (auth token)

**Debugging Auth Issues**:
```typescript
// Check stored token
console.log('Token:', localStorage.getItem('access_token'));

// Test API call
const response = await fetch('http://localhost:9000/api/v1/health');
console.log('Health check:', response.status, await response.text());
```

## Common Development Tasks

### Adding a New API Endpoint

1. **Define Pydantic schemas** (`backend/app/schemas/`):
```python
# backend/app/schemas/teams.py
from pydantic import BaseModel
from uuid import UUID

class TeamResponse(BaseModel):
    team_id: UUID
    team_name: str
    team_code: str
```

2. **Create service method** (`backend/app/services/`):
```python
# backend/app/services/team_service.py
from app.models.org import Team

class TeamService:
    def get_team(self, db: Session, team_id: UUID) -> Team:
        return db.query(Team).filter_by(team_id=team_id).first()
```

3. **Create API route** (`backend/app/api/`):
```python
# backend/app/api/teams.py
from fastapi import APIRouter, Depends
from app.schemas.teams import TeamResponse

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/{team_id}", response_model=TeamResponse)
def get_team(team_id: UUID, db: Session = Depends(get_db)):
    team = TeamService().get_team(db, team_id)
    return team
```

4. **Register router** (`backend/app/main.py`):
```python
from app.api import teams
app.include_router(teams.router, prefix=settings.api_base_path)
```

5. **Write tests** (`backend/tests/`):
```python
# backend/tests/test_api_teams.py
def test_get_team(client, db_session):
    # Create test team
    team = Team(team_id=uuid4(), team_name="Test", team_code="TEST")
    db_session.add(team)
    db_session.commit()
    
    # Call API
    response = client.get(f"/api/v1/teams/{team.team_id}")
    assert response.status_code == 200
    assert response.json()["team_name"] == "Test"
```

### Adding a New Frontend Page

1. **Create page component** (`frontend/src/pages/`):
```typescript
// frontend/src/pages/TeamDetailPage.tsx
export function TeamDetailPage() {
  const { teamId } = useParams();
  const [team, setTeam] = useState<Team | null>(null);
  
  useEffect(() => {
    fetchTeam(teamId).then(setTeam);
  }, [teamId]);
  
  return <div>{/* Render team details */}</div>;
}
```

2. **Add route** (`frontend/src/App.tsx`):
```typescript
<Route path="/teams/:teamId" element={
  <RequireAuth>
    <TeamDetailPage />
  </RequireAuth>
} />
```

3. **Create API method** (`frontend/src/services/api.ts`):
```typescript
export async function fetchTeam(teamId: string): Promise<Team> {
  return request<Team>(`/teams/${teamId}`);
}
```

4. **Write test** (`frontend/tests/pages.test.tsx`):
```typescript
test('TeamDetailPage renders team name', async () => {
  render(<TeamDetailPage />);
  await waitFor(() => {
    expect(screen.getByText('Team Name')).toBeInTheDocument();
  });
});
```

## Troubleshooting

### "Module not found" errors

**Backend**:
```bash
# Reinstall dependencies
cd backend
pip install --force-reinstall .
```

**Frontend**:
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Port already in use

```bash
# Find process using port
lsof -ti:9000  # Backend
lsof -ti:5173  # Frontend

# Kill process
kill $(lsof -ti:9000)
```

### Database migration conflicts

```bash
cd backend
source .venv/bin/activate

# Check current state
alembic current

# If multiple heads
alembic merge heads -m "Merge conflicting migrations"

# Then upgrade
alembic upgrade head
```

### CORS errors in browser

Check `backend/.env`:
```bash
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

Restart backend after changing CORS configuration.

### Authentication failures

1. Check token in browser DevTools → Application → Local Storage
2. Verify backend is running: `curl http://localhost:9000/api/v1/health`
3. Check credentials match seed data: `admin@example.com` / `admin123`
4. Clear localStorage and login again

---

**Document Version**: 1.0  
**Last Updated**: 2026-08-25  
**Maintained By**: Development Team
