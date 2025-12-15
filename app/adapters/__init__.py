"""
AWS Adapters Module

Low-level adapters for interacting with AWS services.
"""
from .bedrock import BedrockAdapter
from .s3 import S3Adapter

__all__ = ['BedrockAdapter', 'S3Adapter']
