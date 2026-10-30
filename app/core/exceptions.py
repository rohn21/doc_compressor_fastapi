"""Standardized API exceptions and error handlers."""

from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.engines.exceptions import (
    CompressionError,
    CorruptImageError,
    CorruptPDFError,
    DecompressionBombError,
    EncryptedPDFError,
    OutputValidationError,
    TargetSizeUnachievableError,
    UnsupportedFormatError,
)


def create_error_response(
    status_code: int,
    error_type: str,
    detail: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Produce consistent JSON error responses across the entire API."""
    content: dict[str, Any] = {
        "error": error_type,
        "detail": detail,
    }
    if details:
        content["details"] = details
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on FastAPI application."""

    @app.exception_handler(UnsupportedFormatError)
    async def unsupported_format_handler(
        request: Request,
        exc: UnsupportedFormatError,
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error_type="UnsupportedFormatError",
            detail=str(exc),
            details=exc.details,
        )

    @app.exception_handler(CorruptImageError)
    @app.exception_handler(CorruptPDFError)
    async def corrupt_file_handler(request: Request, exc: CompressionError) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type=exc.__class__.__name__,
            detail=str(exc),
            details=exc.details,
        )

    @app.exception_handler(EncryptedPDFError)
    @app.exception_handler(TargetSizeUnachievableError)
    @app.exception_handler(OutputValidationError)
    async def validation_handler(request: Request, exc: CompressionError) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type=exc.__class__.__name__,
            detail=str(exc),
            details=exc.details,
        )

    @app.exception_handler(DecompressionBombError)
    async def decompression_bomb_handler(
        request: Request,
        exc: DecompressionBombError,
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_type="DecompressionBombError",
            detail=str(exc),
            details=exc.details,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail_msg = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        extra = exc.detail if isinstance(exc.detail, dict) else None
        return create_error_response(
            status_code=exc.status_code,
            error_type="HTTPException",
            detail=detail_msg,
            details=extra,
        )
