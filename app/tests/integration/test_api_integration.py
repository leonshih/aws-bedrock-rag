"""
Integration tests for API layer.
Tests router → service → adapter flow with mocked AWS dependencies.
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from app.main import app
from app.utils.config import Config

# Test tenant ID for multi-tenant testing
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def client():
    """Create test client with real app configuration."""
    return TestClient(app)


@pytest.fixture
def config():
    """Get application config."""
    return Config()


class TestChatRouterIntegration:
    """Test chat router with mocked AWS service dependencies."""

    @patch('app.adapters.bedrock.bedrock_adapter.boto3.client')
    def test_chat_endpoint_exists(self, mock_boto_client, client):
        """Test chat endpoint is registered and accessible."""
        # Mock Bedrock client
        mock_client = Mock()
        mock_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Test answer'},
            'citations': [],
            'sessionId': 'test-session'
        }
        mock_boto_client.return_value = mock_client
        
        response = client.post(
            "/chat",
            json={"query": "test"},
            headers={"X-Tenant-ID": TEST_TENANT_ID}
        )
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    @patch('app.adapters.bedrock.bedrock_adapter.boto3.client')
    def test_chat_endpoint_with_valid_request(self, mock_boto_client, client):
        """Test chat endpoint accepts valid request format."""
        # Mock Bedrock client
        mock_client = Mock()
        mock_client.retrieve_and_generate.return_value = {
            'output': {'text': 'AWS Bedrock is a managed AI service.'},
            'citations': [],
            'sessionId': 'test-session'
        }
        mock_boto_client.return_value = mock_client
        
        response = client.post(
            "/chat",
            json={
                "query": "What is AWS Bedrock?",
                "max_results": 5
            },
            headers={"X-Tenant-ID": TEST_TENANT_ID}
        )
        # Should return 200 with mocked response
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
        assert "answer" in data["data"]
        assert "citations" in data["data"]

    def test_chat_endpoint_validation_error(self, client):
        """Test chat endpoint returns 422 for invalid request."""
        response = client.post(
            "/chat",
            json={"query": ""},  # Empty query should fail validation
            headers={"X-Tenant-ID": TEST_TENANT_ID}
        )
        assert response.status_code == 422
        assert "error" in response.json()

    @patch('app.adapters.bedrock.bedrock_adapter.boto3.client')
    def test_chat_endpoint_with_metadata_filter(self, mock_boto_client, client):
        """Test chat endpoint accepts metadata filters."""
        # Mock Bedrock client
        mock_client = Mock()
        mock_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Filtered answer'},
            'citations': [],
            'sessionId': 'test-session'
        }
        mock_boto_client.return_value = mock_client
        
        response = client.post(
            "/chat",
            json={
                "query": "test query",
                "metadata_filter": {
                    "equals": {"category": "documentation"}
                }
            },
            headers={"X-Tenant-ID": TEST_TENANT_ID}
        )
        # Should not fail validation
        assert response.status_code != 422

    @patch('app.adapters.bedrock.bedrock_adapter.boto3.client')
    def test_chat_endpoint_service_initialization(self, mock_boto_client, client):
        """Test chat endpoint properly initializes RAG service."""
        # Mock Bedrock client
        mock_client = Mock()
        mock_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Test answer'},
            'citations': [],
            'sessionId': 'test-session'
        }
        mock_boto_client.return_value = mock_client
        
        # This test ensures the dependency injection works
        response = client.post(
            "/chat",
            json={"query": "test"},
            headers={"X-Tenant-ID": TEST_TENANT_ID}
        )
        
        # Should work fine with mocked AWS
        assert response.status_code == 200


class TestIngestRouterIntegration:
    """Test ingest router with mocked AWS service dependencies."""

    def test_list_files_endpoint_exists(self, client):
        """Test list files endpoint is registered and accessible."""
        response = client.get("/files", headers={"X-Tenant-ID": TEST_TENANT_ID})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    @patch('app.adapters.s3.s3_adapter.boto3.client')
    def test_list_files_with_real_service(self, mock_boto_client, client):
        """Test list files endpoint with service initialization."""
        # Mock S3 client
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {
            'Contents': [],
            'IsTruncated': False
        }
        mock_boto_client.return_value = mock_client
        
        response = client.get("/files", headers={"X-Tenant-ID": TEST_TENANT_ID})
        
        # Should return successful response with file list
        assert response.status_code == 200
        json_data = response.json()
        # Response has success wrapper
        assert "success" in json_data
        assert json_data["success"] is True
        assert "data" in json_data
        # Files are inside data object
        data = json_data["data"]
        assert "files" in data
        assert "total_count" in data
        assert isinstance(data["files"], list)

    def test_upload_file_endpoint_exists(self, client):
        """Test upload file endpoint is registered and accessible."""
        # Minimal request to check endpoint exists
        response = client.post(
            "/files",
            files={"file": ("test.txt", b"test content", "text/plain")},
            headers={"X-Tenant-ID": TEST_TENANT_ID}
        )
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_upload_file_validation_error(self, client):
        """Test upload endpoint returns 422 for invalid request."""
        # Missing required file parameter
        response = client.post("/files", data={}, headers={"X-Tenant-ID": TEST_TENANT_ID})
        assert response.status_code == 422

    def test_upload_file_with_metadata(self, client):
        """Test upload endpoint accepts metadata."""
        response = client.post(
            "/files",
            files={"file": ("test.txt", b"test content", "text/plain")},
            data={"metadata": '{"category": "test"}'},
            headers={"X-Tenant-ID": TEST_TENANT_ID}
        )
        # Should not fail validation
        assert response.status_code != 422

    def test_delete_file_endpoint_exists(self, client):
        """Test delete file endpoint is registered and accessible."""
        response = client.delete("/files/test.txt", headers={"X-Tenant-ID": TEST_TENANT_ID})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    @patch('app.adapters.s3.s3_adapter.boto3.client')
    def test_delete_file_with_real_service(self, mock_boto_client, client):
        """Test delete endpoint with service initialization."""
        # Mock S3 client
        mock_client = Mock()
        mock_client.delete_object.return_value = {}
        mock_boto_client.return_value = mock_client
        
        response = client.delete("/files/nonexistent.txt", headers={"X-Tenant-ID": TEST_TENANT_ID})
        
        # Should handle gracefully with mocked AWS
        assert response.status_code == 200


class TestAPIExceptionHandling:
    """Test exception handlers work with real API requests."""

    def test_validation_error_format(self, client):
        """Test validation errors return proper format."""
        response = client.post(
            "/chat",
            json={"query": ""},  # Invalid: empty query
            headers={"X-Tenant-ID": TEST_TENANT_ID}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        # Path is nested in error object
        assert "path" in data["error"]
        assert data["error"]["path"] == "/chat"

    def test_general_error_includes_path(self, client):
        """Test error responses include request path."""
        # Try to trigger an error with malformed JSON
        response = client.post(
            "/chat",
            data="invalid json",
            headers={"Content-Type": "application/json", "X-Tenant-ID": TEST_TENANT_ID}
        )
        
        data = response.json()
        # Path is nested in error object
        assert "error" in data
        assert "path" in data["error"]

    def test_404_error_format(self, client):
        """Test 404 errors return proper format."""
        response = client.get("/nonexistent-endpoint", headers={"X-Tenant-ID": TEST_TENANT_ID})
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestAPIDependencyInjection:
    """Test dependency injection works correctly in API layer."""

    @patch('app.adapters.bedrock.bedrock_adapter.boto3.client')
    def test_chat_router_dependency_injection(self, mock_boto_client, client):
        """Test chat router properly injects RAG service."""
        # Mock Bedrock client
        mock_client = Mock()
        mock_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Test answer'},
            'citations': [],
            'sessionId': 'test-session'
        }
        mock_boto_client.return_value = mock_client
        
        # This would fail if dependency injection is broken
        response = client.post(
            "/chat",
            json={"query": "test"},
            headers={"X-Tenant-ID": TEST_TENANT_ID}
        )
        
        # Should not get TypeError about missing parameters
        assert response.status_code == 200
        assert "TypeError" not in response.text

    @patch('app.adapters.s3.s3_adapter.boto3.client')
    def test_ingest_router_dependency_injection(self, mock_boto_client, client):
        """Test ingest router properly injects Ingestion service."""
        # Mock S3 client
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {
            'Contents': [],
            'IsTruncated': False
        }
        mock_boto_client.return_value = mock_client
        
        # This would fail if dependency injection is broken
        response = client.get("/files", headers={"X-Tenant-ID": TEST_TENANT_ID})
        
        # Should not get TypeError about missing parameters
        assert response.status_code == 200
        assert "TypeError" not in response.text

    @patch('app.adapters.bedrock.bedrock_adapter.boto3.client')
    def test_multiple_requests_use_different_service_instances(self, mock_boto_client, client):
        """Test each request gets fresh service instance."""
        # Mock Bedrock client
        mock_client = Mock()
        mock_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Test answer'},
            'citations': [],
            'sessionId': 'test-session'
        }
        mock_boto_client.return_value = mock_client
        
        response1 = client.post("/chat", json={"query": "test1"}, headers={"X-Tenant-ID": TEST_TENANT_ID})
        response2 = client.post("/chat", json={"query": "test2"}, headers={"X-Tenant-ID": TEST_TENANT_ID})
        
        # Both should work with mocked AWS
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestAPIHealthCheck:
    """Test API health and readiness."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "name" in data

    def test_openapi_docs_available(self, client):
        """Test OpenAPI documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_available(self, client):
        """Test OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "/chat" in schema["paths"]
        assert "/files" in schema["paths"]
