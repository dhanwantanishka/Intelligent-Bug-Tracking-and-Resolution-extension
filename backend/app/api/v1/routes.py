"""
FastAPI Routes for IBTRRS API v1
"""

from fastapi import APIRouter, Depends, status
from app.schemas.repairs import RepairRequest, RepairResponse, HealthResponse
from app.auth import verify_bearer_token
from app.services.repair import orchestrate_repair, index_engine

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok" if index_engine.is_loaded else "degraded",
        api_version="v1",
        index_manifest_id=index_engine.manifest.get("manifest_version"),
        records_indexed=len(index_engine.records)
    )


@router.post("/repairs", response_model=RepairResponse, dependencies=[Depends(verify_bearer_token)])
async def generate_repair(request: RepairRequest):
    return await orchestrate_repair(request)

