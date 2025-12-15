"""
Ingestion Service

Orchestrates document upload, metadata management, and Knowledge Base synchronization.
Handles the complete lifecycle of document ingestion into Bedrock Knowledge Base.
"""
import json
import logging
from typing import List, Optional, Dict, Any, BinaryIO
from datetime import datetime
from app.adapters.s3 import S3Adapter
from app.adapters.bedrock import BedrockAdapter
from app.dtos.file import FileResponse, FileListResponse, FileDeleteResponse, FileMetadata
from app.utils.config import Config

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for document ingestion and management."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize ingestion service.
        
        Args:
            config: Configuration object (uses default if not provided)
        """
        self.config = config or Config()
        self.s3_adapter = S3Adapter(self.config)
        self.bedrock_adapter = BedrockAdapter(self.config)
        self.bucket_name = self.config.S3_BUCKET_NAME
    
    def upload_document(
        self,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileResponse:
        """
        Upload a document to S3 and trigger Knowledge Base sync.
        
        Args:
            file_content: Binary file content
            filename: Name of the file
            metadata: Optional custom metadata attributes as dict
            
        Returns:
            FileResponse with upload details
        """
        logger.info(f"Uploading document: {filename} ({len(file_content)} bytes)")
        
        # Construct S3 key (store in documents/ prefix)
        s3_key = f"documents/{filename}"
        
        # Upload the document to S3
        self.s3_adapter.upload_file(
            file_content=file_content,
            bucket=self.bucket_name,
            key=s3_key
        )
        
        # If metadata provided, create and upload .metadata.json sidecar
        if metadata:
            metadata_key = f"{s3_key}.metadata.json"
            metadata_content = self._generate_metadata_json(metadata)
            
            self.s3_adapter.upload_file(
                file_content=metadata_content.encode('utf-8'),
                bucket=self.bucket_name,
                key=metadata_key,
                metadata={"Content-Type": "application/json"}
            )
            logger.debug(f"Uploaded metadata file: {metadata_key}")
        
        # Trigger Bedrock Knowledge Base sync
        self._trigger_sync()
        logger.info(f"Successfully uploaded {filename}, sync triggered")
        
        # Return file response
        return FileResponse(
            filename=filename,
            size=len(file_content),
            s3_key=s3_key,
            last_modified=datetime.utcnow(),
            metadata=metadata if metadata else None
        )
    
    def list_documents(self, prefix: str = "documents/") -> FileListResponse:
        """
        List all documents in the Knowledge Base.
        
        Args:
            prefix: S3 prefix to filter documents (default: documents/)
            
        Returns:
            FileListResponse with list of files and metadata
        """
        logger.info(f"Listing documents with prefix: {prefix}")
        
        # List all objects in the bucket with the prefix
        s3_objects = self.s3_adapter.list_files(
            bucket=self.bucket_name,
            prefix=prefix
        )
        
        # Filter out .metadata.json files and build FileResponse objects
        files = []
        total_size = 0
        
        # Group files with their metadata
        file_map = {}
        metadata_map = {}
        
        for obj in s3_objects:
            key = obj["key"]
            
            if key.endswith(".metadata.json"):
                # Store metadata for later matching
                base_key = key[:-14]  # Remove .metadata.json
                metadata_map[base_key] = key
            else:
                # Regular file
                file_map[key] = obj
        
        # Build FileResponse objects
        for key, obj in file_map.items():
            filename = key.split("/")[-1]
            size = obj.get("size", 0)
            last_modified = obj.get("last_modified")
            
            # Check if metadata exists
            metadata_attrs = None
            if key in metadata_map:
                metadata_attrs = self._load_metadata(metadata_map[key])
            
            files.append(
                FileResponse(
                    filename=filename,
                    size=size,
                    s3_key=key,
                    last_modified=last_modified,
                    metadata=metadata_attrs
                )
            )
            total_size += size
        
        logger.info(f"Listed {len(files)} documents, total size: {total_size} bytes")
        
        return FileListResponse(
            files=files,
            total_count=len(files),
            total_size=total_size
        )
    
    def delete_document(self, filename: str) -> FileDeleteResponse:
        """
        Delete a document and its metadata from S3, then trigger sync.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            FileDeleteResponse with deletion status
        """
        logger.info(f"Deleting document: {filename}")
        
        # Construct S3 keys
        s3_key = f"documents/{filename}"
        metadata_key = f"{s3_key}.metadata.json"
        
        # Delete the main document
        self.s3_adapter.delete_file(
            bucket=self.bucket_name,
            key=s3_key
        )
        
        # Try to delete metadata file (ignore if doesn't exist)
        try:
            self.s3_adapter.delete_file(
                bucket=self.bucket_name,
                key=metadata_key
            )
            logger.debug(f"Deleted metadata file: {metadata_key}")
        except Exception as e:
            # Metadata file may not exist, continue
            logger.debug(f"No metadata file to delete for {filename}: {e}")
            pass
        
        # Trigger Knowledge Base sync
        self._trigger_sync()
        logger.info(f"Successfully deleted {filename}, sync triggered")
        
        return FileDeleteResponse(
            filename=filename,
            status="deleted",
            message="File and metadata removed, Knowledge Base sync triggered"
        )
    
    def _generate_metadata_json(self, attributes: Dict[str, Any]) -> str:
        """
        Generate .metadata.json content in Bedrock-compatible format.
        
        Args:
            attributes: Custom metadata attributes
            
        Returns:
            JSON string formatted for Bedrock Knowledge Base
        """
        # Bedrock metadata format:
        # {
        #   "metadataAttributes": {
        #     "key1": "value1",
        #     "key2": 123
        #   }
        # }
        metadata_doc = {
            "metadataAttributes": attributes
        }
        return json.dumps(metadata_doc, indent=2)
    
    def _load_metadata(self, metadata_key: str) -> Optional[Dict[str, Any]]:
        """
        Load and parse metadata from S3.
        
        Args:
            metadata_key: S3 key of the .metadata.json file
            
        Returns:
            Dictionary of metadata attributes or None if error
        """
        try:
            content = self.s3_adapter.get_file(
                bucket=self.bucket_name,
                key=metadata_key
            )
            metadata_doc = json.loads(content.decode('utf-8'))
            return metadata_doc.get("metadataAttributes", {})
        except Exception:
            return None
    
    def _trigger_sync(self) -> None:
        """
        Trigger Bedrock Knowledge Base data source sync.
        
        This starts an ingestion job to index new/updated/deleted documents.
        """
        if not self.config.BEDROCK_KB_ID or not self.config.BEDROCK_DATA_SOURCE_ID:
            # Skip sync if KB IDs not configured (e.g., in mock mode)
            return
        
        self.bedrock_adapter.start_ingestion_job(
            kb_id=self.config.BEDROCK_KB_ID,
            data_source_id=self.config.BEDROCK_DATA_SOURCE_ID
        )
