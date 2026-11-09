# Multi-team Knowledge Assistant

A bounded internal knowledge assistant that answers questions about team ownership, service dependencies, stakeholder routing, onboarding guidance, runbooks, and governance processes using approved enterprise sources.

## Architecture Overview

The platform uses a three-store governed pattern:
- **PostgreSQL 15.2**: Authoritative transactional store for source governance, sessions, answers, feedback, and audit records
- **OpenSearch**: Searchable projections for semantic and filtered retrieval
- **Neo4j**: Traversable relationship projections for team ownership and service dependencies

## Prerequisites

- **Python 3.10+** (required)
- **Node.js 18+** (required)
- **npm** (required)
- **pip** (required)
- PostgreSQL 15.2 (optional - SQLite used by default for local development)

## Quick Start

The fastest way to get started is using the provided startup scripts. They will:
- Check prerequisites
- Install dependencies
- Set up the database
- Seed default data
- Start both backend and frontend services

### macOS / Linux

```bash
# Make scripts executable (first time only)
chmod +x start.sh stop.sh

# Start the full stack
./start.sh
```

### Windows

```cmd
# Start the full stack
start.bat
```

The scripts will automatically:
1. Detect available ports (starting at 9000 for backend, 5173 for frontend)
2. Create Python virtual environment
3. Install all dependencies
4. Run database migrations
5. Seed the database with sample data
6. Start backend and frontend services
7. Display service URLs and credentials

### Accessing the Application

After running the startup script, access:
- **Frontend Web UI**: http://localhost:5173
- **Backend API**: http://localhost:9000
- **API Documentation**: http://localhost:9000/docs

### Default Credentials

```
Email:    admin@example.com
Password: admin123
```

### Stopping Services

```bash
# macOS / Linux
./stop.sh

# Windows
stop.bat
```

## Project Structure

```
multiteamdependency/
├── backend/              # Python FastAPI backend service
│   ├── app/
│   │   ├── main.py      # Application entry point
│   │   ├── database.py  # Database session management
│   │   ├── config.py    # Configuration settings
│   │   ├── models/      # SQLAlchemy ORM models
│   │   ├── api/         # API route modules
│   │   ├── services/    # Business logic services
│   │   ├── schemas/     # Pydantic request/response models
│   │   └── seed.py      # Database seed data
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   └── pyproject.toml   # Python dependencies
├── frontend/             # React TypeScript frontend
│   ├── src/
│   │   ├── main.tsx     # Frontend entry point
│   │   ├── App.tsx      # Root component with routing
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable components
│   │   ├── context/     # React context providers
│   │   └── services/    # API client
│   ├── tests/           # Frontend tests
│   ├── package.json     # Node dependencies
│   └── vite.config.ts   # Build configuration
├── infrastructure/       # Kubernetes manifests and IaC
├── docs/                # Documentation
├── storage/             # Local SQLite database (auto-created)
├── shared_config.json   # Cross-layer configuration
├── start.sh            # Unix/macOS/Linux startup script
├── start.bat           # Windows startup script
├── stop.sh             # Unix/macOS/Linux shutdown script
└── stop.bat            # Windows shutdown script
```

## Manual Development Setup

If you prefer to set up services manually instead of using the startup scripts:

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install .

# Set up database (SQLite by default)
export DATABASE_URL="sqlite:///./app.db"  # Optional - this is the default
alembic upgrade head

# Seed database with default admin and sample data
python app/seed.py

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL
echo "VITE_API_URL=http://localhost:9000" > .env

# Start development server
npm run dev -- --port 5173
```

### Running Tests

```bash
# Backend tests
cd backend
pytest -v

# Frontend tests
cd frontend
npm test
```

## Configuration

### Backend Environment Variables

The backend reads configuration from environment variables. For local development, the startup scripts set sensible defaults.

**Optional `.env` file** (backend/.env):
```bash
# Database (defaults to SQLite if not set)
DATABASE_URL=sqlite:///./app.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/knowledge_assistant

# Application settings
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=INFO

# External service integrations
AUTH_API_URL=http://auth-api:8080
USER_SERVICE_URL=http://user-service:8081

# CORS (automatically configured by start.sh)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend Environment Variables

The startup scripts automatically create `frontend/.env` with the correct backend URL.

**Manual configuration** (frontend/.env):
```bash
VITE_API_URL=http://localhost:9000
```

### Shared Configuration

Cross-layer configuration is defined in `shared_config.json` at the project root. The startup scripts automatically update ports in this file when dynamic port detection is used.

```json
{
  "api_base_path": "/api/v1",
  "ports": {
    "backend": 9000,
    "frontend_web": 5173
  },
  "auth": {
    "login_endpoint": "/api/v1/auth/login"
  }
}
```

## API Documentation

When the backend is running, interactive API documentation is available at:
- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc
- **OpenAPI JSON**: http://localhost:9000/openapi.json

## Database

### SQLite (Default for Local Development)

The application uses SQLite by default, requiring no external database setup. The database file is created automatically at `storage/app.db`.

### PostgreSQL (Production)

For production or if you prefer PostgreSQL:

```bash
# Set DATABASE_URL before starting
export DATABASE_URL="postgresql://user:password@localhost:5432/knowledge_assistant"
./start.sh
```

### Migrations

Database migrations are managed with Alembic:

```bash
cd backend

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Create a new migration
alembic revision --autogenerate -m "description"
```

## Seed Data

The seed script creates:
- **1 admin user**: admin@example.com / admin123 (platform_administrator role)
- **4 knowledge stewards**: Assigned to various knowledge domains
- **8 end users**: Distributed across teams
- **8 teams**: PLATFORM, AUTH, PAYMENTS, DATA, FRONTEND, INFRA, SECURITY, SUPPORT
- **7 knowledge domains**: onboarding, ownership, dependencies, runbooks, governance, operations, process
- **15 source records**: Mixed approval states (approved, pending, rejected)
- **8 services**: With realistic dependency relationships

The seed script is idempotent and safe to run multiple times.

## Troubleshooting

### Port Already in Use

The startup scripts automatically detect available ports. If a port conflict occurs, they will increment to the next available port and update all configuration accordingly.

### Python Version Issues

Ensure Python 3.10 or higher is installed:
```bash
python3 --version  # Should show 3.10 or higher
```

### Node.js Version Issues

Ensure Node.js 18 or higher is installed:
```bash
node --version  # Should show v18 or higher
```

### Database Connection Errors

If using PostgreSQL, verify:
1. PostgreSQL server is running
2. Database exists
3. Credentials in DATABASE_URL are correct
4. Host and port are accessible

For SQLite (default), the database is created automatically.

### Module Import Errors

If you see import errors, ensure dependencies are installed:
```bash
# Backend
cd backend
pip install .

# Frontend
cd frontend
npm install
```

## Deployment

See documentation for production deployment:
- `docs/DEPLOYMENT.md` - Deployment procedures and GitOps workflow
- `docs/ARCHITECTURE.md` - System architecture and design decisions
- `docs/RUNBOOK.md` - Operational procedures and troubleshooting
- `infrastructure/` - Kubernetes manifests and IaC templates

## Contributing

1. Follow PEP 8 conventions for Python code
2. Use TypeScript strict mode for frontend code
3. Write tests for new features
4. Run linters before committing:
   - Backend: `ruff check app/`
   - Frontend: `npm run lint`
5. Follow conventional commit format

## License

Internal use only - Enterprise License
