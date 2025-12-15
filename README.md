# AWS Bedrock RAG API

![AWS](https://img.shields.io/badge/AWS-Powered-FF9900?logo=aws&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-Development-yellow)

A production-ready Retrieval-Augmented Generation (RAG) system designed for AWS.

This project utilizes **Knowledge Bases for Amazon Bedrock** to manage the RAG pipeline (Ingestion, Embedding, Retrieval) and hosts the **FastAPI** backend on **Amazon ECS (Fargate)**.

---

## 🚦 Current Status

> **Last Updated:** 2025-12-15  
> **Current Phase:** Phase 1 Complete ✅ | Phase 2 In Progress 🚧

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
- [x] **Unit Tests**: Write mock tests for adapters to ensure correct parameter handling for AWS calls (19 tests passing).
- [x] **FastAPI Conversion**: Migrated from Flask to FastAPI with async endpoints and OpenAPI documentation.
- [x] **Docker Update**: Updated Dockerfile with multi-stage build for FastAPI + Uvicorn.

### Phase 2: Data Contracts & RAG Business Logic

**Goal:** Define strict data interfaces (Contract First) and implement the core service logic.

- [ ] **DTO Definition**: Define Pydantic models in `dtos/` to enforce type safety.
  - [ ] `ChatRequest`: User input schema (e.g., query text, **optional metadata filters**).
  - [ ] `ChatResponse`: Standardized output including the answer and source citations.
  - [ ] `FileUploadRequest`: Schema allowing file binaries and **custom metadata (JSON)**.
  - [ ] `FileResponse`: Schema for file metadata (name, size, **custom_attributes**).
- [ ] **Ingestion Service**: Create `services/ingestion_service.py` to orchestrate consistency.
  - [ ] **Metadata Handling**: Logic to generate `.metadata.json` sidecar files based on input.
  - [ ] **Upload Logic**: Upload source file + metadata JSON to S3 $\rightarrow$ Trigger Bedrock Sync.
  - [ ] **Delete Logic**: Delete source file + metadata JSON from S3 $\rightarrow$ Trigger Bedrock Sync.
- [ ] **Retrieval Service**: Create `services/rag_service.py`.
  - [ ] Implement the logic to call the Bedrock Adapter.
  - [ ] **Filter Generation**: Convert user requirements into Bedrock/OpenSearch metadata filters (e.g., `year > 2023`).
  - [ ] Parse and format "Citations" from Bedrock into a clean structure.

### Phase 3: API Implementation

**Goal:** Expose services via RESTful API endpoints using FastAPI routers.

- [ ] **Chat Router**: Implement `routers/chat.py`.
  - [ ] `POST /chat`: Main endpoint for RAG interactions (supports filtering params).
- [ ] **Ingest Router**: Implement `routers/ingest.py` for Knowledge Base management.
  - [ ] `GET /files`: Retrieve the list of documents and their metadata from S3.
  - [ ] `POST /files`: Endpoint for uploading new documents **with metadata** (Form Data).
  - [ ] `DELETE /files/{filename}`: Endpoint for removing documents and updating the index.
- [ ] **Error Handling**: Implement global exception handlers for specific AWS errors (e.g., `ThrottlingException`, `AccessDenied`) and standard HTTP errors.
- [ ] **API Documentation**: Verify that Swagger UI (`/docs`) correctly renders the schemas and endpoints.

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
aws-bedrock-rag-api/
├── app/                        # [Backend] FastAPI Source Code
│   ├── adapters/               # External system adapters (e.g., Bedrock, S3)
│   ├── dtos/                   # Data Transfer Objects (Pydantic models)
│   ├── processors/             # Domain-specific processing logic
│   ├── routers/                # API Endpoints
│   ├── services/               # Core services (e.g., Bedrock integration)
│   ├── utils/                  # Utility functions and helpers (Used across layers)
│   ├── main.py                 # App entry point
│   ├── Dockerfile              # Docker image definition
│   └── requirements.txt        # Python dependencies
│
├── .env.example               # Environment variables template
└── Makefile                    # Development commands
```

---

## 🚀 Getting Started

### Development Commands

Using the provided Makefile for common tasks:

```bash
make help          # Show all available commands
make install       # Install all dependencies
make test          # Run local tests
make local         # Run FastAPI locally
```
