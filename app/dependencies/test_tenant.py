"""
Unit tests for tenant dependency.
"""
import pytest
from uuid import UUID
from fastapi import HTTPException

from app.dependencies.tenant import get_tenant_context
from app.dtos.common import TenantContext


class TestGetTenantContext:
    """Test suite for get_tenant_context dependency."""
    
    @pytest.mark.asyncio
    async def test_valid_tenant_id(self):
        """Test that valid UUID creates TenantContext successfully."""
        # Arrange
        valid_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        
        # Act
        result = await get_tenant_context(x_tenant_id=valid_uuid)
        
        # Assert
        assert isinstance(result, TenantContext)
        assert result.tenant_id == valid_uuid
    
    @pytest.mark.asyncio
    async def test_tenant_context_properties(self):
        """Test that returned TenantContext has correct properties."""
        # Arrange
        test_uuid = UUID("123e4567-e89b-12d3-a456-426614174000")
        
        # Act
        result = await get_tenant_context(x_tenant_id=test_uuid)
        
        # Assert
        assert result.tenant_id == test_uuid
        assert isinstance(result.tenant_id, UUID)
    
    @pytest.mark.asyncio
    async def test_different_tenant_ids(self):
        """Test that different UUIDs create different contexts."""
        # Arrange
        uuid1 = UUID("550e8400-e29b-41d4-a716-446655440000")
        uuid2 = UUID("123e4567-e89b-12d3-a456-426614174000")
        
        # Act
        context1 = await get_tenant_context(x_tenant_id=uuid1)
        context2 = await get_tenant_context(x_tenant_id=uuid2)
        
        # Assert
        assert context1.tenant_id != context2.tenant_id
        assert context1.tenant_id == uuid1
        assert context2.tenant_id == uuid2


class TestGetTenantContextIntegration:
    """Integration tests for get_tenant_context with FastAPI."""
    
    @pytest.mark.asyncio
    async def test_dependency_returns_tenant_context(self):
        """Test that dependency returns TenantContext instance."""
        # Arrange
        tenant_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        
        # Act
        result = await get_tenant_context(x_tenant_id=tenant_uuid)
        
        # Assert
        assert isinstance(result, TenantContext)
        assert hasattr(result, 'tenant_id')
    
    @pytest.mark.asyncio
    async def test_nil_uuid_accepted(self):
        """Test that nil UUID (all zeros) is accepted."""
        # Arrange
        nil_uuid = UUID("00000000-0000-0000-0000-000000000000")
        
        # Act
        result = await get_tenant_context(x_tenant_id=nil_uuid)
        
        # Assert
        assert result.tenant_id == nil_uuid
    
    @pytest.mark.asyncio
    async def test_max_uuid_accepted(self):
        """Test that max UUID (all Fs) is accepted."""
        # Arrange
        max_uuid = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        
        # Act
        result = await get_tenant_context(x_tenant_id=max_uuid)
        
        # Assert
        assert result.tenant_id == max_uuid
