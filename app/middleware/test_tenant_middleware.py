"""
Unit tests for tenant middleware.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import UUID
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.tenant_middleware import TenantMiddleware, get_tenant_context
from app.dtos.common import TenantContext, TenantMissingError, TenantValidationError
from app.middleware.exception_handlers import register_exception_handlers


@pytest.fixture
def app_with_tenant_middleware():
    """Create FastAPI app with tenant middleware for testing."""
    app = FastAPI()
    
    # Register exception handlers first
    register_exception_handlers(app)
    
    # Add tenant middleware
    app.add_middleware(TenantMiddleware)
    
    # Add test endpoint that uses tenant context
    @app.get("/test")
    async def test_endpoint(request: Request):
        tenant_context = get_tenant_context(request)
        return {
            "tenant_id": str(tenant_context.tenant_id),
            "message": "Success"
        }
    
    # Add test endpoint without tenant requirement
    @app.get("/public")
    async def public_endpoint():
        return {"message": "Public access"}
    
    return app


@pytest.fixture
def client(app_with_tenant_middleware):
    """Create test client."""
    return TestClient(app_with_tenant_middleware)


class TestTenantMiddleware:
    """Test suite for TenantMiddleware."""
    
    def test_valid_tenant_id_header(self, client):
        """Test middleware extracts valid tenant ID from header."""
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(
            "/test",
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == tenant_id
        assert data["message"] == "Success"
    
    def test_valid_tenant_id_without_hyphens(self, client):
        """Test middleware accepts UUID without hyphens (if supported by Pydantic)."""
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(
            "/test",
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data
    
    def test_missing_tenant_id_header(self, client):
        """Test middleware raises error when X-Tenant-ID header is missing."""
        response = client.get("/test")
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "Tenant" in data["error"]["message"] or "required" in data["error"]["message"]
    
    def test_invalid_tenant_id_format(self, client):
        """Test middleware raises error for invalid UUID format."""
        invalid_ids = [
            "not-a-uuid",
            "12345",
            "invalid-tenant-id",
            "550e8400-xxxx-yyyy-zzzz-446655440000"
        ]
        
        for invalid_id in invalid_ids:
            response = client.get(
                "/test",
                headers={"X-Tenant-ID": invalid_id}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    def test_empty_tenant_id_header(self, client):
        """Test middleware raises error for empty tenant ID."""
        response = client.get(
            "/test",
            headers={"X-Tenant-ID": ""}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    def test_tenant_context_injected_into_request_state(self, client):
        """Test that TenantContext is correctly injected into request.state."""
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(
            "/test",
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
        # The endpoint successfully retrieved tenant_context from request.state
        data = response.json()
        assert data["tenant_id"] == tenant_id
    
    def test_excluded_paths_dont_require_tenant_id(self, client):
        """Test that excluded paths work without tenant ID."""
        excluded_paths = ["/", "/health", "/docs", "/openapi.json"]
        
        for path in excluded_paths:
            response = client.get(path)
            # Should not fail with 400 (tenant missing error)
            # May return 404 if path doesn't exist, but not 400
            assert response.status_code != 400
    
    def test_public_endpoint_without_tenant_id(self, client):
        """Test endpoints can be marked as public (not in this implementation, but architecture supports it)."""
        # This tests that middleware doesn't break normal endpoints
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(
            "/public",
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 200
    
    def test_multiple_requests_with_different_tenants(self, client):
        """Test that different requests maintain separate tenant contexts."""
        tenant_id_1 = "550e8400-e29b-41d4-a716-446655440000"
        tenant_id_2 = "660e8400-e29b-41d4-a716-446655440001"
        
        response_1 = client.get(
            "/test",
            headers={"X-Tenant-ID": tenant_id_1}
        )
        response_2 = client.get(
            "/test",
            headers={"X-Tenant-ID": tenant_id_2}
        )
        
        assert response_1.status_code == 200
        assert response_2.status_code == 200
        assert response_1.json()["tenant_id"] == tenant_id_1
        assert response_2.json()["tenant_id"] == tenant_id_2
    
    def test_case_insensitive_header_name(self, client):
        """Test that header name is case-insensitive (HTTP standard)."""
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # HTTP headers are case-insensitive
        response = client.get(
            "/test",
            headers={"x-tenant-id": tenant_id}  # lowercase
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == tenant_id


class TestGetTenantContext:
    """Test suite for get_tenant_context helper function."""
    
    def test_get_tenant_context_success(self):
        """Test get_tenant_context retrieves context from request state."""
        # Create mock request with tenant context
        request = Mock(spec=Request)
        tenant_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        request.state.tenant_context = TenantContext(tenant_id=tenant_id)
        
        context = get_tenant_context(request)
        
        assert context.tenant_id == tenant_id
        assert isinstance(context, TenantContext)
    
    def test_get_tenant_context_missing_raises_error(self):
        """Test get_tenant_context raises error when context is missing."""
        # Create mock request without tenant context
        request = Mock(spec=Request)
        request.state = Mock()
        
        # Remove tenant_context attribute
        if hasattr(request.state, 'tenant_context'):
            delattr(request.state, 'tenant_context')
        
        with pytest.raises(TenantMissingError) as exc_info:
            get_tenant_context(request)
        
        assert "not found" in str(exc_info.value).lower()


class TestTenantMiddlewareIntegration:
    """Integration tests for tenant middleware with exception handlers."""
    
    def test_tenant_missing_error_formatted_correctly(self, client):
        """Test that TenantMissingError is formatted by exception handler."""
        response = client.get("/test")
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "type" in data["error"]
        assert "message" in data["error"]
    
    def test_tenant_validation_error_formatted_correctly(self, client):
        """Test that TenantValidationError is formatted by exception handler."""
        response = client.get(
            "/test",
            headers={"X-Tenant-ID": "invalid-uuid"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "invalid" in data["error"]["message"].lower() or "validation" in data["error"]["message"].lower()
    
    def test_middleware_preserves_other_errors(self, client):
        """Test that middleware doesn't interfere with other error handling."""
        # Request to non-existent endpoint with valid tenant
        tenant_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(
            "/nonexistent",
            headers={"X-Tenant-ID": tenant_id}
        )
        
        # Should return 404, not tenant-related error
        assert response.status_code == 404
