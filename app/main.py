"""
FastAPI application for AWS Bedrock RAG API
"""
import logging
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routers.chat import router as chat_router
from app.routers.ingest import router as ingest_router
from app.middleware.exception_handlers import register_exception_handlers
from app.middleware.tenant_middleware import TenantMiddleware
from app.utils.config import Config

# Load configuration
config = Config()

# Configure logging
log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

# Create console handler with formatting
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)
console_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(console_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.addHandler(console_handler)

# Suppress noisy third-party loggers
logging.getLogger('python_multipart').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AWS Bedrock RAG API",
    description="""
    API for document management and RAG-based question answering using Amazon Bedrock.
    
    ## 🔐 Multi-Tenant Architecture
    
    This API implements **tenant-based data isolation**. All endpoints require the `X-Tenant-ID` header 
    containing a valid UUID v4 identifier.
    
    **Key Features:**
    - **Automatic Data Isolation**: Documents and queries are isolated per tenant
    - **S3 Path Isolation**: Files stored in `documents/{tenant_id}/` 
    - **Query Filtering**: RAG queries automatically filtered by tenant_id
    - **UUID Validation**: Tenant IDs validated at middleware layer
    
    **Required Header:**
    - `X-Tenant-ID`: Your tenant UUID (format: `550e8400-e29b-41d4-a716-446655440000`)
    
    **Errors:**
    - `400 Bad Request`: Missing or invalid tenant ID
    - `422 Unprocessable Entity`: Invalid UUID format
    
    ## 🚀 Getting Started
    
    1. Obtain your tenant UUID from your administrator
    2. Include `X-Tenant-ID` header in all API requests
    3. Upload documents to `/files` endpoint
    4. Query your documents via `/chat` endpoint
    """,
    version="0.1.0"
)

logger.info(f"Starting AWS Bedrock RAG API (Log Level: {config.LOG_LEVEL})")

# Register global exception handlers
register_exception_handlers(app)

# Register tenant middleware
app.add_middleware(TenantMiddleware)

# Register routers
app.include_router(chat_router)
app.include_router(ingest_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(
        content={
            "message": "Hello from AWS Bedrock RAG API!",
            "status": "running",
            "version": "0.1.0"
        }
    )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy"
        }
    )
