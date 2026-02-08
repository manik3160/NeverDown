"""FastAPI application entry point for NeverDown."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import auth, health, incidents, status, webhooks
from api.middleware.request_logging import RequestLoggingMiddleware
from config.logging_config import configure_logging, get_logger
from config.settings import get_settings
from core.exceptions import NeverDownError
from database.connection import close_db, init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    settings = get_settings()
    
    # Startup
    configure_logging(
        log_level=settings.LOG_LEVEL,
        json_logs=not settings.DEBUG,
    )
    logger.info("Starting NeverDown API", version=settings.APP_VERSION)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NeverDown API")
    await close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Autonomous incident detection, analysis, and remediation system",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # Request logging middleware - added FIRST so it runs LAST (after CORS)
    app.add_middleware(RequestLoggingMiddleware)
    
    # CORS middleware - added LAST so it runs FIRST
    # Using wildcard for development. In production, specify exact origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Cannot use credentials with wildcard
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Exception handlers
    @app.exception_handler(NeverDownError)
    async def neverdown_error_handler(request: Request, exc: NeverDownError):
        """Handle NeverDown custom exceptions."""
        return JSONResponse(
            status_code=400,
            content=exc.to_dict(),
        )
    
    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.exception("Unexpected error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"type": type(exc).__name__} if settings.DEBUG else {},
            },
        )
    
    # Include routers
    app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
    app.include_router(incidents.router, prefix=settings.API_PREFIX, tags=["Incidents"])
    app.include_router(status.router, prefix=settings.API_PREFIX, tags=["Status"])
    app.include_router(webhooks.router, prefix=settings.API_PREFIX, tags=["Webhooks"])
    app.include_router(auth.router, prefix=settings.API_PREFIX + "/auth", tags=["Auth"])
    
    return app


# Create the application instance
app = create_app()
