"""Chat router for RAG query endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Annotated

from app.dtos.routers.chat import ChatRequest, ChatResponse
from app.services.rag import RAGService
from app.adapters.bedrock import BedrockAdapter
from app.utils.config import Config
from app.middleware.tenant_middleware import get_tenant_context

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


def get_rag_service() -> RAGService:
    """Dependency injection for RAG service."""
    config = Config()
    return RAGService(config=config)


@router.post(
    "",
    summary="Query the Knowledge Base",
    description="""
    Send a query to the RAG system and receive an AI-generated answer with citations.
    
    **🔐 Multi-Tenant:** This endpoint requires `X-Tenant-ID` header for data isolation.
    All queries are automatically filtered to return only documents belonging to your tenant.
    
    **Features:**
    - Natural language queries
    - Automatic tenant-based data isolation
    - Optional metadata filtering (equals, not_equals, greater_than, less_than, contains)
    - Configurable result count (1-100)
    - Custom model selection
    - Source citations with relevance scores
    
    **Required Headers:**
    - `X-Tenant-ID`: Your tenant UUID (e.g., "550e8400-e29b-41d4-a716-446655440000")
    
    **Example Request:**
    ```json
    {
        "query": "What are the benefits of RAG?",
        "metadata_filters": [
            {"key": "category", "value": "documentation", "operator": "equals"}
        ],
        "max_results": 5
    }
    ```
    """,
    responses={
        200: {
            "description": "Successful response with answer and citations",
            "content": {
                "application/json": {
                    "example": {
                        "answer": "RAG combines retrieval and generation...",
                        "citations": [
                            {
                                "content": "RAG systems retrieve relevant documents...",
                                "document_title": "rag-guide.pdf",
                                "location": {"s3Location": {"uri": "s3://bucket/rag-guide.pdf"}},
                                "score": 0.95
                            }
                        ],
                        "session_id": "session-123",
                        "model_used": "anthropic.claude-3-5-sonnet-20241022-v2:0"
                    }
                }
            }
        },
        400: {"description": "Invalid request (empty query, invalid filters)"},
        500: {"description": "Server error (AWS service unavailable)"}
    }
)
async def query_knowledge_base(
    chat_request: ChatRequest,
    fastapi_request: Request,
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> dict:
    """
    Process a RAG query and return the answer with citations.
    
    Args:
        chat_request: Chat request containing query and optional filters
        fastapi_request: FastAPI request object (to access middleware state)
        rag_service: Injected RAG service instance
        
    Returns:
        Dict with success flag and ChatResponse data
        
    Raises:
        HTTPException: 400 for invalid requests, 500 for server errors
    """
    # Extract tenant_id from middleware (validated by TenantMiddleware)
    tenant_context = get_tenant_context(fastapi_request)
    
    # Pass tenant_id as separate parameter to service layer
    response = rag_service.query(chat_request, tenant_id=tenant_context.tenant_id)
    return response
