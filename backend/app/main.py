from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import NexusRAGException, http_exception_from_domain
from app.core.logging import logger, setup_logging
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting up %s v%s...", settings.PROJECT_NAME, settings.VERSION)
    try:
        await init_db()
    except Exception as e:
        logger.error("Failed to initialize database schema: %s", e)
    yield
    # Shutdown
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade Agentic RAG Platform for Grounded Knowledge Retrieval & Reasoning",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
origins = settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(NexusRAGException)
async def domain_exception_handler(request: Request, exc: NexusRAGException):
    http_exc = http_exception_from_domain(exc)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"detail": http_exc.detail, "type": exc.__class__.__name__},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred.", "type": "InternalServerError"},
    )


# Mount API routers (both /api/v1 and /api for convenience)
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
        "endpoints": {
            "documents": "/api/v1/documents",
            "chat": "/api/v1/chat",
            "streaming": "/api/v1/chat/stream",
            "stats": "/api/v1/stats",
            "evaluation": "/api/v1/evaluation/latest",
        },
    }

