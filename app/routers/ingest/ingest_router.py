"""Ingest router for document management endpoints."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Annotated, Optional
import json

from app.dtos.file import FileResponse, FileListResponse, FileDeleteResponse, FileMetadata
from app.services.ingestion import IngestionService
from app.adapters.s3 import S3Adapter
from app.adapters.bedrock import BedrockAdapter
from app.utils.config import Config

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
    response_model=FileListResponse,
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
    prefix: Optional[str] = None,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)] = None
) -> FileListResponse:
    """
    List all documents in the Knowledge Base.
    
    Args:
        prefix: Optional S3 prefix to filter files
        ingestion_service: Injected Ingestion service instance
        
    Returns:
        FileListResponse with list of files, total count, and total size
        
    Raises:
        HTTPException: 500 for server errors
    """
    response = ingestion_service.list_documents(prefix=prefix)
    return response


@router.post(
    "",
    response_model=FileResponse,
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
    file: Annotated[UploadFile, File(description="The file to upload")],
    metadata: Annotated[Optional[str], Form(description="Optional JSON metadata")] = None,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)] = None
) -> FileResponse:
    """
    Upload a document to the Knowledge Base.
    
    Args:
        file: The uploaded file
        metadata: Optional JSON string with custom metadata
        ingestion_service: Injected Ingestion service instance
        
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
    
    # Upload document
    response = ingestion_service.upload_document(
        file_content=file_content,
        filename=file.filename,
        metadata=metadata_dict
    )
    return response


@router.delete(
    "/{filename}",
    response_model=FileDeleteResponse,
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
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)] = None
) -> FileDeleteResponse:
    """
    Delete a document from the Knowledge Base.
    
    Args:
        filename: Name of the file to delete
        ingestion_service: Injected Ingestion service instance
        
    Returns:
        FileDeleteResponse with deletion status
        
    Raises:
        HTTPException: 404 if file not found, 500 for server errors
    """
    response = ingestion_service.delete_document(filename=filename)
    return response
