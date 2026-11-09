#!/bin/bash
# start.sh — Start the full-stack Multi-team Knowledge Assistant
set -e
trap 'echo "Shutting down..."; [ -f .pids ] && while IFS= read -r pid; do kill "$pid" 2>/dev/null || true; done < .pids; rm -f .pids; exit 0' SIGINT SIGTERM

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

# Portable sed (macOS + Linux)
portable_sed() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

# Port detection
find_available_port() {
    local port=$1
    if command -v lsof &>/dev/null; then
        while lsof -iTCP:$port -sTCP:LISTEN -t >/dev/null 2>&1; do
            echo "Port $port in use, trying $((port+1))..." >&2
            port=$((port+1))
        done
    fi
    echo $port
}

# === Prerequisite checks ===
check_prerequisites() {
    local errors=0
    echo "=== Checking prerequisites ==="

    # Python 3.10+
    if command -v python3 &>/dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
            echo "❌ Python 3.10+ required (found $PYTHON_VERSION)"
            errors=$((errors+1))
        else
            echo "✓ Python $PYTHON_VERSION"
        fi
    else
        echo "❌ Python 3 not found. Install from https://python.org"
        errors=$((errors+1))
    fi

    # Node.js 18+
    if command -v node &>/dev/null; then
        NODE_VERSION=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
        if [ "$NODE_MAJOR" -lt 18 ]; then
            echo "❌ Node.js 18+ required (found $NODE_VERSION)"
            errors=$((errors+1))
        else
            echo "✓ Node.js $NODE_VERSION"
        fi
    else
        echo "❌ Node.js not found. Install from https://nodejs.org"
        errors=$((errors+1))
    fi

    # npm
    if ! command -v npm &>/dev/null; then
        echo "❌ npm not found"
        errors=$((errors+1))
    else
        echo "✓ npm $(npm --version)"
    fi

    # pip
    if command -v python3 &>/dev/null && ! python3 -m pip --version &>/dev/null; then
        echo "❌ pip not found. Run: python3 -m ensurepip"
        errors=$((errors+1))
    else
        echo "✓ pip $(python3 -m pip --version | awk '{print $2}')"
    fi

    # lsof (optional but recommended for port detection)
    if ! command -v lsof &>/dev/null; then
        echo "⚠  lsof not found — port detection may not work (install with: brew install lsof or apt-get install lsof)"
    fi

    if [ $errors -gt 0 ]; then
        echo ""
        echo "❌ $errors prerequisite(s) missing. Please install them and retry."
        exit 1
    fi
    echo ""
}

check_prerequisites

# Detect available ports
BACKEND_PORT=$(find_available_port 9000)
FRONTEND_PORT=$(find_available_port 5173)

echo "=== Configuration ==="
echo "  Backend port:  $BACKEND_PORT"
echo "  Frontend port: $FRONTEND_PORT"
echo ""

# Update shared_config.json with detected ports using Python for JSON safety
if [ -f "shared_config.json" ]; then
    echo "Updating shared_config.json with detected ports..."
    python3 -c "
import json
with open('shared_config.json', 'r') as f:
    cfg = json.load(f)
cfg['ports']['backend'] = $BACKEND_PORT
cfg['ports']['frontend_web'] = $FRONTEND_PORT
cfg['cors_origins'] = ['http://localhost:$FRONTEND_PORT', 'http://localhost:3000']
with open('shared_config.json', 'w') as f:
    json.dump(cfg, f, indent=2)
" 2>/dev/null || echo "⚠  Could not update shared_config.json"
fi

# === Backend Setup ===
BACKEND_DIR="$PROJECT_ROOT/backend"
echo "=== Setting up backend ==="
cd "$BACKEND_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing backend dependencies..."
pip install . -q

# Database setup — default to SQLite for zero-config local dev
export DATABASE_URL="${DATABASE_URL:-sqlite:///$PROJECT_ROOT/storage/app.db}"
mkdir -p "$PROJECT_ROOT/storage"
echo "  Database: $DATABASE_URL"

# Update backend CORS_ORIGINS to include frontend port
export CORS_ORIGINS="http://localhost:$FRONTEND_PORT,http://localhost:3000"

# Update backend .env if it exists
if [ -f ".env" ]; then
    portable_sed "s|CORS_ORIGINS=.*|CORS_ORIGINS=$CORS_ORIGINS|" .env 2>/dev/null || true
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head 2>/dev/null || echo "⚠  Migration warning (may be expected for first run)"

# Seed database with default credentials
echo "Seeding database..."
python3 app/seed.py 2>/dev/null || python3 -c "from app.seed import seed_database; seed_database()" 2>/dev/null || true

# Start backend
echo "Starting backend on http://localhost:$BACKEND_PORT"
uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PROJECT_ROOT/.pids"

cd "$PROJECT_ROOT"

# === Frontend Setup ===
FRONTEND_DIR="$PROJECT_ROOT/frontend"
if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
    echo ""
    echo "=== Setting up frontend ==="
    cd "$FRONTEND_DIR"

    # Install dependencies
    echo "Installing frontend dependencies..."
    npm install --silent 2>/dev/null || npm install

    # Update frontend .env with backend API URL
    echo "VITE_API_URL=http://localhost:$BACKEND_PORT" > .env
    echo "Updated frontend .env with backend URL"

    # Start frontend
    echo "Starting frontend on http://localhost:$FRONTEND_PORT"
    npm run dev -- --port $FRONTEND_PORT --host &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" >> "$PROJECT_ROOT/.pids"

    cd "$PROJECT_ROOT"
fi

# Wait for services to start
echo ""
echo "Waiting for services to start..."
sleep 3

echo ""
echo "=========================================="
echo "  Multi-team Knowledge Assistant"
echo "=========================================="
echo ""
echo "Services running:"
echo "  • Backend API:  http://localhost:$BACKEND_PORT"
echo "  • API Docs:     http://localhost:$BACKEND_PORT/docs"
echo "  • Frontend Web: http://localhost:$FRONTEND_PORT"
echo ""
echo "Default Credentials:"
echo "  • Email:    admin@example.com"
echo "  • Password: admin123"
echo ""
echo "Press Ctrl+C to stop all services"
echo "Or run: ./stop.sh"
echo "=========================================="
echo ""

wait
