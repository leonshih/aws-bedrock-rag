"""
File DTOs for document management

Defines request/response models for file upload/list/delete endpoints.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class FileMetadata(BaseModel):
    """Custom metadata attributes for uploaded documents."""
    
    tenant_id: UUID = Field(
        ...,
        description="Tenant identifier (UUID v4) - Required for data isolation",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom key-value metadata (e.g., author, year, category, tags)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "attributes": {
                    "author": "Dr. Smith",
                    "year": 2023,
                    "category": "medical",
                    "tags": ["cardiology", "research"]
                }
            }
        }


class FileUploadRequest(BaseModel):
    """Request model for file upload (used with multipart/form-data)."""
    
    tenant_id: UUID = Field(
        ...,
        description="Tenant identifier (UUID v4) - Required for data isolation",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    metadata: Optional[FileMetadata] = Field(
        default=None,
        description="Custom metadata to attach to the document"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {
                    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                    "attributes": {
                        "author": "Dr. Smith",
                        "year": 2023,
                        "department": "Cardiology"
                    }
                }
            }
        }


class FileResponse(BaseModel):
    """Response model for individual file information."""
    
    filename: str = Field(..., description="Name of the file")
    size: int = Field(..., description="File size in bytes")
    last_modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    s3_key: Optional[str] = Field(None, description="S3 object key")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom metadata attributes from .metadata.json"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "medical_guideline_2023.pdf",
                "size": 2048576,
                "last_modified": "2023-12-15T10:30:00Z",
                "s3_key": "documents/medical_guideline_2023.pdf",
                "metadata": {
                    "author": "Dr. Smith",
                    "year": 2023,
                    "category": "guidelines"
                }
            }
        }


class FileListResponse(BaseModel):
    """Response model for listing files."""
    
    files: List[FileResponse] = Field(
        default_factory=list,
        description="List of files in the knowledge base"
    )
    total_count: int = Field(..., description="Total number of files")
    total_size: int = Field(..., description="Total size in bytes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "files": [
                    {
                        "filename": "doc1.pdf",
                        "size": 1024000,
                        "s3_key": "documents/doc1.pdf"
                    }
                ],
                "total_count": 1,
                "total_size": 1024000
            }
        }


class FileDeleteResponse(BaseModel):
    """Response model for file deletion."""
    
    filename: str = Field(..., description="Name of the deleted file")
    status: str = Field(..., description="Deletion status")
    message: Optional[str] = Field(None, description="Additional information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "old_document.pdf",
                "status": "deleted",
                "message": "File and metadata removed, sync job triggered"
            }
        }
