from fastapi import APIRouter
from app.api.v1.endpoints import health, webhooks, campaigns, properties

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health")
api_router.include_router(webhooks.router)
api_router.include_router(campaigns.router)
api_router.include_router(properties.router)