"""
Chat DTOs for RAG interactions

Defines request/response models for the chat/query endpoint.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MetadataFilter(BaseModel):
    """Metadata filter for search queries."""
    
    key: str = Field(..., description="Metadata attribute key to filter on")
    value: Any = Field(..., description="Value to match")
    operator: str = Field(
        default="equals",
        description="Comparison operator: equals, not_equals, greater_than, less_than, contains"
    )


class Citation(BaseModel):
    """Source citation from Bedrock response."""
    
    content: str = Field(..., description="Retrieved text snippet")
    document_id: Optional[str] = Field(None, description="Source document identifier")
    document_title: Optional[str] = Field(None, description="Document title or filename")
    location: Optional[Dict[str, Any]] = Field(None, description="Location metadata (S3 URI, page number, etc.)")
    score: Optional[float] = Field(None, description="Relevance score")


class ChatRequest(BaseModel):
    """Request model for chat/query endpoint."""
    
    query: str = Field(..., min_length=1, description="User's question or query text")
    metadata_filters: Optional[List[MetadataFilter]] = Field(
        default=None,
        description="Optional metadata filters to narrow search scope"
    )
    model_id: Optional[str] = Field(
        default=None,
        description="Override default Bedrock model (e.g., anthropic.claude-3-5-sonnet-20241022-v2:0)"
    )
    max_results: Optional[int] = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of documents to retrieve"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the side effects of aspirin?",
                "metadata_filters": [
                    {
                        "key": "year",
                        "value": 2020,
                        "operator": "greater_than"
                    }
                ],
                "max_results": 5
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat/query endpoint."""
    
    success: bool = Field(default=True, description="Operation success status")
    answer: str = Field(..., description="Generated answer from the LLM")
    citations: List[Citation] = Field(
        default_factory=list,
        description="Source documents used to generate the answer"
    )
    session_id: Optional[str] = Field(None, description="Conversation session identifier")
    model_used: Optional[str] = Field(None, description="Bedrock model that generated the response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "answer": "Aspirin's common side effects include stomach upset, heartburn, and increased bleeding risk.",
                "citations": [
                    {
                        "content": "Aspirin can cause gastrointestinal irritation...",
                        "document_title": "aspirin_guide_2023.pdf",
                        "score": 0.95
                    }
                ],
                "model_used": "anthropic.claude-3-5-sonnet-20241022-v2:0"
            }
        }
