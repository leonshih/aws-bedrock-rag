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
    
    def __init__(self):
        """Initialize S3 adapter with AWS S3 client."""
        config = get_config()
        self.region = config.AWS_REGION
        self.client = boto3.client('s3', region_name=self.region)
    
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
