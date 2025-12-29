"""Unit tests for ingest router."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime
from io import BytesIO

from app.main import app
from app.dtos.routers.ingest import FileResponse, FileListResponse, FileDeleteResponse
from app.routers.ingest.ingest_router import get_ingestion_service

# Test tenant ID for all tests
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def mock_ingestion_service():
    """Create a mock Ingestion service."""
    service = Mock()
    
    # Mock list_documents response
    service.list_documents.return_value = {
        "success": True,
        "data": FileListResponse(
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
    }
    
    # Mock upload_document response
    service.upload_document.return_value = {
        "success": True,
        "data": FileResponse(
            filename="uploaded.pdf",
            size=2048000,
            last_modified=datetime(2024, 1, 15, 11, 0, 0),
            s3_key="documents/uploaded.pdf",
            metadata={"category": "test"}
        )
    }
    
    # Mock delete_document response
    service.delete_document.return_value = {
        "success": True,
        "data": FileDeleteResponse(
            filename="test-doc.pdf",
            status="deleted",
            message="File deleted successfully"
        )
    }
    
    return service


@pytest.fixture
def client(mock_ingestion_service):
    """Create test client with mocked Ingestion service."""
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion_service
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


def test_list_files_success(client, mock_ingestion_service):
    """Test successful file listing."""
    response = client.get("/files", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["total_count"] == 1
    assert data["data"]["total_size"] == 1024000
    assert len(data["data"]["files"]) == 1
    assert data["data"]["files"][0]["filename"] == "test-doc.pdf"
    assert mock_ingestion_service.list_documents.call_count == 1


def test_list_files_with_prefix(client, mock_ingestion_service):
    """Test file listing with prefix filter."""
    response = client.get("/files?prefix=documents/2024/", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
    call_args = mock_ingestion_service.list_documents.call_args
    assert call_args[1]["prefix"] == "documents/2024/"


def test_list_files_empty(client, mock_ingestion_service):
    """Test listing when no files exist."""
    mock_ingestion_service.list_documents.return_value = {
        "success": True,
        "data": FileListResponse(
            files=[],
            total_count=0,
            total_size=0
        )
    }
    
    response = client.get("/files", headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_count"] == 0
    assert len(data["data"]["files"]) == 0


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
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["filename"] == "uploaded.pdf"
    assert data["data"]["size"] == 2048000
    assert mock_ingestion_service.upload_document.call_count == 1


def test_upload_file_with_metadata(client, mock_ingestion_service):
    """Test file upload with metadata."""
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    metadata = '{"category": "research", "year": "2024"}'
    data = {"metadata": metadata}
    
    response = client.post("/files", files=files, data=data, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
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
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["filename"] == "test-doc.pdf"
    assert data["data"]["status"] == "deleted"
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
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert mock_ingestion_service.upload_document.call_count == 2


def test_upload_with_empty_metadata(client, mock_ingestion_service):
    """Test file upload with empty metadata string."""
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    data = {"metadata": ""}
    
    response = client.post("/files", files=files, data=data, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    # Empty string is treated as no metadata (None)
    assert response.status_code == 200
    call_args = mock_ingestion_service.upload_document.call_args
    assert call_args[1]["metadata"] is None


def test_upload_with_complex_metadata(client, mock_ingestion_service):
    """Test file upload with complex nested metadata."""
    file_content = b"Test PDF content"
    files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
    metadata = '{"category": "research", "tags": ["AI", "ML"], "author": {"name": "John", "email": "john@example.com"}}'
    data = {"metadata": metadata}
    
    response = client.post("/files", files=files, data=data, headers={"X-Tenant-ID": TEST_TENANT_ID})
    
    assert response.status_code == 200
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
    
    # Check wrapper structure
    assert data["success"] is True
    assert "data" in data
    
    # Check required fields in data
    assert "files" in data["data"]
    assert "total_count" in data["data"]
    assert "total_size" in data["data"]
    
    # Check file structure
    if len(data["data"]["files"]) > 0:
        file_obj = data["data"]["files"][0]
        assert "filename" in file_obj
        assert "size" in file_obj
        assert "last_modified" in file_obj
        assert "s3_key" in file_obj
        assert "metadata" in file_obj
