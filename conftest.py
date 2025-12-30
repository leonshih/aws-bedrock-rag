"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and applies to all tests.
"""
import os
import pytest


def pytest_configure(config):
    """
    Force MOCK_MODE=true for all test runs.
    
    This ensures tests never accidentally hit real AWS services,
    preventing unexpected costs and test failures due to missing credentials.
    """
    os.environ["MOCK_MODE"] = "true"
    os.environ["APP_ENV"] = "test"


# Shared test constants
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"
