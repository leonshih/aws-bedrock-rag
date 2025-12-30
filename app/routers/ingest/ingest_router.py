"""Ingest router for document management endpoints."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from typing import Annotated, Optional
import json

from app.dtos.routers.ingest import FileResponse, FileListResponse, FileDeleteResponse, FileMetadata
from app.services.ingestion import IngestionService
from app.adapters.s3 import S3Adapter
from app.adapters.bedrock import BedrockAdapter
from app.utils.config import Config
from app.middleware.tenant_middleware import get_tenant_context

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
    
    **Features:**
    - Lists all files in the S3 bucket
    - Includes custom metadata for each file
    - Returns total count and total size
    - Supports optional prefix filtering
    
    **Example Response:**
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
    }
)
async def list_files(
    request: Request,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)] = None
) -> dict:
    """
    List all documents for the authenticated tenant.
    
    Args:
        request: FastAPI request object (to access middleware state)
        ingestion_service: Injected Ingestion service instance
        
    Returns:
        Dict with success flag and FileListResponse data
        
    Raises:
        HTTPException: 500 for server errors
    """
    # Extract tenant_id from middleware (validated by TenantMiddleware)
    tenant_context = get_tenant_context(request)
    
    # Pass tenant_id to service for path isolation
    response = ingestion_service.list_documents(tenant_id=tenant_context.tenant_id)
    return response


@router.post(
    "",
    summary="Upload a document",
    description="""
    Upload a new document to the Knowledge Base with optional metadata.
    
    **Features:**
    - Accepts any file type (PDF, TXT, DOCX, etc.)
    - Optional custom metadata (JSON format)
    - Automatically triggers Knowledge Base sync
    - Generates S3 key with documents/ prefix
    
    **Metadata Format:**
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
        200: {"description": "File uploaded successfully"},
        400: {"description": "Invalid file or metadata"},
        500: {"description": "Failed to upload file"}
    }
)
async def upload_file(
    request: Request,
    file: Annotated[UploadFile, File(description="The file to upload")],
    metadata: Annotated[Optional[str], Form(description="Optional JSON metadata")] = None,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)] = None
) -> dict:
    """
    Upload a document to the Knowledge Base.
    
    Args:
        request: FastAPI request object (to access middleware state)
        file: The uploaded file
        metadata: Optional JSON string with custom metadata
        ingestion_service: Injected Ingestion service instance
        
    Returns:
        Dict with success flag and FileResponse data
        
    Raises:
        HTTPException: 400 for invalid input, 500 for server errors
    """
    # Extract tenant_id from middleware (validated by TenantMiddleware)
    tenant_context = get_tenant_context(request)
    
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
    
    **Features:**
    - Deletes the file from S3
    - Removes associated metadata
    - Automatically triggers Knowledge Base sync
    
    **Example Response:**
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
    }
)
async def delete_file(
    filename: str,
    request: Request,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)] = None
) -> dict:
    """
    Delete a document from the Knowledge Base.
    
    Args:
        filename: Name of the file to delete
        request: FastAPI request object (to access middleware state)
        ingestion_service: Injected Ingestion service instance
        
    Returns:
        Dict with success flag and FileDeleteResponse data
        
    Raises:
        HTTPException: 404 if file not found, 500 for server errors
    """
    # Extract tenant_id from middleware (validated by TenantMiddleware)
    tenant_context = get_tenant_context(request)
    
    # Delete document with tenant_id for path isolation
    response = ingestion_service.delete_document(
        filename=filename,
        tenant_id=tenant_context.tenant_id
    )
    return response
