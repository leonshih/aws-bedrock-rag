"""
Unit tests for S3 Adapter
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from botocore.exceptions import ClientError
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
        
        response = adapter.list_files(bucket)
        files = response["data"].objects
        
        assert len(files) == 2
        assert any(f.key == 'file1.txt' for f in files)
        assert any(f.key == 'file2.txt' for f in files)
    
    def test_list_files_with_prefix(self, adapter):
        """Test listing files with prefix filter."""
        bucket = "test-bucket"
        
        adapter.upload_file(b"Content 1", bucket, "docs/file1.txt")
        adapter.upload_file(b"Content 2", bucket, "docs/file2.txt")
        adapter.upload_file(b"Content 3", bucket, "other/file3.txt")
        
        response = adapter.list_files(bucket, prefix="docs/")
        files = response["data"].objects
        
        assert len(files) == 2
        assert all(f.key.startswith('docs/') for f in files)
    
    def test_delete_file_success(self, adapter):
        """Test file deletion."""
        bucket = "test-bucket"
        key = "file-to-delete.txt"
        content = b"Delete me"
        
        # Upload file first
        adapter.upload_file(content, bucket, key)
        
        # Verify it exists
        list_response = adapter.list_files(bucket)
        assert len(list_response["data"].objects) == 1
        
        # Delete file
        response = adapter.delete_file(bucket, key)
        
        assert response["success"] is True
        assert response["data"].deleted is True
        
        # Verify it's deleted
        list_response = adapter.list_files(bucket)
        assert len(list_response["data"].objects) == 0
    
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
        
        response = adapter.list_files(bucket)
        files = response["data"].objects
        
        assert len(files) == 1
        assert files[0].size == 5
        assert files[0].key == key
    
    def test_multiple_buckets_isolated(self, adapter):
        """Test files in different buckets are isolated."""
        bucket1 = "bucket1"
        bucket2 = "bucket2"
        
        adapter.upload_file(b"Content 1", bucket1, "file1.txt")
        adapter.upload_file(b"Content 2", bucket2, "file2.txt")
        
        response1 = adapter.list_files(bucket1)
        response2 = adapter.list_files(bucket2)
        files1 = response1["data"].objects
        files2 = response2["data"].objects
        
        assert len(files1) == 1
        assert len(files2) == 1
        assert files1[0].key == 'file1.txt'


class TestS3AdapterRealMode:
    """Test cases for S3Adapter with real AWS client (mocked)."""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client."""
        return Mock()
    
    @pytest.fixture
    def adapter_real(self, mock_s3_client):
        """Create an S3 adapter in real mode with mocked boto3 client."""
        with patch('boto3.client', return_value=mock_s3_client):
            adapter = S3Adapter(mock_mode=False)
            adapter.client = mock_s3_client
            return adapter
    
    def test_initialization_real_mode(self):
        """Test adapter initializes correctly in real mode."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_boto.return_value = mock_client
            
            adapter = S3Adapter(mock_mode=False)
            
            assert adapter.mock_mode is False
            assert adapter.client is not None
            mock_boto.assert_called_once_with('s3', region_name=adapter.region)
    
    def test_upload_file_real_mode_success(self, adapter_real, mock_s3_client):
        """Test upload_file with real client."""
        content = b"Test file content"
        bucket = "test-bucket"
        key = "test-file.txt"
        
        mock_s3_client.put_object.return_value = {
            'ETag': '"abc123"',
            'VersionId': 'v1'
        }
        
        response = adapter_real.upload_file(content, bucket, key)
        
        # Verify API call
        mock_s3_client.put_object.assert_called_once_with(
            Bucket=bucket,
            Key=key,
            Body=content
        )
        
        # Verify response
        assert response["success"] is True
        data = response["data"]
        assert data.etag == '"abc123"'
        assert data.version_id == 'v1'
    
    def test_upload_file_with_metadata(self, adapter_real, mock_s3_client):
        """Test upload_file includes metadata when provided."""
        content = b"Test content"
        bucket = "test-bucket"
        key = "file.txt"
        metadata = {"author": "test-user", "version": "1.0"}
        
        mock_s3_client.put_object.return_value = {
            'ETag': '"def456"',
            'VersionId': 'v2'
        }
        
        adapter_real.upload_file(content, bucket, key, metadata)
        
        call_args = mock_s3_client.put_object.call_args[1]
        assert call_args['Metadata'] == metadata
    
    def test_upload_file_client_error_propagates(self, adapter_real, mock_s3_client):
        """Test upload_file propagates ClientError."""
        content = b"Test content"
        bucket = "test-bucket"
        key = "file.txt"
        
        error_response = {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}}
        mock_s3_client.put_object.side_effect = ClientError(error_response, 'PutObject')
        
        with pytest.raises(ClientError) as exc_info:
            adapter_real.upload_file(content, bucket, key)
        
        assert exc_info.value.response['Error']['Code'] == 'NoSuchBucket'
    
    def test_list_files_real_mode_success(self, adapter_real, mock_s3_client):
        """Test list_files with real client."""
        bucket = "test-bucket"
        prefix = "documents/"
        
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'documents/file1.pdf',
                    'Size': 1024,
                    'LastModified': datetime(2024, 1, 1, 0, 0, 0),
                    'ETag': '"etag1"'
                },
                {
                    'Key': 'documents/file2.pdf',
                    'Size': 2048,
                    'LastModified': datetime(2024, 1, 2, 0, 0, 0),
                    'ETag': '"etag2"'
                }
            ],
            'KeyCount': 2
        }
        
        response = adapter_real.list_files(bucket, prefix)
        
        # Verify API call
        mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket=bucket,
            Prefix=prefix
        )
        
        # Verify response
        assert response["success"] is True
        data = response["data"]
        assert data.total_count == 2
        assert len(data.objects) == 2
        assert data.objects[0].key == 'documents/file1.pdf'
        assert data.objects[0].size == 1024
        assert data.objects[1].key == 'documents/file2.pdf'
        assert data.total_size == 3072
    
    def test_list_files_empty_bucket(self, adapter_real, mock_s3_client):
        """Test list_files handles empty bucket."""
        bucket = "empty-bucket"
        
        mock_s3_client.list_objects_v2.return_value = {
            'KeyCount': 0,
            'IsTruncated': False
        }
        
        response = adapter_real.list_files(bucket)
        
        assert response["success"] is True
        data = response["data"]
        assert data.total_count == 0
        assert len(data.objects) == 0
    
    def test_list_files_client_error_propagates(self, adapter_real, mock_s3_client):
        """Test list_files propagates ClientError."""
        bucket = "test-bucket"
        
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_s3_client.list_objects_v2.side_effect = ClientError(error_response, 'ListObjectsV2')
        
        with pytest.raises(ClientError) as exc_info:
            adapter_real.list_files(bucket)
        
        assert exc_info.value.response['Error']['Code'] == 'AccessDenied'
    
    def test_delete_file_real_mode_success(self, adapter_real, mock_s3_client):
        """Test delete_file with real client."""
        bucket = "test-bucket"
        key = "file-to-delete.txt"
        
        mock_s3_client.delete_object.return_value = {
            'DeleteMarker': True,
            'VersionId': 'v3'
        }
        
        response = adapter_real.delete_file(bucket, key)
        
        # Verify API call
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket=bucket,
            Key=key
        )
        
        # Verify response
        assert response["success"] is True
        data = response["data"]
        assert data.deleted is True
        assert data.key == key
    
    def test_delete_file_client_error_propagates(self, adapter_real, mock_s3_client):
        """Test delete_file propagates ClientError."""
        bucket = "test-bucket"
        key = "file.txt"
        
        error_response = {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}}
        mock_s3_client.delete_object.side_effect = ClientError(error_response, 'DeleteObject')
        
        with pytest.raises(ClientError) as exc_info:
            adapter_real.delete_file(bucket, key)
        
        assert exc_info.value.response['Error']['Code'] == 'NoSuchKey'
