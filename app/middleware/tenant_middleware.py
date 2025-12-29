"""
Tenant middleware for multi-tenant request handling.

Extracts and validates tenant ID from HTTP headers and injects
TenantContext into request state.
"""
from uuid import UUID
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
import logging

from app.dtos.common import TenantContext, TenantMissingError, TenantValidationError

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant ID from request headers.
    
    This middleware:
    1. Extracts 'X-Tenant-ID' header from incoming requests
    2. Validates the UUID format
    3. Creates TenantContext and injects into request.state
    4. Raises appropriate exceptions for missing or invalid tenant IDs
    """
    
    # Endpoints that don't require tenant ID
    EXCLUDED_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request to extract and validate tenant ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from downstream handlers or error response
        """
        # Skip tenant validation for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Extract tenant ID from header
        tenant_id_header = request.headers.get("X-Tenant-ID")
        
        if not tenant_id_header:
            logger.warning(
                f"Tenant ID missing for path: {request.url.path}",
                extra={"path": request.url.path, "method": request.method}
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "type": "tenant_missing_error",
                        "message": "X-Tenant-ID header is required",
                        "path": request.url.path
                    }
                }
            )
        
        # Validate and create TenantContext
        try:
            tenant_context = TenantContext(tenant_id=tenant_id_header)
            # Inject into request state for downstream access
            request.state.tenant_context = tenant_context
        except ValidationError as e:
            # Extract error details from Pydantic validation error
            error_details = e.errors()[0] if e.errors() else {}
            error_msg = error_details.get('msg', 'Invalid UUID format')
            
            logger.warning(
                f"Tenant ID validation failed: {tenant_id_header}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "tenant_id": tenant_id_header,
                    "error": error_msg
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "type": "tenant_validation_error",
                        "message": f"Invalid tenant ID format: {tenant_id_header}",
                        "detail": error_msg,
                        "path": request.url.path
                    }
                }
            )
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Tenant ID validation error: {tenant_id_header}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "tenant_id": tenant_id_header,
                    "error": str(e)
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "type": "tenant_validation_error",
                        "message": f"Invalid tenant ID: {tenant_id_header}",
                        "detail": str(e),
                        "path": request.url.path
                    }
                }
            )
        
        # Continue to next handler
        response = await call_next(request)
        return response


def get_tenant_context(request: Request) -> TenantContext:
    """
    Helper function to retrieve TenantContext from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        TenantContext object injected by middleware
        
    Raises:
        TenantMissingError: If tenant context not found in request state
    """
    if not hasattr(request.state, 'tenant_context'):
        raise TenantMissingError("Tenant context not found in request state")
    
    return request.state.tenant_context
