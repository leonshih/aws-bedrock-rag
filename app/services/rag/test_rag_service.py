"""
Unit tests for RAG Service

Tests query processing, metadata filtering, and citation parsing.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.rag import RAGService
from app.dtos.routers.chat import ChatRequest, ChatResponse, MetadataFilter
from app.utils.config import Config


class TestRAGService:
    """Tests for RAGService."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=Config)
        config.AWS_REGION = "us-east-1"
        config.BEDROCK_KB_ID = "test-kb-id"
        config.BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        config.MOCK_MODE = True
        return config
    
    @pytest.fixture
    def rag_service(self, mock_config):
        """Create RAG service with mock config."""
        return RAGService(config=mock_config)
    
    def test_initialization(self, mock_config):
        """Test RAG service initialization."""
        service = RAGService(config=mock_config)
        assert service.config == mock_config
        assert service.bedrock_adapter is not None
    
    def test_initialization_with_default_config(self):
        """Test RAG service initialization without config."""
        service = RAGService()
        assert service.config is not None
        assert service.bedrock_adapter is not None
    
    @patch('app.services.rag.rag_service.BedrockAdapter')
    def test_query_basic(self, mock_bedrock_adapter_class, mock_config):
        """Test basic query without filters."""
        # Setup mock adapter
        mock_adapter = Mock()
        mock_adapter.retrieve_and_generate.return_value = {
            "output": {"text": "This is the answer."},
            "citations": [],
            "sessionId": "session-123"
        }
        mock_bedrock_adapter_class.return_value = mock_adapter
        
        # Create service and make request
        service = RAGService(config=mock_config)
        request = ChatRequest(query="What is aspirin?")
        response = service.query(request)
        
        # Verify response structure
        assert isinstance(response, dict)
        assert response["success"] is True
        assert "data" in response
        assert isinstance(response["data"], ChatResponse)
        assert response["data"].answer == "This is the answer."
        assert response["data"].session_id == "session-123"
        assert response["data"].model_used == mock_config.BEDROCK_MODEL_ID
        assert response["data"].citations == []
        
        # Verify adapter was called correctly
        mock_adapter.retrieve_and_generate.assert_called_once()
        call_kwargs = mock_adapter.retrieve_and_generate.call_args[1]
        assert call_kwargs["query"] == "What is aspirin?"
        assert call_kwargs["kb_id"] == "test-kb-id"
        assert "anthropic.claude-3-5-sonnet-20241022-v2:0" in call_kwargs["model_arn"]
    
    @patch('app.services.rag.rag_service.BedrockAdapter')
    def test_query_with_custom_model(self, mock_bedrock_adapter_class, mock_config):
        """Test query with custom model override."""
        mock_adapter = Mock()
        mock_adapter.retrieve_and_generate.return_value = {
            "output": {"text": "Answer"},
            "citations": []
        }
        mock_bedrock_adapter_class.return_value = mock_adapter
        
        service = RAGService(config=mock_config)
        request = ChatRequest(
            query="Test query",
            model_id="anthropic.claude-3-haiku-20240307-v1:0"
        )
        response = service.query(request)
        
        assert response["success"] is True
        assert response["data"].model_used == "anthropic.claude-3-haiku-20240307-v1:0"
        call_kwargs = mock_adapter.retrieve_and_generate.call_args[1]
        assert "anthropic.claude-3-haiku-20240307-v1:0" in call_kwargs["model_arn"]
    
    def test_build_filter_expression_equals(self, rag_service):
        """Test building equals filter expression."""
        filter_obj = MetadataFilter(key="category", value="medical", operator="equals")
        expression = rag_service._build_filter_expression(filter_obj)
        
        assert expression == {
            "equals": {
                "key": "category",
                "value": "medical"
            }
        }
    
    def test_build_filter_expression_not_equals(self, rag_service):
        """Test building not_equals filter expression."""
        filter_obj = MetadataFilter(key="status", value="draft", operator="not_equals")
        expression = rag_service._build_filter_expression(filter_obj)
        
        assert expression == {
            "notEquals": {
                "key": "status",
                "value": "draft"
            }
        }
    
    def test_build_filter_expression_greater_than(self, rag_service):
        """Test building greater_than filter expression."""
        filter_obj = MetadataFilter(key="year", value=2020, operator="greater_than")
        expression = rag_service._build_filter_expression(filter_obj)
        
        assert expression == {
            "greaterThan": {
                "key": "year",
                "value": 2020
            }
        }
    
    def test_build_filter_expression_less_than(self, rag_service):
        """Test building less_than filter expression."""
        filter_obj = MetadataFilter(key="price", value=100, operator="less_than")
        expression = rag_service._build_filter_expression(filter_obj)
        
        assert expression == {
            "lessThan": {
                "key": "price",
                "value": 100
            }
        }
    
    def test_build_filter_expression_contains(self, rag_service):
        """Test building contains filter expression."""
        filter_obj = MetadataFilter(key="tags", value="cardiology", operator="contains")
        expression = rag_service._build_filter_expression(filter_obj)
        
        assert expression == {
            "stringContains": {
                "key": "tags",
                "value": "cardiology"
            }
        }
    
    def test_build_filter_expression_unknown_operator(self, rag_service):
        """Test building filter with unknown operator returns None."""
        filter_obj = MetadataFilter(key="field", value="value", operator="unknown")
        expression = rag_service._build_filter_expression(filter_obj)
        
        assert expression is None
    
    def test_build_retrieval_config_single_filter(self, rag_service):
        """Test building retrieval config with single filter."""
        filters = [
            MetadataFilter(key="year", value=2023, operator="equals")
        ]
        config = rag_service._build_retrieval_config(filters)
        
        assert "vectorSearchConfiguration" in config
        assert "filter" in config["vectorSearchConfiguration"]
        assert config["vectorSearchConfiguration"]["filter"]["equals"]["key"] == "year"
    
    def test_build_retrieval_config_multiple_filters(self, rag_service):
        """Test building retrieval config with multiple filters (AND logic)."""
        filters = [
            MetadataFilter(key="year", value=2020, operator="greater_than"),
            MetadataFilter(key="category", value="medical", operator="equals")
        ]
        config = rag_service._build_retrieval_config(filters)
        
        assert "vectorSearchConfiguration" in config
        filter_expr = config["vectorSearchConfiguration"]["filter"]
        assert "andAll" in filter_expr
        assert len(filter_expr["andAll"]) == 2
    
    def test_build_retrieval_config_empty_filters(self, rag_service):
        """Test building retrieval config with empty filter list."""
        config = rag_service._build_retrieval_config([])
        assert config == {}
    
    def test_extract_answer(self, rag_service):
        """Test extracting answer from Bedrock response."""
        bedrock_response = {
            "output": {
                "text": "This is the generated answer."
            }
        }
        answer = rag_service._extract_answer(bedrock_response)
        assert answer == "This is the generated answer."
    
    def test_extract_answer_missing_output(self, rag_service):
        """Test extracting answer when output is missing."""
        bedrock_response = {}
        answer = rag_service._extract_answer(bedrock_response)
        assert answer == ""
    
    def test_parse_citations(self, rag_service):
        """Test parsing citations from Bedrock response."""
        bedrock_response = {
            "citations": [
                {
                    "retrievedReferences": [
                        {
                            "content": {
                                "text": "Aspirin is a pain reliever."
                            },
                            "location": {
                                "type": "S3",
                                "s3Location": {
                                    "uri": "s3://bucket/documents/aspirin_guide.pdf"
                                }
                            },
                            "metadata": {
                                "score": 0.95
                            }
                        }
                    ]
                }
            ]
        }
        
        citations = rag_service._parse_citations(bedrock_response)
        
        assert len(citations) == 1
        assert citations[0].content == "Aspirin is a pain reliever."
        assert citations[0].document_title == "aspirin_guide.pdf"
        assert citations[0].location["s3_uri"] == "s3://bucket/documents/aspirin_guide.pdf"
        assert citations[0].score == 0.95
    
    def test_parse_citations_multiple_references(self, rag_service):
        """Test parsing multiple citations."""
        bedrock_response = {
            "citations": [
                {
                    "retrievedReferences": [
                        {
                            "content": {"text": "Reference 1"},
                            "location": {
                                "type": "S3",
                                "s3Location": {"uri": "s3://bucket/doc1.pdf"}
                            }
                        },
                        {
                            "content": {"text": "Reference 2"},
                            "location": {
                                "type": "S3",
                                "s3Location": {"uri": "s3://bucket/doc2.pdf"}
                            }
                        }
                    ]
                }
            ]
        }
        
        citations = rag_service._parse_citations(bedrock_response)
        assert len(citations) == 2
        assert citations[0].content == "Reference 1"
        assert citations[1].content == "Reference 2"
    
    def test_parse_citations_empty(self, rag_service):
        """Test parsing citations when none exist."""
        bedrock_response = {"citations": []}
        citations = rag_service._parse_citations(bedrock_response)
        assert citations == []
    
    @patch('app.services.rag.rag_service.BedrockAdapter')
    def test_query_with_filters_integration(self, mock_bedrock_adapter_class, mock_config):
        """Test full query flow with metadata filters."""
        mock_adapter = Mock()
        mock_adapter.retrieve_and_generate.return_value = {
            "output": {"text": "Filtered answer."},
            "citations": [
                {
                    "retrievedReferences": [
                        {
                            "content": {"text": "Source text"},
                            "location": {
                                "type": "S3",
                                "s3Location": {"uri": "s3://bucket/doc.pdf"}
                            }
                        }
                    ]
                }
            ]
        }
        mock_bedrock_adapter_class.return_value = mock_adapter
        
        service = RAGService(config=mock_config)
        request = ChatRequest(
            query="Recent studies?",
            metadata_filters=[
                MetadataFilter(key="year", value=2020, operator="greater_than")
            ]
        )
        response = service.query(request)
        
        assert response["success"] is True
        assert response["data"].answer == "Filtered answer."
        assert len(response["data"].citations) == 1
        
        # Verify retrieval_config was passed
        call_kwargs = mock_adapter.retrieve_and_generate.call_args[1]
        assert call_kwargs["retrieval_config"] is not None
        assert "vectorSearchConfiguration" in call_kwargs["retrieval_config"]
