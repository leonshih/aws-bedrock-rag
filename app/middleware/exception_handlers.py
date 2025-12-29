"""Global exception handlers for FastAPI application."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from botocore.exceptions import ClientError, BotoCoreError, ParamValidationError
import logging

from app.dtos.common import TenantMissingError, TenantValidationError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(TenantMissingError, tenant_missing_exception_handler)
    app.add_exception_handler(TenantValidationError, tenant_validation_exception_handler)
    app.add_exception_handler(ParamValidationError, param_validation_exception_handler)
    app.add_exception_handler(ClientError, aws_exception_handler)
    app.add_exception_handler(BotoCoreError, aws_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(FileNotFoundError, not_found_exception_handler)
    app.add_exception_handler(ValueError, value_error_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)


async def tenant_missing_exception_handler(request: Request, exc: TenantMissingError) -> JSONResponse:
    """
    Handle TenantMissingError exceptions.
    
    Args:
        request: FastAPI request object
        exc: TenantMissingError exception
        
    Returns:
        JSONResponse with 400 status
    """
    logger.warning(
        f"Tenant ID missing: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "type": "tenant_missing_error",
                "message": exc.message,
                "path": request.url.path
            }
        }
    )


async def tenant_validation_exception_handler(request: Request, exc: TenantValidationError) -> JSONResponse:
    """
    Handle TenantValidationError exceptions.
    
    Args:
        request: FastAPI request object
        exc: TenantValidationError exception
        
    Returns:
        JSONResponse with 400 status
    """
    logger.warning(
        f"Tenant ID validation failed: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "detail": exc.detail
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "type": "tenant_validation_error",
                "message": exc.message,
                "detail": exc.detail,
                "path": request.url.path
            }
        }
    )


async def param_validation_exception_handler(request: Request, exc: ParamValidationError) -> JSONResponse:
    """
    Handle AWS parameter validation errors.
    
    Args:
        request: FastAPI request object
        exc: ParamValidationError exception
        
    Returns:
        JSONResponse with 400 status
    """
    logger.exception(
        f"AWS Parameter validation error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "type": "param_validation_error",
                "message": "Invalid parameters provided to AWS service",
                "detail": str(exc),
                "path": request.url.path
            }
        }
    )


async def aws_exception_handler(request: Request, exc: ClientError) -> JSONResponse:
    """
    Handle AWS Boto3 ClientError exceptions.
    
    Maps AWS-specific errors to appropriate HTTP status codes and
    provides user-friendly error messages.
    
    Args:
        request: FastAPI request object
        exc: AWS ClientError exception
        
    Returns:
        JSONResponse with error details
    """
    error_code = exc.response.get("Error", {}).get("Code", "Unknown")
    error_message = exc.response.get("Error", {}).get("Message", str(exc))
    
    # Log the full error with stack trace for debugging
    logger.exception(
        f"AWS Error: {error_code} - {error_message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_code": error_code
        }
    )
    
    # Map AWS error codes to HTTP status codes
    status_code_map = {
        # Access/Permission errors
        "AccessDenied": status.HTTP_403_FORBIDDEN,
        "AccessDeniedException": status.HTTP_403_FORBIDDEN,
        "UnauthorizedException": status.HTTP_401_UNAUTHORIZED,
        "InvalidAccessKeyId": status.HTTP_401_UNAUTHORIZED,
        
        # Rate limiting
        "ThrottlingException": status.HTTP_429_TOO_MANY_REQUESTS,
        "TooManyRequestsException": status.HTTP_429_TOO_MANY_REQUESTS,
        "ProvisionedThroughputExceededException": status.HTTP_429_TOO_MANY_REQUESTS,
        
        # Resource errors
        "ResourceNotFoundException": status.HTTP_404_NOT_FOUND,
        "NoSuchKey": status.HTTP_404_NOT_FOUND,
        "NoSuchBucket": status.HTTP_404_NOT_FOUND,
        
        # Validation errors
        "ValidationException": status.HTTP_400_BAD_REQUEST,
        "InvalidParameterException": status.HTTP_400_BAD_REQUEST,
        "InvalidRequestException": status.HTTP_400_BAD_REQUEST,
        
        # Service errors
        "ServiceException": status.HTTP_503_SERVICE_UNAVAILABLE,
        "InternalServerError": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = status_code_map.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # User-friendly error messages
    user_messages = {
        "AccessDenied": "Access denied. Please check your AWS credentials and permissions.",
        "ThrottlingException": "Too many requests. Please try again later.",
        "ResourceNotFoundException": "The requested resource was not found.",
        "ValidationException": "Invalid request parameters.",
    }
    
    user_message = user_messages.get(
        error_code,
        "An AWS service error occurred. Please try again later."
    )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "type": "aws_error",
                "code": error_code,
                "message": user_message,
                "detail": error_message if status_code >= 500 else None,
                "path": request.url.path
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException.
    
    Wraps FastAPI's HTTPException in our standard error format.
    
    Args:
        request: FastAPI request object
        exc: HTTPException
        
    Returns:
        JSONResponse with standard error format
    """
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": "http_error",
                "message": exc.detail,
                "path": request.url.path
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle FastAPI/Pydantic validation errors.
    
    Provides detailed validation error messages to help users
    understand what went wrong with their request.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError exception
        
    Returns:
        JSONResponse with validation error details
    """
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Format validation errors for better readability
    formatted_errors = []
    for error in exc.errors():
        formatted_errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": formatted_errors,
                "path": request.url.path
            }
        }
    )


async def not_found_exception_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
    """
    Handle FileNotFoundError exceptions.
    
    Args:
        request: FastAPI request object
        exc: FileNotFoundError exception
        
    Returns:
        JSONResponse with 404 status
    """
    logger.warning(
        f"File not found: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error": {
                "type": "not_found",
                "message": str(exc),
                "path": request.url.path
            }
        }
    )


async def value_error_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Handle ValueError exceptions (typically from invalid input).
    
    Args:
        request: FastAPI request object
        exc: ValueError exception
        
    Returns:
        JSONResponse with 400 status
    """
    logger.warning(
        f"Validation error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "type": "validation_error",
                "message": str(exc),
                "path": request.url.path
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unhandled exceptions.
    
    Acts as a catch-all for unexpected errors, ensuring that the API
    always returns a proper JSON response even in case of unexpected failures.
    
    Args:
        request: FastAPI request object
        exc: Any unhandled exception
        
    Returns:
        JSONResponse with generic error message
    """
    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )
    
    # Don't expose internal error details to users in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": "internal_error",
                "message": "An internal error occurred. Please try again later.",
                "path": request.url.path,
                # Include exception type for debugging (remove in production)
                "exception_type": type(exc).__name__
            }
        }
    )
