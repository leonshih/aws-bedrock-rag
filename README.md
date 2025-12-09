# AWS Bedrock RAG API

![AWS](https://img.shields.io/badge/AWS-Powered-FF9900?logo=aws&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker&logoColor=white)
![AWS CDK](https://img.shields.io/badge/IaC-AWS%20CDK-orange)
![Status](https://img.shields.io/badge/Status-Development-yellow)

A production-ready Retrieval-Augmented Generation (RAG) system designed for AWS.

This project utilizes **Knowledge Bases for Amazon Bedrock** to manage the RAG pipeline (Ingestion, Embedding, Retrieval) and hosts the **FastAPI** backend on **Amazon ECS (Fargate)**.

**📚 Documentation:**

- [Architecture Overview](ARCHITECTURE.md) - System design and component details
- [Deployment Guide](DEPLOYMENT.md) - Step-by-step deployment instructions
- [API Examples](API_EXAMPLES.md) - Complete API usage guide with code examples
- [Next Steps](NEXT_STEPS.md) - Future enhancements and roadmap
- [CI/CD Setup](.github/CICD_SETUP.md) - GitHub Actions configuration guide

---

## 🚦 Current Status

> **Last Updated:** 2025-12-08
> **Current Phase:** 🟡 Phase 1 - Infrastructure & Implementation

| Module                   | Status       | Notes                                           |
| :----------------------- | :----------- | :---------------------------------------------- |
| **Infrastructure (CDK)** | 🟢 Completed | VPC, ECS, ALB, S3, OpenSearch Serverless ready. |
| **RAG Pipeline**         | 🟡 Partial   | S3 and OpenSearch ready; KB needs manual setup. |
| **Backend API**          | 🟢 Completed | FastAPI with Bedrock integration implemented.   |
| **CI/CD**                | 🟡 Partial   | GitHub Actions workflow ready; needs secrets.   |
| **Monitoring**           | 🟡 Partial   | CloudWatch Logs enabled; dashboards pending.    |

---

## 🗺 Development Roadmap

This roadmap follows a **Layered Architecture** approach. Phases 1-3 focus on **CDK Implementation**, while Phase 4 focuses on **Application Logic**.

### Phase 1: Network Foundation (CDK: Network Stack)

**Goal:** Implement the network layer using AWS CDK.

- [ ] **Project Init**: Initialize CDK Monorepo structure and virtual environment.
- [ ] **CDK Network Stack**: Write CDK code to define a VPC with Public/Private Subnets and NAT Gateways.
- [ ] **Security Groups**: Implement Security Groups for ALB (Public) and Fargate (Private) in CDK.

### Phase 2: RAG Data Pipeline (CDK: Data Stack)

**Goal:** Implement the data storage and retrieval layer using AWS CDK.

- [ ] **S3 & OpenSearch**: Write CDK code to provision the S3 Bucket and OpenSearch Serverless Collection.
- [ ] **Bedrock Knowledge Base**: Implement `CfnKnowledgeBase` in CDK to connect S3 and OpenSearch.
- [ ] **IAM Policies**: Define CDK permissions allowing Bedrock to access S3 and OpenSearch.
- [ ] **Verification**: Manual sync test via AWS Console to ensure the stack works.

### Phase 3: Compute & Hosting (CDK: Compute Stack)

**Goal:** Implement the container hosting environment using AWS CDK.

- [ ] **ECR Repository**: Add ECR repository definition to CDK.
- [ ] **Dockerization**: Create a dummy `Dockerfile` (Hello World) for initial infrastructure testing.
- [ ] **ECS Cluster**: Write CDK code to define the ECS Cluster and Fargate Task Definition.
- [ ] **ALB & Service**: Implement `ApplicationLoadBalancedFargateService` pattern in CDK.
- [ ] **Connectivity**: Validate that the Fargate service can reach Bedrock APIs (via NAT).

### Phase 4: Backend Implementation (Application Layer)

**Goal:** Develop the FastAPI application logic (Python).

- [ ] **FastAPI Dev**: Replace dummy Docker image with actual `main.py` logic.
- [ ] **Bedrock Integration**: Implement `boto3` client logic to call `retrieve_and_generate`.
- [ ] **API Logic**: Define Pydantic models (Request/Response schemas).
- [ ] **Deployment**: Deploy the full application image to ECS.

### Phase 5: Production Readiness (Optimization)

**Goal:** Optimize for production traffic.

- [ ] **Streaming**: Implement Server-Sent Events (SSE) for token streaming.
- [ ] **Auto-Scaling**: Update CDK to include Auto Scaling policies.
- [ ] **CI/CD**: Set up GitHub Actions for automated CDK deploy and Docker build.

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
pip install -r requirements.txt

# 3. Deploy to AWS
npx cdk bootstrap  # First time only
npx cdk deploy

# 4. Create Knowledge Base (manual step via AWS Console)
# 5. Upload documents to S3 and sync
```

📖 **Detailed Guides:**

- [Complete Deployment Guide](DEPLOYMENT.md)
- [API Usage Examples](API_EXAMPLES.md)

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
