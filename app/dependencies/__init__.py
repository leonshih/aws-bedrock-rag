"""
Dependencies module for FastAPI dependency injection.

This module contains reusable dependencies for:
- Authentication and authorization
- Request validation
- Context extraction
"""

from app.dependencies.tenant import get_tenant_context

__all__ = ["get_tenant_context"]
