"""
Unit tests for common DTOs (TenantContext, Response wrappers).
"""
import pytest
from uuid import UUID
from pydantic import ValidationError

from app.dtos.common import (
    TenantContext,
    TenantMissingError,
    TenantValidationError,
    SuccessResponse,
    ErrorResponse,
    ErrorDetail,
    create_success_response,
    create_error_response,
)


class TestTenantContext:
    """Test suite for TenantContext model."""
    
    def test_valid_uuid_string(self):
        """Test TenantContext accepts valid UUID string."""
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        context = TenantContext(tenant_id=tenant_id)
        
        assert context.tenant_id == UUID(tenant_id)
        assert isinstance(context.tenant_id, UUID)
    
    def test_valid_uuid_object(self):
        """Test TenantContext accepts UUID object directly."""
        tenant_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        context = TenantContext(tenant_id=tenant_id)
        
        assert context.tenant_id == tenant_id
        assert isinstance(context.tenant_id, UUID)
    
    def test_invalid_uuid_format(self):
        """Test TenantContext rejects invalid UUID format."""
        invalid_ids = [
            "not-a-uuid",
            "12345",
            "550e8400-invalid-uuid",
            "550e8400e29b41d4a716446655440000xxx",  # Too long
        ]
        
        for invalid_id in invalid_ids:
            with pytest.raises(ValidationError) as exc_info:
                TenantContext(tenant_id=invalid_id)
            
            errors = exc_info.value.errors()
            assert any("uuid" in str(err).lower() for err in errors)
    
    def test_none_tenant_id(self):
        """Test TenantContext rejects None tenant_id."""
        with pytest.raises(ValidationError) as exc_info:
            TenantContext(tenant_id=None)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_empty_string_tenant_id(self):
        """Test TenantContext rejects empty string."""
        with pytest.raises(ValidationError):
            TenantContext(tenant_id="")
    
    def test_uuid_normalization(self):
        """Test UUID is normalized to standard format."""
        # UUID without hyphens (if Pydantic accepts it)
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        context = TenantContext(tenant_id=tenant_id)
        
        # Verify it's stored as UUID object
        assert str(context.tenant_id) == tenant_id
    
    def test_json_serialization(self):
        """Test TenantContext can be serialized to JSON."""
        context = TenantContext(tenant_id="550e8400-e29b-41d4-a716-446655440000")
        json_data = context.model_dump_json()
        
        assert "550e8400-e29b-41d4-a716-446655440000" in json_data
    
    def test_json_schema_example(self):
        """Test TenantContext has proper JSON schema example."""
        schema = TenantContext.model_json_schema()
        
        assert "example" in schema or "examples" in str(schema)


class TestTenantMissingError:
    """Test suite for TenantMissingError exception."""
    
    def test_default_message(self):
        """Test TenantMissingError has default message."""
        error = TenantMissingError()
        
        assert error.message == "X-Tenant-ID header is required"
        assert str(error) == "X-Tenant-ID header is required"
    
    def test_custom_message(self):
        """Test TenantMissingError accepts custom message."""
        custom_msg = "Tenant identifier is missing"
        error = TenantMissingError(message=custom_msg)
        
        assert error.message == custom_msg
        assert str(error) == custom_msg
    
    def test_exception_inheritance(self):
        """Test TenantMissingError is an Exception."""
        error = TenantMissingError()
        
        assert isinstance(error, Exception)


class TestTenantValidationError:
    """Test suite for TenantValidationError exception."""
    
    def test_default_message(self):
        """Test TenantValidationError has default message."""
        error = TenantValidationError()
        
        assert "Invalid tenant ID format" in error.message
        assert "UUID" in error.message
    
    def test_custom_message(self):
        """Test TenantValidationError accepts custom message."""
        custom_msg = "Tenant ID validation failed"
        error = TenantValidationError(message=custom_msg)
        
        assert error.message == custom_msg
    
    def test_with_detail(self):
        """Test TenantValidationError with detail information."""
        detail = "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        error = TenantValidationError(detail=detail)
        
        assert error.detail == detail
    
    def test_exception_inheritance(self):
        """Test TenantValidationError is an Exception."""
        error = TenantValidationError()
        
        assert isinstance(error, Exception)


class TestSuccessResponse:
    """Test suite for SuccessResponse generic wrapper."""
    
    def test_success_response_with_dict(self):
        """Test SuccessResponse wraps dict data."""
        data = {"message": "Operation successful", "count": 42}
        response = SuccessResponse(data=data)
        
        assert response.success is True
        assert response.data == data
    
    def test_success_response_with_pydantic_model(self):
        """Test SuccessResponse wraps Pydantic model."""
        tenant = TenantContext(tenant_id="550e8400-e29b-41d4-a716-446655440000")
        response = SuccessResponse(data=tenant)
        
        assert response.success is True
        assert response.data == tenant
    
    def test_success_response_with_list(self):
        """Test SuccessResponse wraps list data."""
        data = [1, 2, 3, 4, 5]
        response = SuccessResponse(data=data)
        
        assert response.success is True
        assert response.data == data
    
    def test_success_response_json_serialization(self):
        """Test SuccessResponse serializes to JSON."""
        data = {"key": "value"}
        response = SuccessResponse(data=data)
        json_str = response.model_dump_json()
        
        assert '"success":true' in json_str or '"success": true' in json_str
        assert '"key":"value"' in json_str or '"key": "value"' in json_str
    
    def test_success_default_value(self):
        """Test success field defaults to True."""
        response = SuccessResponse(data={"test": "data"})
        
        assert response.success is True


class TestErrorResponse:
    """Test suite for ErrorResponse wrapper."""
    
    def test_error_response_structure(self):
        """Test ErrorResponse has correct structure."""
        error_detail = ErrorDetail(
            type="ValidationError",
            message="Invalid input",
            detail="Field 'email' is required"
        )
        response = ErrorResponse(success=False, error=error_detail)
        
        assert response.success is False
        assert response.error.type == "ValidationError"
        assert response.error.message == "Invalid input"
        assert response.error.detail == "Field 'email' is required"
    
    def test_error_response_without_detail(self):
        """Test ErrorResponse works without detail field."""
        error_detail = ErrorDetail(
            type="NotFoundError",
            message="Resource not found"
        )
        response = ErrorResponse(success=False, error=error_detail)
        
        assert response.error.detail is None
    
    def test_error_response_json_serialization(self):
        """Test ErrorResponse serializes to JSON."""
        error_detail = ErrorDetail(
            type="ServerError",
            message="Internal server error"
        )
        response = ErrorResponse(success=False, error=error_detail)
        json_str = response.model_dump_json()
        
        assert '"success":false' in json_str or '"success": false' in json_str
        assert '"type":"ServerError"' in json_str or '"type": "ServerError"' in json_str


class TestErrorDetail:
    """Test suite for ErrorDetail model."""
    
    def test_error_detail_required_fields(self):
        """Test ErrorDetail requires type and message."""
        detail = ErrorDetail(type="TestError", message="Test message")
        
        assert detail.type == "TestError"
        assert detail.message == "Test message"
        assert detail.detail is None
    
    def test_error_detail_with_all_fields(self):
        """Test ErrorDetail with all fields."""
        detail = ErrorDetail(
            type="ValidationError",
            message="Validation failed",
            detail="Additional context here"
        )
        
        assert detail.type == "ValidationError"
        assert detail.message == "Validation failed"
        assert detail.detail == "Additional context here"
    
    def test_error_detail_json_schema(self):
        """Test ErrorDetail has JSON schema example."""
        schema = ErrorDetail.model_json_schema()
        
        # Check schema has example or properties defined
        assert "properties" in schema
        assert "type" in schema["properties"]
        assert "message" in schema["properties"]


class TestHelperFunctions:
    """Test suite for helper functions."""
    
    def test_create_error_response_basic(self):
        """Test create_error_response with basic parameters."""
        response = create_error_response(
            error_type="validation_error",
            message="Invalid input"
        )
        
        assert response["success"] is False
        assert response["error"]["type"] == "validation_error"
        assert response["error"]["message"] == "Invalid input"
        assert response["error"]["detail"] is None
    
    def test_create_error_response_with_detail(self):
        """Test create_error_response with detail parameter."""
        response = create_error_response(
            error_type="tenant_error",
            message="Tenant not found",
            detail="Tenant ID does not exist in database"
        )
        
        assert response["success"] is False
        assert response["error"]["type"] == "tenant_error"
        assert response["error"]["message"] == "Tenant not found"
        assert response["error"]["detail"] == "Tenant ID does not exist in database"
    
    def test_create_error_response_structure(self):
        """Test create_error_response returns correct structure."""
        response = create_error_response(
            error_type="test_error",
            message="Test message"
        )
        
        # Verify top-level structure
        assert "success" in response
        assert "error" in response
        assert len(response) == 2
        
        # Verify error object structure
        assert "type" in response["error"]
        assert "message" in response["error"]
        assert "detail" in response["error"]
        assert len(response["error"]) == 3
