# AWS Bedrock RAG API

![AWS](https://img.shields.io/badge/AWS-Powered-FF9900?logo=aws&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-Development-yellow)

A production-ready Retrieval-Augmented Generation (RAG) system designed for AWS.

This project utilizes **Knowledge Bases for Amazon Bedrock** to manage the RAG pipeline (Ingestion, Embedding, Retrieval) and hosts the **FastAPI** backend on **Amazon ECS (Fargate)**.

---

## 🚦 Current Status

> **Last Updated:** 2025-12-16  
> **Current Phase:** Phase 3 Complete ✅ | Phase 4 Next 🚀  
> **Mock Mode:** Enabled for local development without AWS credentials  
> **Test Coverage:** 155 tests passing (19 adapters + 34 dtos + 32 services + 28 routers + 10 middleware + 32 integration)

---

## 🗺 Development Roadmap

### Phase 0: Project Initialization ✅

**Goal:** Set up project structure and tooling.

- [x] **Project Structure**: Initialize directories, .gitignore, and configuration files.
- [x] **Development Tools**: Create Makefile and environment template.

### Phase 1: AWS Integration & Core Adapters ✅

**Goal:** Establish low-level connectivity with AWS services and implement the infrastructure layer using `boto3`.

- [x] **AWS Configuration**: Set up environment variables in `.env` (e.g., `AWS_REGION`, `BEDROCK_KB_ID`, `BEDROCK_DATA_SOURCE_ID`, `S3_BUCKET_NAME`).
- [x] **Bedrock Adapter**: Implement `adapters/bedrock/bedrock_adapter.py`.
  - [x] `retrieve_and_generate`: Wrapper for the Bedrock Agent Runtime API to handle RAG queries.
  - [x] `start_ingestion_job`: Wrapper to trigger a Knowledge Base sync (required after file changes).
- [x] **S3 Adapter**: Implement `adapters/s3/s3_adapter.py`.
  - [x] `upload_file`: Upload source documents to the target Bucket.
  - [x] `list_files`: List objects in the Bucket to display current knowledge base assets.
  - [x] `delete_file`: Remove objects from S3.
  - [x] `get_file`: Download file content from S3.
- [x] **Unit Tests**: Write mock tests for adapters to ensure correct parameter handling for AWS calls.
- [x] **FastAPI Conversion**: Migrated from Flask to FastAPI with async endpoints and OpenAPI documentation.
- [x] **Docker Update**: Updated Dockerfile with multi-stage build for FastAPI + Uvicorn.

### Phase 2: Data Contracts & RAG Business Logic ✅

**Goal:** Define strict data interfaces (Contract First) and implement the core service logic.

- [x] **DTO Definition**: Define Pydantic models in `dtos/` to enforce type safety.
  - [x] `ChatRequest`: User input schema with query text and optional metadata filters.
  - [x] `ChatResponse`: Standardized output including the answer and source citations.
  - [x] `Citation`: Citation structure with content, document info, and relevance score.
  - [x] `MetadataFilter`: Filter schema supporting equals, not_equals, greater_than, less_than, contains operators.
  - [x] `FileUploadRequest`: Schema allowing file binaries and custom metadata (JSON).
  - [x] `FileResponse`: Schema for file metadata (name, size, custom_attributes, S3 key).
  - [x] `FileListResponse`: List response with total count and size.
  - [x] `FileDeleteResponse`: Deletion confirmation response.
- [x] **RAG Service**: Create `services/rag/rag_service.py` for retrieval-augmented generation.
  - [x] `query()`: Process RAG queries using Bedrock Knowledge Base.
  - [x] **Filter Generation**: Convert metadata filters into Bedrock/OpenSearch format.
  - [x] **Citation Parsing**: Parse and format citations from Bedrock response.
- [x] **Ingestion Service**: Create `services/ingestion/ingestion_service.py` for document management.
  - [x] **Metadata Handling**: Generate `.metadata.json` sidecar files in Bedrock format.
  - [x] **Upload Logic**: Upload source file + metadata JSON to S3 → Trigger Bedrock Sync.
  - [x] **List Logic**: List documents with metadata loaded from sidecar files.
  - [x] **Delete Logic**: Delete source file + metadata JSON from S3 → Trigger Bedrock Sync.

### Phase 3: API Implementation ✅

**Goal:** Expose services via RESTful API endpoints using FastAPI routers.

- [x] **Chat Router**: Implement `routers/chat/chat_router.py`.
  - [x] `POST /chat`: Main endpoint for RAG interactions (supports filtering params).
  - [x] Dependency injection with RAGService.
  - [x] Comprehensive OpenAPI documentation with examples.
  - [x] Removed try-catch blocks to let exceptions propagate to global handlers.
- [x] **Ingest Router**: Implement `routers/ingest/ingest_router.py` for Knowledge Base management.
  - [x] `GET /files`: Retrieve the list of documents and their metadata from S3.
  - [x] `POST /files`: Endpoint for uploading new documents **with metadata** (Form Data).
  - [x] `DELETE /files/{filename}`: Endpoint for removing documents and updating the index.
  - [x] JSON metadata parsing and validation.
  - [x] Removed try-catch blocks for unified error handling.
- [x] **Global Exception Handlers**: Comprehensive error handling with full stack traces (10 tests).
  - [x] AWS error mapping (ClientError, BotoCoreError, ParamValidationError).
  - [x] Pydantic validation error formatting (422).
  - [x] HTTPException wrapper with standard error format.
  - [x] FileNotFoundError handler (404).
  - [x] ValueError handler for validation errors (400).
  - [x] General exception catch-all with full stack trace logging.
  - [x] All error responses include `success: false` field.
  - [x] User-friendly error messages without exposing internal details.
- [x] **Logging Infrastructure**: Complete logging setup.
  - [x] Root logger configuration with console handler.
  - [x] LOG_LEVEL from .env (INFO by default).
  - [x] Third-party logger suppression (python_multipart, urllib3, botocore).
  - [x] Service layer logging (INFO for operations, DEBUG for details).
  - [x] Full error stack traces with logger.exception().
- [x] **Response DTOs**: All response models include success field.
  - [x] ChatResponse: `success: bool = True`
  - [x] FileResponse: `success: bool = True`
  - [x] FileListResponse: `success: bool = True`
  - [x] FileDeleteResponse: `success: bool = True`
  - [x] All error responses: `success: false`
- [x] **API Documentation**: Swagger UI (`/docs`) available with complete schemas and examples.
- [x] **Integration Tests**: Comprehensive integration tests (32 tests).
  - [x] Test real service instantiation without mocks.
  - [x] Verify dependency injection works with actual constructors.
  - [x] Test API endpoints with real service dependencies.
  - [x] Test exception handlers with real API requests.
  - [x] Validate OpenAPI schema and documentation.
- [x] **Bug Fixes**: All tests passing.
  - [x] Fixed PYTHONPATH configuration in Makefile.
  - [x] Fixed service layer key naming inconsistencies (Key vs key).
  - [x] Fixed TestClient configuration for proper exception handling.
  - [x] All 155 tests passing successfully.
  - [ ] Test complete RAG query flow (mock mode).
  - [ ] Test document upload → list → delete workflow.
  - [ ] Verify error handling across full stack.

### Phase 4: Containerization & Deployment 🚢

**Goal:** Package the application and deploy it to Amazon ECS Fargate.

- [ ] **Docker Optimization**: Finalize the `Dockerfile` using multi-stage builds to minimize image size.
- [ ] **Local Verification**: Run the full stack locally using `make local` or Docker to ensure all components interact correctly.
- [ ] **ECS Preparation**:
  - [ ] Create an ECR repository and push the image.
  - [ ] Define the ECS Task Definition (CPU/Memory, Task Role, Execution Role).
- [ ] **Deployment**:
  - [ ] Create/Update the ECS Service.
  - [ ] Verify Health Checks and log streaming in CloudWatch.

---

## 🛠 Tech Stack

| Category              | Technology                  | Description                                      |
| :-------------------- | :-------------------------- | :----------------------------------------------- |
| **Backend Framework** | **FastAPI**                 | High-performance Python async framework.         |
| **Compute Engine**    | **Amazon ECS (Fargate)**    | Serverless container compute (Zero cold starts). |
| **RAG Engine**        | **Bedrock Knowledge Bases** | Managed RAG workflow.                            |
| **LLM**               | **Claude 3.5 Sonnet**       | Generation Model.                                |
| **Vector DB**         | **OpenSearch Serverless**   | Vector Store.                                    |

---

## 📂 Project Structure

```text
aws-bedrock-rag/
├── app/                        # FastAPI Application
│   ├── adapters/              # External system integrations (AWS Bedrock, S3)
│   │   ├── bedrock/          # Bedrock Knowledge Base adapter
│   │   └── s3/               # S3 storage adapter
│   │
│   ├── dtos/                  # Data Transfer Objects (Pydantic models)
│   │   ├── chat/             # Chat/RAG DTOs
│   │   └── file/             # File management DTOs
│   │
│   ├── services/              # Business logic layer
│   │   ├── rag/              # RAG query service
│   │   └── ingestion/        # Document ingestion service
│   │
│   ├── routers/               # API endpoints (FastAPI routers)
│   ├── utils/                 # Utilities (config, helpers)
│   ├── main.py               # Application entry point
│   ├── Dockerfile            # Multi-stage Docker build
│   └── requirements.txt      # Python dependencies
│
├── .env.example              # Environment variables template
├── Makefile                  # Development commands
└── README.md                 # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- AWS Account (for production deployment)
- Docker (optional, for containerized deployment)

### Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd aws-bedrock-rag
   ```

2. **Create environment file**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration (use MOCK_MODE=true for local development)
   ```

3. **Install dependencies**

   ```bash
   make install
   ```

4. **Run tests**

   ```bash
   make test
   ```

5. **Start development server**
   ```bash
   make local
   # Server will start at http://localhost:8000
   # API docs available at http://localhost:8000/docs
   ```

### Development Commands

```bash
make help          # Show all available commands
make install       # Install all dependencies in virtual environment
make test          # Run all unit tests
make local         # Run FastAPI server with hot-reload
make docker-build  # Build Docker image
make docker-run    # Run Docker container locally
```

### Testing Strategy

This project follows a comprehensive testing pyramid approach:

#### 1. **Unit Tests** (Current: 113 tests ✅)

- **Location**: Co-located with source code (`test_*.py` files)
- **Coverage**: Adapters, DTOs, Services, Routers
- **Characteristics**:
  - Mock all external dependencies (AWS, file system)
  - Fast execution (~0.5s for all tests)
  - Test individual components in isolation
- **Run**: `make test` or `pytest app/ -v`

#### 2. **Integration Tests** (Planned)

- **Purpose**: Verify component interactions without mocks
- **Test Cases**:
  - Service instantiation with real dependencies
  - Dependency injection validation
  - Router → Service → Adapter integration
- **Benefits**: Catch initialization errors and parameter mismatches
- **Run**: `pytest app/tests/integration/ -v`

#### 3. **E2E Tests** (Planned)

- **Purpose**: Test complete user workflows in mock mode
- **Test Cases**:
  - Complete RAG query flow with metadata filtering
  - Document lifecycle: upload → list → query → delete
  - Error handling across full request/response cycle
- **Benefits**: Ensure features work end-to-end from API to business logic
- **Run**: `pytest app/tests/e2e/ -v`

#### 4. **Contract Tests** (Optional)

- **Purpose**: Ensure mocks match real implementations
- **Verification**: Mock interface signatures match real services
- **Benefits**: Prevent mock drift from actual code

### Environment Variables

Key configuration in `.env`:

```bash
# Environment
APP_ENV=dev                    # dev, staging, production

# AWS Configuration
AWS_REGION=ap-northeast-1
AWS_PROFILE=default           # (optional) AWS CLI profile

# Bedrock Configuration
BEDROCK_KB_ID=your-kb-id-here
BEDROCK_DATA_SOURCE_ID=your-data-source-id-here
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# S3 Configuration
S3_BUCKET_NAME=your-bucket-name-here

# Application Configuration
MOCK_MODE=true                # Enable mock mode for local development without AWS
LOG_LEVEL=INFO
```
