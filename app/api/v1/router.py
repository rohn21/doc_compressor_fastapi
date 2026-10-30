"""API v1 master router aggregating health, compression, and batch routes."""

from fastapi import APIRouter

from app.api.v1 import batches, compression, health

api_v1_router = APIRouter()

api_v1_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

api_v1_router.include_router(
    compression.router,
    prefix="/compression",
    tags=["Compression"],
)

api_v1_router.include_router(
    batches.router,
    prefix="/batches",
    tags=["Batches"],
)
