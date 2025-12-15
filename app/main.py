"""
FastAPI application for AWS Bedrock RAG API
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routers.chat import router as chat_router

app = FastAPI(
    title="AWS Bedrock RAG API",
    description="API for document management and RAG-based question answering using Amazon Bedrock",
    version="0.1.0"
)

# Register routers
app.include_router(chat_router)

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
