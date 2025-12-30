"""
Integration tests for service layer.
Tests real service instantiation and dependency injection without mocks.
"""

import pytest
from app.utils.config import Config
from app.services.rag.rag_service import RAGService
from app.services.ingestion.ingestion_service import IngestionService


class TestRAGServiceIntegration:
    """Test RAG service initialization and configuration."""

    def test_rag_service_initialization(self):
        """Test RAG service can be initialized with config."""
        config = Config()
        service = RAGService(config=config)
        
        assert service is not None
        assert service.config == config
        assert service.bedrock_adapter is not None
        assert hasattr(service, 'query')

    def test_rag_service_has_required_methods(self):
        """Test RAG service has all required methods."""
        config = Config()
        service = RAGService(config=config)
        
        # Verify public API
        assert callable(getattr(service, 'query', None))
        
    def test_rag_service_config_propagation(self):
        """Test configuration is properly propagated to adapters."""
        config = Config()
        service = RAGService(config=config)
        
        # Verify adapter has access to config values
        assert service.bedrock_adapter.model_id == config.BEDROCK_MODEL_ID
        assert service.bedrock_adapter.region == config.AWS_REGION

    def test_rag_service_multiple_instances(self):
        """Test multiple service instances can coexist."""
        config1 = Config()
        config2 = Config()
        
        service1 = RAGService(config=config1)
        service2 = RAGService(config=config2)
        
        assert service1 is not service2
        assert service1.bedrock_adapter is not service2.bedrock_adapter


class TestIngestionServiceIntegration:
    """Test Ingestion service initialization and configuration."""

    def test_ingestion_service_initialization(self):
        """Test Ingestion service can be initialized with config."""
        config = Config()
        service = IngestionService(config=config)
        
        assert service is not None
        assert service.config == config
        assert service.s3_adapter is not None
        assert service.bedrock_adapter is not None
        assert hasattr(service, 'upload_document')
        assert hasattr(service, 'list_documents')
        assert hasattr(service, 'delete_document')

    def test_ingestion_service_has_required_methods(self):
        """Test Ingestion service has all required methods."""
        config = Config()
        service = IngestionService(config=config)
        
        # Verify public API
        assert callable(getattr(service, 'upload_document', None))
        assert callable(getattr(service, 'list_documents', None))
        assert callable(getattr(service, 'delete_document', None))

    def test_ingestion_service_config_propagation(self):
        """Test configuration is properly propagated to adapters."""
        config = Config()
        service = IngestionService(config=config)
        
        # Verify adapters have access to config values
        assert service.s3_adapter.region == config.AWS_REGION
        assert service.bedrock_adapter.region == config.AWS_REGION

    def test_ingestion_service_multiple_instances(self):
        """Test multiple service instances can coexist."""
        config1 = Config()
        config2 = Config()
        
        service1 = IngestionService(config=config1)
        service2 = IngestionService(config=config2)
        
        assert service1 is not service2
        assert service1.s3_adapter is not service2.s3_adapter
        assert service1.bedrock_adapter is not service2.bedrock_adapter


class TestServiceDependencyInjection:
    """Test dependency injection patterns used in services."""

    def test_services_accept_config_parameter(self):
        """Test all services accept config as constructor parameter."""
        config = Config()
        
        # This is the pattern used in router dependencies
        rag_service = RAGService(config=config)
        ingestion_service = IngestionService(config=config)
        
        assert rag_service is not None
        assert ingestion_service is not None

    def test_services_do_not_accept_adapter_parameters(self):
        """Test services reject direct adapter injection (anti-pattern)."""
        from app.adapters.bedrock.bedrock_adapter import BedrockAdapter
        from app.adapters.s3.s3_adapter import S3Adapter
        
        bedrock = BedrockAdapter()
        s3 = S3Adapter()
        
        # These should fail - services should not accept adapters directly
        with pytest.raises(TypeError):
            RAGService(bedrock_adapter=bedrock)  # type: ignore
            
        with pytest.raises(TypeError):
            IngestionService(s3_adapter=s3, bedrock_adapter=bedrock)  # type: ignore

    def test_config_singleton_behavior(self):
        """Test Config can be instantiated multiple times with same values."""
        config1 = Config()
        config2 = Config()
        
        # Same environment variables should produce same values
        assert config1.BEDROCK_KB_ID == config2.BEDROCK_KB_ID
        assert config1.S3_BUCKET_NAME == config2.S3_BUCKET_NAME
        assert config1.AWS_REGION == config2.AWS_REGION
