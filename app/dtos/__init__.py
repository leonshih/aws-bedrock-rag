"""
Data Transfer Objects (DTOs)

Pydantic models for type-safe data validation and serialization.

Structure:
- common.py: Common models (TenantContext, ErrorDetail, Exception classes)
- routers/: Router layer DTOs
  - chat/: Chat/RAG related DTOs
  - ingest/: File management DTOs
- adapters/: Adapter layer DTOs
  - s3/: S3 adapter DTOs
  - bedrock/: Bedrock adapter DTOs
"""
from .common import (
    TenantContext,
    TenantMissingError,
    TenantValidationError,
    ErrorDetail,
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
    # Common models
    "TenantContext",
    "TenantMissingError",
    "TenantValidationError",
    "ErrorDetail",
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
