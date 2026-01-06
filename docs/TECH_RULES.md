# Technical Rules & Guidelines

This document defines the technical standards, coding conventions, and architectural rules for the AWS Bedrock RAG API project.

---

## 🏗️ Architectural Rules

### 1. Layer Separation (MANDATORY)

**Rule:** Components must only communicate with adjacent layers.

```mermaid
graph LR
    Router[Router Layer] --> Service[Service Layer]
    Service --> Adapter[Adapter Layer]
    Adapter --> AWS[AWS SDK / External]
```

**Enforcement:**

- Routers must **not** instantiate adapters directly.
- Services must **not** import `boto3` clients.
- Adapters are the **only** layer allowed to use AWS SDKs.

**Rationale:** ensures that business logic (Service) is decoupled from infrastructure details (AWS). This allows swapping infrastructure (e.g., S3 to Azure Blob) without changing the Service layer.

---

### 2. DTO Organization (MANDATORY)

**Rule:** DTOs must be organized by **architectural layer**.

```text
✅ CORRECT STRUCTURE:
app/dtos/
├── common.py          # Shared enums/types
├── routers/           # API Request/Response models
│   ├── chat.py
│   └── ingest.py
└── adapters/          # External service DTOs (if needed)
    ├── s3.py
    └── bedrock.py
```

**Rationale:**

- Layer-based organization reflects data flow.
- Prevents circular dependencies.
- Makes data contracts explicit at layer boundaries.

---

### 3. Response Format & Status Codes (MANDATORY)

**Rule:**

1. **Services** must return **Pydantic Models** (Domain Objects), NEVER raw dictionaries.
2. **Routers** return the Pydantic model directly.
3. Use **HTTP Status Codes** to indicate success or failure. Do NOT use a generic `{ "success": true }` wrapper.

**Service Layer:**

```python
# ✅ CORRECT: Service returns Pydantic Model
def get_document(self, doc_id: str) -> DocumentDTO:
    data = self.s3_adapter.get_object(doc_id)
    return DocumentDTO(id=doc_id, content=data.content)
```

**Router Layer:**

```python
# ✅ CORRECT: HTTP 200/201 + Direct Model
@router.post("/docs", status_code=201)
async def create_doc(request: CreateDocRequest) -> DocumentDTO:
    return service.create_document(request)

# ❌ BAD: Manual dictionary construction
return {"answer": "...", "session_id": "..."}  # Use Pydantic models instead
```

---

### 4. Exception Handling Strategy (MANDATORY)

**Rule:** Exception handling is divided into **Translation** (Adapter) and **Presentation** (Middleware).

1.  **Adapters (Translation Layer):** MUST catch technical exceptions (e.g., `boto3`, `requests`) and **raise Domain Exceptions**.
    - _Goal:_ Isolate the Service layer from low-level library details.
2.  **Services & Routers:** MUST NOT use `try-catch` blocks for flow control. Let Domain Exceptions propagate.
3.  **Middleware (Presentation Layer):** Catches Domain Exceptions and converts them to standard HTTP Error Responses.

**Implementation Example:**

```python
# 1. Adapter Layer: Translates Technical Error -> Domain Error
class S3Adapter:
    def get_file(self, key: str):
        try:
            self.client.get_object(Bucket=..., Key=key)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                # ✅ Translate to Domain Exception
                raise DocumentNotFoundError(f"File {key} not found")
            if error_code == 'AccessDenied':
                raise StoragePermissionError("Access denied")
            # Re-raise unexpected errors
            raise e

# 2. Service Layer: Pure Business Logic (No try-catch)
class IngestionService:
    def process_file(self, key: str):
        # Implicitly allows DocumentNotFoundError to bubble up
        file = self.s3_adapter.get_file(key)
        return file

# 3. Middleware: Domain Error -> HTTP Response
@app.exception_handler(DocumentNotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "message": str(exc)}
    )
```

---

### 5. Dependency Injection (MANDATORY)

**Rule:** Services must use **Constructor Injection**. Do not instantiate dependencies (Adapters) inside the Service.

**Service Definition:**

```python
# ✅ CORRECT: Constructor Injection
class RAGService:
    def __init__(self, s3_adapter: S3Adapter, bedrock_adapter: BedrockAdapter):
        self.s3_adapter = s3_adapter
        self.bedrock_adapter = bedrock_adapter

# ❌ BAD: Internal Instantiation
class RAGService:
    def __init__(self):
        self.s3_adapter = S3Adapter()  # VIOLATION: Hard dependency
```

**Router Wiring (FastAPI Depends):**

```python
# app/dependencies.py
def get_s3_adapter() -> S3Adapter:
    return S3Adapter()

def get_rag_service(
    s3: Annotated[S3Adapter, Depends(get_s3_adapter)]
) -> RAGService:
    return RAGService(s3_adapter=s3)

# Router
@router.post("/chat")
async def chat(
    service: Annotated[RAGService, Depends(get_rag_service)]
):
    ...
```

---

### 5.1 Multi-Tenant Dependency (MANDATORY)

**Rule:** Tenant ID validation and extraction must use **FastAPI Dependency Injection**, not middleware.

**Implementation Pattern:**

```python
# app/dependencies/tenant.py
async def get_tenant_context(
    x_tenant_id: Annotated[UUID, Header(description="Tenant UUID")]
) -> TenantContext:
    """Extract and validate tenant ID from X-Tenant-ID header."""
    try:
        return TenantContext(tenant_id=x_tenant_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

# app/routers/chat/chat_router.py
@router.post("/chat")
async def query_knowledge_base(
    chat_request: ChatRequest,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> ChatResponse:
    # Pass tenant_id as explicit parameter to service
    return rag_service.query(chat_request, tenant_id=tenant_context.tenant_id)
```

**Key Principles:**

1. **tenant_id is NOT part of request DTOs** (e.g., `ChatRequest`, `FileUploadRequest`)
2. **Flow:** `X-Tenant-ID` header → `get_tenant_context` dependency → Router extracts `tenant_id` → Pass to Service as parameter
3. **Service Layer:** Accept `tenant_id: UUID` as separate parameter (NOT in DTO)
4. **Testing:** Override dependency using `app.dependency_overrides[get_tenant_context]`
5. **Swagger UI:** FastAPI automatically displays X-Tenant-ID parameter in API docs

**Benefits:**

- ✅ Explicit dependencies in function signatures
- ✅ Easier testing (use `dependency_overrides` instead of mocking middleware)
- ✅ Automatic Swagger UI documentation
- ✅ Follows FastAPI best practices

---

## 📝 Coding Standards

### 6. Type Hints (MANDATORY)

**Rule:** All functions must have complete type annotations for arguments and return values.

```python
def upload_document(
    self,
    file_content: bytes,
    metadata: Optional[Dict[str, Any]] = None
) -> UploadResultDTO:
    ...
```

---

### 7. Pydantic Models (MANDATORY)

**Rule:** All DTOs must be Pydantic `BaseModel` subclasses with validation.

```python
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    max_results: int = Field(default=5, ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {"query": "Explain quantum computing"}
        }
```

---

### 8. Logging (MANDATORY)

**Rule:** Use structured logging with appropriate levels (`logger.info`, `logger.error`).

- **NEVER** use `print()`.
- **NEVER** log sensitive data (API Keys, PII).

---

### 9. Test Organization (MANDATORY)

**Rule:** Use a **Mirrored Directory Structure** for tests. This ensures tests are easily excluded from production builds.

```text
✅ CORRECT STRUCTURE:
project_root/
├── app/
│   └── services/
│       └── rag_service.py
└── tests/
    └── services/
        └── test_rag_service.py    # Mirrors app structure
```

**Naming:**

- Test files: `test_<module_name>.py`
- Test classes: `class Test<ClassName>:`

---

### 10. Mock Usage & Testing Strategy (MANDATORY)

**Rule:**

1. **Service Tests:** Use **Constructor Injection** to pass Mock objects. Do NOT use `patch` unless absolutely necessary.
2. **Adapter Tests:** Use `patch` to mock external libraries (`boto3`, `requests`).

**Service Layer Test (Preferred):**

```python
class TestRAGService:
    def test_query_flow(self):
        # 1. Create Mocks with defined specs (ensures interface match)
        mock_s3 = Mock(spec=S3Adapter)
        mock_bedrock = Mock(spec=BedrockAdapter)

        # 2. Setup Behavior
        mock_bedrock.generate.return_value = "AI Answer"

        # 3. Inject Mocks via Constructor
        service = RAGService(s3_adapter=mock_s3, bedrock_adapter=mock_bedrock)

        # 4. Act & Assert
        result = service.query("question")
        assert result == "AI Answer"
        mock_bedrock.generate.assert_called_once()
```

**Adapter Layer Test:**

```python
class TestS3Adapter:
    @patch('boto3.client')
    def test_upload(self, mock_boto_client):
        # Test implementation with mocked boto3
        pass
```

---

### 11. Type Safety & Protocol Contracts (MANDATORY)

**Rule:** All Adapters MUST implement explicit Protocol contracts to ensure compile-time type safety and prevent interface drift.

**Background:**

- **Problem:** Mock-based testing allows calling methods that don't exist on real adapters, causing runtime errors in production.
- **Solution:** Use `typing.Protocol` to define adapter interfaces + enforce `Mock(spec=RealClass)` in tests.

**Implementation Pattern:**

**Step 1: Define Protocol Contract**

```python
# app/adapters/protocols/s3_protocol.py
from typing import Protocol, Dict, Optional
from app.dtos.adapters.s3 import S3UploadResult, S3ListResult, S3DeleteResult

class S3AdapterProtocol(Protocol):
    """
    Contract for S3 storage operations.
    All S3 adapter implementations MUST provide these methods.
    """

    def upload_file(
        self,
        file_content: bytes,
        bucket: str,
        key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> S3UploadResult:
        """Upload a file to S3 with optional metadata."""
        ...

    def list_files(self, bucket: str, prefix: str = "") -> S3ListResult:
        """List files in S3 bucket."""
        ...

    def delete_file(self, bucket: str, key: str) -> S3DeleteResult:
        """Delete a file from S3."""
        ...

    def get_file(self, bucket: str, key: str) -> bytes:
        """Download file content from S3."""
        ...
```

**Step 2: Service Layer Uses Protocol Type Hint**

```python
# app/services/ingestion/ingestion_service.py
from app.adapters.protocols.s3_protocol import S3AdapterProtocol

class IngestionService:
    def __init__(self, s3_adapter: S3AdapterProtocol):  # ✅ Type hint with Protocol
        self.s3_adapter = s3_adapter

    def load_metadata(self, key: str):
        content = self.s3_adapter.get_file(key)  # ✅ mypy verifies this exists
        return json.loads(content)
```

**Step 3: Adapter Implements Protocol (Implicitly)**

```python
# app/adapters/s3/s3_adapter.py
class S3Adapter:  # ✅ Duck-typing: satisfies S3AdapterProtocol
    """S3 storage adapter implementation."""

    def upload_file(self, file_content: bytes, bucket: str, key: str,
                    metadata: Optional[Dict[str, str]] = None) -> S3UploadResult:
        # Implementation
        pass

    def get_file(self, bucket: str, key: str) -> bytes:
        # ⚠️ If we forget this method, mypy will error when used as S3AdapterProtocol
        pass
```

**Step 4: Contract Tests Verify Implementation**

```python
# app/adapters/s3/test_s3_adapter_contract.py
import pytest
from app.adapters.s3.s3_adapter import S3Adapter

@pytest.mark.contract
class TestS3AdapterContract:
    """Verify S3Adapter implements all required methods."""

    def test_adapter_has_all_required_methods(self):
        """Ensure adapter implements full protocol."""
        adapter = S3Adapter()

        # ✅ These fail if method doesn't exist
        assert hasattr(adapter, 'upload_file')
        assert hasattr(adapter, 'list_files')
        assert hasattr(adapter, 'delete_file')
        assert hasattr(adapter, 'get_file')  # ✅ Catches missing implementations

        # Verify they're callable
        assert callable(adapter.get_file)
```

**Step 5: Mock Tests Use Specification**

```python
# app/services/ingestion/test_ingestion_service.py
from unittest.mock import Mock
from app.adapters.s3.s3_adapter import S3Adapter

def test_load_metadata():
    # ✅ CORRECT: Mock with spec
    mock_s3 = Mock(spec=S3Adapter)
    mock_s3.get_file.return_value = b'{"data": "test"}'

    service = IngestionService(s3_adapter=mock_s3)
    result = service.load_metadata("key")

    # ❌ This would fail: mock_s3.non_existent_method()
    # AttributeError: Mock object has no attribute 'non_existent_method'
```

**Benefits:**

- ✅ **Compile-time Safety:** mypy catches missing adapter methods before runtime
- ✅ **Mock Safety:** `Mock(spec=Adapter)` prevents calling non-existent methods in tests
- ✅ **Contract Enforcement:** Protocol ensures all adapters implement required interface
- ✅ **Documentation:** Protocol serves as explicit interface documentation

**See Also:** `docs/TYPE_SAFETY_GUIDE.md` for comprehensive implementation guide.

---
