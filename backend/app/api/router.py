from fastapi import APIRouter
from backend.app.api.v1.items import router as items_router
from backend.app.api.v1.query import router as query_router
from backend.app.api.v1.stats import router as stats_router

api_v1_router = APIRouter()

api_v1_router.include_router(items_router)
api_v1_router.include_router(query_router)
api_v1_router.include_router(stats_router)
