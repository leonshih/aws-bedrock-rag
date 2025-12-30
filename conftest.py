"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and applies to all tests.
"""
import os
import pytest


def pytest_configure(config):
    """
    Configure test environment settings.
    
    Sets APP_ENV to 'test' for all test runs.
    """
    os.environ["APP_ENV"] = "test"


# Shared test constants
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"
