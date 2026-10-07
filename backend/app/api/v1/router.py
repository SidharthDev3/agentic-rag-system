from fastapi import APIRouter
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.documents import router as documents_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.search import router as search_router
from app.api.v1.stats import router as stats_router

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(documents_router)
api_router.include_router(chat_router)
api_router.include_router(conversations_router)
api_router.include_router(stats_router)
api_router.include_router(search_router)
api_router.include_router(evaluation_router)

