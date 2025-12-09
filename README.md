# AWS Bedrock RAG API

![AWS](https://img.shields.io/badge/AWS-Powered-FF9900?logo=aws&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker&logoColor=white)
![AWS CDK](https://img.shields.io/badge/IaC-AWS%20CDK-orange)
![Status](https://img.shields.io/badge/Status-Development-yellow)

A production-ready Retrieval-Augmented Generation (RAG) system designed for AWS.

This project utilizes **Knowledge Bases for Amazon Bedrock** to manage the RAG pipeline (Ingestion, Embedding, Retrieval) and hosts the **FastAPI** backend on **Amazon ECS (Fargate)**.

---

## 🚦 Current Status

> **Last Updated:** 2025-12-09
> **Current Phase:** ✅ Phase 0 Complete → 🟡 Phase 1A - Infrastructure Foundation

| Module                   | Status         | Notes                                            |
| :----------------------- | :------------- | :----------------------------------------------- |
| **Infrastructure (CDK)** | 🔴 Not Started | Architecture design finalized; CDK init pending. |
| **RAG Pipeline**         | 🔴 Not Started | Knowledge Base and S3 bucket to be provisioned.  |
| **Backend API**          | 🔴 Not Started | FastAPI skeleton and Dockerfile to be created.   |
| **CI/CD**                | 🔴 Not Started | GitHub Actions workflow pending.                 |
| **Monitoring**           | 🔴 Not Started | CloudWatch integration pending.                  |

---

## 🗺 Development Roadmap

This roadmap follows an **Incremental MVP** approach, building a working system first, then adding complexity.

### Phase 0: Project Initialization ✅

**Goal:** Set up project structure and tooling.

- [x] **Project Structure**: Initialize directories, .gitignore, and configuration files.
- [x] **Dependencies**: Set up requirements.txt for CDK and FastAPI.
- [x] **Development Tools**: Create Makefile and environment template.
- [x] **CDK Configuration**: Add cdk.json with feature flags.

### Phase 1A: Infrastructure Foundation (Single Stack)

**Goal:** Deploy a minimal working infrastructure to AWS.

- [ ] **CDK App Init**: Create `infra/app.py` as CDK entry point.
- [ ] **Base Stack**: Create `infra/stacks/base_stack.py` with all resources.
- [ ] **VPC & Networking**: Define VPC with Public/Private Subnets and NAT Gateway.
- [ ] **Security Groups**: Set up security groups for ALB and Fargate.
- [ ] **ECS Cluster**: Provision ECS Cluster and basic Fargate setup.
- [ ] **ALB**: Configure Application Load Balancer.
- [ ] **Hello World Docker**: Create minimal Dockerfile for testing.
- [ ] **Deployment**: Verify `make deploy` works and service is accessible.

### Phase 1B: FastAPI Application

**Goal:** Replace Hello World with a real FastAPI application.

- [ ] **FastAPI Setup**: Create `app/main.py` with basic structure.
- [ ] **Health Endpoint**: Implement `/health` endpoint for ALB health checks.
- [ ] **API Structure**: Set up routers and basic response models.
- [ ] **Dockerfile**: Update to run FastAPI with uvicorn.
- [ ] **Local Testing**: Verify `make local` runs the app successfully.
- [ ] **Redeploy**: Push updated image to ECR and deploy to ECS.

### Phase 2: RAG Integration

**Goal:** Add Bedrock Knowledge Base and RAG functionality.

- [ ] **S3 Bucket**: Add S3 bucket to CDK stack for document storage.
- [ ] **OpenSearch Serverless**: Provision OpenSearch collection for vector store.
- [ ] **Bedrock Knowledge Base**: Create Knowledge Base linking S3 and OpenSearch.
- [ ] **IAM Roles**: Configure permissions for Bedrock and ECS Task.
- [ ] **Bedrock Service**: Implement `app/services/bedrock.py` with boto3 client.
- [ ] **RAG Endpoint**: Create `/api/v1/rag/query` endpoint.
- [ ] **Testing**: Verify end-to-end RAG pipeline works.

### Phase 3: Production Readiness

**Goal:** Optimize for production traffic and operations.

- [ ] **Streaming**: Implement Server-Sent Events (SSE) for token streaming.
- [ ] **Auto-Scaling**: Add ECS auto-scaling policies based on CPU/memory.
- [ ] **Monitoring**: Configure CloudWatch dashboards and alarms.
- [ ] **Logging**: Structured logging with correlation IDs.
- [ ] **CI/CD**: Set up GitHub Actions for automated testing and deployment.
- [ ] **Documentation**: Complete API_EXAMPLES.md and DEPLOYMENT.md.

---

## 🛠 Tech Stack

| Category              | Technology                  | Description                                      |
| :-------------------- | :-------------------------- | :----------------------------------------------- |
| **Infrastructure**    | **AWS CDK (Python)**        | Infrastructure as Code.                          |
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
│   ├── Dockerfile              # Docker image definition
│   ├── main.py                 # App entry point
│   ├── routers/                # API Endpoints
│   ├── services/               # Bedrock integration logic
│   └── requirements.txt        # Python dependencies
│
├── infra/                      # [Infra] AWS CDK Code
│   ├── app.py                  # CDK App entry point
│   └── stacks/                 # Stack definitions
│       └── rag_stack.py        # Main stack (VPC, ECS, Bedrock)
│
├── cdk.json                    # CDK Configuration
└── requirements.txt            # CDK Deployment dependencies
```

---

## 🚀 Getting Started

### Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd aws-bedrock-rag
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
make install

# 3. Deploy to AWS
make bootstrap  # First time only
make deploy

# 4. Create Knowledge Base (manual step via AWS Console)
# 5. Upload documents to S3 and sync
```

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for AWS CDK CLI)
- **Docker** (MUST be running to build the image)
- **AWS CLI** (Configured via `aws configure`)

### Development Commands

Using the provided Makefile for common tasks:

```bash
make help          # Show all available commands
make install       # Install all dependencies
make test          # Run local tests
make local         # Run FastAPI locally
make docker-build  # Build Docker image
make deploy        # Deploy to AWS
make destroy       # Destroy all resources
```

### Testing the API

After deployment, access the interactive API documentation:

```
http://YOUR-ALB-DNS/docs
```

Simple query example:

```bash
curl -X POST "http://YOUR-ALB-DNS/api/v1/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "knowledge_base_id": "YOUR-KB-ID"
  }'
```

---
