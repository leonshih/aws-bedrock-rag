"""Unit tests for exception handlers."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError

from app.middleware.exception_handlers import register_exception_handlers


@pytest.fixture
def test_app():
    """Create a test FastAPI app with exception handlers."""
    app = FastAPI()
    register_exception_handlers(app)
    
    # Add test endpoints that raise different exceptions
    @app.get("/test/aws-access-denied")
    def test_access_denied():
        raise ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "TestOperation"
        )
    
    @app.get("/test/aws-throttling")
    def test_throttling():
        raise ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "TestOperation"
        )
    
    @app.get("/test/aws-not-found")
    def test_not_found():
        raise ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Not found"}},
            "TestOperation"
        )
    
    @app.get("/test/aws-validation")
    def test_validation():
        raise ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid params"}},
            "TestOperation"
        )
    
    @app.get("/test/general-exception")
    def test_general():
        raise RuntimeError("Something went wrong")
    
    @app.get("/test/validation/{item_id}")
    def test_validation_error(item_id: int):
        return {"item_id": item_id}
    
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app, raise_server_exceptions=False)


def test_aws_access_denied_handler(client):
    """Test AccessDenied error returns 403."""
    response = client.get("/test/aws-access-denied")
    
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "aws_error"
    assert data["error"]["code"] == "AccessDenied"
    assert "credentials" in data["error"]["message"].lower()


def test_aws_throttling_handler(client):
    """Test ThrottlingException returns 429."""
    response = client.get("/test/aws-throttling")
    
    assert response.status_code == 429
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "aws_error"
    assert data["error"]["code"] == "ThrottlingException"
    assert "too many requests" in data["error"]["message"].lower()


def test_aws_not_found_handler(client):
    """Test ResourceNotFoundException returns 404."""
    response = client.get("/test/aws-not-found")
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "aws_error"
    assert data["error"]["code"] == "ResourceNotFoundException"


def test_aws_validation_handler(client):
    """Test ValidationException returns 400."""
    response = client.get("/test/aws-validation")
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "aws_error"
    assert data["error"]["code"] == "ValidationException"


def test_general_exception_handler(client):
    """Test unhandled exceptions return 500."""
    response = client.get("/test/general-exception")
    
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "internal_error"
    assert data["error"]["exception_type"] == "RuntimeError"


def test_validation_error_handler(client):
    """Test Pydantic validation errors return 422."""
    # Pass invalid type (string instead of int)
    response = client.get("/test/validation/invalid")
    
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "validation_error"
    assert "details" in data["error"]
    assert len(data["error"]["details"]) > 0


def test_error_includes_path(client):
    """Test that all errors include the request path."""
    response = client.get("/test/aws-access-denied")
    
    data = response.json()
    assert data["error"]["path"] == "/test/aws-access-denied"


def test_server_errors_include_detail(client):
    """Test that 5xx errors include error details."""
    response = client.get("/test/general-exception")
    
    data = response.json()
    assert response.status_code >= 500
    # Internal errors should not expose details to users
    assert "message" in data["error"]


def test_client_errors_no_detail(client):
    """Test that 4xx errors don't expose internal details."""
    response = client.get("/test/aws-access-denied")
    
    data = response.json()
    assert response.status_code < 500
    # Client errors should have user-friendly messages
    assert "detail" not in data["error"] or data["error"]["detail"] is None


def test_validation_error_format(client):
    """Test validation error format is user-friendly."""
    response = client.get("/test/validation/not-a-number")
    
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "validation_error"
    details = data["error"]["details"]
    assert isinstance(details, list)
    
    # Check that each detail has expected fields
    for detail in details:
        assert "field" in detail
        assert "message" in detail
        assert "type" in detail


def test_tenant_missing_handler(client):
    """Test TenantMissingError exception handler."""
    from app.dtos.common import TenantMissingError
    
    # Add a test route that raises TenantMissingError
    @client.app.get("/test/tenant-missing")
    async def raise_tenant_missing():
        raise TenantMissingError(message="X-Tenant-ID header is required")
    
    response = client.get("/test/tenant-missing")
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "tenant_missing_error"
    assert data["error"]["message"] == "X-Tenant-ID header is required"
    assert "path" in data["error"]


def test_tenant_validation_handler(client):
    """Test TenantValidationError exception handler."""
    from app.dtos.common import TenantValidationError
    
    # Add a test route that raises TenantValidationError
    @client.app.get("/test/tenant-validation")
    async def raise_tenant_validation():
        raise TenantValidationError(
            message="Invalid tenant ID format",
            detail="Tenant ID must be a valid UUID"
        )
    
    response = client.get("/test/tenant-validation")
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "tenant_validation_error"
    assert data["error"]["message"] == "Invalid tenant ID format"
    assert data["error"]["detail"] == "Tenant ID must be a valid UUID"
    assert "path" in data["error"]


def test_param_validation_handler(client):
    """Test ParamValidationError exception handler."""
    from botocore.exceptions import ParamValidationError
    
    # Add a test route that raises ParamValidationError
    @client.app.get("/test/param-validation")
    async def raise_param_validation():
        raise ParamValidationError(report="Parameter validation failed: Invalid bucket name")
    
    response = client.get("/test/param-validation")
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "param_validation_error"
    assert "Invalid parameters provided to AWS service" in data["error"]["message"]
    assert "path" in data["error"]
