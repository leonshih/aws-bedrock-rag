"""
RAG Service

Orchestrates retrieval-augmented generation using Bedrock Knowledge Base.
Handles query processing, metadata filtering, and citation parsing.
"""
import logging
from typing import List, Optional, Dict, Any
from app.adapters.bedrock import BedrockAdapter
from app.dtos.chat import ChatRequest, ChatResponse, Citation, MetadataFilter
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
        self.bedrock_adapter = BedrockAdapter(self.config)
    
    def query(
        self,
        request: ChatRequest
    ) -> ChatResponse:
        """
        Process a RAG query using Bedrock Knowledge Base.
        
        Args:
            request: Chat request with query and optional filters
            
        Returns:
            ChatResponse with generated answer and citations
        """
        logger.info(f"Processing RAG query: '{request.query[:100]}...', filters={len(request.metadata_filters or [])}, max_results={request.max_results}")
        
        # Build model ARN
        model_id = request.model_id or self.config.BEDROCK_MODEL_ID
        model_arn = f"arn:aws:bedrock:{self.config.AWS_REGION}::foundation-model/{model_id}"
        
        # Convert metadata filters to Bedrock format
        retrieval_config = None
        if request.metadata_filters:
            retrieval_config = self._build_retrieval_config(request.metadata_filters)
        
        # Call Bedrock adapter
        bedrock_response = self.bedrock_adapter.retrieve_and_generate(
            query=request.query,
            kb_id=self.config.BEDROCK_KB_ID,
            model_arn=model_arn,
            retrieval_config=retrieval_config
        )
        
        # Parse response and extract citations
        answer = self._extract_answer(bedrock_response)
        citations = self._parse_citations(bedrock_response)
        
        return ChatResponse(
            answer=answer,
            citations=citations,
            session_id=bedrock_response.get("sessionId"),
            model_used=model_id
        )
    
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
    
    def _extract_answer(self, bedrock_response: Dict[str, Any]) -> str:
        """
        Extract the generated answer from Bedrock response.
        
        Args:
            bedrock_response: Raw response from Bedrock adapter
            
        Returns:
            Generated answer text
        """
        # Navigate response structure: output -> text
        output = bedrock_response.get("output", {})
        return output.get("text", "")
    
    def _parse_citations(
        self,
        bedrock_response: Dict[str, Any]
    ) -> List[Citation]:
        """
        Parse citations from Bedrock response into Citation DTOs.
        
        Args:
            bedrock_response: Raw response from Bedrock adapter
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        # Navigate response structure: citations -> retrievedReferences
        raw_citations = bedrock_response.get("citations", [])
        
        for citation_item in raw_citations:
            # Each citation contains retrievedReferences
            retrieved_refs = citation_item.get("retrievedReferences", [])
            
            for ref in retrieved_refs:
                # Extract content
                content_data = ref.get("content", {})
                content_text = content_data.get("text", "")
                
                # Extract location info
                location_data = ref.get("location", {})
                s3_location = location_data.get("s3Location", {})
                
                # Extract document title from S3 URI
                uri = s3_location.get("uri", "")
                document_title = uri.split("/")[-1] if uri else None
                
                # Build location metadata
                location = {
                    "s3_uri": uri,
                    "type": location_data.get("type")
                }
                
                # Extract score if available
                score = ref.get("metadata", {}).get("score")
                
                citations.append(
                    Citation(
                        content=content_text,
                        document_title=document_title,
                        location=location,
                        score=score
                    )
                )
        
        return citations
