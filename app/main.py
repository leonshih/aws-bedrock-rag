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

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AWS Bedrock RAG API",
    description="API for document management and RAG-based question answering using Amazon Bedrock",
    version="0.1.0"
)

logger.info(f"Starting AWS Bedrock RAG API (Log Level: {config.LOG_LEVEL})")

# Register global exception handlers
register_exception_handlers(app)

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
