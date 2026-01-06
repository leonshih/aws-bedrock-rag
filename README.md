# AWS Bedrock RAG API

![AWS](https://img.shields.io/badge/AWS-Powered-FF9900?logo=aws&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)

A production-ready **Retrieval-Augmented Generation (RAG)** API powered by AWS Bedrock Knowledge Bases and FastAPI. Built with clean architecture principles, comprehensive testing, and multi-tenant support.

---

## Quick Links

- **[Project Status](PROJECT_STATUS.md)** - Development roadmap and progress tracking
- **[Architecture](ARCHITECTURE.md)** - System design and technical architecture
- **[Technical Rules](docs/TECH_RULES.md)** - Coding standards and best practices
- **[Glossary](docs/GLOSSARY.md)** - Terms, concepts, and acronyms

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **AWS Account** with Bedrock access (optional for mock mode)
- **Docker** (optional)

### Installation

## 📂 Project Structure

```text
aws-bedrock-rag/
├── app/                        # FastAPI Application
│   ├── adapters/              # External system integrations (AWS Bedrock, S3)
│   ├── dependencies/          # FastAPI dependencies (tenant validation, auth)
│   ├── dtos/                  # Data Transfer Objects (Layer-based organization)
│   │   ├── common.py         # Shared DTOs (Tenant context, Error models)
│   │   ├── routers/          # Router layer DTOs
│   │   └── adapters/         # Adapter layer DTOs
│   │
│   ├── services/              # Business logic layer
│   ├── routers/               # API endpoints (FastAPI routers)
│   ├── middleware/            # Exception handlers
│   ├── utils/                 # Utilities (config, helpers)
│   ├── main.py               # Application entry point
│   ├── Dockerfile            # Multi-stage Docker build
│   └── requirements.txt      # Python dependencies
│
├── .env.example              # Environment variables template
├── Makefile                  # Development commands
└── README.md                 # Project documentation
```

### DTO Organization Principles

**Layer-Based Structure**: DTOs are organized by architectural layer, not by domain feature:

- **`dtos/common.py`**: Base response types used across all layers
- **`dtos/routers/`**: Request/Response DTOs for API endpoints
- **`dtos/adapters/`**: DTOs for external service interactions (AWS, databases)
- **`dtos/services/`**: (Future) Internal service DTOs if needed

**Import Examples**:

```python
# Router layer DTOs
from app.dtos.routers.chat import ChatRequest, ChatResponse, Citation
from app.dtos.routers.ingest import FileUploadRequest, FileResponse

# Adapter layer DTOs
from app.dtos.adapters.s3 import S3UploadResult, S3ListResult
from app.dtos.adapters.bedrock import BedrockRAGResult

# Common DTOs (Tenant context, Error models)
from app.dtos.common import TenantContext, ErrorDetail
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
   # Edit .env with your AWS credentials and configuration
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

---

## 📚 API Documentation

Interactive API documentation is available at `/docs` when running the server:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Response Format

All endpoints return **Pydantic models directly** with appropriate **HTTP status codes** (REST standard):

```json
// Success (HTTP 200/201)
{
  "answer": "RAG combines retrieval and generation...",
  "session_id": "session-123",
  "model_used": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "citations": [/* citation objects */]
}

// Error (HTTP 4xx/5xx)
{
  "detail": {
    "type": "ValidationError",
    "message": "Invalid tenant ID format",
    "path": "/chat"
  }
}
```

**HTTP Status Codes:**

- `200 OK`: Successful query/retrieval
- `201 Created`: Resource created (file upload)
- `400 Bad Request`: Validation errors
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server errors

See [Architecture Documentation](ARCHITECTURE.md) for detailed request/response flows.

---

## 🔐 Multi-Tenant Support

All API endpoints require a `X-Tenant-ID` header for tenant isolation. Validation is handled through **FastAPI dependency injection** (`app/dependencies/tenant.py`).

```bash
# Query with tenant context
curl -X POST "http://localhost:8000/chat" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?"}'

# Upload document
curl -X POST "http://localhost:8000/files" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@document.pdf" \
  -F 'metadata={"category": "research"}'

# List files
curl -X GET "http://localhost:8000/files" \
  -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000"
```

**Tenant Isolation Features:**

- **Dependency-based validation:** `get_tenant_context()` extracts and validates `X-Tenant-ID`
- **Automatic Swagger UI integration:** FastAPI generates header input fields in `/docs`
- **UUID v4 format validation:** Returns **422 Unprocessable Entity** for invalid/missing tenant IDs
- **S3 path isolation:** Documents stored under `s3://{bucket}/{tenant_id}/{filename}`
- **Knowledge Base filtering:** Bedrock queries include `equalTo` filters on `tenant_id` metadata
- **Test-friendly design:** Use `dependency_overrides` to mock tenant context in tests

**Testing Multi-Tenant Logic:**

```python
from app.dependencies import get_tenant_context
from app.dtos.common import TenantContext
from uuid import UUID

def override_tenant():
    return TenantContext(tenant_id=UUID("550e8400-e29b-41d4-a716-446655440000"))

app.dependency_overrides[get_tenant_context] = override_tenant
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test suite
pytest app/services/ -v
pytest app/tests/integration/ -v

# Run with coverage
pytest --cov=app --cov-report=html
```

See [Architecture Documentation](ARCHITECTURE.md#testing-strategy) for testing principles and strategy.

---

## 🏗️ Architecture

This project follows clean architecture principles with clear layer separation:

```
API Layer (Routers)
    ↓
Service Layer (Business Logic)
    ↓
Adapter Layer (AWS Integration)
    ↓
External Services (Bedrock, S3)
```

**Key Principles:**

- Layer-based DTO organization
- Dependency injection with FastAPI
- Global exception handling
- Type-safe contracts with Pydantic

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

---

## 🔧 Tech Stack

- **FastAPI 0.104+**: Modern async web framework
- **Pydantic 2.4+**: Data validation and serialization
- **AWS Bedrock**: Knowledge Bases, Claude 3.5 Sonnet
- **boto3**: AWS SDK for Python
- **pytest**: Testing framework with 98.7% pass rate

---
