"""
Unit tests for S3 Adapter
"""
import pytest
from app.adapters.s3 import S3Adapter


class TestS3Adapter:
    """Test cases for S3Adapter in mock mode."""
    
    @pytest.fixture
    def adapter(self):
        """Create a mock S3 adapter instance."""
        return S3Adapter(mock_mode=True)
    
    def test_initialization_mock_mode(self, adapter):
        """Test adapter initializes correctly in mock mode."""
        assert adapter.mock_mode is True
        assert adapter.client is None
        assert adapter._mock_storage == {}
    
    def test_upload_file_success(self, adapter):
        """Test file upload returns proper response."""
        content = b"Test file content"
        bucket = "test-bucket"
        key = "test-file.txt"
        
        response = adapter.upload_file(content, bucket, key)
        
        # Verify wrapper structure
        assert response["success"] is True
        assert "data" in response
        
        # Verify data structure
        data = response["data"]
        assert hasattr(data, "etag")
        assert data.etag is not None
    
    def test_upload_file_with_metadata(self, adapter):
        """Test file upload with metadata."""
        content = b"Test content"
        bucket = "test-bucket"
        key = "file.txt"
        metadata = {"author": "test", "version": "1.0"}
        
        response = adapter.upload_file(content, bucket, key, metadata)
        
        assert response is not None
        assert response["success"] is True
        assert "data" in response
    
    def test_list_files_empty_bucket(self, adapter):
        """Test listing files in empty bucket."""
        bucket = "empty-bucket"
        
        response = adapter.list_files(bucket)
        
        assert response["success"] is True
        data = response["data"]
        assert data.total_count == 0
        assert len(data.objects) == 0
    
    def test_list_files_after_upload(self, adapter):
        """Test listing files after uploading."""
        bucket = "test-bucket"
        content1 = b"Content 1"
        content2 = b"Content 2"
        
        adapter.upload_file(content1, bucket, "file1.txt")
        adapter.upload_file(content2, bucket, "file2.txt")
        
        files = adapter.list_files(bucket)
        
        assert len(files) == 2
        assert any(f['Key'] == 'file1.txt' for f in files)
        assert any(f['Key'] == 'file2.txt' for f in files)
    
    def test_list_files_with_prefix(self, adapter):
        """Test listing files with prefix filter."""
        bucket = "test-bucket"
        
        adapter.upload_file(b"Content 1", bucket, "docs/file1.txt")
        adapter.upload_file(b"Content 2", bucket, "docs/file2.txt")
        adapter.upload_file(b"Content 3", bucket, "other/file3.txt")
        
        files = adapter.list_files(bucket, prefix="docs/")
        
        assert len(files) == 2
        assert all(f['Key'].startswith('docs/') for f in files)
    
    def test_delete_file_success(self, adapter):
        """Test file deletion."""
        bucket = "test-bucket"
        key = "file-to-delete.txt"
        content = b"Delete me"
        
        # Upload file first
        adapter.upload_file(content, bucket, key)
        
        # Verify it exists
        files = adapter.list_files(bucket)
        assert len(files) == 1
        
        # Delete file
        response = adapter.delete_file(bucket, key)
        
        assert response['ResponseMetadata']['HTTPStatusCode'] == 204
        
        # Verify it's deleted
        files = adapter.list_files(bucket)
        assert len(files) == 0
    
    def test_delete_nonexistent_file(self, adapter):
        """Test deleting non-existent file doesn't raise error."""
        bucket = "test-bucket"
        key = "nonexistent.txt"
        
        # Should not raise exception
        response = adapter.delete_file(bucket, key)
        assert response is not None
    
    def test_get_file_success(self, adapter):
        """Test downloading file content."""
        bucket = "test-bucket"
        key = "test.txt"
        original_content = b"Test content to download"
        
        adapter.upload_file(original_content, bucket, key)
        
        downloaded_content = adapter.get_file(bucket, key)
        
        assert downloaded_content == original_content
    
    def test_get_file_not_found(self, adapter):
        """Test downloading non-existent file raises error."""
        bucket = "test-bucket"
        key = "nonexistent.txt"
        
        with pytest.raises(KeyError):
            adapter.get_file(bucket, key)
    
    def test_file_size_in_list(self, adapter):
        """Test file size is correctly reported in list."""
        bucket = "test-bucket"
        key = "sized-file.txt"
        content = b"12345"  # 5 bytes
        
        adapter.upload_file(content, bucket, key)
        
        files = adapter.list_files(bucket)
        
        assert len(files) == 1
        assert files[0]['Size'] == 5
        assert files[0]['Key'] == key
    
    def test_multiple_buckets_isolated(self, adapter):
        """Test files in different buckets are isolated."""
        bucket1 = "bucket1"
        bucket2 = "bucket2"
        
        adapter.upload_file(b"Content 1", bucket1, "file1.txt")
        adapter.upload_file(b"Content 2", bucket2, "file2.txt")
        
        files1 = adapter.list_files(bucket1)
        files2 = adapter.list_files(bucket2)
        
        assert len(files1) == 1
        assert len(files2) == 1
        assert files1[0]['Key'] == 'file1.txt'
        assert files2[0]['Key'] == 'file2.txt'
