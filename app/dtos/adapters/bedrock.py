"""
Bedrock Adapter Response DTOs

Type-safe response models for Bedrock operations.
"""
from typing import Optional
from pydantic import BaseModel, Field


class BedrockRetrievalReference(BaseModel):
    """Reference to a retrieved document from Knowledge Base."""
    
    content: str = Field(description="Text content of the reference")
    s3_uri: str = Field(description="S3 URI of the source document")
    score: Optional[float] = Field(default=None, description="Relevance score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "RAG combines retrieval and generation...",
                "s3_uri": "s3://bucket/documents/rag-guide.pdf",
                "score": 0.95
            }
        }


class BedrockRAGResult(BaseModel):
    """Result of Bedrock RAG query operation."""
    
    answer: str = Field(description="Generated answer from the model")
    session_id: str = Field(description="Bedrock session ID for conversation tracking")
    references: list[BedrockRetrievalReference] = Field(
        default_factory=list,
        description="List of retrieved references used to generate the answer"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "RAG (Retrieval-Augmented Generation) combines...",
                "session_id": "session-abc123",
                "references": [
                    {
                        "content": "RAG systems retrieve relevant documents...",
                        "s3_uri": "s3://bucket/rag-guide.pdf",
                        "score": 0.95
                    }
                ]
            }
        }


class BedrockIngestionJobResult(BaseModel):
    """Result of starting a Bedrock Knowledge Base ingestion job."""
    
    job_id: str = Field(description="Unique identifier for the ingestion job")
    status: str = Field(description="Current status of the ingestion job")
    knowledge_base_id: str = Field(description="ID of the Knowledge Base")
    data_source_id: str = Field(description="ID of the data source")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "ingestion-job-abc123",
                "status": "STARTING",
                "knowledge_base_id": "KB12345",
                "data_source_id": "DS67890"
            }
        }
