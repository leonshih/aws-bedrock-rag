# AWS Bedrock RAG API

![AWS](https://img.shields.io/badge/AWS-Powered-FF9900?logo=aws&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker&logoColor=white)
![AWS CDK](https://img.shields.io/badge/IaC-AWS%20CDK-orange)
![Status](https://img.shields.io/badge/Status-Planning-lightgrey)

A Retrieval-Augmented Generation (RAG) system designed for AWS.

This project utilizes **Knowledge Bases for Amazon Bedrock** to manage the RAG pipeline (Ingestion, Embedding, Retrieval) and hosts the **FastAPI** backend on **Amazon ECS (Fargate)**.

---

## 🚦 Current Status

> **Last Updated:** 2025-12-08
> **Current Phase:** ⚪ Phase 0 - Planning & Initialization

| Module                   | Status         | Notes                                            |
| :----------------------- | :------------- | :----------------------------------------------- |
| **Infrastructure (CDK)** | 🔴 Not Started | Architecture design finalized; CDK init pending. |
| **RAG Pipeline**         | 🔴 Not Started | Knowledge Base and S3 bucket to be provisioned.  |
| **Backend API**          | 🔴 Not Started | FastAPI skeleton and Dockerfile to be created.   |
| **CI/CD**                | 🔴 Not Started | GitHub Actions workflow pending.                 |
| **Monitoring**           | 🔴 Not Started | CloudWatch integration pending.                  |

---

## 🗺 Development Roadmap

This roadmap outlines the step-by-step implementation plan.

### Phase 1: Infrastructure & Networking (Week 1) - ⏳ Pending

- [ ] **Project Init**: Initialize Monorepo structure (`infra/` + `app/`).
- [ ] **Network Setup**: Define VPC, Public/Private Subnets, and Security Groups in CDK.
- [ ] **RAG Core**: Provision S3 Bucket, OpenSearch Serverless, and Bedrock Knowledge Base.
- [ ] **IAM Roles**: Define Task Execution Roles for ECS to access Bedrock and CloudWatch.

### Phase 2: Backend & Containerization (Week 2) - ⏳ Pending

- [ ] **Dockerization**: Write `Dockerfile` for the FastAPI application.
- [ ] **ECS Cluster**: Define ECS Cluster and Fargate Service in CDK.
- [ ] **Load Balancing**: Configure Application Load Balancer (ALB) and Target Groups.
- [ ] **API Logic**: Implement `retrieve_and_generate` logic using `boto3`.

### Phase 3: Optimization (Week 3) - ⏳ Pending

- [ ] **Streaming Support**: Implement Server-Sent Events (SSE) for token streaming response.
- [ ] **Prompt Engineering**: Refine System Prompts within Bedrock.
- [ ] **Hybrid Search**: Tune OpenSearch parameters for better retrieval accuracy.

### Phase 4: Production Readiness (Week 4) - ⏳ Pending

- [ ] **Auto-Scaling**: Configure ECS Service Auto Scaling based on CPU/Memory usage.
- [ ] **Security**: Implement WAF (Web Application Firewall) in front of ALB.
- [ ] **CI/CD**: Set up pipeline to build Docker image -> Push to ECR -> Update ECS Service.

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

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for AWS CDK CLI)
- **Docker** (MUST be running to build the image)
- **AWS CLI** (Configured via `aws configure`)

### 1. Installation

```bash
# Clone repository
git clone [https://github.com/your-org/aws-bedrock-rag-api.git](https://github.com/your-org/aws-bedrock-rag-api.git)
cd aws-bedrock-rag-api

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Deployment (CDK)

Deploying to ECS involves building a Docker image and provisioning a VPC/ALB, which takes longer than Lambda deployments.

```bash
# Bootstrap CDK (First time only)
npx cdk bootstrap

# Deploy Stack
npx cdk deploy
```

> ⏳ **Note:** The initial deployment may take **15-20 minutes** due to the provisioning of the VPC, NAT Gateways, OpenSearch Collection, and the Application Load Balancer.

After deployment, CDK will output the **ALB DNS Name** (e.g., `http://RagSt-FastA-JV8...@aws.com`).

### 3. Data Ingestion

1. Upload PDF/Docx files to the created S3 Bucket.
2. Navigate to AWS Console -> **Amazon Bedrock** -> **Knowledge bases**.
3. Select your Knowledge Base and click **"Sync"**.

---
