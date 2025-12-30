"""
Unit tests for S3 Adapter
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from botocore.exceptions import ClientError
from app.adapters.s3 import S3Adapter


class TestS3Adapter:
    """Test cases for S3Adapter with mocked boto3 client."""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client."""
        return Mock()
    
    @pytest.fixture
    def adapter(self, mock_s3_client):
        """Create an S3 adapter instance with mocked boto3 client."""
        with patch('boto3.client', return_value=mock_s3_client):
            return S3Adapter()
    
    def test_initialization(self, adapter, mock_s3_client):
        """Test adapter initializes correctly with boto3 client."""
        assert adapter.client is not None
        assert adapter.client == mock_s3_client
        assert adapter.region is not None
    
    def test_initialization_creates_s3_client(self):
        """Test adapter creates S3 client on init."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_boto.return_value = mock_client
            
            adapter = S3Adapter()
            
            mock_boto.assert_called_once_with(
                's3',
                region_name=adapter.region
            )
            assert adapter.client == mock_client
    
    def test_upload_file_success(self, adapter, mock_s3_client):
        """Test file upload with successful AWS response."""
        content = b"Test file content"
        bucket = "test-bucket"
        key = "test-file.txt"
        
        # Mock AWS response
        mock_s3_client.put_object.return_value = {
            'ETag': '"abc123"',
            'VersionId': 'v1'
        }
        
        response = adapter.upload_file(content, bucket, key)
        
        # Verify API call
        mock_s3_client.put_object.assert_called_once_with(
            Bucket=bucket,
            Key=key,
            Body=content
        )
        
        # Verify response structure
        assert response["success"] is True
        data = response["data"]
        assert data.etag == '"abc123"'
        assert data.version_id == 'v1'
    
    def test_upload_file_with_metadata(self, adapter, mock_s3_client):
        """Test file upload with metadata."""
        content = b"Test content"
        bucket = "test-bucket"
        key = "file.txt"
        metadata = {"author": "test", "version": "1.0"}
        
        mock_s3_client.put_object.return_value = {
            'ETag': '"def456"',
            'VersionId': None
        }
        
        response = adapter.upload_file(content, bucket, key, metadata)
        
        # Verify metadata was passed
        mock_s3_client.put_object.assert_called_once_with(
            Bucket=bucket,
            Key=key,
            Body=content,
            Metadata=metadata
        )
        
        assert response["success"] is True
        assert response["data"].etag == '"def456"'
        assert response["data"].version_id is None
    
    def test_upload_file_client_error_propagates(self, adapter, mock_s3_client):
        """Test upload_file propagates ClientError."""
        content = b"Test"
        bucket = "test-bucket"
        key = "file.txt"
        
        # Mock ClientError
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_s3_client.put_object.side_effect = ClientError(error_response, 'PutObject')
        
        with pytest.raises(ClientError) as exc_info:
            adapter.upload_file(content, bucket, key)
        
        assert exc_info.value.response['Error']['Code'] == 'AccessDenied'
    
    def test_list_files_success(self, adapter, mock_s3_client):
        """Test list_files with successful AWS response."""
        bucket = "test-bucket"
        prefix = "documents/"
        
        # Mock AWS response
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'documents/file1.txt',
                    'Size': 1024,
                    'LastModified': datetime(2025, 12, 30, 10, 0, 0),
                    'ETag': '"etag1"'
                },
                {
                    'Key': 'documents/file2.pdf',
                    'Size': 2048,
                    'LastModified': datetime(2025, 12, 30, 11, 0, 0),
                    'ETag': '"etag2"'
                }
            ]
        }
        
        response = adapter.list_files(bucket, prefix)
        
        # Verify API call
        mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket=bucket,
            Prefix=prefix
        )
        
        # Verify response
        assert response["success"] is True
        data = response["data"]
        assert data.total_count == 2
        assert data.total_size == 3072  # 1024 + 2048
        assert len(data.objects) == 2
        assert data.objects[0].key == 'documents/file1.txt'
        assert data.objects[0].size == 1024
        assert data.objects[1].key == 'documents/file2.pdf'
    
    def test_list_files_empty_bucket(self, adapter, mock_s3_client):
        """Test list_files with empty bucket."""
        bucket = "empty-bucket"
        
        # Mock empty response
        mock_s3_client.list_objects_v2.return_value = {}
        
        response = adapter.list_files(bucket)
        
        assert response["success"] is True
        data = response["data"]
        assert data.total_count == 0
        assert data.total_size == 0
        assert len(data.objects) == 0
    
    def test_list_files_with_prefix(self, adapter, mock_s3_client):
        """Test list_files filters by prefix."""
        bucket = "test-bucket"
        prefix = "specific-folder/"
        
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'specific-folder/file.txt',
                    'Size': 512,
                    'LastModified': datetime(2025, 12, 30, 12, 0, 0),
                    'ETag': '"etag"'
                }
            ]
        }
        
        response = adapter.list_files(bucket, prefix)
        
        # Verify prefix was passed
        call_args = mock_s3_client.list_objects_v2.call_args[1]
        assert call_args['Prefix'] == prefix
        
        assert response["success"] is True
        assert len(response["data"].objects) == 1
    
    def test_list_files_client_error_propagates(self, adapter, mock_s3_client):
        """Test list_files propagates ClientError."""
        bucket = "test-bucket"
        
        error_response = {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}}
        mock_s3_client.list_objects_v2.side_effect = ClientError(error_response, 'ListObjectsV2')
        
        with pytest.raises(ClientError) as exc_info:
            adapter.list_files(bucket)
        
        assert exc_info.value.response['Error']['Code'] == 'NoSuchBucket'
    
    def test_delete_file_success(self, adapter, mock_s3_client):
        """Test delete_file with successful AWS response."""
        bucket = "test-bucket"
        key = "file-to-delete.txt"
        
        # Mock successful deletion (delete_object doesn't return much)
        mock_s3_client.delete_object.return_value = {}
        
        response = adapter.delete_file(bucket, key)
        
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
    
    def test_delete_file_client_error_propagates(self, adapter, mock_s3_client):
        """Test delete_file propagates ClientError."""
        bucket = "test-bucket"
        key = "file.txt"
        
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        mock_s3_client.delete_object.side_effect = ClientError(error_response, 'DeleteObject')
        
        with pytest.raises(ClientError) as exc_info:
            adapter.delete_file(bucket, key)
        
        assert exc_info.value.response['Error']['Code'] == 'AccessDenied'
    
    def test_multiple_operations_use_same_client(self, adapter, mock_s3_client):
        """Test multiple operations reuse the same boto3 client instance."""
        bucket = "test-bucket"
        
        # Setup mocks
        mock_s3_client.put_object.return_value = {'ETag': '"etag"'}
        mock_s3_client.list_objects_v2.return_value = {'Contents': []}
        mock_s3_client.delete_object.return_value = {}
        
        # Perform multiple operations
        adapter.upload_file(b"content", bucket, "file1.txt")
        adapter.list_files(bucket)
        adapter.delete_file(bucket, "file1.txt")
        
        # Verify same client instance used
        assert adapter.client == mock_s3_client
        assert mock_s3_client.put_object.call_count == 1
        assert mock_s3_client.list_objects_v2.call_count == 1
        assert mock_s3_client.delete_object.call_count == 1
