"""
Bedrock Adapter

Low-level adapter for Amazon Bedrock Knowledge Base interactions.
"""
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError

from app.utils.config import get_config
from app.dtos.common import create_success_response, SuccessResponse
from app.dtos.adapters.bedrock import BedrockRAGResult, BedrockRetrievalReference, BedrockIngestionJobResult


class BedrockAdapter:
    """Adapter for Amazon Bedrock Agent Runtime API."""
    
    def __init__(self):
        """Initialize Bedrock adapter with AWS Bedrock client."""
        config = get_config()
        self.region = config.AWS_REGION
        self.model_id = config.BEDROCK_MODEL_ID
        self.client = boto3.client(
            'bedrock-agent-runtime',
            region_name=self.region
        )
    
    def retrieve_and_generate(
        self,
        query: str,
        kb_id: str,
        model_arn: Optional[str] = None,
        retrieval_config: Optional[Dict[str, dict]] = None
    ) -> SuccessResponse[BedrockRAGResult]:
        """
        Perform RAG query using Bedrock Knowledge Base.
        
        Args:
            query: User query string
            kb_id: Knowledge Base ID
            model_arn: Optional model ARN. If None, uses config model ID.
            retrieval_config: Optional retrieval configuration (e.g., metadata filters)
        
        Returns:
            Dict with success flag and BedrockRAGResult data containing answer, session_id, and references.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        # Use model_arn if provided, otherwise use model_id directly
        # For cross-region inference profiles, AWS expects the model ID, not full ARN
        # For standard regional models, both model ID and ARN work
        if not model_arn:
            model_arn = self.model_id
        
        try:
            kb_config = {
                'knowledgeBaseId': kb_id,
                'modelArn': model_arn
            }
            
            # Add retrieval configuration if provided
            if retrieval_config:
                kb_config['retrievalConfiguration'] = retrieval_config
            
            response = self.client.retrieve_and_generate(
                input={'text': query},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': kb_config
                }
            )
            
            # Parse response and create typed result
            answer = response.get('output', {}).get('text', '')
            session_id = response.get('sessionId', '')
            
            # Extract references from citations
            references = []
            for citation in response.get('citations', []):
                for ref in citation.get('retrievedReferences', []):
                    ref_obj = BedrockRetrievalReference(
                        content=ref.get('content', {}).get('text', ''),
                        s3_uri=ref.get('location', {}).get('s3Location', {}).get('uri', ''),
                        score=ref.get('metadata', {}).get('score')
                    )
                    references.append(ref_obj)
            
            result = BedrockRAGResult(
                answer=answer,
                session_id=session_id,
                references=references
            )
            return create_success_response(result)
        except ClientError as e:
            raise e
    
    def start_ingestion_job(
        self,
        kb_id: str,
        data_source_id: str
    ) -> SuccessResponse[BedrockIngestionJobResult]:
        """
        Start a Knowledge Base ingestion job (sync).
        
        Args:
            kb_id: Knowledge Base ID
            data_source_id: Data Source ID
        
        Returns:
            Dict with success flag and BedrockIngestionJobResult data.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        # Note: This uses bedrock-agent client, not bedrock-agent-runtime
        agent_client = boto3.client('bedrock-agent', region_name=self.region)
        
        try:
            response = agent_client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id
            )
            
            # Parse response and create typed result
            job_info = response.get('ingestionJob', {})
            result = BedrockIngestionJobResult(
                job_id=job_info.get('ingestionJobId', ''),
                status=job_info.get('status', 'UNKNOWN'),
                knowledge_base_id=job_info.get('knowledgeBaseId', kb_id),
                data_source_id=job_info.get('dataSourceId', data_source_id)
            )
            return create_success_response(result)
        except ClientError as e:
            raise e
