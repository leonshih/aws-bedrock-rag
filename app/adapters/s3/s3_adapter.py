"""
S3 Adapter

Low-level adapter for Amazon S3 file operations.
"""
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError

from app.utils.config import get_config
from app.dtos.common import create_success_response, SuccessResponse
from app.dtos.adapters.s3 import S3UploadResult, S3ObjectInfo, S3ListResult, S3DeleteResult


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
    ) -> SuccessResponse[S3UploadResult]:
        """
        Upload a file to S3.
        
        Args:
            file_content: File content as bytes
            bucket: S3 bucket name
            key: S3 object key (file path)
            metadata: Optional metadata dictionary
        
        Returns:
            Dict with success flag and S3UploadResult data containing ETag and version ID.
        
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
            
            result = S3UploadResult(
                etag=response.get('ETag', ''),
                version_id=response.get('VersionId')
            )
            return create_success_response(result)
        except ClientError as e:
            raise e
    
    def list_files(
        self,
        bucket: str,
        prefix: str = ""
    ) -> SuccessResponse[S3ListResult]:
        """
        List files in S3 bucket.
        
        Args:
            bucket: S3 bucket name
            prefix: Optional prefix to filter objects
        
        Returns:
            Dict with success flag and S3ListResult data containing list of objects with metadata.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        if self.mock_mode:
            return self._mock_list_files(bucket, prefix)
        
        try:
            params = {'Bucket': bucket}
            if prefix is not None:
                params['Prefix'] = prefix
            
            response = self.client.list_objects_v2(**params)
            
            objects = []
            total_size = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    obj_info = S3ObjectInfo(
                        key=obj['Key'],
                        size=obj['Size'],
                        last_modified=obj['LastModified'].isoformat(),
                        etag=obj.get('ETag', '')
                    )
                    objects.append(obj_info)
                    total_size += obj['Size']
            
            result = S3ListResult(
                objects=objects,
                total_count=len(objects),
                total_size=total_size
            )
            return create_success_response(result)
        except ClientError as e:
            raise e
    
    def delete_file(
        self,
        bucket: str,
        key: str
    ) -> SuccessResponse[S3DeleteResult]:
        """
        Delete a file from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (file path)
        
        Returns:
            Dict with success flag and S3DeleteResult data.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        if self.mock_mode:
            return self._mock_delete_file(bucket, key)
        
        try:
            self.client.delete_object(
                Bucket=bucket,
                Key=key
            )
            
            result = S3DeleteResult(
                deleted=True,
                key=key
            )
            return create_success_response(result)
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
    ) -> SuccessResponse[S3UploadResult]:
        """Mock implementation for local testing."""
        if bucket not in self._mock_storage:
            self._mock_storage[bucket] = {}
        
        self._mock_storage[bucket][key] = file_content
        
        result = S3UploadResult(
            etag='"mock-etag"',
            version_id=None
        )
        return create_success_response(result)
    
    def _mock_list_files(
        self,
        bucket: str,
        prefix: str = ""
    ) -> SuccessResponse[S3ListResult]:
        """Mock implementation for local testing."""
        if bucket not in self._mock_storage:
            result = S3ListResult(
                objects=[],
                total_count=0,
                total_size=0
            )
            return create_success_response(result)
        
        objects = []
        total_size = 0
        
        for key, content in self._mock_storage[bucket].items():
            if key.startswith(prefix):
                obj_info = S3ObjectInfo(
                    key=key,
                    size=len(content),
                    last_modified='2025-12-15T00:00:00',
                    etag='"mock-etag"'
                )
                objects.append(obj_info)
                total_size += len(content)
        
        result = S3ListResult(
            objects=objects,
            total_count=len(objects),
            total_size=total_size
        )
        return create_success_response(result)
    
    def _mock_delete_file(
        self,
        bucket: str,
        key: str
    ) -> SuccessResponse[S3DeleteResult]:
        """Mock implementation for local testing."""
        if bucket in self._mock_storage and key in self._mock_storage[bucket]:
            del self._mock_storage[bucket][key]
        
        result = S3DeleteResult(
            deleted=True,
            key=key
        )
        return create_success_response(result)
    
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
