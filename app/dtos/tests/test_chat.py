"""
Unit tests for Chat DTOs

Tests Pydantic validation and serialization for chat-related models.
"""
import pytest
from pydantic import ValidationError
from app.dtos.routers.chat import (
    MetadataFilter,
    Citation,
    ChatRequest,
    ChatResponse,
)


class TestMetadataFilter:
    """Tests for MetadataFilter model."""
    
    def test_valid_metadata_filter(self):
        """Test creating a valid metadata filter."""
        filter_obj = MetadataFilter(
            key="year",
            value=2023,
            operator="greater_than"
        )
        assert filter_obj.key == "year"
        assert filter_obj.value == 2023
        assert filter_obj.operator == "greater_than"
    
    def test_default_operator(self):
        """Test default operator is 'equals'."""
        filter_obj = MetadataFilter(key="category", value="medical")
        assert filter_obj.operator == "equals"
    
    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            MetadataFilter()


class TestCitation:
    """Tests for Citation model."""
    
    def test_valid_citation(self):
        """Test creating a valid citation."""
        citation = Citation(
            content="Sample text from document",
            document_id="doc123",
            document_title="test.pdf",
            score=0.95
        )
        assert citation.content == "Sample text from document"
        assert citation.document_id == "doc123"
        assert citation.score == 0.95
    
    def test_citation_with_minimal_fields(self):
        """Test citation with only required field."""
        citation = Citation(content="Text snippet")
        assert citation.content == "Text snippet"
        assert citation.document_id is None
        assert citation.score is None
    
    def test_citation_with_location_metadata(self):
        """Test citation with location information."""
        citation = Citation(
            content="Sample text",
            location={"s3_uri": "s3://bucket/doc.pdf", "page": 5}
        )
        assert citation.location["page"] == 5


class TestChatRequest:
    """Tests for ChatRequest model."""
    
    def test_valid_chat_request(self):
        """Test creating a valid chat request."""
        request = ChatRequest(query="What is aspirin?")
        assert request.query == "What is aspirin?"
        assert request.metadata_filters is None
        assert request.max_results == 5
    
    def test_chat_request_with_filters(self):
        """Test chat request with metadata filters."""
        request = ChatRequest(
            query="Show recent studies",
            metadata_filters=[
                MetadataFilter(key="year", value=2020, operator="greater_than")
            ]
        )
        assert len(request.metadata_filters) == 1
        assert request.metadata_filters[0].key == "year"
    
    def test_chat_request_with_custom_model(self):
        """Test chat request with custom model override."""
        request = ChatRequest(
            query="Test query",
            model_id="anthropic.claude-3-haiku-20240307-v1:0"
        )
        assert request.model_id == "anthropic.claude-3-haiku-20240307-v1:0"
    
    def test_empty_query_validation(self):
        """Test validation error for empty query."""
        with pytest.raises(ValidationError):
            ChatRequest(query="")
    
    def test_missing_query_validation(self):
        """Test validation error for missing query."""
        with pytest.raises(ValidationError):
            ChatRequest()
    
    def test_max_results_bounds(self):
        """Test max_results validation bounds."""
        # Valid range
        request = ChatRequest(query="test", max_results=50)
        assert request.max_results == 50
        
        # Below minimum
        with pytest.raises(ValidationError):
            ChatRequest(query="test", max_results=0)
        
        # Above maximum
        with pytest.raises(ValidationError):
            ChatRequest(query="test", max_results=101)


class TestChatResponse:
    """Tests for ChatResponse model."""
    
    def test_valid_chat_response(self):
        """Test creating a valid chat response."""
        response = ChatResponse(
            answer="Aspirin is a pain reliever.",
            citations=[
                Citation(content="Aspirin info", document_title="med_guide.pdf")
            ]
        )
        assert response.answer == "Aspirin is a pain reliever."
        assert len(response.citations) == 1
    
    def test_chat_response_minimal(self):
        """Test chat response with only required fields."""
        response = ChatResponse(answer="Answer text")
        assert response.answer == "Answer text"
        assert response.citations == []
        assert response.session_id is None
    
    def test_chat_response_with_model_info(self):
        """Test chat response with model information."""
        response = ChatResponse(
            answer="Test answer",
            model_used="anthropic.claude-3-5-sonnet-20241022-v2:0",
            session_id="session123"
        )
        assert response.model_used == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert response.session_id == "session123"
    
    def test_chat_response_serialization(self):
        """Test serialization to dict."""
        response = ChatResponse(
            answer="Test",
            citations=[Citation(content="Source")]
        )
        data = response.model_dump()
        assert data["answer"] == "Test"
        assert len(data["citations"]) == 1
        assert data["citations"][0]["content"] == "Source"
