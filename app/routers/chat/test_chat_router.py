"""Unit tests for chat router."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.dtos.chat import ChatResponse, Citation
from app.routers.chat.chat_router import get_rag_service


@pytest.fixture
def mock_rag_service():
    """Create a mock RAG service."""
    service = Mock()
    service.query.return_value = ChatResponse(
        answer="This is a test answer about RAG systems.",
        citations=[
            Citation(
                content="RAG combines retrieval and generation.",
                document_title="test-doc.pdf",
                location={"s3Location": {"uri": "s3://test-bucket/test-doc.pdf"}},
                score=0.95
            )
        ],
        session_id="test-session-123",
        model_used="anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    return service


@pytest.fixture
def client(mock_rag_service):
    """Create test client with mocked RAG service."""
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_query_success(client, mock_rag_service):
    """Test successful query processing."""
    response = client.post(
        "/chat",
        json={"query": "What is RAG?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is a test answer about RAG systems."
    assert len(data["citations"]) == 1
    assert data["citations"][0]["document_title"] == "test-doc.pdf"
    assert data["session_id"] == "test-session-123"
    assert mock_rag_service.query.call_count == 1


def test_query_with_filters(client, mock_rag_service):
    """Test query with metadata filters."""
    response = client.post(
        "/chat",
        json={
            "query": "What is RAG?",
            "metadata_filters": [
                {"key": "category", "value": "documentation", "operator": "equals"}
            ]
        }
    )
    
    assert response.status_code == 200
    call_args = mock_rag_service.query.call_args[0][0]
    assert len(call_args.metadata_filters) == 1
    assert call_args.metadata_filters[0].key == "category"


def test_query_with_max_results(client, mock_rag_service):
    """Test query with custom max_results."""
    response = client.post(
        "/chat",
        json={
            "query": "What is RAG?",
            "max_results": 10
        }
    )
    
    assert response.status_code == 200
    call_args = mock_rag_service.query.call_args[0][0]
    assert call_args.max_results == 10


def test_query_with_custom_model(client, mock_rag_service):
    """Test query with custom model_id."""
    response = client.post(
        "/chat",
        json={
            "query": "What is RAG?",
            "model_id": "custom-model-id"
        }
    )
    
    assert response.status_code == 200
    call_args = mock_rag_service.query.call_args[0][0]
    assert call_args.model_id == "custom-model-id"


def test_query_empty_string(client):
    """Test query with empty string."""
    response = client.post(
        "/chat",
        json={"query": ""}
    )
    
    assert response.status_code == 422  # Pydantic validation error


def test_query_missing_query_field(client):
    """Test request without query field."""
    response = client.post(
        "/chat",
        json={}
    )
    
    assert response.status_code == 422  # Pydantic validation error


def test_query_invalid_max_results(client):
    """Test query with invalid max_results."""
    response = client.post(
        "/chat",
        json={
            "query": "What is RAG?",
            "max_results": 0  # Below minimum
        }
    )
    
    assert response.status_code == 422  # Pydantic validation error


def test_query_value_error(client, mock_rag_service):
    """Test handling of ValueError from service."""
    mock_rag_service.query.side_effect = ValueError("Invalid filter format")
    
    response = client.post(
        "/chat",
        json={"query": "What is RAG?"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Invalid filter format" in data["error"]["message"]


def test_query_generic_exception(client, mock_rag_service):
    """Test handling of generic exception from service."""
    mock_rag_service.query.side_effect = Exception("AWS service unavailable")
    
    response = client.post(
        "/chat",
        json={"query": "What is RAG?"}
    )
    
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert "error" in data


def test_query_with_all_parameters(client, mock_rag_service):
    """Test query with all optional parameters."""
    response = client.post(
        "/chat",
        json={
            "query": "What is RAG?",
            "metadata_filters": [
                {"key": "category", "value": "documentation", "operator": "equals"},
                {"key": "year", "value": "2024", "operator": "greater_than"}
            ],
            "max_results": 15,
            "model_id": "custom-model"
        }
    )
    
    assert response.status_code == 200
    call_args = mock_rag_service.query.call_args[0][0]
    assert call_args.query == "What is RAG?"
    assert len(call_args.metadata_filters) == 2
    assert call_args.max_results == 15
    assert call_args.model_id == "custom-model"


def test_response_structure(client, mock_rag_service):
    """Test that response matches expected structure."""
    response = client.post(
        "/chat",
        json={"query": "What is RAG?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "answer" in data
    assert "citations" in data
    assert "session_id" in data
    assert "model_used" in data
    
    # Check citation structure
    assert isinstance(data["citations"], list)
    if len(data["citations"]) > 0:
        citation = data["citations"][0]
        assert "content" in citation
        assert "document_title" in citation
        assert "location" in citation
        assert "score" in citation
