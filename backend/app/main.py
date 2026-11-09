"""FastAPI main application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    Limiter = None
    RateLimitExceeded = None

from app.config import settings
from app.database import init_db
from app.api import health, questions, answers, citations, feedback, governance, test_auth


def get_limiter_key(request: Request) -> str:
    """Get rate limiter key from request user context or IP."""
    # Try to get user_id from request state (set by auth middleware)
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"
    # Fallback to IP address
    if SLOWAPI_AVAILABLE:
        return get_remote_address(request)
    return request.client.host if request.client else "unknown"


if SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_limiter_key)
else:
    limiter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown tasks."""
    # Startup
    init_db()
    
    # Seed database with default credentials and sample data
    from app.seed import seed_database
    seed_database()
    
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Multi-team Knowledge Assistant API",
    description="API for the multi-team knowledge assistant platform",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Configure rate limiting if available
if SLOWAPI_AVAILABLE and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        error_dict = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": error.get("input"),
        }
        # Convert ctx to serializable format if present
        if "ctx" in error:
            ctx = error["ctx"]
            serializable_ctx = {}
            for key, value in ctx.items():
                if isinstance(value, Exception):
                    serializable_ctx[key] = str(value)
                else:
                    serializable_ctx[key] = value
            error_dict["ctx"] = serializable_ctx
        errors.append(error_dict)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    # Log the exception (in production, use proper logging)
    if settings.debug:
        import traceback
        traceback.print_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(health.router, prefix=settings.api_base_path, tags=["health"])
app.include_router(test_auth.router, prefix=settings.api_base_path, tags=["auth"])
app.include_router(questions.router, prefix=settings.api_base_path, tags=["questions"])
app.include_router(answers.router, prefix=settings.api_base_path, tags=["answers"])
app.include_router(citations.router, prefix=settings.api_base_path, tags=["citations"])
app.include_router(feedback.router, prefix=settings.api_base_path, tags=["feedback"])
app.include_router(governance.router, prefix=settings.api_base_path, tags=["governance"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Multi-team Knowledge Assistant API",
        "version": "1.0.0",
        "docs": f"{settings.api_base_path}/docs" if settings.debug else None,
    }
