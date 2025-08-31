"""
Test configuration and fixtures for Attack-a-Crack v2 backend tests.

This module provides shared test fixtures and configuration for all tests.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import AsyncGenerator, Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Set up test environment variables."""
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:5173"
    os.environ["DEBUG"] = "true"
    
    yield
    
    # Cleanup environment
    test_vars = ["ENVIRONMENT", "DATABASE_URL", "CORS_ORIGINS", "DEBUG"]
    for var in test_vars:
        os.environ.pop(var, None)


@pytest_asyncio.fixture
async def app():
    """Create FastAPI application instance for testing."""
    # This will fail initially - no main.py exists yet
    from app.main import app
    return app


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_settings():
    """Mock settings for testing configuration."""
    return {
        "environment": "test",
        "database_url": "postgresql://test:test@localhost:5432/test_db",
        "cors_origins": ["http://localhost:3000", "http://localhost:5173"],
        "debug": True,
    }