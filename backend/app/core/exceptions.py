from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from backend.app.core.logging import logger

class AppException(Exception):
    """Base application exception."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

class ItemNotFoundError(AppException):
    def __init__(self, item_id: str):
        super().__init__(
            message=f"Item with ID '{item_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ITEM_NOT_FOUND",
            details={"item_id": item_id},
        )

class ScrapingError(AppException):
    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"Failed to scrape URL '{url}': {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="SCRAPING_FAILED",
            details={"url": url, "reason": reason},
        )

class SSRFSecurityError(AppException):
    def __init__(self, url: str, reason: str = "Access to local or private network ranges is prohibited."):
        super().__init__(
            message=f"URL '{url}' is forbidden: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="SSRF_SECURITY_VIOLATION",
            details={"url": url, "reason": reason},
        )

class EmbeddingError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Embedding generation failed: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="EMBEDDING_FAILED",
            details=details,
        )

class LLMProviderError(AppException):
    def __init__(self, provider: str, message: str):
        super().__init__(
            message=f"LLM Provider '{provider}' error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="LLM_PROVIDER_ERROR",
            details={"provider": provider, "error": message},
        )

class InvalidInputError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_INPUT",
            details=details,
        )

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        f"Handled AppException [{exc.error_code}]: {exc.message} "
        f"Path: {request.url.path} Details: {exc.details}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "path": request.url.path,
            }
        },
    )

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled Exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {"error": str(exc)},
                "path": request.url.path,
            }
        },
    )
