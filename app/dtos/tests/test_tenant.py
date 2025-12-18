"""
Unit tests for Tenant-related DTOs

Tests UUID validation and tenant context functionality.
"""
import pytest
from uuid import UUID, uuid4
from pydantic import ValidationError
from app.dtos.common import (
    TenantContext,
    TenantMissingError,
    TenantValidationError,
)


class TestTenantContext:
    """Tests for TenantContext model."""
    
    def test_valid_uuid_string(self):
        """Test creating TenantContext with valid UUID string."""
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        context = TenantContext(tenant_id=tenant_id)
        
        assert context.tenant_id == UUID(tenant_id)
        assert str(context.tenant_id) == tenant_id
    
    def test_valid_uuid_object(self):
        """Test creating TenantContext with UUID object."""
        tenant_id = uuid4()
        context = TenantContext(tenant_id=tenant_id)
        
        assert context.tenant_id == tenant_id
        assert isinstance(context.tenant_id, UUID)
    
    def test_invalid_uuid_format(self):
        """Test validation error with invalid UUID format."""
        with pytest.raises(ValidationError) as exc_info:
            TenantContext(tenant_id="invalid-uuid-format")
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert "tenant_id" in str(errors[0])
    
    def test_empty_string_uuid(self):
        """Test validation error with empty string."""
        with pytest.raises(ValidationError):
            TenantContext(tenant_id="")
    
    def test_missing_tenant_id(self):
        """Test validation error when tenant_id is missing."""
        with pytest.raises(ValidationError) as exc_info:
            TenantContext()
        
        errors = exc_info.value.errors()
        assert any("tenant_id" in str(error) for error in errors)
    
    def test_json_serialization(self):
        """Test JSON serialization of TenantContext."""
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        context = TenantContext(tenant_id=tenant_id)
        
        json_data = context.model_dump()
        assert "tenant_id" in json_data
        assert isinstance(json_data["tenant_id"], UUID)
    
    def test_json_deserialization(self):
        """Test JSON deserialization into TenantContext."""
        json_data = {
            "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        context = TenantContext(**json_data)
        
        assert context.tenant_id == UUID(json_data["tenant_id"])
    
    def test_model_dump_json(self):
        """Test model_dump_json returns valid JSON string."""
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        context = TenantContext(tenant_id=tenant_id)
        
        json_str = context.model_dump_json()
        assert tenant_id in json_str
        assert isinstance(json_str, str)
    
    def test_uuid_v4_format(self):
        """Test that generated UUIDs follow v4 format."""
        context = TenantContext(tenant_id=uuid4())
        
        # UUID v4 has specific version bits set
        assert context.tenant_id.version == 4
    
    def test_case_insensitive_uuid(self):
        """Test UUID parsing is case-insensitive."""
        uuid_lower = "550e8400-e29b-41d4-a716-446655440000"
        uuid_upper = "550E8400-E29B-41D4-A716-446655440000"
        
        context_lower = TenantContext(tenant_id=uuid_lower)
        context_upper = TenantContext(tenant_id=uuid_upper)
        
        assert context_lower.tenant_id == context_upper.tenant_id


class TestTenantMissingError:
    """Tests for TenantMissingError exception."""
    
    def test_default_message(self):
        """Test TenantMissingError has correct default message."""
        error = TenantMissingError()
        assert error.message == "X-Tenant-ID header is required"
        assert str(error) == "X-Tenant-ID header is required"
    
    def test_custom_message(self):
        """Test TenantMissingError with custom message."""
        custom_msg = "Tenant ID is required for this operation"
        error = TenantMissingError(message=custom_msg)
        assert error.message == custom_msg
        assert str(error) == custom_msg
    
    def test_exception_inheritance(self):
        """Test TenantMissingError is a proper Exception."""
        error = TenantMissingError()
        assert isinstance(error, Exception)


class TestTenantValidationError:
    """Tests for TenantValidationError exception."""
    
    def test_default_message(self):
        """Test TenantValidationError has correct default message."""
        error = TenantValidationError()
        assert "Invalid tenant ID format" in error.message
        assert "UUID" in error.message
    
    def test_custom_message(self):
        """Test TenantValidationError with custom message."""
        custom_msg = "Tenant ID must be a valid UUID v4"
        error = TenantValidationError(message=custom_msg)
        assert error.message == custom_msg
    
    def test_with_detail(self):
        """Test TenantValidationError with additional detail."""
        error = TenantValidationError(
            message="Invalid UUID",
            detail="Expected format: 550e8400-e29b-41d4-a716-446655440000"
        )
        assert error.message == "Invalid UUID"
        assert error.detail == "Expected format: 550e8400-e29b-41d4-a716-446655440000"
    
    def test_exception_inheritance(self):
        """Test TenantValidationError is a proper Exception."""
        error = TenantValidationError()
        assert isinstance(error, Exception)


class TestTenantContextEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_nil_uuid(self):
        """Test TenantContext with nil UUID (all zeros)."""
        nil_uuid = "00000000-0000-0000-0000-000000000000"
        context = TenantContext(tenant_id=nil_uuid)
        
        assert str(context.tenant_id) == nil_uuid
    
    def test_max_uuid(self):
        """Test TenantContext with max UUID (all Fs)."""
        max_uuid = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        context = TenantContext(tenant_id=max_uuid)
        
        assert str(context.tenant_id) == max_uuid
    
    def test_uuid_without_hyphens_accepted(self):
        """Test that UUID without hyphens is accepted (Python UUID supports this)."""
        # Python's UUID class accepts UUIDs without hyphens
        context = TenantContext(tenant_id="550e8400e29b41d4a716446655440000")
        assert str(context.tenant_id) == "550e8400-e29b-41d4-a716-446655440000"
    
    def test_uuid_with_extra_characters_fails(self):
        """Test that UUID with extra characters is rejected."""
        with pytest.raises(ValidationError):
            TenantContext(tenant_id="550e8400-e29b-41d4-a716-446655440000-extra")
    
    def test_multiple_instances_independent(self):
        """Test that multiple TenantContext instances are independent."""
        context1 = TenantContext(tenant_id=uuid4())
        context2 = TenantContext(tenant_id=uuid4())
        
        assert context1.tenant_id != context2.tenant_id
