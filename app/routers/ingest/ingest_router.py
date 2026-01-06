"""Ingest router for document management endpoints."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Annotated, Optional
import json

from app.dtos.routers.ingest import FileResponse, FileListResponse, FileDeleteResponse, FileMetadata
from app.dtos.common import TenantContext
from app.services.ingestion import IngestionService
from app.adapters.s3 import S3Adapter
from app.adapters.bedrock import BedrockAdapter
from app.utils.config import Config
from app.dependencies import get_tenant_context

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={
        404: {"description": "File not found"},
        500: {"description": "Internal server error"}
    }
)


def get_ingestion_service() -> IngestionService:
    """Dependency injection for Ingestion service."""
    config = Config()
    return IngestionService(config=config)


@router.get(
    "",
    summary="List all documents",
    description="""
    Retrieve a list of all documents in the Knowledge Base with their metadata.
    
    **🔐 Multi-Tenant:** This endpoint requires `X-Tenant-ID` header.
    Only documents belonging to your tenant will be listed.
    
    **Required Headers:**
    - `X-Tenant-ID`: Your tenant UUID (e.g., "550e8400-e29b-41d4-a716-446655440000")
    
    **Features:**
    - Lists all files for your tenant
    - Includes custom metadata for each file
    - Returns total count and total size
    - Automatic tenant-based path isolation
    
    **Example Response:
    ```json
    {
        "files": [
            {
                "filename": "document.pdf",
                "size": 1024000,
                "last_modified": "2024-01-15T10:30:00Z",
                "s3_key": "documents/document.pdf",
                "metadata": {"category": "research", "year": "2024"}
            }
        ],
        "total_count": 1,
        "total_size": 1024000
    }
    ```
    """,
    responses={
        200: {"description": "Successful response with file list"},
        500: {"description": "Failed to retrieve files from S3"}
    },
    status_code=200
)
async def list_files(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)]
) -> FileListResponse:
    """
    List all documents for the authenticated tenant.
    
    Args:
        tenant_context: Tenant context from dependency injection (validated)
        ingestion_service: Injected Ingestion service instance
        
    Returns:
        FileListResponse with file list and statistics
        
    Raises:
        HTTPException: 500 for server errors
    """
    # Pass tenant_id to service for path isolation
    return ingestion_service.list_documents(tenant_id=tenant_context.tenant_id)


@router.post(
    "",
    summary="Upload a document",
    description="""
    Upload a new document to the Knowledge Base with optional metadata.
    
    **🔐 Multi-Tenant:** This endpoint requires `X-Tenant-ID` header.
    Files are automatically stored in tenant-isolated S3 paths.
    
    **Required Headers:**
    - `X-Tenant-ID`: Your tenant UUID (e.g., "550e8400-e29b-41d4-a716-446655440000")
    
    **Features:**
    - Accepts any file type (PDF, TXT, DOCX, etc.)
    - Optional custom metadata (JSON format)
    - Automatically triggers Knowledge Base sync
    - Tenant-isolated storage (documents/{tenant_id}/)
    
    **Metadata Format:
    The metadata should be a JSON string containing key-value pairs:
    ```json
    {
        "category": "research",
        "year": "2024",
        "author": "John Doe",
        "tags": ["AI", "ML"]
    }
    ```
    
    **Example Response:**
    ```json
    {
        "filename": "document.pdf",
        "size": 1024000,
        "last_modified": "2024-01-15T10:30:00Z",
        "s3_key": "documents/document.pdf",
        "metadata": {"category": "research", "year": "2024"}
    }
    ```
    """,
    responses={
        201: {"description": "File uploaded successfully"},
        400: {"description": "Invalid file or metadata"},
        500: {"description": "Failed to upload file"}
    },
    status_code=201
)
async def upload_file(
    file: Annotated[UploadFile, File(description="The file to upload")],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)],
    metadata: Annotated[Optional[str], Form(description="Optional JSON metadata")] = None
) -> FileResponse:
    """
    Upload a document to the Knowledge Base.
    
    Args:
        file: The uploaded file
        tenant_context: Tenant context from dependency injection (validated)
        ingestion_service: Injected Ingestion service instance
        metadata: Optional JSON string with custom metadata
        
    Returns:
        FileResponse with file details
        
    Raises:
        HTTPException: 400 for invalid input, 500 for server errors
    """
    # Read file content
    file_content = await file.read()
    
    # Parse metadata if provided
    metadata_dict = None
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
            if not isinstance(metadata_dict, dict):
                raise ValueError("Metadata must be a JSON object")
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON metadata: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Upload document with tenant_id for path isolation
    response = ingestion_service.upload_document(
        file_content=file_content,
        filename=file.filename,
        tenant_id=tenant_context.tenant_id,
        metadata=metadata_dict
    )
    return response


@router.delete(
    "/{filename}",
    summary="Delete a document",
    description="""
    Delete a document from the Knowledge Base.
    
    **🔐 Multi-Tenant:** This endpoint requires `X-Tenant-ID` header.
    Only files belonging to your tenant can be deleted.
    
    **Required Headers:**
    - `X-Tenant-ID`: Your tenant UUID (e.g., "550e8400-e29b-41d4-a716-446655440000")
    
    **Features:**
    - Deletes the file from S3
    - Removes associated metadata
    - Tenant-isolated deletion (only your tenant's files)
    - Automatically triggers Knowledge Base sync
    
    **Example Response:
    ```json
    {
        "filename": "document.pdf",
        "status": "deleted",
        "message": "File deleted successfully"
    }
    ```
    """,
    responses={
        200: {"description": "File deleted successfully"},
        404: {"description": "File not found"},
        500: {"description": "Failed to delete file"}
    },
    status_code=200
)
async def delete_file(
    filename: str,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)]
) -> FileDeleteResponse:
    """
    Delete a document from the Knowledge Base.
    
    Args:
        filename: Name of the file to delete
        tenant_context: Tenant context from dependency injection (validated)
        ingestion_service: Injected Ingestion service instance
        
    Returns:
        FileDeleteResponse with deletion details
        
    Raises:
        HTTPException: 404 if file not found, 500 for server errors
    """
    # Delete document with tenant_id for path isolation
    response = ingestion_service.delete_document(
        filename=filename,
        tenant_id=tenant_context.tenant_id
    )
    return response
