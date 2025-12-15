"""
Bedrock Adapter

Low-level adapter for Amazon Bedrock Knowledge Base interactions.
"""
import json
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

from app.utils.config import get_config


class BedrockAdapter:
    """Adapter for Amazon Bedrock Agent Runtime API."""
    
    def __init__(self, mock_mode: Optional[bool] = None):
        """
        Initialize Bedrock adapter.
        
        Args:
            mock_mode: Override config mock mode. If None, uses config value.
        """
        config = get_config()
        self.mock_mode = mock_mode if mock_mode is not None else config.is_mock_enabled()
        self.region = config.AWS_REGION
        self.model_id = config.BEDROCK_MODEL_ID
        
        if not self.mock_mode:
            self.client = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region
            )
        else:
            self.client = None
    
    def retrieve_and_generate(
        self,
        query: str,
        kb_id: str,
        model_arn: Optional[str] = None,
        retrieval_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform RAG query using Bedrock Knowledge Base.
        
        Args:
            query: User query string
            kb_id: Knowledge Base ID
            model_arn: Optional model ARN. If None, uses config model ID.
            retrieval_config: Optional retrieval configuration (e.g., metadata filters)
        
        Returns:
            Dict containing the response with answer and citations.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        if self.mock_mode:
            return self._mock_retrieve_and_generate(query, kb_id)
        
        if not model_arn:
            model_arn = f"arn:aws:bedrock:{self.region}::foundation-model/{self.model_id}"
        
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
            return response
        except ClientError as e:
            raise e
    
    def start_ingestion_job(
        self,
        kb_id: str,
        data_source_id: str
    ) -> Dict[str, Any]:
        """
        Start a Knowledge Base ingestion job (sync).
        
        Args:
            kb_id: Knowledge Base ID
            data_source_id: Data Source ID
        
        Returns:
            Dict containing ingestion job details.
        
        Raises:
            ClientError: If AWS API call fails.
        """
        if self.mock_mode:
            return self._mock_start_ingestion_job(kb_id, data_source_id)
        
        # Note: This uses bedrock-agent client, not bedrock-agent-runtime
        agent_client = boto3.client('bedrock-agent', region_name=self.region)
        
        try:
            response = agent_client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id
            )
            return response
        except ClientError as e:
            raise e
    
    def _mock_retrieve_and_generate(
        self,
        query: str,
        kb_id: str
    ) -> Dict[str, Any]:
        """Mock implementation for local testing."""
        return {
            'ResponseMetadata': {
                'RequestId': 'mock-request-id',
                'HTTPStatusCode': 200
            },
            'sessionId': 'mock-session-id',
            'output': {
                'text': f'Mock response for query: "{query}". This is a simulated answer from the Knowledge Base.'
            },
            'citations': [
                {
                    'generatedResponsePart': {
                        'textResponsePart': {
                            'text': 'Mock response',
                            'span': {'start': 0, 'end': 13}
                        }
                    },
                    'retrievedReferences': [
                        {
                            'content': {
                                'text': 'This is mock reference content from the knowledge base.'
                            },
                            'location': {
                                's3Location': {
                                    'uri': f's3://mock-bucket/mock-document.pdf'
                                }
                            },
                            'metadata': {
                                'x-amz-bedrock-kb-source-uri': 'mock-source-uri'
                            }
                        }
                    ]
                }
            ]
        }
    
    def _mock_start_ingestion_job(
        self,
        kb_id: str,
        data_source_id: str
    ) -> Dict[str, Any]:
        """Mock implementation for local testing."""
        return {
            'ResponseMetadata': {
                'RequestId': 'mock-request-id',
                'HTTPStatusCode': 200
            },
            'ingestionJob': {
                'knowledgeBaseId': kb_id,
                'dataSourceId': data_source_id,
                'ingestionJobId': 'mock-ingestion-job-id',
                'status': 'STARTING'
            }
        }
