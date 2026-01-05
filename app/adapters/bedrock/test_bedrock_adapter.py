"""
Unit tests for Bedrock Adapter
"""
import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from app.adapters.bedrock import BedrockAdapter


class TestBedrockAdapter:
    """Test cases for BedrockAdapter with mocked boto3 client."""
    
    @pytest.fixture
    def mock_bedrock_runtime_client(self):
        """Create a mock bedrock-agent-runtime client."""
        return Mock()
    
    @pytest.fixture
    def adapter(self, mock_bedrock_runtime_client):
        """Create a Bedrock adapter instance with mocked boto3 client."""
        with patch('boto3.client', return_value=mock_bedrock_runtime_client):
            return BedrockAdapter()
    
    def test_initialization(self, adapter, mock_bedrock_runtime_client):
        """Test adapter initializes correctly with boto3 client."""
        assert adapter.client is not None
        assert adapter.client == mock_bedrock_runtime_client
        assert adapter.region is not None
        assert adapter.model_id is not None
    
    def test_initialization_creates_bedrock_client(self):
        """Test adapter creates bedrock-agent-runtime client on init."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_boto.return_value = mock_client
            
            adapter = BedrockAdapter()
            
            mock_boto.assert_called_once_with(
                'bedrock-agent-runtime',
                region_name=adapter.region
            )
            assert adapter.client == mock_client
    
    def test_retrieve_and_generate_success(self, adapter, mock_bedrock_runtime_client):
        """Test retrieve_and_generate with successful AWS response."""
        query = "What is AWS Bedrock?"
        kb_id = "test-kb-id"
        
        # Mock AWS response
        mock_bedrock_runtime_client.retrieve_and_generate.return_value = {
            'output': {
                'text': 'AWS Bedrock is a fully managed service.'
            },
            'sessionId': 'session-123',
            'citations': [
                {
                    'retrievedReferences': [
                        {
                            'content': {'text': 'Reference content 1'},
                            'location': {'s3Location': {'uri': 's3://bucket/doc1.pdf'}},
                            'metadata': {'score': 0.95}
                        },
                        {
                            'content': {'text': 'Reference content 2'},
                            'location': {'s3Location': {'uri': 's3://bucket/doc2.pdf'}},
                            'metadata': {'score': 0.88}
                        }
                    ]
                }
            ]
        }
        
        response = adapter.retrieve_and_generate(query, kb_id)
        
        # Verify API call
        mock_bedrock_runtime_client.retrieve_and_generate.assert_called_once()
        call_args = mock_bedrock_runtime_client.retrieve_and_generate.call_args[1]
        assert call_args['input']['text'] == query
        assert call_args['retrieveAndGenerateConfiguration']['knowledgeBaseConfiguration']['knowledgeBaseId'] == kb_id
        
        # Verify response structure (direct DTO access)
        assert response.answer == 'AWS Bedrock is a fully managed service.'
        assert response.session_id == 'session-123'
        assert len(response.references) == 2
        
        # Verify references
        assert response.references[0].content == 'Reference content 1'
        assert response.references[0].s3_uri == 's3://bucket/doc1.pdf'
        assert response.references[0].score == 0.95
        assert response.references[1].score == 0.88
    
    def test_retrieve_and_generate_with_custom_model_arn(self, adapter, mock_bedrock_runtime_client):
        """Test retrieve_and_generate uses custom model ARN when provided."""
        query = "Test query"
        kb_id = "test-kb-id"
        custom_model = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-v2"
        
        mock_bedrock_runtime_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Answer'},
            'sessionId': 'session-456',
            'citations': []
        }
        
        adapter.retrieve_and_generate(query, kb_id, model_arn=custom_model)
        
        call_args = mock_bedrock_runtime_client.retrieve_and_generate.call_args[1]
        kb_config = call_args['retrieveAndGenerateConfiguration']['knowledgeBaseConfiguration']
        assert kb_config['modelArn'] == custom_model
    
    def test_retrieve_and_generate_uses_default_model(self, adapter, mock_bedrock_runtime_client):
        """Test retrieve_and_generate uses default model_id when model_arn not provided."""
        query = "Test query"
        kb_id = "test-kb-id"
        
        mock_bedrock_runtime_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Answer'},
            'sessionId': 'session-default',
            'citations': []
        }
        
        adapter.retrieve_and_generate(query, kb_id)
        
        call_args = mock_bedrock_runtime_client.retrieve_and_generate.call_args[1]
        kb_config = call_args['retrieveAndGenerateConfiguration']['knowledgeBaseConfiguration']
        assert kb_config['modelArn'] == adapter.model_id
    
    def test_retrieve_and_generate_with_retrieval_config(self, adapter, mock_bedrock_runtime_client):
        """Test retrieve_and_generate includes retrieval configuration when provided."""
        query = "Test query"
        kb_id = "test-kb-id"
        retrieval_config = {
            'vectorSearchConfiguration': {
                'numberOfResults': 10,
                'filter': {'equals': {'key': 'tenant_id', 'value': 'tenant-123'}}
            }
        }
        
        mock_bedrock_runtime_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Answer'},
            'sessionId': 'session-789',
            'citations': []
        }
        
        adapter.retrieve_and_generate(query, kb_id, retrieval_config=retrieval_config)
        
        call_args = mock_bedrock_runtime_client.retrieve_and_generate.call_args[1]
        kb_config = call_args['retrieveAndGenerateConfiguration']['knowledgeBaseConfiguration']
        assert 'retrievalConfiguration' in kb_config
        assert kb_config['retrievalConfiguration'] == retrieval_config
    
    def test_retrieve_and_generate_handles_empty_citations(self, adapter, mock_bedrock_runtime_client):
        """Test retrieve_and_generate handles response with no citations."""
        query = "Test query"
        kb_id = "test-kb-id"
        
        mock_bedrock_runtime_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Answer without citations'},
            'sessionId': 'session-no-citations',
            'citations': []
        }
        
        response = adapter.retrieve_and_generate(query, kb_id)
        
        # Direct DTO access
        assert response.answer == 'Answer without citations'
        assert len(response.references) == 0
    
    def test_retrieve_and_generate_handles_missing_score(self, adapter, mock_bedrock_runtime_client):
        """Test retrieve_and_generate handles references without score."""
        query = "Test query"
        kb_id = "test-kb-id"
        
        mock_bedrock_runtime_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Answer'},
            'sessionId': 'session-no-score',
            'citations': [
                {
                    'retrievedReferences': [
                        {
                            'content': {'text': 'Content without score'},
                            'location': {'s3Location': {'uri': 's3://bucket/doc.pdf'}},
                            'metadata': {}  # No score
                        }
                    ]
                }
            ]
        }
        
        response = adapter.retrieve_and_generate(query, kb_id)
        
        # Direct DTO access
        assert len(response.references) == 1
        assert response.references[0].score is None
    
    def test_retrieve_and_generate_client_error_propagates(self, adapter, mock_bedrock_runtime_client):
        """Test retrieve_and_generate propagates ClientError."""
        query = "Test query"
        kb_id = "test-kb-id"
        
        # Mock ClientError
        error_response = {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}}
        mock_bedrock_runtime_client.retrieve_and_generate.side_effect = ClientError(
            error_response, 'RetrieveAndGenerate'
        )
        
        with pytest.raises(ClientError) as exc_info:
            adapter.retrieve_and_generate(query, kb_id)
        
        assert exc_info.value.response['Error']['Code'] == 'AccessDeniedException'
    
    def test_start_ingestion_job_success(self):
        """Test start_ingestion_job with successful AWS response."""
        kb_id = "test-kb-id"
        data_source_id = "test-ds-id"
        
        # Mock the bedrock-agent client (different from bedrock-agent-runtime)
        mock_agent_client = Mock()
        mock_agent_client.start_ingestion_job.return_value = {
            'ingestionJob': {
                'ingestionJobId': 'job-123',
                'status': 'STARTING',
                'knowledgeBaseId': kb_id,
                'dataSourceId': data_source_id
            }
        }
        
        with patch('boto3.client') as mock_boto:
            # First call returns runtime client, second call returns agent client
            mock_boto.side_effect = [Mock(), mock_agent_client]
            
            adapter = BedrockAdapter()
            response = adapter.start_ingestion_job(kb_id, data_source_id)
        
        # Verify API call
        mock_agent_client.start_ingestion_job.assert_called_once_with(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )
        
        # Verify response (direct DTO access)
        assert response.job_id == 'job-123'
        assert response.status == 'STARTING'
        assert response.knowledge_base_id == kb_id
        assert response.data_source_id == data_source_id
    
    def test_start_ingestion_job_client_error_propagates(self):
        """Test start_ingestion_job propagates ClientError."""
        kb_id = "test-kb-id"
        data_source_id = "test-ds-id"
        
        # Mock the bedrock-agent client
        mock_agent_client = Mock()
        error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'KB not found'}}
        mock_agent_client.start_ingestion_job.side_effect = ClientError(
            error_response, 'StartIngestionJob'
        )
        
        with patch('boto3.client') as mock_boto:
            # First call returns runtime client, second call returns agent client
            mock_boto.side_effect = [Mock(), mock_agent_client]
            
            adapter = BedrockAdapter()
            
            with pytest.raises(ClientError) as exc_info:
                adapter.start_ingestion_job(kb_id, data_source_id)
        
        assert exc_info.value.response['Error']['Code'] == 'ResourceNotFoundException'
    
    def test_multiple_queries_use_same_client(self, adapter, mock_bedrock_runtime_client):
        """Test multiple queries reuse the same boto3 client instance."""
        kb_id = "test-kb-id"
        
        mock_bedrock_runtime_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Answer'},
            'sessionId': 'session-multi',
            'citations': []
        }
        
        # Make multiple calls
        adapter.retrieve_and_generate("Query 1", kb_id)
        adapter.retrieve_and_generate("Query 2", kb_id)
        adapter.retrieve_and_generate("Query 3", kb_id)
        
        # Verify same client instance used
        assert mock_bedrock_runtime_client.retrieve_and_generate.call_count == 3
        assert adapter.client == mock_bedrock_runtime_client
