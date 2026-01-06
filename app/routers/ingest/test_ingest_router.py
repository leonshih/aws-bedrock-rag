"""Unit tests for ingest router."""

import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime
from io import BytesIO

from app.main import app
from app.dtos.routers.ingest import FileResponse, FileListResponse, FileDeleteResponse
from app.dtos.common import TenantContext
from app.routers.ingest.ingest_router import get_ingestion_service
from app.dependencies import get_tenant_context

# Test tenant ID for all tests
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def mock_tenant_context():
    """Create a mock tenant context."""
    return TenantContext(tenant_id=UUID(TEST_TENANT_ID))


@pytest.fixture
def mock_ingestion_service():
    """Create a mock Ingestion service."""
    service = Mock()
    
    # Mock list_documents response
    service.list_documents.return_value = FileListResponse(
        files=[
            FileResponse(
                filename="test-doc.pdf",
                size=1024000,
                last_modified=datetime(2024, 1, 15, 10, 30, 0),
                s3_key="documents/test-doc.pdf",
                metadata={"category": "research", "year": "2024"}
            )
        ],
        total_count=1,
        total_size=1024000
    )
    
    # Mock upload_document response
    service.upload_document.return_value = FileResponse(
        filename="uploaded.pdf",
        size=2048000,
        last_modified=datetime(2024, 1, 15, 11, 0, 0),
        s3_key="documents/uploaded.pdf",
        metadata={"category": "test"}
    )
    
    # Mock delete_document response
    service.delete_document.return_value = FileDeleteResponse(
        filename="test-doc.pdf",
        status="deleted",
        message="File deleted successfully"
    )
    
    return service


@pytest.fixture
def client(mock_ingestion_service, mock_tenant_context):
    """Create test client with mocked dependencies."""
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion_service
    app.dependency_overrides[get_tenant_context] = lambda: mock_tenant_context
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


def test_list_files_success(client, mock_ingestion_service):
    """Test successful file listing."""
    response = client.get("/files", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["total_size"] == 1024000
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == "test-doc.pdf"
    assert mock_ingestion_service.list_documents.call_count == 1


def test_list_files_with_prefix(client, mock_ingestion_service):
    """Test file listing with prefix filter."""
    from uuid import UUID
    response = client.get("/files?prefix=documents/2024/", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
    # Verify tenant_id was passed to service
    call_args = mock_ingestion_service.list_documents.call_args
    # tenant_id should be passed as keyword argument (as UUID object)
    assert call_args[1]["tenant_id"] == UUID(TEST_TENANT_ID)


def test_list_files_empty(client, mock_ingestion_service):
    """Test listing when no files exist."""
    mock_ingestion_service.list_documents.return_value = FileListResponse(
        files=[],
        total_count=0,
        total_size=0
    )
    
    response = client.get("/files", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 0
    assert len(data["files"]) == 0


def test_list_files_error(client, mock_ingestion_service):
    """Test handling of error during listing."""
    mock_ingestion_service.list_documents.side_effect = Exception("S3 error")
    
    response = client.get("/files", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert "error" in data


def test_upload_file_success(client, mock_ingestion_service):
    """Test successful file upload."""
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    
    response = client.post("/files", files=files, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "uploaded.pdf"
    assert data["size"] == 2048000
    assert mock_ingestion_service.upload_document.call_count == 1


def test_upload_file_with_metadata(client, mock_ingestion_service):
    """Test file upload with metadata."""
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    metadata = '{"category": "research", "year": "2024"}'
    data = {"metadata": metadata}
    
    response = client.post("/files", files=files, data=data, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 201
    call_args = mock_ingestion_service.upload_document.call_args
    assert call_args[1]["metadata"] == {"category": "research", "year": "2024"}


def test_upload_file_with_invalid_json_metadata(client, mock_ingestion_service):
    """Test file upload with invalid JSON metadata."""
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    data = {"metadata": "not valid json{"}
    
    response = client.post("/files", files=files, data=data, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Invalid JSON metadata" in data["error"]["message"]


def test_upload_file_with_non_dict_metadata(client, mock_ingestion_service):
    """Test file upload with non-dictionary metadata."""
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    data = {"metadata": '["not", "a", "dict"]'}
    
    response = client.post("/files", files=files, data=data, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Metadata must be a JSON object" in data["error"]["message"]


def test_upload_file_service_error(client, mock_ingestion_service):
    """Test handling of error during upload."""
    mock_ingestion_service.upload_document.side_effect = Exception("S3 upload failed")
    
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    
    response = client.post("/files", files=files, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert "error" in data


def test_delete_file_success(client, mock_ingestion_service):
    """Test successful file deletion."""
    response = client.delete("/files/test-doc.pdf", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test-doc.pdf"
    assert data["status"] == "deleted"
    assert mock_ingestion_service.delete_document.call_count == 1


def test_delete_file_not_found(client, mock_ingestion_service):
    """Test deletion of non-existent file."""
    mock_ingestion_service.delete_document.side_effect = FileNotFoundError("File not found")
    
    response = client.delete("/files/nonexistent.pdf", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "File not found" in data["error"]["message"]


def test_delete_file_error(client, mock_ingestion_service):
    """Test handling of error during deletion."""
    mock_ingestion_service.delete_document.side_effect = Exception("S3 delete failed")
    
    response = client.delete("/files/test-doc.pdf", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert "error" in data


def test_upload_multiple_files_sequentially(client, mock_ingestion_service):
    """Test uploading multiple files."""
    files1 = {"file": ("file1.pdf", BytesIO(b"Content 1"), "application/pdf")}
    files2 = {"file": ("file2.pdf", BytesIO(b"Content 2"), "application/pdf")}
    
    response1 = client.post("/files", files=files1, headers={"X-Tenant-ID": TEST_TENANT_ID})
    response2 = client.post("/files", files=files2, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response1.status_code == 201
    assert response2.status_code == 201
    assert mock_ingestion_service.upload_document.call_count == 2


def test_upload_with_empty_metadata(client, mock_ingestion_service):
    """Test file upload with empty metadata string."""
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    data = {"metadata": ""}
    
    response = client.post("/files", files=files, data=data, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    # Empty string is treated as no metadata (None)
    assert response.status_code == 201
    call_args = mock_ingestion_service.upload_document.call_args
    assert call_args[1]["metadata"] is None


def test_upload_with_complex_metadata(client, mock_ingestion_service):
    """Test file upload with complex nested metadata."""
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    metadata = '{"category": "research", "tags": ["AI", "ML"], "author": {"name": "John", "email": "john@example.com"}}'
    data = {"metadata": metadata}
    
    response = client.post("/files", files=files, data=data, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 201
    call_args = mock_ingestion_service.upload_document.call_args
    expected_metadata = {
        "category": "research",
        "tags": ["AI", "ML"],
        "author": {"name": "John", "email": "john@example.com"}
    }
    assert call_args[1]["metadata"] == expected_metadata


def test_delete_with_special_characters_in_filename(client, mock_ingestion_service):
    """Test deletion with special characters in filename."""
    response = client.delete("/files/test%20doc%20(1).pdf", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
    call_args = mock_ingestion_service.delete_document.call_args
    # FastAPI should decode URL encoding
    assert "test doc (1).pdf" in str(call_args)


def test_list_files_response_structure(client, mock_ingestion_service):
    """Test that list response has correct structure."""
    response = client.get("/files", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure (direct Pydantic model)
    assert "files" in data
    assert "total_count" in data
    assert "total_size" in data


def test_upload_file_with_valid_extension(client, mock_ingestion_service):
    """Test file upload with valid extension (.pdf)."""
    file_content = b"Test PDF content"
    files = {"file": ("document.pdf", BytesIO(file_content), "application/pdf")}
    
    response = client.post("/files", files=files, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "uploaded.pdf"
    assert mock_ingestion_service.upload_document.call_count == 1


def test_upload_file_with_invalid_extension(client, mock_ingestion_service):
    """Test file upload with invalid extension (.exe)."""
    file_content = b"Executable content"
    files = {"file": ("malicious.exe", BytesIO(file_content), "application/octet-stream")}
    
    response = client.post("/files", files=files, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert ".exe" in data["error"]["message"]
    assert "not allowed" in data["error"]["message"]
    # Service should not be called
    assert mock_ingestion_service.upload_document.call_count == 0


def test_upload_file_without_extension(client, mock_ingestion_service):
    """Test file upload without extension."""
    file_content = b"File without extension"
    files = {"file": ("README", BytesIO(file_content), "text/plain")}
    
    response = client.post("/files", files=files, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "must have a valid extension" in data["error"]["message"]
    # Service should not be called
    assert mock_ingestion_service.upload_document.call_count == 0


def test_upload_file_case_insensitive_extension(client, mock_ingestion_service):
    """Test file upload with uppercase extension (.PDF)."""
    file_content = b"Test PDF content"
    files = {"file": ("document.PDF", BytesIO(file_content), "application/pdf")}
    
    response = client.post("/files", files=files, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    # Should accept .PDF (case-insensitive)
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "uploaded.pdf"
    assert mock_ingestion_service.upload_document.call_count == 1
