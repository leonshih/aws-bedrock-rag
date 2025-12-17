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
