"""FastAPI application setup."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from ..config import Config
from .routes import router
from .websocket import websocket_router

logger = logging.getLogger(__name__)


def create_app(config: Config) -> FastAPI:
    """Create and configure FastAPI application.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="HaikuBot API",
        description="IRC Haiku Bot with REST API and WebSocket support",
        version="2.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.web.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(router, prefix="/api")
    app.include_router(websocket_router)

    # Serve frontend static files if they exist
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        # Mount static assets
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

        # Catch-all route for SPA - serves index.html for all non-API routes
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve the React SPA for all routes except API."""
            index_file = frontend_dist / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return {"error": "Frontend not found"}

        logger.info(f"Serving frontend from: {frontend_dist}")

    @app.on_event("startup")
    async def startup_event():
        """Run on application startup."""
        logger.info("FastAPI application starting up")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Run on application shutdown."""
        logger.info("FastAPI application shutting down")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app

