"""
Configuration Management

Centralized configuration loader for environment variables.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration from environment variables."""
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-1")
    AWS_PROFILE: Optional[str] = os.getenv("AWS_PROFILE")
    
    # Bedrock Configuration
    BEDROCK_KB_ID: str = os.getenv("BEDROCK_KB_ID", "")
    BEDROCK_DATA_SOURCE_ID: str = os.getenv("BEDROCK_DATA_SOURCE_ID", "")
    BEDROCK_MODEL_ID: str = os.getenv(
        "BEDROCK_MODEL_ID",
        "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    
    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    
    # Application Configuration
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Tenant Configuration
    TENANT_HEADER_NAME: str = os.getenv("TENANT_HEADER_NAME", "X-Tenant-ID")
    TENANT_ID_REQUIRED: bool = os.getenv("TENANT_ID_REQUIRED", "true").lower() == "true"
    
    # File Upload Configuration
    ALLOWED_FILE_EXTENSIONS: frozenset = frozenset([
        ".pdf", ".txt", ".doc", ".docx", ".md", ".csv",
        ".json", ".xml", ".html", ".htm", ".rtf", ".odt",
        ".xls", ".xlsx", ".ppt", ".pptx"
    ])


def get_config() -> Config:
    """
    Get application configuration.
    
    Returns:
        Config: Configuration object with environment variables.
    """
    return Config
