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
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "true").lower() == "true"
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.APP_ENV == "production"
    
    @classmethod
    def is_mock_enabled(cls) -> bool:
        """Check if mock mode is enabled."""
        return cls.MOCK_MODE


def get_config() -> Config:
    """
    Get application configuration.
    
    Returns:
        Config: Configuration object with environment variables.
    """
    return Config


def get_config_with_status() -> dict:
    """
    Get application configuration with success status.
    
    Returns:
        Dict with success flag and config data.
    """
    return {
        "success": True,
        "data": Config
    }
