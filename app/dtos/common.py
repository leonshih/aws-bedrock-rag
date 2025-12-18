"""
Common DTOs for standardized API responses.

Provides base classes for consistent response structure across all layers.
"""
from typing import Generic, TypeVar, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# Generic type variable for response data
T = TypeVar('T')


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


class SuccessResponse(BaseModel, Generic[T]):
    """
    Standard success response wrapper.
    
    All successful API responses follow this structure:
    {
        "success": true,
        "data": <actual response data>
    }
    """
    
    success: bool = Field(default=True, description="Indicates successful operation")
    data: T = Field(description="Response data payload")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"message": "Operation completed successfully"}
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response wrapper.
    
    All error responses follow this structure:
    {
        "success": false,
        "error": {
            "type": "error_type",
            "message": "Error message",
            "detail": "Additional details"
        }
    }
    """
    
    success: bool = Field(default=False, description="Indicates failed operation")
    error: ErrorDetail = Field(description="Error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "type": "not_found",
                    "message": "Resource not found",
                    "detail": "The requested file does not exist"
                }
            }
        }


def create_success_response(data: T) -> dict:
    """
    Helper function to create a success response.
    
    Args:
        data: The response data to wrap
        
    Returns:
        Dict with success=True and data
    """
    return {
        "success": True,
        "data": data
    }


def create_error_response(
    error_type: str,
    message: str,
    detail: Optional[str] = None
) -> dict:
    """
    Helper function to create an error response.
    
    Args:
        error_type: Error type identifier
        message: Human-readable error message
        detail: Optional additional details
        
    Returns:
        Dict with success=False and error details
    """
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
            "detail": detail
        }
    }
