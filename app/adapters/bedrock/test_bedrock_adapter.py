"""
Unit tests for Bedrock Adapter
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from app.adapters.bedrock import BedrockAdapter


class TestBedrockAdapter:
    """Test cases for BedrockAdapter in mock mode."""
    
    @pytest.fixture
    def adapter(self):
        """Create a mock Bedrock adapter instance."""
        return BedrockAdapter(mock_mode=True)
    
    def test_initialization_mock_mode(self, adapter):
        """Test adapter initializes correctly in mock mode."""
        assert adapter.mock_mode is True
        assert adapter.client is None
        assert adapter.region is not None
        assert adapter.model_id is not None
    
    def test_retrieve_and_generate_returns_response(self, adapter):
        """Test retrieve_and_generate returns proper response structure."""
        query = "What is AWS Bedrock?"
        kb_id = "test-kb-id"
        
        response = adapter.retrieve_and_generate(query, kb_id)
        
        # Verify wrapper structure
        assert response["success"] is True
        assert "data" in response
        
        # Verify data structure
        data = response["data"]
        assert hasattr(data, "answer")
        assert hasattr(data, "session_id")
        assert hasattr(data, "references")
        
        # Verify content
        assert query in data.answer
        assert data.session_id == "mock-session-id"
        assert len(data.references) > 0
    
    def test_retrieve_and_generate_with_custom_model(self, adapter):
        """Test retrieve_and_generate accepts custom model ARN."""
        query = "Test query"
        kb_id = "test-kb-id"
        model_arn = "arn:aws:bedrock:us-east-1::foundation-model/custom-model"
        
        response = adapter.retrieve_and_generate(query, kb_id, model_arn)
        
        # In mock mode, should still return valid response
        assert response is not None
        assert response["success"] is True
        assert "data" in response
    
    def test_retrieve_and_generate_citations_structure(self, adapter):
        """Test citations have proper structure."""
        query = "Test query"
        kb_id = "test-kb-id"
        
        response = adapter.retrieve_and_generate(query, kb_id)
        
        data = response["data"]
        references = data.references
        assert len(references) > 0
        
        first_ref = references[0]
        assert hasattr(first_ref, "content")
        assert hasattr(first_ref, "s3_uri")
        assert hasattr(first_ref, "score")
        assert first_ref.content is not None
        assert first_ref.s3_uri is not None
    
    def test_start_ingestion_job_returns_response(self, adapter):
        """Test start_ingestion_job returns proper response structure."""
        kb_id = "test-kb-id"
        data_source_id = "test-ds-id"
        
        response = adapter.start_ingestion_job(kb_id, data_source_id)
        
        # Verify wrapper structure
        assert response["success"] is True
        assert "data" in response
        
        # Verify data structure
        data = response["data"]
        assert hasattr(data, "job_id")
        assert hasattr(data, "status")
        assert hasattr(data, "knowledge_base_id")
        assert hasattr(data, "data_source_id")
        assert data.knowledge_base_id == kb_id
        assert data.data_source_id == data_source_id
    
    def test_start_ingestion_job_status(self, adapter):
        """Test ingestion job returns valid status."""
        kb_id = "test-kb-id"
        data_source_id = "test-ds-id"
        
        response = adapter.start_ingestion_job(kb_id, data_source_id)
        
        status = response["data"].status
        valid_statuses = ['STARTING', 'IN_PROGRESS', 'COMPLETE', 'FAILED']
        assert status in valid_statuses
    
    def test_multiple_queries_independent(self, adapter):
        """Test multiple queries return independent responses."""
        query1 = "First query"
        query2 = "Second query"
        kb_id = "test-kb-id"
        
        response1 = adapter.retrieve_and_generate(query1, kb_id)
        response2 = adapter.retrieve_and_generate(query2, kb_id)
        
        # Responses should be different
        data1 = response1["data"]
        data2 = response2["data"]
        assert data1.session_id == data2.session_id  # Mock uses same session
        assert query1 in data1.answer
        assert query2 in data2.answer


class TestBedrockAdapterRealMode:
    """Test cases for BedrockAdapter with real AWS client (mocked)."""
    
    @pytest.fixture
    def mock_bedrock_client(self):
        """Create a mock Bedrock client."""
        return Mock()
    
    @pytest.fixture
    def adapter_real(self, mock_bedrock_client):
        """Create a Bedrock adapter in real mode with mocked boto3 client."""
        with patch('boto3.client', return_value=mock_bedrock_client):
            adapter = BedrockAdapter(mock_mode=False)
            adapter.client = mock_bedrock_client
            return adapter
    
    def test_initialization_real_mode(self):
        """Test adapter initializes correctly in real mode."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_boto.return_value = mock_client
            
            adapter = BedrockAdapter(mock_mode=False)
            
            assert adapter.mock_mode is False
            assert adapter.client is not None
            mock_boto.assert_called_once_with(
                'bedrock-agent-runtime',
                region_name=adapter.region
            )
    
    def test_retrieve_and_generate_real_mode_success(self, adapter_real, mock_bedrock_client):
        """Test retrieve_and_generate with real client returns parsed response."""
        query = "What is AWS Bedrock?"
        kb_id = "test-kb-id"
        
        # Mock AWS response
        mock_bedrock_client.retrieve_and_generate.return_value = {
            'output': {
                'text': 'AWS Bedrock is a fully managed service.'
            },
            'sessionId': 'real-session-123',
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
        
        response = adapter_real.retrieve_and_generate(query, kb_id)
        
        # Verify API call
        mock_bedrock_client.retrieve_and_generate.assert_called_once()
        call_args = mock_bedrock_client.retrieve_and_generate.call_args[1]
        assert call_args['input']['text'] == query
        assert call_args['retrieveAndGenerateConfiguration']['knowledgeBaseConfiguration']['knowledgeBaseId'] == kb_id
        
        # Verify response structure
        assert response["success"] is True
        data = response["data"]
        assert data.answer == 'AWS Bedrock is a fully managed service.'
        assert data.session_id == 'real-session-123'
        assert len(data.references) == 2
        
        # Verify references
        assert data.references[0].content == 'Reference content 1'
        assert data.references[0].s3_uri == 's3://bucket/doc1.pdf'
        assert data.references[0].score == 0.95
        assert data.references[1].score == 0.88
    
    def test_retrieve_and_generate_with_custom_model_arn(self, adapter_real, mock_bedrock_client):
        """Test retrieve_and_generate uses custom model ARN when provided."""
        query = "Test query"
        kb_id = "test-kb-id"
        custom_model = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-v2"
        
        mock_bedrock_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Answer'},
            'sessionId': 'session-456',
            'citations': []
        }
        
        adapter_real.retrieve_and_generate(query, kb_id, model_arn=custom_model)
        
        call_args = mock_bedrock_client.retrieve_and_generate.call_args[1]
        kb_config = call_args['retrieveAndGenerateConfiguration']['knowledgeBaseConfiguration']
        assert kb_config['modelArn'] == custom_model
    
    def test_retrieve_and_generate_with_retrieval_config(self, adapter_real, mock_bedrock_client):
        """Test retrieve_and_generate includes retrieval configuration when provided."""
        query = "Test query"
        kb_id = "test-kb-id"
        retrieval_config = {
            'vectorSearchConfiguration': {
                'numberOfResults': 10,
                'filter': {'equals': {'key': 'tenant_id', 'value': 'tenant-123'}}
            }
        }
        
        mock_bedrock_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Answer'},
            'sessionId': 'session-789',
            'citations': []
        }
        
        adapter_real.retrieve_and_generate(query, kb_id, retrieval_config=retrieval_config)
        
        call_args = mock_bedrock_client.retrieve_and_generate.call_args[1]
        kb_config = call_args['retrieveAndGenerateConfiguration']['knowledgeBaseConfiguration']
        assert 'retrievalConfiguration' in kb_config
        assert kb_config['retrievalConfiguration'] == retrieval_config
    
    def test_retrieve_and_generate_handles_empty_citations(self, adapter_real, mock_bedrock_client):
        """Test retrieve_and_generate handles response with no citations."""
        query = "Test query"
        kb_id = "test-kb-id"
        
        mock_bedrock_client.retrieve_and_generate.return_value = {
            'output': {'text': 'Answer without citations'},
            'sessionId': 'session-no-citations',
            'citations': []
        }
        
        response = adapter_real.retrieve_and_generate(query, kb_id)
        
        assert response["success"] is True
        data = response["data"]
        assert data.answer == 'Answer without citations'
        assert len(data.references) == 0
    
    def test_retrieve_and_generate_handles_missing_score(self, adapter_real, mock_bedrock_client):
        """Test retrieve_and_generate handles references without score."""
        query = "Test query"
        kb_id = "test-kb-id"
        
        mock_bedrock_client.retrieve_and_generate.return_value = {
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
        
        response = adapter_real.retrieve_and_generate(query, kb_id)
        
        assert response["success"] is True
        data = response["data"]
        assert len(data.references) == 1
        assert data.references[0].score is None
    
    def test_retrieve_and_generate_client_error_propagates(self, adapter_real, mock_bedrock_client):
        """Test retrieve_and_generate propagates ClientError."""
        query = "Test query"
        kb_id = "test-kb-id"
        
        # Mock ClientError
        error_response = {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access denied'}}
        mock_bedrock_client.retrieve_and_generate.side_effect = ClientError(
            error_response, 'RetrieveAndGenerate'
        )
        
        with pytest.raises(ClientError) as exc_info:
            adapter_real.retrieve_and_generate(query, kb_id)
        
        assert exc_info.value.response['Error']['Code'] == 'AccessDeniedException'
    
    def test_start_ingestion_job_real_mode_success(self, adapter_real, mock_bedrock_client):
        """Test start_ingestion_job with real client."""
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
        
        with patch('boto3.client', return_value=mock_agent_client):
            response = adapter_real.start_ingestion_job(kb_id, data_source_id)
        
        # Verify API call
        mock_agent_client.start_ingestion_job.assert_called_once_with(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )
        
        # Verify response
        assert response["success"] is True
        data = response["data"]
        assert data.job_id == 'job-123'
        assert data.status == 'STARTING'
        assert data.knowledge_base_id == kb_id
        assert data.data_source_id == data_source_id
    
    def test_start_ingestion_job_client_error_propagates(self, adapter_real, mock_bedrock_client):
        """Test start_ingestion_job propagates ClientError."""
        kb_id = "test-kb-id"
        data_source_id = "test-ds-id"
        
        # Mock the bedrock-agent client
        mock_agent_client = Mock()
        error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'KB not found'}}
        mock_agent_client.start_ingestion_job.side_effect = ClientError(
            error_response, 'StartIngestionJob'
        )
        
        with patch('boto3.client', return_value=mock_agent_client):
            with pytest.raises(ClientError) as exc_info:
                adapter_real.start_ingestion_job(kb_id, data_source_id)
        
        assert exc_info.value.response['Error']['Code'] == 'ResourceNotFoundException'
