# Architecture Documentation

## 🏗️ System Architecture

This project implements a **Retrieval-Augmented Generation (RAG)** system using AWS Bedrock Knowledge Bases with a FastAPI backend.

---

## 📐 Architectural Layers

```
┌─────────────────────────────────────────────────┐
│           API Layer (FastAPI Routers)           │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│         Service Layer (Business Logic)          │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│       Adapter Layer (AWS Integrations)          │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│            External Services (AWS)              │
└─────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow

### Chat/Query Request Flow

```
1. Client → POST /chat
   └── Body: {query, metadata_filters, max_results}

2. Router Layer (chat_router.py)
   ├── Validates request schema
   ├── Extracts request data
   └── Injects RAGService dependency

3. Service Layer (rag_service.py)
   ├── Builds retrieval configuration
   ├── Applies metadata filters
   └── Calls BedrockAdapter.retrieve_and_generate()

4. Adapter Layer (bedrock_adapter.py)
   ├── Constructs Bedrock API request
   ├── Calls bedrock-agent-runtime client
   └── Returns BedrockRAGResult

5. Response Flow
   ├── Service returns ChatResponse (Pydantic model)
   ├── Router adds HTTP 200 status code
   └── Client receives ChatResponse JSON directly
```

### Document Ingestion Flow

```
1. Client → POST /files
   └── Form Data: {file, metadata (JSON)}

2. Router Layer (ingest_router.py)
   ├── Parses multipart/form-data
   ├── Validates metadata JSON
   └── Injects IngestionService dependency

3. Service Layer (ingestion_service.py)
   ├── Generates S3 key: documents/{filename}
   ├── Creates .metadata.json sidecar file
   ├── Uploads both files to S3
   └── Triggers Knowledge Base sync

4. S3 Adapter (s3_adapter.py)
   ├── Uploads file with metadata
   ├── Sets metadata attributes
   └── Returns S3UploadResult

5. Bedrock Adapter (bedrock_adapter.py)
   ├── Starts ingestion job
   └── Returns job status

6. Response Flow
   ├── Service returns FileUploadResponse (Pydantic model)
   ├── Router adds HTTP 201 status code (resource created)
   └── Client receives FileUploadResponse JSON directly
```

---

## 🗂️ Data Models (DTOs)

### Layer-Based DTO Organization

DTOs are organized by **architectural layer**, not by domain:

```
app/dtos/
├── common.py              # Shared DTOs (Tenant context, Error models)
│   ├── TenantContext      # Multi-tenant context model (UUID validation)
│   ├── TenantMissingError
│   ├── TenantValidationError
│   └── ErrorDetail        # Error response schema
│
├── routers/               # API request/response models
│   ├── chat.py           # ChatRequest, ChatResponse, Citation
│   └── ingest.py         # FileUploadRequest, FileResponse, FileListResponse
│
└── adapters/              # External service DTOs
    ├── s3.py             # S3UploadResult, S3ObjectInfo, S3ListResult
    └── bedrock.py        # BedrockRAGResult, BedrockRetrievalReference
```

**Design Principles:**

- **Immutable**: Pydantic models with validation
- **Type-Safe**: Full type hints for IDE support
- **Layer-Specific**: DTOs don't cross layer boundaries
- **Self-Documenting**: JSON schema examples in `Config`

---

## 🏢 Multi-Tenant Architecture (Phase 4)

### Tenant Context Model

```python
from app.dtos.common import TenantContext

# Tenant identifier with UUID validation
context = TenantContext(tenant_id="550e8400-e29b-41d4-a716-446655440000")
```

**Validation Rules:**

- Must be valid UUID v4 format
- Accepts UUID with or without hyphens
- Automatically normalized to standard format
- Cannot be None or empty

**Exception Handling:**

- `TenantMissingError`: Raised when `X-Tenant-ID` header is missing
- `TenantValidationError`: Raised when UUID format is invalid

### Tenant Isolation Strategy

**Current Status:** ✅ Model, Dependency Injection, S3 Isolation, RAG Filter implemented

**Implementation Layers:**

1. **Dependency Layer** (✅): Extract and validate `X-Tenant-ID` from HTTP headers via FastAPI dependencies
2. **Storage Layer** (✅): Enforce S3 path prefix `documents/{tenant_id}/`
3. **Retrieval Layer** (✅): Auto-inject tenant filter in Bedrock Knowledge Base queries
4. **Validation Layer** (✅): UUID format enforcement via Pydantic and FastAPI

**Implemented Flow:**

```
Client Request → Router (Depends(get_tenant_context)) → Service (receive tenant_id as parameter) → Adapter (apply S3 prefix / tenant filter)
```

**Tenant Filter Details:**

```python
# Automatic tenant filter injection in RAGService
filter = {
    "equals": {
        "key": "tenant_id",
        "value": str(tenant_id)
    }
}
# Combined with user filters using AND logic
```

---

## 🛠️ Technology Stack

| Layer          | Technology              | Purpose                           |
| -------------- | ----------------------- | --------------------------------- |
| **API**        | FastAPI 0.104+          | Async HTTP framework with OpenAPI |
| **Validation** | Pydantic 2.4+           | Data validation and serialization |
| **AWS SDK**    | Boto3 1.28+             | AWS service clients               |
| **Compute**    | ECS Fargate             | Serverless container runtime      |
| **LLM**        | Claude 3.5 Sonnet       | Text generation                   |
| **Vector DB**  | OpenSearch Serverless   | Semantic search                   |
| **Storage**    | S3                      | Document storage                  |
| **RAG Engine** | Bedrock Knowledge Bases | Managed RAG pipeline              |
| **Testing**    | Pytest 7.4+             | Unit and integration tests        |
| **Container**  | Docker                  | Multi-stage builds                |

---

## 📦 Dependency Injection

### Service Layer Dependencies

```python
# Router Layer
def get_rag_service() -> RAGService:
    """Dependency injection for RAG service."""
    return RAGService()

@router.post("/chat")
async def chat(
    request: ChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
):
    return rag_service.query(request)
```

### Configuration Management

```python
# Service Layer
class RAGService:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()  # Default config if not provided
        self.bedrock_adapter = BedrockAdapter()
```

**Design Principles:**

- **Constructor Injection:** Services receive config in `__init__`
- **Default Fallback:** Use `Config()` if not provided
- **No Adapter Injection:** Services instantiate adapters internally
- **Testability:** Easy to mock dependencies

---

### Error Handling Flow

```
Exception Raised
    │
    ├── Pydantic ValidationError → 422 Unprocessable Entity
    ├── HTTPException → Pass through status code
    ├── FileNotFoundError → 404 Not Found
    ├── ValueError → 400 Bad Request
    ├── AWS ClientError → Map to appropriate status
    │   ├── AccessDenied → 403 Forbidden
    │   ├── ThrottlingException → 429 Too Many Requests
    │   ├── ResourceNotFoundException → 404 Not Found
    │   └── ValidationException → 400 Bad Request
    └── Generic Exception → 500 Internal Server Error

All errors logged with full stack trace via logger.exception()
```

---

## 🧪 Testing Strategy

### Test Pyramid

```
         ╱╲
        ╱  ╲      E2E Tests (Planned)
       ╱────╲     Full workflow validation
      ╱      ╲
     ╱────────╲   Integration Tests (32 tests)
    ╱          ╲  Component interactions
   ╱────────────╲
  ╱              ╲ Unit Tests (113 tests)
 ╱────────────────╲ Isolated component tests
```

### Test Organization

```
app/
├── adapters/
│   ├── bedrock/
│   │   ├── bedrock_adapter.py
│   │   └── test_bedrock_adapter.py     # Co-located tests
│   ...
│
├── services/
│   ├── rag/
│   │   ├── rag_service.py
│   │   └── test_rag_service.py
│   ...
│
└── tests/
    └── integration/                     # Cross-component tests
        ├── test_api_integration.py
        └── test_service_integration.py
```

**Testing Principles:**

- **Unit Tests:** Mock all external dependencies (AWS, file system)
- **Integration Tests:** Real service instantiation, no mocks
- **High Coverage:** Aim for >90% coverage on core modules

---

## 🔧 Configuration Management

### Environment Variables

Loaded from `.env` via [`app/utils/config.py`](app/utils/config.py):

```python
class Config:
    # AWS Configuration
    AWS_REGION: str
    BEDROCK_KB_ID: str
    BEDROCK_DATA_SOURCE_ID: str
    BEDROCK_MODEL_ID: str
    S3_BUCKET_NAME: str

    # Application Configuration
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
```

---

## 📊 Data Flow Diagrams

### Metadata Handling

```
File Upload
    │
    ├─→ Generate .metadata.json sidecar
    │   └─→ Format: {"metadataAttributes": {custom_attrs}}
    │
    ├─→ Upload file.pdf to S3
    │
    ├─→ Upload file.pdf.metadata.json to S3
    │
    └─→ Trigger Bedrock ingestion job
        └─→ Knowledge Base indexes metadata

File List
    │
    ├─→ S3 list objects
    │   ├─→ Filter out .metadata.json files
    │   └─→ Match metadata files with source files
    │
    ├─→ Load metadata from .metadata.json
    │
    └─→ Return FileResponse with metadata attributes

Query
    │
    ├─→ Convert metadata filters to Bedrock format
    │
    ├─→ Bedrock Knowledge Base search
    │   └─→ OpenSearch filters by metadata
    │
    └─→ Return results with citations
```

---

## 🔒 Security Considerations

### Input Validation

- ✅ **Schema Validation:** Pydantic models with field constraints (min/max length, format)
- ✅ **Type Safety:** Full type hints prevent type-related bugs
- ⏳ **File Type Validation:** MIME type checking for uploads (PDF, TXT, DOCX, etc.)
- ⏳ **File Size Limits:** Max file size enforcement in request body

### Multi-Tenant Isolation

- ✅ **Tenant Context Model:** UUID v4 validated data model ([`TenantContext`](app/dtos/common.py))
- ✅ **UUID Validation:** Pydantic-based format validation (accepts with/without hyphens)
- ✅ **Exception Types:** `TenantMissingError`, `TenantValidationError`
- ✅ **Tenant ID Validation:** UUID v4 format validation for `X-Tenant-ID` header via dependency injection
- ✅ **Mandatory Tenant Header:** FastAPI automatically rejects requests without valid tenant ID (HTTP 422)
- ✅ **Dependency Injection:** `get_tenant_context` dependency extracts and validates tenant from header
- ✅ **Path Isolation:** Enforce `documents/{tenant_id}/` prefix in S3 operations
- ✅ **Immutable Filters:** Auto-inject tenant filter into all RAG queries at service layer
- ✅ **Swagger UI Integration:** X-Tenant-ID parameter automatically displayed in API docs
- ⏳ **Ownership Validation:** Verify tenant owns file before delete/download operations

---

## 📈 Scalability

### Current Capacity

- **Concurrent Requests:** Limited by FastAPI worker count
- **File Size:** No explicit limit (S3 supports up to 5TB)
- **Query Latency:** ~2-5s (Bedrock retrieval + generation)

### Future Optimizations

- **Async Processing:** Background jobs for large file ingestion
- **Caching:** Redis for frequently accessed metadata
- **CDN:** CloudFront for static file delivery
- **Auto-Scaling:** ECS Fargate with target tracking policies

---

## 🔗 External Dependencies

### AWS Services

- **Bedrock Knowledge Base:** Document indexing and retrieval
- **Bedrock Agent Runtime:** RAG query execution
- **S3:** Document storage
- **OpenSearch Serverless:** Vector database (managed by Knowledge Base)
- **ECS Fargate:** Container runtime (deployment target)
- **CloudWatch:** Logging and monitoring (planned)

### Python Libraries

- **FastAPI:** Web framework
- **Pydantic:** Data validation
- **Boto3:** AWS SDK
- **Uvicorn:** ASGI server
- **Pytest:** Testing framework

---

## 🎯 Design Principles

1. **Contract-First Development:** Define DTOs before implementation
2. **Layer Separation:** Clear boundaries between routers, services, and adapters
3. **Dependency Injection:** Testable and modular architecture
4. **Error Transparency:** Global exception handlers with full logging
5. **Type Safety:** Comprehensive type hints throughout codebase
6. **Test Coverage:** Co-located unit tests for every component
7. **Documentation:** OpenAPI specs with examples for all endpoints
8. **Immutability:** Pydantic models prevent accidental mutations
