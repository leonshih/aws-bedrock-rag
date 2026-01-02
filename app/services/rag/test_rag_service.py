"""
Unit tests for RAG Service

Tests query processing, metadata filtering, and citation parsing.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.rag import RAGService
from app.dtos.routers.chat import ChatRequest, ChatResponse, MetadataFilter
from app.utils.config import Config

# Test tenant ID for multi-tenant testing
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"


class TestRAGService:
    """Tests for RAGService."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=Config)
        config.AWS_REGION = "us-east-1"
        config.BEDROCK_KB_ID = "test-kb-id"
        config.BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
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
        from app.dtos.adapters.bedrock import BedrockRAGResult
        
        # Setup mock adapter
        mock_adapter = Mock()
        mock_adapter.retrieve_and_generate.return_value = {
            "success": True,
            "data": BedrockRAGResult(
                answer="This is the answer.",
                session_id="session-123",
                references=[]
            )
        }
        mock_bedrock_adapter_class.return_value = mock_adapter
        
        # Create service and make request
        service = RAGService(config=mock_config)
        request = ChatRequest(query="What is aspirin?")
        response = service.query(request, tenant_id=TEST_TENANT_ID)
        
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
        from app.dtos.adapters.bedrock import BedrockRAGResult
        
        mock_adapter = Mock()
        mock_adapter.retrieve_and_generate.return_value = {
            "success": True,
            "data": BedrockRAGResult(
                answer="Answer",
                session_id="session-456",
                references=[]
            )
        }
        mock_bedrock_adapter_class.return_value = mock_adapter
        
        service = RAGService(config=mock_config)
        request = ChatRequest(
            query="Test query",
            model_id="anthropic.claude-3-haiku-20240307-v1:0"
        )
        response = service.query(request, tenant_id=TEST_TENANT_ID)
        
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
    
    # NOTE: The following tests for private methods (_extract_answer, _parse_citations) 
    # have been removed as these methods were refactored into the main query flow.
    # The functionality is now tested through the query integration tests above.
    
    @patch('app.services.rag.rag_service.BedrockAdapter')
    def test_query_with_filters_integration(self, mock_bedrock_adapter_class, mock_config):
        """Test full query flow with metadata filters."""
        from app.dtos.adapters.bedrock import BedrockRAGResult, BedrockRetrievalReference
        
        mock_adapter = Mock()
        mock_adapter.retrieve_and_generate.return_value = {
            "success": True,
            "data": BedrockRAGResult(
                answer="Filtered answer.",
                session_id="session-789",
                references=[
                    BedrockRetrievalReference(
                        content="Source text",
                        s3_uri="s3://bucket/doc.pdf",
                        score=0.85
                    )
                ]
            )
        }
        mock_bedrock_adapter_class.return_value = mock_adapter
        
        service = RAGService(config=mock_config)
        request = ChatRequest(
            query="Recent studies?",
            metadata_filters=[
                MetadataFilter(key="year", value=2020, operator="greater_than")
            ]
        )
        response = service.query(request, tenant_id=TEST_TENANT_ID)
        
        assert response["success"] is True
        assert response["data"].answer == "Filtered answer."
        assert len(response["data"].citations) == 1
        
        # Verify retrieval_config was passed
        call_kwargs = mock_adapter.retrieve_and_generate.call_args[1]
        assert call_kwargs["retrieval_config"] is not None
        assert "vectorSearchConfiguration" in call_kwargs["retrieval_config"]
    
    @patch('app.services.rag.rag_service.BedrockAdapter')
    def test_query_auto_injects_tenant_filter(self, mock_bedrock_adapter_class, mock_config):
        """Test that tenant_id is automatically injected as a filter in all queries."""
        from app.dtos.adapters.bedrock import BedrockRAGResult
        
        mock_adapter = Mock()
        mock_adapter.retrieve_and_generate.return_value = {
            "success": True,
            "data": BedrockRAGResult(
                answer="Tenant-filtered answer.",
                session_id="session-tenant-1",
                references=[]
            )
        }
        mock_bedrock_adapter_class.return_value = mock_adapter
        
        service = RAGService(config=mock_config)
        request = ChatRequest(query="Test query without filters")
        response = service.query(request, tenant_id=TEST_TENANT_ID)
        
        # Verify response
        assert response["success"] is True
        
        # Verify tenant filter was injected
        call_kwargs = mock_adapter.retrieve_and_generate.call_args[1]
        retrieval_config = call_kwargs["retrieval_config"]
        assert retrieval_config is not None
        assert "vectorSearchConfiguration" in retrieval_config
        
        # Extract filter and verify tenant_id
        filter_expr = retrieval_config["vectorSearchConfiguration"]["filter"]
        assert "equals" in filter_expr
        assert filter_expr["equals"]["key"] == "tenant_id"
        assert filter_expr["equals"]["value"] == TEST_TENANT_ID
    
    @patch('app.services.rag.rag_service.BedrockAdapter')
    def test_query_combines_tenant_and_user_filters(self, mock_bedrock_adapter_class, mock_config):
        """Test that tenant filter is combined with user-provided filters using AND logic."""
        from app.dtos.adapters.bedrock import BedrockRAGResult
        
        mock_adapter = Mock()
        mock_adapter.retrieve_and_generate.return_value = {
            "success": True,
            "data": BedrockRAGResult(
                answer="Multi-filtered answer.",
                session_id="session-multi-1",
                references=[]
            )
        }
        mock_bedrock_adapter_class.return_value = mock_adapter
        
        service = RAGService(config=mock_config)
        request = ChatRequest(
            query="Recent medical studies",
            metadata_filters=[
                MetadataFilter(key="category", value="medical", operator="equals"),
                MetadataFilter(key="year", value=2020, operator="greater_than")
            ]
        )
        response = service.query(request, tenant_id=TEST_TENANT_ID)
        
        # Verify response
        assert response["success"] is True
        
        # Verify filters are combined with AND logic
        call_kwargs = mock_adapter.retrieve_and_generate.call_args[1]
        retrieval_config = call_kwargs["retrieval_config"]
        filter_expr = retrieval_config["vectorSearchConfiguration"]["filter"]
        
        # Should have andAll with 3 filters: tenant_id + category + year
        assert "andAll" in filter_expr
        assert len(filter_expr["andAll"]) == 3
        
        # Verify tenant filter is included
        filters = filter_expr["andAll"]
        tenant_filters = [f for f in filters if "equals" in f and f["equals"]["key"] == "tenant_id"]
        assert len(tenant_filters) == 1
        assert tenant_filters[0]["equals"]["value"] == TEST_TENANT_ID
    
    def test_build_retrieval_config_with_tenant_only_tenant_filter(self, rag_service):
        """Test building retrieval config with only tenant filter."""
        from uuid import UUID
        
        tenant_id = UUID(TEST_TENANT_ID)
        config = rag_service._build_retrieval_config_with_tenant(
            tenant_id=tenant_id,
            user_filters=None
        )
        
        assert "vectorSearchConfiguration" in config
        filter_expr = config["vectorSearchConfiguration"]["filter"]
        assert "equals" in filter_expr
        assert filter_expr["equals"]["key"] == "tenant_id"
        assert filter_expr["equals"]["value"] == TEST_TENANT_ID
    
    def test_build_retrieval_config_with_tenant_and_user_filters(self, rag_service):
        """Test building retrieval config with tenant and user filters combined."""
        from uuid import UUID
        
        tenant_id = UUID(TEST_TENANT_ID)
        user_filters = [
            MetadataFilter(key="category", value="medical", operator="equals")
        ]
        
        config = rag_service._build_retrieval_config_with_tenant(
            tenant_id=tenant_id,
            user_filters=user_filters
        )
        
        filter_expr = config["vectorSearchConfiguration"]["filter"]
        assert "andAll" in filter_expr
        assert len(filter_expr["andAll"]) == 2
        
        # Verify both filters are present
        filters = filter_expr["andAll"]
        tenant_filter = next(f for f in filters if "equals" in f and f["equals"]["key"] == "tenant_id")
        category_filter = next(f for f in filters if "equals" in f and f["equals"]["key"] == "category")
        
        assert tenant_filter["equals"]["value"] == TEST_TENANT_ID
        assert category_filter["equals"]["value"] == "medical"

