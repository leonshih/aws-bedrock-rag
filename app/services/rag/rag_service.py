"""
RAG Service

Orchestrates retrieval-augmented generation using Bedrock Knowledge Base.
Handles query processing, metadata filtering, and citation parsing.
"""
import logging
from typing import List, Optional, Dict, Any
from app.adapters.bedrock import BedrockAdapter
from app.dtos.routers.chat import ChatRequest, ChatResponse, Citation, MetadataFilter
from app.utils.config import Config

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based query processing."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize RAG service.
        
        Args:
            config: Configuration object (uses default if not provided)
        """
        self.config = config or Config()
        self.bedrock_adapter = BedrockAdapter()
    
    def query(
        self,
        request: ChatRequest
    ) -> dict:
        """
        Process a RAG query using Bedrock Knowledge Base.
        
        Args:
            request: Chat request with query and optional filters
            
        Returns:
            Dict with success flag and ChatResponse data
        """
        logger.info(f"Processing RAG query: '{request.query[:100]}...', filters={len(request.metadata_filters or [])}, max_results={request.max_results}")
        
        # Use model ID directly (supports both inference profiles and direct model IDs)
        # For inference profiles: us.anthropic.claude-3-5-sonnet-20241022-v2:0
        # For direct models: anthropic.claude-3-opus-20240229-v1:0
        model_id = request.model_id or self.config.BEDROCK_MODEL_ID
        
        # Convert metadata filters to Bedrock format
        retrieval_config = None
        if request.metadata_filters:
            retrieval_config = self._build_retrieval_config(request.metadata_filters)
        
        # Call Bedrock adapter
        bedrock_response = self.bedrock_adapter.retrieve_and_generate(
            query=request.query,
            kb_id=self.config.BEDROCK_KB_ID,
            model_arn=model_id,  # Pass model_id directly, adapter will handle it
            retrieval_config=retrieval_config
        )
        
        # Extract Bedrock result from adapter response
        bedrock_result = bedrock_response["data"]
        
        # Convert Bedrock references to Citations
        citations = [
            Citation(
                content=ref.content,
                document_title=ref.s3_uri.split("/")[-1] if ref.s3_uri else None,
                location={"s3_uri": ref.s3_uri, "type": "s3"},
                score=ref.score
            )
            for ref in bedrock_result.references
        ]
        
        return {
            "success": True,
            "data": ChatResponse(
                answer=bedrock_result.answer,
                citations=citations,
                session_id=bedrock_result.session_id,
                model_used=model_id
            )
        }
    
    def _build_retrieval_config(
        self,
        filters: List[MetadataFilter]
    ) -> Dict[str, Any]:
        """
        Convert metadata filters to Bedrock retrieval configuration.
        
        Args:
            filters: List of metadata filters from request
            
        Returns:
            Bedrock-compatible retrieval configuration
        """
        if not filters:
            return {}
        
        # Build filter expressions for OpenSearch
        filter_expressions = []
        for f in filters:
            filter_expr = self._build_filter_expression(f)
            if filter_expr:
                filter_expressions.append(filter_expr)
        
        if not filter_expressions:
            return {}
        
        # Combine multiple filters with AND logic
        if len(filter_expressions) == 1:
            combined_filter = filter_expressions[0]
        else:
            combined_filter = {
                "andAll": filter_expressions
            }
        
        return {
            "vectorSearchConfiguration": {
                "filter": combined_filter
            }
        }
    
    def _build_filter_expression(
        self,
        filter_obj: MetadataFilter
    ) -> Optional[Dict[str, Any]]:
        """
        Build a single filter expression for OpenSearch.
        
        Args:
            filter_obj: Metadata filter object
            
        Returns:
            OpenSearch filter expression or None if invalid
        """
        key = filter_obj.key
        value = filter_obj.value
        operator = filter_obj.operator
        
        # Map operators to OpenSearch filter format
        if operator == "equals":
            return {
                "equals": {
                    "key": key,
                    "value": value
                }
            }
        elif operator == "not_equals":
            return {
                "notEquals": {
                    "key": key,
                    "value": value
                }
            }
        elif operator == "greater_than":
            return {
                "greaterThan": {
                    "key": key,
                    "value": value
                }
            }
        elif operator == "less_than":
            return {
                "lessThan": {
                    "key": key,
                    "value": value
                }
            }
        elif operator == "contains":
            # For string contains, use stringContains
            return {
                "stringContains": {
                    "key": key,
                    "value": str(value)
                }
            }
        else:
            # Unknown operator, skip this filter
            return None
    

