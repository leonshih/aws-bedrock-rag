"""Chat router for RAG query endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated

from app.dtos.chat import ChatRequest, ChatResponse
from app.services.rag import RAGService
from app.adapters.bedrock import BedrockAdapter
from app.utils.config import Config

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
    response_model=ChatResponse,
    summary="Query the Knowledge Base",
    description="""
    Send a query to the RAG system and receive an AI-generated answer with citations.
    
    **Features:**
    - Natural language queries
    - Optional metadata filtering (equals, not_equals, greater_than, less_than, contains)
    - Configurable result count (1-100)
    - Custom model selection
    - Source citations with relevance scores
    
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
    request: ChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> ChatResponse:
    """
    Process a RAG query and return the answer with citations.
    
    Args:
        request: Chat request containing query and optional filters
        rag_service: Injected RAG service instance
        
    Returns:
        ChatResponse with answer, citations, session_id, and model_used
        
    Raises:
        HTTPException: 400 for invalid requests, 500 for server errors
    """
    response = rag_service.query(request)
    return response
