"""
S3 Adapter

Low-level adapter for Amazon S3 file operations.
"""
from typing import Dict, Any, List, Optional, BinaryIO
import boto3
from botocore.exceptions import ClientError

from app.utils.config import get_config


class S3Adapter:
    """Adapter for Amazon S3 operations."""
    
    def __init__(self, mock_mode: Optional[bool] = None):
        """
        Initialize S3 adapter.
        
        Args:
            mock_mode: Override config mock mode. If None, uses config value.
        """
        config = get_config()
        self.mock_mode = mock_mode if mock_mode is not None else config.is_mock_enabled()
        self.region = config.AWS_REGION
        
        if not self.mock_mode:
            self.client = boto3.client('s3', region_name=self.region)
        else:
            self.client = None
            # Mock storage: {bucket: {key: content}}
            self._mock_storage: Dict[str, Dict[str, bytes]] = {}
    
    def upload_file(
        self,
        file_content: bytes,
        bucket: str,
        key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to S3.
        
        Args:
            file_content: File content as bytes
            bucket: S3 bucket name
            key: S3 object key (file path)
            metadata: Optional metadata dictionary
        
        Returns:
            Dict containing upload response.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        if self.mock_mode:
            return self._mock_upload_file(file_content, bucket, key, metadata)
        
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            response = self.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_content,
                **extra_args
            )
            return response
        except ClientError as e:
            raise e
    
    def list_files(
        self,
        bucket: str,
        prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """
        List files in S3 bucket.
        
        Args:
            bucket: S3 bucket name
            prefix: Optional prefix to filter objects
        
        Returns:
            List of objects with metadata.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        if self.mock_mode:
            return self._mock_list_files(bucket, prefix)
        
        try:
            response = self.client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            return [
                {
                    'Key': obj['Key'],
                    'Size': obj['Size'],
                    'LastModified': obj['LastModified'].isoformat(),
                    'ETag': obj.get('ETag', '')
                }
                for obj in response['Contents']
            ]
        except ClientError as e:
            raise e
    
    def delete_file(
        self,
        bucket: str,
        key: str
    ) -> Dict[str, Any]:
        """
        Delete a file from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (file path)
        
        Returns:
            Dict containing delete response.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        if self.mock_mode:
            return self._mock_delete_file(bucket, key)
        
        try:
            response = self.client.delete_object(
                Bucket=bucket,
                Key=key
            )
            return response
        except ClientError as e:
            raise e
    
    def get_file(
        self,
        bucket: str,
        key: str
    ) -> bytes:
        """
        Download a file from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (file path)
        
        Returns:
            File content as bytes.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        if self.mock_mode:
            return self._mock_get_file(bucket, key)
        
        try:
            response = self.client.get_object(
                Bucket=bucket,
                Key=key
            )
            return response['Body'].read()
        except ClientError as e:
            raise e
    
    # Mock implementations
    
    def _mock_upload_file(
        self,
        file_content: bytes,
        bucket: str,
        key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Mock implementation for local testing."""
        if bucket not in self._mock_storage:
            self._mock_storage[bucket] = {}
        
        self._mock_storage[bucket][key] = file_content
        
        return {
            'ResponseMetadata': {
                'RequestId': 'mock-request-id',
                'HTTPStatusCode': 200
            },
            'ETag': '"mock-etag"'
        }
    
    def _mock_list_files(
        self,
        bucket: str,
        prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """Mock implementation for local testing."""
        if bucket not in self._mock_storage:
            return []
        
        files = []
        for key, content in self._mock_storage[bucket].items():
            if key.startswith(prefix):
                files.append({
                    'Key': key,
                    'Size': len(content),
                    'LastModified': '2025-12-15T00:00:00',
                    'ETag': '"mock-etag"'
                })
        
        return files
    
    def _mock_delete_file(
        self,
        bucket: str,
        key: str
    ) -> Dict[str, Any]:
        """Mock implementation for local testing."""
        if bucket in self._mock_storage and key in self._mock_storage[bucket]:
            del self._mock_storage[bucket][key]
        
        return {
            'ResponseMetadata': {
                'RequestId': 'mock-request-id',
                'HTTPStatusCode': 204
            }
        }
    
    def _mock_get_file(
        self,
        bucket: str,
        key: str
    ) -> bytes:
        """Mock implementation for local testing."""
        if bucket not in self._mock_storage:
            raise KeyError(f"Bucket '{bucket}' not found")
        
        if key not in self._mock_storage[bucket]:
            raise KeyError(f"Key '{key}' not found in bucket '{bucket}'")
        
        return self._mock_storage[bucket][key]
