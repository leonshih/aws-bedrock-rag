"""
Tenant dependency for multi-tenant request handling.

Extracts and validates tenant ID from HTTP headers using FastAPI
dependency injection pattern.
"""
from uuid import UUID
from fastapi import Header, HTTPException, status
from typing import Annotated
from pydantic import ValidationError
import logging

from app.dtos.common import TenantContext

logger = logging.getLogger(__name__)


async def get_tenant_context(
    x_tenant_id: Annotated[
        UUID,
        Header(
            description="Tenant UUID for data isolation (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)",
            examples=["550e8400-e29b-41d4-a716-446655440000"]
        )
    ]
) -> TenantContext:
    """
    Extract and validate tenant ID from X-Tenant-ID header.
    
    This dependency function:
    1. Extracts 'X-Tenant-ID' header from incoming requests
    2. Validates the UUID format (handled by FastAPI)
    3. Creates and returns TenantContext
    4. Raises HTTPException for missing or invalid tenant IDs
    
    Args:
        x_tenant_id: Tenant UUID from request header (auto-extracted by FastAPI)
        
    Returns:
        TenantContext with validated tenant_id
        
    Raises:
        HTTPException: 422 if header is missing or invalid UUID format
        HTTPException: 400 if validation fails for other reasons
        
    Example:
        ```python
        @router.post("/endpoint")
        async def endpoint(
            tenant_context: Annotated[TenantContext, Depends(get_tenant_context)]
        ):
            tenant_id = tenant_context.tenant_id
        ```
    """
    try:
        # Create TenantContext with validated UUID
        tenant_context = TenantContext(tenant_id=x_tenant_id)
        
        logger.debug(
            f"Tenant context created successfully",
            extra={"tenant_id": str(tenant_context.tenant_id)}
        )
        
        return tenant_context
        
    except ValidationError as e:
        # Extract error details from Pydantic validation error
        error_details = e.errors()[0] if e.errors() else {}
        error_msg = error_details.get('msg', 'Invalid tenant ID format')
        
        logger.warning(
            f"Tenant ID validation failed: {x_tenant_id}",
            extra={"error": error_msg}
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "tenant_validation_error",
                "message": error_msg,
                "tenant_id": str(x_tenant_id)
            }
        )
