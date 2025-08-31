"""
Test configuration and fixtures for Attack-a-Crack v2 backend tests.

This module provides shared test fixtures and configuration for all tests.
"""

import asyncio
import os
import sys
import pytest
import pytest_asyncio

# Fix import path for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, '/app')
from httpx import AsyncClient
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
# StaticPool removed - PostgreSQL only


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


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine with connection pooling."""
    # Use PostgreSQL for all tests - NEVER SQLite!
    # As per CLAUDE.md database specialist rules
    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://attackacrack:attackacrack_password@db:5432/attackacrack_dev"
    )
    
    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=2,  # Smaller pool for tests
        max_overflow=5
    )
    
    # Create tables using our models
    try:
        from app.models.base import Base
        # Import all models to ensure they're registered
        from app.models import User, Contact, Campaign, Message, WebhookEvent
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except ImportError:
        # Models don't exist yet - this is expected in RED phase
        pass
    
    yield engine
    
    # Cleanup
    try:
        from app.models.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except:
        pass
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session with automatic rollback."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Start transaction
        transaction = await session.begin()
        
        try:
            yield session
        finally:
            # Always rollback to keep tests isolated
            if transaction.is_active:
                await transaction.rollback()


@pytest_asyncio.fixture
async def db_session_commit(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session that commits (for testing transactions)."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        # Let the test handle commit/rollback


@pytest.fixture
def test_database_url():
    """Provide test database URL for migration tests."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )