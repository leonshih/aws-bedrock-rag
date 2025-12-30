# Technical Rules & Guidelines

This document defines the technical standards, coding conventions, and architectural rules for the AWS Bedrock RAG API project.

---

## 🏗️ Architectural Rules

### 1. Layer Separation (MANDATORY)

**Rule:** Components must only communicate with adjacent layers.

```
✅ ALLOWED:
Router → Service → Adapter → AWS

❌ FORBIDDEN:
Router → Adapter (skipping Service)
Service → AWS Client (skipping Adapter)
```

**Enforcement:**

- Routers must **not** instantiate adapters directly
- Services must **not** import `boto3` clients
- Adapters are the **only** layer allowed to use AWS SDKs

**Example Violation:**

```python
# ❌ BAD: Router directly using adapter
from app.adapters.s3 import S3Adapter

@router.post("/files")
async def upload(file: UploadFile):
    s3 = S3Adapter()  # VIOLATION: Skip service layer
    s3.upload_file(...)
```

**Correct Pattern:**

```python
# ✅ GOOD: Router uses service
@router.post("/files")
async def upload(
    file: UploadFile,
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)]
):
    ingestion_service.upload_document(...)
```

---

### 2. DTO Organization (MANDATORY)

**Rule:** DTOs must be organized by **architectural layer**, not by domain feature.

```
✅ CORRECT STRUCTURE:
app/dtos/
├── common.py          # Shared response wrappers
├── routers/           # API request/response models
│   ├── chat.py
│   └── ingest.py
└── adapters/          # External service DTOs
    ├── s3.py
    └── bedrock.py

❌ WRONG STRUCTURE:
app/dtos/
├── chat/              # Domain-based (wrong)
│   ├── request.py
│   ├── response.py
│   └── citation.py
└── file/              # Domain-based (wrong)
```

**Rationale:**

- Layer-based organization reflects data flow
- Prevents circular dependencies
- Makes data contracts explicit at layer boundaries

---

### 3. Response Format (MANDATORY)

**Rule:** All API responses must include a `success` field.

```python
# ✅ CORRECT: Success response
{
    "success": true,
    "data": {...}
}

# ✅ CORRECT: Error response
{
    "success": false,
    "error": {
        "type": "ValidationError",
        "message": "...",
        "detail": "..."
    }
}
```

**Implementation:**

- **Services/Adapters:** Return `dict` with `{success: True, data: DTO}`
- **Type Hints:** Use `SuccessResponse[T]` for IDE support
- **Exceptions:** Global middleware converts to error format

**Example:**

```python
# Service layer
def list_documents(self) -> dict:
    result = self.s3_adapter.list_files(...)
    return {
        "success": True,
        "data": FileListResponse(files=result["data"].objects, ...)
    }
```

---

### 4. Exception Handling (MANDATORY)

**Rule:** Services and routers must **NOT** use try-catch blocks. Let exceptions propagate to global handlers.

```python
# ❌ BAD: Local exception handling
@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = rag_service.query(request)
        return result
    except Exception as e:
        return {"error": str(e)}  # VIOLATION

# ✅ GOOD: Let middleware handle exceptions
@router.post("/chat")
async def chat(request: ChatRequest, rag_service: RAGService = Depends(...)):
    return rag_service.query(request)  # Exception propagates automatically
```

**Rationale:**

- Centralized error handling in [`middleware/exception_handlers.py`](../app/middleware/exception_handlers.py)
- Consistent error format across all endpoints
- Full stack traces logged via `logger.exception()`

**Exception Mapping:**

- `ValidationError` → 422 Unprocessable Entity
- `HTTPException` → Pass through status code
- `FileNotFoundError` → 404 Not Found
- `ValueError` → 400 Bad Request
- `ClientError (AWS)` → Varies by error code
- Generic exceptions → 500 Internal Server Error

---

### 5. Dependency Injection (MANDATORY)

**Rule:** Use FastAPI's `Depends()` for service injection in routers.

```python
# ✅ CORRECT: Dependency injection
def get_rag_service() -> RAGService:
    return RAGService()

@router.post("/chat")
async def chat(
    request: ChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
):
    return rag_service.query(request)
```

**Forbidden Patterns:**

```python
# ❌ BAD: Direct instantiation
@router.post("/chat")
async def chat(request: ChatRequest):
    service = RAGService()  # VIOLATION: Should use Depends()
    return service.query(request)

# ❌ BAD: Adapter injection into service
service = RAGService(bedrock_adapter=adapter)  # VIOLATION
```

**Configuration Injection:**

```python
# ✅ CORRECT: Config injection
class RAGService:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()  # Default fallback
```

---

## 📝 Coding Standards

### 6. Type Hints (MANDATORY)

**Rule:** All functions must have complete type annotations.

```python
# ✅ CORRECT: Full type hints
def upload_document(
    self,
    file_content: bytes,
    filename: str,
    metadata: Optional[Dict[str, Any]] = None
) -> dict:
    ...

# ❌ BAD: Missing type hints
def upload_document(self, file_content, filename, metadata=None):
    ...
```

**Rationale:**

- IDE autocomplete and error detection
- Self-documenting code
- Type safety validation

---

### 7. Pydantic Models (MANDATORY)

**Rule:** All DTOs must be Pydantic `BaseModel` subclasses with validation.

```python
# ✅ CORRECT: Pydantic model with validation
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    max_results: Optional[int] = Field(default=5, ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {"query": "What is AWS Bedrock?"}
        }

# ❌ BAD: Plain dict or TypedDict
ChatRequest = TypedDict("ChatRequest", {"query": str})  # VIOLATION
```

**Required Elements:**

- Field descriptions with `Field(..., description="...")`
- Validation constraints (`min_length`, `ge`, `le`, etc.)
- JSON schema examples in `Config`

---

### 8. Logging (MANDATORY)

**Rule:** Use structured logging with appropriate levels.

```python
import logging
logger = logging.getLogger(__name__)

# ✅ CORRECT: Structured logging
logger.info(f"Uploading document: {filename}")
logger.debug(f"S3 key generated: {s3_key}")
logger.error(f"Upload failed: {filename}", exc_info=True)
logger.exception("Unexpected error during upload")  # Auto-includes stack trace
```

**Log Levels:**

- `DEBUG`: Detailed debugging information (S3 keys, API payloads)
- `INFO`: Normal operational events (uploads, queries, deletions)
- `WARNING`: Recoverable issues (retry attempts, deprecated features)
- `ERROR`: Errors that require attention (failed uploads, AWS errors)
- `EXCEPTION`: Same as ERROR but includes full stack trace

**Forbidden:**

```python
# ❌ BAD: Print statements
print(f"Uploading {filename}")  # VIOLATION

# ❌ BAD: Exposing sensitive data
logger.info(f"AWS credentials: {aws_key}")  # VIOLATION
```

---

### 9. Test Organization (MANDATORY)

**Rule:** Unit tests must be co-located with source code.

```
✅ CORRECT STRUCTURE:
app/
├── services/
│   ├── rag/
│   │   ├── rag_service.py
│   │   └── test_rag_service.py      # Co-located
│   └── ingestion/
│       ├── ingestion_service.py
│       └── test_ingestion_service.py # Co-located

❌ WRONG STRUCTURE:
app/
├── services/
│   └── rag/
│       └── rag_service.py
└── tests/
    └── services/
        └── test_rag_service.py      # Separated (wrong)
```

**Test File Naming:**

- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature>_integration.py`

**Test Class Naming:**

```python
# ✅ CORRECT
class TestRAGService:
    """Tests for RAGService."""

    def test_query_basic(self):
        ...

# ❌ BAD
class RAGServiceTest:  # VIOLATION: Wrong naming convention
```

---

### 10. Mock Usage & Testing Strategy (MANDATORY)

**Rule:** Unit tests must mock all external dependencies using standard Python testing libraries.

#### ✅ CORRECT: Use `unittest.mock` or `pytest-mock`

```python
# Adapter Layer: Mock boto3 clients
from unittest.mock import Mock, patch

@patch('boto3.client')
def test_s3_upload(mock_boto3_client):
    mock_s3 = Mock()
    mock_boto3_client.return_value = mock_s3
    mock_s3.put_object.return_value = {'ETag': '"abc123"'}

    adapter = S3Adapter()
    result = adapter.upload_file(b"content", "bucket", "key")

    mock_s3.put_object.assert_called_once()
    assert result["success"] is True

# Service Layer: Mock adapters
@patch('app.services.rag.rag_service.BedrockAdapter')
def test_query_basic(mock_bedrock_class):
    mock_adapter = Mock()
    mock_adapter.retrieve_and_generate.return_value = {
        "success": True,
        "data": BedrockRAGResult(...)
    }
    mock_bedrock_class.return_value = mock_adapter

    service = RAGService()
    result = service.query(request, tenant_id=UUID("..."))

    mock_adapter.retrieve_and_generate.assert_called_once()

# Router Layer: Mock services
@pytest.fixture
def mock_rag_service():
    service = Mock(spec=RAGService)
    service.query.return_value = {"success": True, "data": {...}}
    return service

async def test_chat_endpoint(client, mock_rag_service):
    response = await client.post("/api/v1/chat", json={...})
    assert response.status_code == 200
```

#### ❌ FORBIDDEN: Built-in Mock Mode in Production Code

**DO NOT implement mock logic inside adapters or services:**

```python
# ❌ VIOLATION: Mock mode in production code
class S3Adapter:
    def __init__(self, mock_mode: bool = False):  # WRONG
        self.mock_mode = mock_mode
        if self.mock_mode:
            self._mock_storage = {}

    def upload_file(self, ...):
        if self.mock_mode:  # WRONG
            return self._mock_upload(...)
        # Real implementation
```

**Why This is Wrong:**

1. **Violates Single Responsibility Principle:** Adapters should handle real AWS operations, not test logic
2. **Maintenance Burden:** Every method needs dual implementation (real + mock)
3. **Testing Anti-Pattern:** Tests should control mocking, not production code
4. **Production Risk:** Mock code ships to production, increasing attack surface
5. **Non-Standard:** Deviates from Python testing best practices

#### ✅ CORRECT: Pure Production Code + Test-Time Mocking

```python
# app/adapters/s3/s3_adapter.py (Production Code)
class S3Adapter:
    """Pure adapter with only real AWS implementation."""

    def __init__(self):
        config = get_config()
        self.client = boto3.client('s3', region_name=config.AWS_REGION)

    def upload_file(
        self,
        file_content: bytes,
        bucket: str,
        key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> SuccessResponse[S3UploadResult]:
        """Upload file to S3 (no mock logic here)."""
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

# app/adapters/s3/test_s3_adapter.py (Test Code)
class TestS3Adapter:
    """Tests mock boto3, not S3Adapter itself."""

    @patch('boto3.client')
    def test_upload_file_success(self, mock_boto3_client):
        # Setup mock
        mock_s3 = Mock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.put_object.return_value = {
            'ETag': '"mock-etag"',
            'VersionId': 'v1'
        }

        # Test real code path with mocked dependency
        adapter = S3Adapter()
        result = adapter.upload_file(b"test", "bucket", "key")

        # Verify
        assert result["success"] is True
        assert result["data"].etag == '"mock-etag"'
        mock_s3.put_object.assert_called_once_with(
            Bucket="bucket",
            Key="key",
            Body=b"test"
        )
```

#### Mock Patterns by Layer

| Layer       | What to Mock      | How to Mock                                      |
| ----------- | ----------------- | ------------------------------------------------ |
| **Adapter** | `boto3` clients   | `@patch('boto3.client')`                         |
| **Service** | Adapter instances | `@patch('app.services.*.*.AdapterClass')`        |
| **Router**  | Service instances | `@pytest.fixture` with `Mock(spec=ServiceClass)` |

#### Additional Testing Guidelines

1. **Fixture Organization:** Use `conftest.py` for shared fixtures
2. **Mock Verification:** Always assert mock calls with `.assert_called_once()` or `.assert_called_with()`
3. **Real vs Mock:** Never mix real AWS calls in unit tests (use integration tests for that)
4. **Deterministic Tests:** Mock responses should be predictable and not depend on external state

---

## 🔐 Security Rules

### 11. Input Validation (MANDATORY)

**Rule:** All external inputs must be validated with Pydantic.

```python
# ✅ CORRECT: Pydantic validation
class FileUploadRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v):
        if v and len(v) > 100:  # Custom validation
            raise ValueError("Metadata too large")
        return v

# ❌ BAD: Manual validation
def upload_file(metadata: dict):
    if metadata and len(metadata) > 100:  # VIOLATION: Should use Pydantic
        raise ValueError("Metadata too large")
```

---

### 12. Error Message Sanitization (MANDATORY)

**Rule:** Error responses must **not** expose internal implementation details.

```python
# ✅ CORRECT: User-friendly error messages
{
    "success": false,
    "error": {
        "type": "ValidationError",
        "message": "Invalid file format",
        "detail": "Only PDF, TXT, and DOCX files are supported"
    }
}

# ❌ BAD: Exposed internals
{
    "error": "boto3.exceptions.ClientError: S3 access denied for key /app/secrets/db.yaml"
}  # VIOLATION: Exposes internal paths and AWS details
```

**Exception Handler Implementation:**

```python
@app.exception_handler(ClientError)
async def aws_error_handler(request: Request, exc: ClientError):
    error_code = exc.response["Error"]["Code"]

    # Map AWS error to user-friendly message
    if error_code == "AccessDenied":
        message = "Permission denied"
    else:
        message = "AWS service error"

    # Log full error internally
    logger.error(f"AWS Error: {error_code}", exc_info=True)

    # Return sanitized message
    return ErrorResponse(
        type=error_code,
        message=message,
        detail=None  # No internal details
    )
```

---

## 📦 Dependency Management

### 13. Import Rules (MANDATORY)

**Rule:** Use absolute imports from `app` root.

```python
# ✅ CORRECT: Absolute imports
from app.adapters.bedrock import BedrockAdapter
from app.dtos.routers.chat import ChatRequest
from app.services.rag import RAGService

# ❌ BAD: Relative imports
from ..adapters.bedrock import BedrockAdapter  # VIOLATION
from .chat import ChatRequest  # VIOLATION
```

**Import Order:**

1. Standard library imports
2. Third-party imports (FastAPI, Pydantic, boto3)
3. Local application imports (alphabetical by module)

```python
# ✅ CORRECT ORDER
import json
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.adapters.bedrock import BedrockAdapter
from app.dtos.routers.chat import ChatRequest
from app.services.rag import RAGService
```

---

### 14. Configuration Management (MANDATORY)

**Rule:** All configuration must be loaded from [`app/utils/config.py`](../app/utils/config.py).

```python
# ✅ CORRECT: Use Config class
from app.utils.config import Config

class RAGService:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.kb_id = self.config.BEDROCK_KB_ID

# ❌ BAD: Direct environment access
import os
kb_id = os.getenv("BEDROCK_KB_ID")  # VIOLATION: Should use Config
```

**Environment Variable Naming:**

- Use `SCREAMING_SNAKE_CASE`
- Prefix AWS configs with `AWS_`, Bedrock with `BEDROCK_`, S3 with `S3_`

---

## 🧪 Testing Rules

### 15. Test Coverage (MANDATORY)

**Rule:** All new code must include unit tests.

```python
# Every new service method requires tests:
class RAGService:
    def query(self, request: ChatRequest) -> dict:
        ...  # Implementation

# Corresponding test file: test_rag_service.py
class TestRAGService:
    def test_query_basic(self):
        ...  # Test basic query

    def test_query_with_filters(self):
        ...  # Test metadata filtering

    def test_query_with_custom_model(self):
        ...  # Test model override
```

**Minimum Test Coverage:**

- **Adapters:** 80%+ line coverage
- **Services:** 85%+ line coverage
- **Routers:** 90%+ line coverage
- **DTOs:** 100% (validation tests)

---

### 16. Test Independence (MANDATORY)

**Rule:** Tests must not depend on execution order or external state.

```python
# ✅ CORRECT: Independent tests
class TestIngestionService:
    @pytest.fixture
    def service(self):
        return IngestionService()  # Fresh instance per test

    def test_upload(self, service):
        result = service.upload_document(...)
        assert result["success"] is True

    def test_list(self, service):
        result = service.list_documents()  # Independent of upload test
        assert result["success"] is True

# ❌ BAD: Tests depend on order
class TestIngestionService:
    def test_1_upload(self):
        self.filename = service.upload_document(...)  # State persists

    def test_2_list(self):
        result = service.list_documents()
        assert self.filename in result  # VIOLATION: Depends on test_1
```

---

### 17. Fixture Usage (RECOMMENDED)

**Rule:** Use pytest fixtures for common test setup.

```python
# ✅ CORRECT: Reusable fixtures
@pytest.fixture
def mock_config():
    config = Mock()
    config.S3_BUCKET_NAME = "test-bucket"
    config.BEDROCK_KB_ID = "test-kb-id"
    return config

@pytest.fixture
def ingestion_service(mock_config):
    return IngestionService(config=mock_config)

def test_upload(ingestion_service):
    result = ingestion_service.upload_document(...)
```

---

## 📚 Documentation Rules

### 18. Docstrings (MANDATORY)

**Rule:** All public classes and methods must have docstrings.

```python
# ✅ CORRECT: Comprehensive docstrings
class RAGService:
    """Service for RAG-based query processing.

    This service orchestrates retrieval and generation using
    Bedrock Knowledge Bases. It handles metadata filtering
    and citation parsing.
    """

    def query(self, request: ChatRequest) -> dict:
        """
        Process a RAG query with metadata filtering.

        Args:
            request: Chat request with query and optional filters

        Returns:
            Success response with answer and citations

        Raises:
            ValueError: If query is empty
        """
        ...

# ❌ BAD: Missing or incomplete docstrings
class RAGService:  # VIOLATION: No class docstring
    def query(self, request):  # VIOLATION: No method docstring
        ...
```

**Docstring Format:**

- Class: Purpose and responsibilities
- Method: Description, Args, Returns, Raises

---

### 19. OpenAPI Documentation (MANDATORY)

**Rule:** All router endpoints must have complete OpenAPI documentation.

```python
# ✅ CORRECT: Full OpenAPI spec
@router.post(
    "/chat",
    summary="Chat with RAG system",
    description="""
    Process a query using Retrieval-Augmented Generation.

    **Features:**
    - Semantic search over knowledge base
    - Metadata filtering support
    - Citation tracking
    """,
    responses={
        200: {"description": "Successful response with answer"},
        400: {"description": "Invalid request format"},
        500: {"description": "Internal server error"}
    }
)
async def chat(request: ChatRequest):
    ...

# ❌ BAD: No documentation
@router.post("/chat")  # VIOLATION: Missing summary, description, responses
async def chat(request: ChatRequest):
    ...
```

---

## 🚫 Anti-Patterns

### Forbidden Practices

1. **❌ Circular Dependencies**

   ```python
   # service.py
   from app.routers.chat import router  # VIOLATION

   # router.py
   from app.services.rag import RAGService  # Creates cycle
   ```

2. **❌ Global State**

   ```python
   # VIOLATION: Mutable global state
   uploaded_files = []

   def upload(file):
       uploaded_files.append(file)  # Not thread-safe
   ```

3. **❌ Hardcoded Values**

   ```python
   # VIOLATION: Hardcoded configuration
   S3_BUCKET = "my-bucket"

   # ✅ CORRECT: Use config
   self.config.S3_BUCKET_NAME
   ```

4. **❌ String Formatting with Untrusted Input**

   ```python
   # VIOLATION: SQL/NoSQL injection risk
   query = f"SELECT * FROM docs WHERE title = '{user_input}'"

   # ✅ CORRECT: Parameterized queries
   query = {"term": {"title": user_input}}
   ```

5. **❌ Ignoring Type Hints**
   ```python
   # VIOLATION: Type hint mismatch
   def upload(file: bytes) -> str:
       return 123  # Returns int, not str
   ```

---

## 🔄 Code Review Checklist

Before submitting a PR, verify:

- [ ] All functions have type hints
- [ ] All DTOs are Pydantic models with validation
- [ ] No try-catch blocks in routers/services
- [ ] Tests are co-located with source code
- [ ] All tests pass (`make test`)
- [ ] Imports are absolute from `app` root
- [ ] Docstrings for all public APIs
- [ ] OpenAPI docs for all endpoints
- [ ] Logging uses `logger`, not `print()`
- [ ] No hardcoded values (use `Config`)
- [ ] Response format includes `success` field
- [ ] Layer separation preserved (no layer skipping)

---

## 📝 Version History

- **v1.1** (2025-12-30): Added comprehensive mock usage guidelines and testing strategy
- **v1.0** (2025-12-18): Initial rules documentation
