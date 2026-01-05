# Glossary

This document defines key terms, concepts, and acronyms used throughout the AWS Bedrock RAG API project.

---

## A

### Adapter

A design pattern that provides a consistent interface to external systems. In this project, adapters wrap AWS service clients (Bedrock, S3) to isolate boto3 dependencies from business logic.

**Example:** [`BedrockAdapter`](../app/adapters/bedrock/bedrock_adapter.py), [`S3Adapter`](../app/adapters/s3/s3_adapter.py)

### API Gateway

(Planned) AWS service for managing HTTP endpoints, authentication, and rate limiting. Will be placed in front of the ECS service.

### AWS Bedrock

Amazon's fully managed service for foundation models (LLMs). Provides access to models like Claude, Titan, and Jurassic.

**Key Services:**

- **Bedrock Runtime:** Direct model invocation
- **Bedrock Knowledge Bases:** Managed RAG pipeline
- **Bedrock Agent Runtime:** Enhanced RAG with agents

---

## B

### Bedrock Knowledge Base

A managed service that handles the complete RAG pipeline: ingestion, embedding generation, vector storage, and retrieval. Eliminates the need to manage OpenSearch clusters manually.

**Components:**

- **Data Source:** S3 bucket containing documents
- **Vector Store:** OpenSearch Serverless for embeddings
- **Embedding Model:** Titan Embeddings v2 (default)

### Boto3

The official AWS SDK for Python. Provides low-level clients for interacting with AWS services.

**Usage in Project:** Only used in adapter layer ([`app/adapters/`](../app/adapters/))

---

## C

### Citation

A reference to a source document that was used to generate an answer in RAG. Includes the retrieved text snippet, document metadata, and relevance score.

**Model:** [`Citation`](../app/dtos/routers/chat.py)

**Example:**

```json
{
  "content": "RAG combines retrieval and generation...",
  "document_title": "rag-guide.pdf",
  "location": { "s3Location": { "uri": "s3://bucket/rag-guide.pdf" } },
  "score": 0.95
}
```

### Claude

Anthropic's family of large language models. This project uses **Claude 3.5 Sonnet** for text generation in RAG responses.

**Model ID:** `anthropic.claude-3-5-sonnet-20241022-v2:0`

### Config

A centralized configuration class that loads environment variables from `.env`.

**Location:** [`app/utils/config.py`](../app/utils/config.py)

**Usage:**

```python
config = Config()
kb_id = config.BEDROCK_KB_ID
```

---

## D

### Data Source

In Bedrock Knowledge Bases, a data source defines the S3 bucket/prefix where documents are stored. Changes to the data source require an **ingestion job** to update the index.

### Dependency Injection

A design pattern where dependencies are provided to a component rather than created internally. FastAPI uses this for service instantiation in routers.

**Example:**

```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
):
    return rag_service.query(request)
```

### DTO (Data Transfer Object)

A Pydantic model used for data validation and serialization. DTOs define the structure of requests, responses, and inter-layer data exchange.

**Organization:** Layer-based structure in [`app/dtos/`](../app/dtos/)

---

## E

### ECS (Elastic Container Service)

AWS container orchestration service. This project will deploy to **ECS Fargate** (serverless compute).

### Embedding

A numerical vector representation of text. Bedrock Knowledge Bases automatically generate embeddings using **Titan Embeddings v2**.

**Dimensions:** 1024 (Titan v2 default)

### Exception Handler

Middleware that catches exceptions and converts them to standardized error responses.

**Location:** [`app/middleware/exception_handlers.py`](../app/middleware/exception_handlers.py)

---

## F

### FastAPI

A modern, high-performance Python web framework with automatic OpenAPI documentation.

**Key Features:**

- Async/await support
- Automatic request validation
- OpenAPI/Swagger UI
- Dependency injection

### Fargate

AWS serverless compute engine for ECS. Eliminates the need to manage EC2 instances.

### Filter

A metadata-based search constraint in RAG queries. Filters narrow retrieval results to specific document attributes.

**Example:**

```python
MetadataFilter(key="category", value="medical", operator="equals")
```

---

## I

### Ingestion Job

A Bedrock Knowledge Base operation that syncs S3 documents with the OpenSearch vector store. Must be triggered after uploading/deleting files.

**Adapter Method:** [`BedrockAdapter.start_ingestion_job()`](../app/adapters/bedrock/bedrock_adapter.py)

### Inference Profile

A Bedrock resource that provides cross-region routing for model access. Required for newer models like Claude 3.5 Sonnet v2.

**Example:** `us.anthropic.claude-3-5-sonnet-20241022-v2:0`

---

## K

### Knowledge Base (KB)

Short for **Bedrock Knowledge Base**. The managed RAG service used by this project.

**Configuration:**

- `BEDROCK_KB_ID`: Unique identifier for the knowledge base
- `BEDROCK_DATA_SOURCE_ID`: ID of the S3 data source

---

## L

### Layer

An architectural component grouping in the project:

1. **Router Layer:** HTTP endpoints ([`app/routers/`](../app/routers/))
2. **Service Layer:** Business logic ([`app/services/`](../app/services/))
3. **Adapter Layer:** External integrations ([`app/adapters/`](../app/adapters/))

### LLM (Large Language Model)

A foundation model trained on vast text corpora. Used for generating natural language responses in RAG.

**Examples:** Claude, GPT-4, Titan

---

## M

### Metadata

Custom attributes attached to documents. Stored in `.metadata.json` sidecar files and indexed by Bedrock for filtering.

**Format:**

```json
{
  "metadataAttributes": {
    "author": "Dr. Smith",
    "year": 2023,
    "category": "medical"
  }
}
```

---

## O

### OpenAPI

A standard specification for REST APIs. FastAPI auto-generates OpenAPI schemas from route definitions.

**Access:** `http://localhost:8000/docs` (Swagger UI)

### OpenSearch Serverless

AWS managed vector database used by Bedrock Knowledge Bases. Handles vector storage and similarity search.

**Collection Type:** Optimized for vector search (cosine similarity)

---

## P

### Phase

A major milestone in the project development lifecycle, defined in [`PROJECT_STATUS.md`](../PROJECT_STATUS.md). Each Phase contains multiple **Tasks** (checklist items) that must be completed sequentially.

**Characteristics:**

- Phases are numbered sequentially (Phase 0, Phase 1, Phase 2, etc.)
- Each Phase has a completion percentage
- A Phase is considered complete only when ALL tasks within it are marked `[x]`
- **Critical Rule:** Must complete ALL tasks in Phase N before starting Phase N+1

**Example:**

```markdown
### ⏳ Phase 4: Multi-Tenant Architecture (In Progress - 88% Complete)

- [x] Tenant context model with UUID validation
- [x] Tenant middleware implementation
- [ ] Multi-tenant test coverage ← Must complete this before Phase 5
```

### Pydantic

A Python library for data validation using type hints. All DTOs in this project are Pydantic `BaseModel` subclasses.

**Features:**

- Automatic validation
- JSON serialization
- OpenAPI schema generation

### Pytest

The testing framework used in this project.

**Usage:**

```bash
make test              # Run all tests
pytest app/services/   # Run service tests only
```

---

## R

### RAG (Retrieval-Augmented Generation)

A technique that combines document retrieval with LLM generation. Improves answer accuracy by grounding responses in retrieved context.

**Pipeline:**

1. User submits a query
2. System retrieves relevant documents (retrieval)
3. LLM generates an answer using retrieved context (generation)

### Retrieval Configuration

Parameters that control document search behavior in RAG queries.

**Key Settings:**

- `numberOfResults`: Max documents to retrieve (default: 5)
- `vectorSearchConfiguration`: Metadata filters and overrides

### Router

A FastAPI component that defines HTTP endpoints. Routers handle request validation and response serialization.

**Example:** [`ChatRouter`](../app/routers/chat/chat_router.py)

---

## S

### S3 (Simple Storage Service)

AWS object storage service. Used to store source documents and metadata files.

**Bucket Structure:**

```
s3://bucket-name/
└── documents/
    ├── file.pdf
    └── file.pdf.metadata.json
```

### Service

A business logic layer component. Services orchestrate adapters and implement domain-specific workflows.

**Examples:** [`RAGService`](../app/services/rag/rag_service.py), [`IngestionService`](../app/services/ingestion/ingestion_service.py)

### Sidecar File

A companion file that stores metadata for a primary document. In this project, `.metadata.json` files are sidecars for uploaded documents.

**Naming Convention:** `{filename}.metadata.json`

### Session ID

A unique identifier for a conversation in Bedrock. Used to maintain context across multiple queries.

**Source:** Generated by Bedrock Agent Runtime

---

## U

### UUID (Universally Unique Identifier)

A 128-bit identifier standard (RFC 4122). Used for generating unique identifiers.

**Format:** `550e8400-e29b-41d4-a716-446655440000` (8-4-4-4-12 hex digits)

### Uvicorn

An ASGI server for FastAPI applications. Used to run the API in development and production.

**Usage:**

```bash
uvicorn app.main:app --reload  # Development
```

---

## V

### Vector Database

A specialized database optimized for storing and searching high-dimensional vectors (embeddings). This project uses **OpenSearch Serverless** via Bedrock Knowledge Bases.

### Vector Search

A similarity search technique that finds documents with embeddings closest to the query embedding (cosine similarity).

---

## Common Acronyms

| Acronym  | Full Name                         | Description                                |
| -------- | --------------------------------- | ------------------------------------------ |
| **API**  | Application Programming Interface | HTTP endpoints for external access         |
| **AWS**  | Amazon Web Services               | Cloud platform                             |
| **DTO**  | Data Transfer Object              | Validated data structure                   |
| **ECS**  | Elastic Container Service         | Container orchestration                    |
| **IAM**  | Identity and Access Management    | AWS permissions system                     |
| **KB**   | Knowledge Base                    | Short for Bedrock Knowledge Base           |
| **LLM**  | Large Language Model              | Foundation model for text generation       |
| **RAG**  | Retrieval-Augmented Generation    | Technique combining retrieval + generation |
| **S3**   | Simple Storage Service            | Object storage                             |
| **SDK**  | Software Development Kit          | Library for API access (boto3)             |
| **UUID** | Universally Unique Identifier     | 128-bit unique ID                          |

---

## File and Directory Naming

### Project Structure Terms

| Term           | Location          | Description                   |
| -------------- | ----------------- | ----------------------------- |
| **Adapter**    | `app/adapters/`   | External service wrappers     |
| **DTO**        | `app/dtos/`       | Pydantic data models          |
| **Service**    | `app/services/`   | Business logic layer          |
| **Router**     | `app/routers/`    | HTTP endpoint handlers        |
| **Middleware** | `app/middleware/` | Request/response interceptors |
| **Utils**      | `app/utils/`      | Helper functions and config   |

### File Naming Conventions

```
service_name.py          # Implementation file
test_service_name.py     # Unit tests (co-located)
__init__.py              # Package exports
```

---

## Configuration Variables

### Environment Variable Glossary

| Variable                 | Type  | Description                                  |
| ------------------------ | ----- | -------------------------------------------- |
| `ENVIRONMENT`            | `str` | Deployment environment (dev/staging/prod)    |
| `AWS_REGION`             | `str` | AWS region (e.g., us-east-1)                 |
| `AWS_PROFILE`            | `str` | AWS CLI profile name (optional)              |
| `BEDROCK_KB_ID`          | `str` | Knowledge Base identifier                    |
| `BEDROCK_DATA_SOURCE_ID` | `str` | Data source identifier                       |
| `BEDROCK_MODEL_ID`       | `str` | LLM model identifier or inference profile    |
| `S3_BUCKET_NAME`         | `str` | S3 bucket for document storage               |
| `APP_ENV`                | `str` | Application environment (dev/prod)           |
| `LOG_LEVEL`              | `str` | Logging verbosity (DEBUG/INFO/WARNING/ERROR) |

---

## Bedrock API Operations

### Agent Runtime API

| Operation               | Purpose           | Used In                                                                                |
| ----------------------- | ----------------- | -------------------------------------------------------------------------------------- |
| `retrieve_and_generate` | Execute RAG query | [`BedrockAdapter.retrieve_and_generate()`](../app/adapters/bedrock/bedrock_adapter.py) |

### Bedrock Agent API

| Operation             | Purpose                   | Used In                                                                              |
| --------------------- | ------------------------- | ------------------------------------------------------------------------------------ |
| `start_ingestion_job` | Sync S3 with vector store | [`BedrockAdapter.start_ingestion_job()`](../app/adapters/bedrock/bedrock_adapter.py) |

### S3 API

| Operation         | Purpose              | Used In                                                       |
| ----------------- | -------------------- | ------------------------------------------------------------- |
| `put_object`      | Upload file          | [`S3Adapter.upload_file()`](../app/adapters/s3/s3_adapter.py) |
| `list_objects_v2` | List bucket contents | [`S3Adapter.list_files()`](../app/adapters/s3/s3_adapter.py)  |
| `delete_object`   | Delete file          | [`S3Adapter.delete_file()`](../app/adapters/s3/s3_adapter.py) |
| `get_object`      | Download file        | [`S3Adapter.get_file()`](../app/adapters/s3/s3_adapter.py)    |

---

## Error Types

### HTTP Status Codes

| Code    | Name                  | Usage                           |
| ------- | --------------------- | ------------------------------- |
| **200** | OK                    | Successful request              |
| **400** | Bad Request           | Validation error, invalid input |
| **403** | Forbidden             | AWS access denied               |
| **404** | Not Found             | Resource doesn't exist          |
| **422** | Unprocessable Entity  | Pydantic validation failure     |
| **429** | Too Many Requests     | Rate limit exceeded             |
| **500** | Internal Server Error | Unexpected exception            |

### AWS Error Codes

| Code                        | Meaning                | HTTP Status |
| --------------------------- | ---------------------- | ----------- |
| `AccessDenied`              | IAM permission denied  | 403         |
| `ThrottlingException`       | Rate limit exceeded    | 429         |
| `ResourceNotFoundException` | Resource doesn't exist | 404         |
| `ValidationException`       | Invalid parameters     | 400         |

---

## T

### Tenant

An isolated customer/organization in a multi-tenant system. Each tenant's data is logically separated to ensure data privacy and security.

**In This Project:**

- Identified by UUID v4 (`tenant_id`)
- Enforced at middleware layer (✅ implemented)
- Isolated via S3 path prefixes (`documents/{tenant_id}/`) (✅ implemented)
- Automatically filtered in Bedrock Knowledge Base queries (✅ implemented)

### Tenant Context

A data model containing tenant identification information, passed through request lifecycle.

**Model:** [`TenantContext`](../app/dtos/common.py)

**Fields:**

- `tenant_id`: UUID - Unique tenant identifier

**Validation:**

- Must be valid UUID v4 format
- Cannot be None or empty
- Accepts UUID with or without hyphens

**Example:**

```python
context = TenantContext(tenant_id="550e8400-e29b-41d4-a716-446655440000")
```

### Tenant Isolation

Architectural pattern ensuring each tenant's data is completely separated from others.

**Implementation Layers:**

1. **Storage:** S3 paths prefixed with `{tenant_id}/` (✅ implemented)
2. **Retrieval:** Auto-injected metadata filters in RAG queries (✅ implemented)
3. **Middleware:** Automatic tenant extraction from headers (✅ implemented)
4. **Validation:** UUID format enforcement (✅ implemented)

### TenantMissingError

Exception raised when required `X-Tenant-ID` header is missing from HTTP request.

**HTTP Status:** 400 Bad Request

### TenantValidationError

Exception raised when `tenant_id` format is invalid (not a valid UUID).

**HTTP Status:** 422 Unprocessable Entity

### Task

A single actionable checklist item within a **Phase** in [`PROJECT_STATUS.md`](../PROJECT_STATUS.md). Tasks represent atomic units of work that can be completed and verified independently.

**Format:**

- Uncompleted: `- [ ] Task description`
- Completed: `- [x] Task description`

**Rules:**

1. **One Task at a Time:** Only work on ONE uncompleted task per development cycle
2. **Sequential Execution:** Tasks must be completed in the order they appear
3. **Definition of Done:** A task is complete when:
   - Implementation is finished
   - Tests are written and passing
   - Documentation is updated
   - Changes are committed to git

**Example:**

```markdown
### Phase 5 Checklist:

- [x] Remove SuccessResponse[T] from common.py ← Completed task
- [ ] Refactor RAGService.query() method ← Current task (in-progress)
- [ ] Update Router layer ← Next task (not started)
```

**Reference:** See [Development Workflow](../.github/copilot-instructions.md#step-1-atomic-selection) for task selection rules.

---

## Testing Terminology

### Test Types

| Type                 | Scope                  | Mocks             | Location                   |
| -------------------- | ---------------------- | ----------------- | -------------------------- |
| **Unit Test**        | Single component       | All external deps | Co-located with source     |
| **Integration Test** | Component interactions | None/minimal      | `app/tests/integration/`   |
| **E2E Test**         | Full workflow          | None              | `app/tests/e2e/` (planned) |

### Pytest Fixtures

**Definition:** Reusable test setup functions decorated with `@pytest.fixture`

**Example:**

```python
@pytest.fixture
def mock_config():
    config = Mock()
    config.S3_BUCKET_NAME = "test-bucket"
    return config
```

---

## Version History

- **v1.0** (2025-12-18): Initial glossary
