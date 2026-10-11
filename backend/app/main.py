"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.routes import router as api_v1_router
from app.auth import ensure_token_file
from app.services.repair import index_engine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url=None,  # Disabled for security by default
    redoc_url=None
)

app.include_router(api_v1_router)


@app.on_event("startup")
async def startup_event():
    # Ensure bearer token is initialized on loopback startup
    ensure_token_file()
    # Attempt to load index artifacts
    index_engine.load()

