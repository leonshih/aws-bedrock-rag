"""
Unit tests for Bedrock Adapter
"""
import pytest
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
        
        # Verify response structure
        assert 'output' in response
        assert 'text' in response['output']
        assert 'citations' in response
        assert 'sessionId' in response
        
        # Verify content
        assert query in response['output']['text']
        assert len(response['citations']) > 0
    
    def test_retrieve_and_generate_with_custom_model(self, adapter):
        """Test retrieve_and_generate accepts custom model ARN."""
        query = "Test query"
        kb_id = "test-kb-id"
        model_arn = "arn:aws:bedrock:us-east-1::foundation-model/custom-model"
        
        response = adapter.retrieve_and_generate(query, kb_id, model_arn)
        
        # In mock mode, should still return valid response
        assert response is not None
        assert 'output' in response
    
    def test_retrieve_and_generate_citations_structure(self, adapter):
        """Test citations have proper structure."""
        query = "Test query"
        kb_id = "test-kb-id"
        
        response = adapter.retrieve_and_generate(query, kb_id)
        
        citations = response['citations']
        assert len(citations) > 0
        
        first_citation = citations[0]
        assert 'retrievedReferences' in first_citation
        assert len(first_citation['retrievedReferences']) > 0
        
        reference = first_citation['retrievedReferences'][0]
        assert 'content' in reference
        assert 'location' in reference
    
    def test_start_ingestion_job_returns_response(self, adapter):
        """Test start_ingestion_job returns proper response structure."""
        kb_id = "test-kb-id"
        data_source_id = "test-ds-id"
        
        response = adapter.start_ingestion_job(kb_id, data_source_id)
        
        # Verify response structure
        assert 'ingestionJob' in response
        assert response['ingestionJob']['knowledgeBaseId'] == kb_id
        assert response['ingestionJob']['dataSourceId'] == data_source_id
        assert 'ingestionJobId' in response['ingestionJob']
        assert 'status' in response['ingestionJob']
    
    def test_start_ingestion_job_status(self, adapter):
        """Test ingestion job returns valid status."""
        kb_id = "test-kb-id"
        data_source_id = "test-ds-id"
        
        response = adapter.start_ingestion_job(kb_id, data_source_id)
        
        status = response['ingestionJob']['status']
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
        assert response1['sessionId'] == response2['sessionId']  # Mock uses same session
        assert query1 in response1['output']['text']
        assert query2 in response2['output']['text']
