from fastapi.routing import APIRouter

from backend.web.api import docs, health, iam

api_router = APIRouter()
api_router.include_router(docs.router)
api_router.include_router(health.router, prefix="", tags=["health"])
api_router.include_router(iam.router, prefix="", tags=["iam"])
