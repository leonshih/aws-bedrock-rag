"""
Unit tests for File DTOs

Tests Pydantic validation and serialization for file-related models.
"""
import pytest
from datetime import datetime
from uuid import UUID
from pydantic import ValidationError
from app.dtos.routers.ingest import (
    FileMetadata,
    FileUploadRequest,
    FileResponse,
    FileListResponse,
    FileDeleteResponse,
)

# Test tenant ID for all test cases
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"


class TestFileMetadata:
    """Tests for FileMetadata model."""
    
    def test_valid_file_metadata(self):
        """Test creating valid file metadata."""
        metadata = FileMetadata(
            tenant_id=TEST_TENANT_ID,
            attributes={
                "author": "Dr. Smith",
                "year": 2023,
                "tags": ["medical", "research"]
            }
        )
        assert metadata.tenant_id == UUID(TEST_TENANT_ID)
        assert metadata.attributes["author"] == "Dr. Smith"
        assert metadata.attributes["year"] == 2023
        assert len(metadata.attributes["tags"]) == 2
    
    def test_empty_metadata(self):
        """Test metadata with no attributes."""
        metadata = FileMetadata(tenant_id=TEST_TENANT_ID)
        assert metadata.tenant_id == UUID(TEST_TENANT_ID)
        assert metadata.attributes == {}
    
    def test_metadata_with_various_types(self):
        """Test metadata supports various value types."""
        metadata = FileMetadata(
            tenant_id=TEST_TENANT_ID,
            attributes={
                "string": "value",
                "number": 42,
                "boolean": True,
                "list": [1, 2, 3],
                "nested": {"key": "value"}
            }
        )
        assert metadata.tenant_id == UUID(TEST_TENANT_ID)
        assert metadata.attributes["string"] == "value"
        assert metadata.attributes["number"] == 42
        assert metadata.attributes["boolean"] is True


class TestFileUploadRequest:
    """Tests for FileUploadRequest model."""
    
    def test_valid_upload_request(self):
        """Test creating valid upload request."""
        request = FileUploadRequest(
            tenant_id=TEST_TENANT_ID,
            metadata=FileMetadata(
                tenant_id=TEST_TENANT_ID,
                attributes={"author": "John Doe", "year": 2023}
            )
        )
        assert request.tenant_id == UUID(TEST_TENANT_ID)
        assert request.metadata.attributes["author"] == "John Doe"
    
    def test_upload_request_without_metadata(self):
        """Test upload request without metadata."""
        request = FileUploadRequest(tenant_id=TEST_TENANT_ID)
        assert request.tenant_id == UUID(TEST_TENANT_ID)
        assert request.metadata is None
    
    def test_upload_request_serialization(self):
        """Test serialization of upload request."""
        request = FileUploadRequest(
            tenant_id=TEST_TENANT_ID,
            metadata=FileMetadata(tenant_id=TEST_TENANT_ID, attributes={"key": "value"})
        )
        data = request.model_dump()
        assert data["tenant_id"] == UUID(TEST_TENANT_ID)
        assert data["metadata"]["attributes"]["key"] == "value"


class TestFileResponse:
    """Tests for FileResponse model."""
    
    def test_valid_file_response(self):
        """Test creating valid file response."""
        response = FileResponse(
            filename="test.pdf",
            size=1024000,
            s3_key="documents/test.pdf"
        )
        assert response.filename == "test.pdf"
        assert response.size == 1024000
        assert response.s3_key == "documents/test.pdf"
    
    def test_file_response_with_metadata(self):
        """Test file response with metadata."""
        response = FileResponse(
            filename="doc.pdf",
            size=2048,
            metadata={"author": "Dr. Smith", "year": 2023}
        )
        assert response.metadata["author"] == "Dr. Smith"
    
    def test_file_response_with_timestamp(self):
        """Test file response with last_modified timestamp."""
        now = datetime.now()
        response = FileResponse(
            filename="file.pdf",
            size=1024,
            last_modified=now
        )
        assert response.last_modified == now
    
    def test_file_response_minimal_fields(self):
        """Test file response with only required fields."""
        response = FileResponse(filename="minimal.pdf", size=512)
        assert response.filename == "minimal.pdf"
        assert response.size == 512
        assert response.last_modified is None
        assert response.s3_key is None
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError):
            FileResponse(filename="test.pdf")  # Missing size
        
        with pytest.raises(ValidationError):
            FileResponse(size=1024)  # Missing filename


class TestFileListResponse:
    """Tests for FileListResponse model."""
    
    def test_valid_file_list_response(self):
        """Test creating valid file list response."""
        response = FileListResponse(
            files=[
                FileResponse(filename="doc1.pdf", size=1024),
                FileResponse(filename="doc2.pdf", size=2048)
            ],
            total_count=2,
            total_size=3072
        )
        assert len(response.files) == 2
        assert response.total_count == 2
        assert response.total_size == 3072
    
    def test_empty_file_list(self):
        """Test file list response with no files."""
        response = FileListResponse(files=[], total_count=0, total_size=0)
        assert response.files == []
        assert response.total_count == 0
    
    def test_file_list_default_files(self):
        """Test file list with default empty files list."""
        response = FileListResponse(total_count=0, total_size=0)
        assert response.files == []
    
    def test_file_list_serialization(self):
        """Test serialization of file list response."""
        response = FileListResponse(
            files=[FileResponse(filename="test.pdf", size=1024)],
            total_count=1,
            total_size=1024
        )
        data = response.model_dump()
        assert len(data["files"]) == 1
        assert data["files"][0]["filename"] == "test.pdf"


class TestFileDeleteResponse:
    """Tests for FileDeleteResponse model."""
    
    def test_valid_delete_response(self):
        """Test creating valid delete response."""
        response = FileDeleteResponse(
            filename="deleted.pdf",
            status="deleted",
            message="File removed successfully"
        )
        assert response.filename == "deleted.pdf"
        assert response.status == "deleted"
        assert response.message == "File removed successfully"
    
    def test_delete_response_without_message(self):
        """Test delete response without optional message."""
        response = FileDeleteResponse(
            filename="file.pdf",
            status="deleted"
        )
        assert response.filename == "file.pdf"
        assert response.message is None
    
    def test_delete_response_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError):
            FileDeleteResponse(status="deleted")  # Missing filename
        
        with pytest.raises(ValidationError):
            FileDeleteResponse(filename="file.pdf")  # Missing status
