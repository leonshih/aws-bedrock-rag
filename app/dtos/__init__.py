"""
Data Transfer Objects (DTOs)

Pydantic models for type-safe data validation and serialization.

Structure:
- common.py: Base response wrappers (SuccessResponse, ErrorResponse)
- routers/: Router layer DTOs
  - chat/: Chat/RAG related DTOs
  - ingest/: File management DTOs
- adapters/: Adapter layer DTOs
  - s3/: S3 adapter DTOs
  - bedrock/: Bedrock adapter DTOs
"""
from .common import (
    SuccessResponse,
    ErrorResponse,
    ErrorDetail,
    create_success_response,
    create_error_response,
)
from .routers.chat import ChatRequest, ChatResponse, Citation, MetadataFilter
from .routers.ingest import (
    FileMetadata,
    FileUploadRequest,
    FileResponse,
    FileListResponse,
    FileDeleteResponse,
)
from .adapters.s3 import (
    S3UploadResult,
    S3ObjectInfo,
    S3ListResult,
    S3DeleteResult,
)
from .adapters.bedrock import (
    BedrockRAGResult,
    BedrockRetrievalReference,
    BedrockIngestionJobResult,
)

__all__ = [
    # Chat DTOs
    "ChatRequest",
    "ChatResponse", 
    "Citation",
    "MetadataFilter",
    # File DTOs
    "FileMetadata",
    "FileUploadRequest",
    "FileResponse",
    "FileListResponse",
    "FileDeleteResponse",
    # Common response wrappers
    "SuccessResponse",
    "ErrorResponse",
    "ErrorDetail",
    "create_success_response",
    "create_error_response",
    # S3 adapter DTOs
    "S3UploadResult",
    "S3ObjectInfo",
    "S3ListResult",
    "S3DeleteResult",
    # Bedrock adapter DTOs
    "BedrockRAGResult",
    "BedrockRetrievalReference",
    "BedrockIngestionJobResult",
]
