"""
Common DTOs for multi-tenant context and error handling.

Provides base classes for tenant validation and error details.
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class TenantContext(BaseModel):
    """Tenant context for multi-tenant operations."""
    
    tenant_id: UUID = Field(
        ...,
        description="Tenant identifier (UUID v4)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    @field_validator('tenant_id')
    @classmethod
    def validate_tenant_id(cls, v: UUID) -> UUID:
        """Validate tenant_id is a valid UUID."""
        if v is None:
            raise ValueError("tenant_id cannot be None")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class TenantMissingError(Exception):
    """Exception raised when tenant ID is missing from request."""
    
    def __init__(self, message: str = "X-Tenant-ID header is required"):
        self.message = message
        super().__init__(self.message)


class TenantValidationError(Exception):
    """Exception raised when tenant ID format is invalid."""
    
    def __init__(self, message: str = "Invalid tenant ID format. Must be a valid UUID", detail: Optional[str] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class ErrorDetail(BaseModel):
    """Standard error detail structure."""
    
    type: str = Field(description="Error type identifier")
    message: str = Field(description="Human-readable error message")
    detail: Optional[str] = Field(default=None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "validation_error",
                "message": "Invalid input provided",
                "detail": "Field 'email' must be a valid email address"
            }
        }
