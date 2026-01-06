"""
S3 Adapter Response DTOs

Type-safe response models for S3 operations.
"""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class S3UploadResult(BaseModel):
    """Result of S3 file upload operation."""
    
    etag: str = Field(description="S3 object ETag")
    version_id: Optional[str] = Field(default=None, description="S3 object version ID if versioning enabled")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "etag": "\"5d41402abc4b2a76b9719d911017c592\"",
                "version_id": "v1"
            }
        }
    )


class S3ObjectInfo(BaseModel):
    """Information about an S3 object."""
    
    key: str = Field(description="S3 object key (path)")
    size: int = Field(description="Object size in bytes")
    last_modified: str = Field(description="Last modification timestamp (ISO format)")
    etag: str = Field(description="S3 object ETag")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "documents/example.pdf",
                "size": 1024000,
                "last_modified": "2024-01-15T10:30:00Z",
                "etag": "\"5d41402abc4b2a76b9719d911017c592\""
            }
        }
    )


class S3ListResult(BaseModel):
    """Result of S3 list objects operation."""
    
    objects: list[S3ObjectInfo] = Field(description="List of S3 objects")
    total_count: int = Field(description="Total number of objects")
    total_size: int = Field(description="Total size of all objects in bytes")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "objects": [
                    {
                        "key": "documents/example.pdf",
                        "size": 1024000,
                        "last_modified": "2024-01-15T10:30:00Z",
                        "etag": "\"abc123\""
                    }
                ],
                "total_count": 1,
                "total_size": 1024000
            }
        }
    )


class S3DeleteResult(BaseModel):
    """Result of S3 file deletion operation."""
    
    deleted: bool = Field(description="Whether the object was successfully deleted")
    key: str = Field(description="The key of the deleted object")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deleted": True,
                "key": "documents/example.pdf"
            }
        }
    )


class S3GetResult(BaseModel):
    """Result of S3 file download operation."""
    
    content: bytes = Field(description="File content as bytes")
    content_type: Optional[str] = Field(default=None, description="Content type of the object")
    metadata: Optional[dict[str, str]] = Field(default=None, description="Object metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": b"file content",
                "content_type": "application/json",
                "metadata": {"key": "value"}
            }
        }
    )
