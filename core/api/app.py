"""
Main FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import get_settings
from .v1 import accounts, compliance, customers, payments, regulatory, transactions


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    get_settings()

    app = FastAPI(
        title="BaaS Core Banking API",
        description="Banking as a Service Core Banking System built on Formance",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(accounts.router, prefix="/api/v1")
    app.include_router(transactions.router, prefix="/api/v1")
    app.include_router(customers.router, prefix="/api/v1")
    app.include_router(payments.router, prefix="/api/v1")
    app.include_router(compliance.router, prefix="/api/v1")
    app.include_router(regulatory.router, prefix="/api/v1")

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "name": "BaaS Core Banking API",
            "version": "0.1.0",
            "status": "operational",
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler"""
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"},
        )

    return app


app = create_app()
