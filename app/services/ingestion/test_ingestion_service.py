"""
Unit tests for Ingestion Service

Tests document upload, listing, deletion, and metadata handling.
"""
import pytest
import json
from unittest.mock import Mock, patch, ANY
from datetime import datetime
from app.services.ingestion import IngestionService
from app.dtos.routers.ingest import FileMetadata, FileResponse
from app.utils.config import Config

# Test tenant ID for multi-tenant testing
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"


class TestIngestionService:
    """Tests for IngestionService."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=Config)
        config.S3_BUCKET_NAME = "test-bucket"
        config.BEDROCK_KB_ID = "test-kb-id"
        config.BEDROCK_DATA_SOURCE_ID = "test-ds-id"
        config.MOCK_MODE = True
        return config
    
    @pytest.fixture
    def ingestion_service(self, mock_config):
        """Create ingestion service with mock config."""
        return IngestionService(config=mock_config)
    
    def test_initialization(self, mock_config):
        """Test ingestion service initialization."""
        service = IngestionService(config=mock_config)
        assert service.config == mock_config
        assert service.s3_adapter is not None
        assert service.bedrock_adapter is not None
        assert service.bucket_name == "test-bucket"
    
    def test_initialization_with_default_config(self):
        """Test ingestion service initialization without config."""
        service = IngestionService()
        assert service.config is not None
        assert service.s3_adapter is not None
        assert service.bedrock_adapter is not None
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_upload_document_basic(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test basic document upload without metadata."""
        # Setup mocks
        mock_s3 = Mock()
        mock_bedrock = Mock()
        mock_s3_adapter_class.return_value = mock_s3
        mock_bedrock_adapter_class.return_value = mock_bedrock
        
        # Create service and upload
        service = IngestionService(config=mock_config)
        file_content = b"Test file content"
        response = service.upload_document(
            file_content=file_content,
            filename="test.pdf",
            tenant_id=TEST_TENANT_ID
        )
        
        # Verify response
        assert isinstance(response, dict)
        assert response["success"] is True
        assert "data" in response
        assert isinstance(response["data"], FileResponse)
        assert response["data"].filename == "test.pdf"
        assert response["data"].size == len(file_content)
        assert response["data"].s3_key == f"documents/{TEST_TENANT_ID}/test.pdf"
        assert response["data"].metadata is None
        
        # Verify S3 upload was called with tenant-specific path
        mock_s3.upload_file.assert_called_once_with(
            file_content=file_content,
            bucket="test-bucket",
            key=f"documents/{TEST_TENANT_ID}/test.pdf"
        )
        
        # Verify sync was triggered
        mock_bedrock.start_ingestion_job.assert_called_once_with(
            kb_id="test-kb-id",
            data_source_id="test-ds-id"
        )
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_upload_document_with_metadata(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test document upload with custom metadata."""
        mock_s3 = Mock()
        mock_bedrock = Mock()
        mock_s3_adapter_class.return_value = mock_s3
        mock_bedrock_adapter_class.return_value = mock_bedrock
        
        service = IngestionService(config=mock_config)
        file_content = b"Test content"
        metadata = {
            "author": "Dr. Smith",
            "year": 2023,
            "category": "medical"
        }
        
        response = service.upload_document(
            file_content=file_content,
            filename="document.pdf",
            tenant_id=TEST_TENANT_ID,
            metadata=metadata
        )
        
        # Verify response includes metadata
        assert response["success"] is True
        assert response["data"].metadata == metadata
        
        # Verify two S3 uploads: file + metadata
        assert mock_s3.upload_file.call_count == 2
        
        # Check first call (main file) - with tenant path
        first_call = mock_s3.upload_file.call_args_list[0]
        assert first_call[1]["key"] == f"documents/{TEST_TENANT_ID}/document.pdf"
        
        # Check second call (metadata sidecar) - with tenant path
        second_call = mock_s3.upload_file.call_args_list[1]
        assert second_call[1]["key"] == f"documents/{TEST_TENANT_ID}/document.pdf.metadata.json"
        metadata_content = second_call[1]["file_content"].decode('utf-8')
        metadata_json = json.loads(metadata_content)
        assert metadata_json["metadataAttributes"]["author"] == "Dr. Smith"
        assert metadata_json["metadataAttributes"]["year"] == 2023
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_list_documents_empty(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test listing documents when bucket is empty."""
        from app.dtos.adapters.s3 import S3ListResult
        
        mock_s3 = Mock()
        mock_s3.list_files.return_value = {
            "success": True,
            "data": S3ListResult(objects=[], total_count=0, total_size=0)
        }
        mock_s3_adapter_class.return_value = mock_s3
        mock_bedrock_adapter_class.return_value = Mock()
        
        service = IngestionService(config=mock_config)
        response = service.list_documents(tenant_id=TEST_TENANT_ID)
        
        assert response["success"] is True
        assert response["data"].total_count == 0
        assert response["data"].total_size == 0
        assert response["data"].files == []
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_list_documents_with_files(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test listing documents with files."""
        from app.dtos.adapters.s3 import S3ListResult, S3ObjectInfo
        
        mock_s3 = Mock()
        mock_s3.list_files.return_value = {
            "success": True,
            "data": S3ListResult(
                objects=[
                    S3ObjectInfo(
                        key=f"documents/{TEST_TENANT_ID}/doc1.pdf",
                        size=1024,
                        last_modified="2023-12-01T00:00:00",
                        etag="etag1"
                    ),
                    S3ObjectInfo(
                        key=f"documents/{TEST_TENANT_ID}/doc2.pdf",
                        size=2048,
                        last_modified="2023-12-02T00:00:00",
                        etag="etag2"
                    )
                ],
                total_count=2,
                total_size=3072
            )
        }
        mock_s3_adapter_class.return_value = mock_s3
        mock_bedrock_adapter_class.return_value = Mock()
        
        service = IngestionService(config=mock_config)
        response = service.list_documents(tenant_id=TEST_TENANT_ID)
        
        assert response["success"] is True
        assert response["data"].total_count == 2
        assert response["data"].total_size == 3072
        assert len(response["data"].files) == 2
        assert response["data"].files[0].filename == "doc1.pdf"
        assert response["data"].files[1].filename == "doc2.pdf"
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_list_documents_filters_metadata_files(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test that .metadata.json files are filtered from list."""
        from app.dtos.adapters.s3 import S3ListResult, S3ObjectInfo
        
        mock_s3 = Mock()
        mock_s3.list_files.return_value = {
            "success": True,
            "data": S3ListResult(
                objects=[
                    S3ObjectInfo(
                        key=f"documents/{TEST_TENANT_ID}/doc1.pdf",
                        size=1024,
                        last_modified="2023-12-01T00:00:00",
                        etag="etag1"
                    ),
                    S3ObjectInfo(
                        key=f"documents/{TEST_TENANT_ID}/doc1.pdf.metadata.json",
                        size=256,
                        last_modified="2023-12-01T00:00:00",
                        etag="etag2"
                    )
                ],
                total_count=2,
                total_size=1280
            )
        }
        mock_s3.get_file.return_value = json.dumps({
            "metadataAttributes": {"author": "Dr. Smith"}
        }).encode('utf-8')
        mock_s3_adapter_class.return_value = mock_s3
        mock_bedrock_adapter_class.return_value = Mock()
        
        service = IngestionService(config=mock_config)
        response = service.list_documents(tenant_id=TEST_TENANT_ID)
        
        # Should only list the main file, not the metadata file
        assert response["success"] is True
        assert response["data"].total_count == 1
        assert response["data"].files[0].filename == "doc1.pdf"
        # Metadata should be loaded and attached
        assert response["data"].files[0].metadata == {"author": "Dr. Smith"}
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_delete_document(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test document deletion."""
        mock_s3 = Mock()
        mock_bedrock = Mock()
        mock_s3_adapter_class.return_value = mock_s3
        mock_bedrock_adapter_class.return_value = mock_bedrock
        
        service = IngestionService(config=mock_config)
        response = service.delete_document("test.pdf", tenant_id=TEST_TENANT_ID)
        
        # Verify response
        assert response["success"] is True
        assert response["data"].filename == "test.pdf"
        assert response["data"].status == "deleted"
        assert "sync triggered" in response["data"].message
        
        # Verify S3 delete was called with tenant-specific path
        assert mock_s3.delete_file.call_count == 2
        calls = mock_s3.delete_file.call_args_list
        assert calls[0][1]["key"] == f"documents/{TEST_TENANT_ID}/test.pdf"
        assert calls[1][1]["key"] == f"documents/{TEST_TENANT_ID}/test.pdf.metadata.json"
        
        # Verify sync was triggered
        mock_bedrock.start_ingestion_job.assert_called_once()
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_delete_document_handles_missing_metadata(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test deletion when metadata file doesn't exist."""
        mock_s3 = Mock()
        mock_bedrock = Mock()
        
        # Make metadata deletion raise an exception
        def delete_side_effect(bucket, key):
            if key.endswith(".metadata.json"):
                raise Exception("File not found")
        
        mock_s3.delete_file.side_effect = delete_side_effect
        mock_s3_adapter_class.return_value = mock_s3
        mock_bedrock_adapter_class.return_value = mock_bedrock
        
        service = IngestionService(config=mock_config)
        # Should not raise exception
        response = service.delete_document("test.pdf", tenant_id=TEST_TENANT_ID)
        
        assert response["success"] is True
        assert response["data"].status == "deleted"
    
    def test_generate_metadata_json(self, ingestion_service):
        """Test metadata JSON generation."""
        attributes = {
            "author": "Dr. Smith",
            "year": 2023,
            "tags": ["medical", "research"]
        }
        
        json_string = ingestion_service._generate_metadata_json(attributes)
        metadata_doc = json.loads(json_string)
        
        assert "metadataAttributes" in metadata_doc
        assert metadata_doc["metadataAttributes"]["author"] == "Dr. Smith"
        assert metadata_doc["metadataAttributes"]["year"] == 2023
        assert metadata_doc["metadataAttributes"]["tags"] == ["medical", "research"]
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_load_metadata_success(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test loading metadata from S3."""
        mock_s3 = Mock()
        metadata_content = json.dumps({
            "metadataAttributes": {
                "author": "Dr. Smith",
                "year": 2023
            }
        })
        mock_s3.get_file.return_value = metadata_content.encode('utf-8')
        mock_s3_adapter_class.return_value = mock_s3
        mock_bedrock_adapter_class.return_value = Mock()
        
        service = IngestionService(config=mock_config)
        metadata = service._load_metadata("documents/test.pdf.metadata.json")
        
        assert metadata["author"] == "Dr. Smith"
        assert metadata["year"] == 2023
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_load_metadata_handles_errors(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test loading metadata handles errors gracefully."""
        mock_s3 = Mock()
        mock_s3.get_file.side_effect = Exception("File not found")
        mock_s3_adapter_class.return_value = mock_s3
        mock_bedrock_adapter_class.return_value = Mock()
        
        service = IngestionService(config=mock_config)
        metadata = service._load_metadata("documents/missing.pdf.metadata.json")
        
        assert metadata is None
    
    @patch('app.services.ingestion.ingestion_service.S3Adapter')
    @patch('app.services.ingestion.ingestion_service.BedrockAdapter')
    def test_trigger_sync_skips_when_no_kb_id(self, mock_bedrock_adapter_class, mock_s3_adapter_class, mock_config):
        """Test sync is skipped when KB IDs are not configured."""
        mock_config.BEDROCK_KB_ID = ""
        mock_config.BEDROCK_DATA_SOURCE_ID = ""
        
        mock_bedrock = Mock()
        mock_bedrock_adapter_class.return_value = mock_bedrock
        mock_s3_adapter_class.return_value = Mock()
        
        service = IngestionService(config=mock_config)
        service._trigger_sync()
        
        # Should not call start_ingestion_job
        mock_bedrock.start_ingestion_job.assert_not_called()
