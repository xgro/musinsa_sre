from fastapi.routing import APIRouter

from backend.web.api import docs, health

api_router = APIRouter()
api_router.include_router(docs.router)
api_router.include_router(health.router, prefix="", tags=["health"])
