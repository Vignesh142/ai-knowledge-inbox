from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
)
from backend.app.db.database import db
from backend.app.api.router import api_v1_router
from backend.app.api.middleware import RequestLoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting up {settings.PROJECT_NAME} v{settings.VERSION}...")
    # Initialize SQLite database schema
    await db.init_db()
    # Sync existing chunks into the active vector store dimension
    from backend.app.services.ingestion_service import ingestion_service
    await ingestion_service.sync_all_chunks_to_vector_store()
    logger.info("Application startup completed successfully.")
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade AI Knowledge Inbox with semantic chunking, ChromaDB vector store, and streaming RAG.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"],
)

# Request Timing & Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# Exception Handlers
@app.exception_handler(AppException)
async def custom_app_exception_handler(request: Request, exc: AppException):
    return await app_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    # Use jsonable_encoder to safely serialize error contexts including exceptions
    clean_errors = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed. Please check your request payload.",
                "details": clean_errors,
                "path": request.url.path,
            }
        },
    )

@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    return await unhandled_exception_handler(request, exc)

# Mount API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "ingest": f"{settings.API_V1_PREFIX}/items/ingest",
            "items": f"{settings.API_V1_PREFIX}/items",
            "query": f"{settings.API_V1_PREFIX}/query",
            "stream": f"{settings.API_V1_PREFIX}/query/stream",
            "stats": f"{settings.API_V1_PREFIX}/stats",
            "health": f"{settings.API_V1_PREFIX}/health",
        },
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
