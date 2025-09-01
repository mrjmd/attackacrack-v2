"""
Test configuration and fixtures for Attack-a-Crack v2 backend tests.

This module provides shared test fixtures and configuration for all tests.
"""

import asyncio
import os
import sys
import pytest
import pytest_asyncio
from threading import Lock

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


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear the LRU cache for settings between tests to prevent isolation issues."""
    # Clear settings cache before each test
    from app.core.config import get_settings
    get_settings.cache_clear()
    
    yield
    
    # Clear again after test to ensure clean slate
    get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Set up test environment variables."""
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://attackacrack:attackacrack_password@db:5432/attackacrack_test"
    os.environ["TEST_DATABASE_URL"] = "postgresql+asyncpg://attackacrack:attackacrack_password@db:5432/attackacrack_test"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:5173"
    os.environ["DEBUG"] = "true"
    
    yield
    
    # Cleanup environment
    test_vars = ["ENVIRONMENT", "DATABASE_URL", "TEST_DATABASE_URL", "CORS_ORIGINS", "DEBUG"]
    for var in test_vars:
        os.environ.pop(var, None)


@pytest_asyncio.fixture
async def app():
    """Create FastAPI application instance for testing."""
    # This will fail initially - no main.py exists yet
    from app.main import app
    return app


# Removed clear_database fixture - db_session transaction rollback provides isolation


@pytest_asyncio.fixture
async def client(app, db_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""
    from app.core.deps import get_db, get_current_user
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Create a shared session factory for consistent database access
    TestSession = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Override the database dependency to use our test database
    async def override_get_db():
        async with TestSession() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    
    # Create separate auth function for dependency override
    from app.models.user import User
    from sqlalchemy import select
    from uuid import UUID
    from fastapi import HTTPException, status, Request
    
    async def override_get_current_user(request: Request):
        """Override get_current_user to use test database session."""
        async with TestSession() as session:
            # Extract token from request
            authorization = request.headers.get('authorization')
            if not authorization or not authorization.startswith('Bearer '):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            token = authorization.split(' ')[1] if len(authorization.split(' ')) > 1 else ''
            
            # Mock token validation
            if token and token.startswith("test_token_for_"):
                try:
                    user_id_str = token.replace("test_token_for_", "")
                    user_id = UUID(user_id_str)
                    
                    query = select(User).where(User.id == user_id)
                    result = await session.execute(query)
                    user = result.scalar_one_or_none()
                    
                    if not user or not user.is_active:
                        # For test environment, create user if not found
                        import os
                        if os.getenv('ENVIRONMENT') == 'test':
                            try:
                                mock_user = User(
                                    id=user_id,
                                    email=f"test_{user_id_str[:8]}@example.com",
                                    name="Test User",
                                    is_active=True
                                )
                                session.add(mock_user)
                                await session.commit()
                                await session.refresh(mock_user)
                                return mock_user
                            except Exception:
                                await session.rollback()
                        
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authentication credentials",
                            headers={"WWW-Authenticate": "Bearer"}
                        )
                    
                    # User authenticated successfully
                    return user
                except ValueError:
                    # Invalid UUID format
                    pass
            
            # Invalid or missing token
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    # Apply the overrides
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    finally:
        # Clean up the overrides
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_settings():
    """Mock settings for testing configuration."""
    return {
        "environment": "test",
        "database_url": "postgresql+asyncpg://attackacrack:attackacrack_password@db:5432/attackacrack_test",
        "cors_origins": ["http://localhost:3000", "http://localhost:5173"],
        "debug": True,
    }


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create test database engine with connection pooling."""
    import uuid
    import asyncpg
    from sqlalchemy import text
    
    # Create a unique database name for this test session
    unique_db = f"test_{str(uuid.uuid4()).replace('-', '_')[:8]}"
    
    # Base connection to create the test database
    base_url = "postgresql+asyncpg://attackacrack:attackacrack_password@db:5432/postgres"
    base_engine = create_async_engine(base_url)
    
    # Create unique test database (must be outside transaction)
    async with base_engine.connect() as conn:
        await conn.execute(text('COMMIT'))  # End any transaction
        await conn.execute(text(f'CREATE DATABASE "{unique_db}"'))
    
    await base_engine.dispose()
    
    # Now connect to the unique test database
    database_url = f"postgresql+asyncpg://attackacrack:attackacrack_password@db:5432/{unique_db}"
    
    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=5,  # Smaller pool for unique database
        max_overflow=10,
        isolation_level="READ_COMMITTED"  # Ensure proper isolation
    )
    
    # Database setup: Create tables in the fresh database
    try:
        from app.models.base import Base
        
        # Import all models to ensure they're registered with metadata
        from app.models.property import Property, contact_property_association
        from app.models import User, Contact, Campaign, Message, WebhookEvent, PropertyList
        
        # Create all tables normally - the unique database ensures no conflicts
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
                
    except ImportError:
        # Models don't exist yet - this is expected in RED phase
        pass
    
    yield engine
    
    # Cleanup: Close engine and drop the unique database
    await engine.dispose()
    
    # Clean up the unique test database
    base_engine = create_async_engine(base_url)
    async with base_engine.connect() as conn:
        await conn.execute(text('COMMIT'))  # End any transaction
        # Terminate connections to the database before dropping
        await conn.execute(text(f"""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = '{unique_db}' AND pid <> pg_backend_pid()
        """))
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{unique_db}"'))
    
    await base_engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing with proper isolation."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Clean up BEFORE the test to ensure clean state
    async with async_session() as cleanup_session:
        print("[DEBUG] PRE-TEST cleanup starting...")
        await _cleanup_database(cleanup_session)
    
    async with async_session() as session:
        try:
            yield session
        finally:
            # Clean up AFTER the test
            print("[DEBUG] POST-TEST cleanup starting...")
            await _cleanup_database(session)


async def _cleanup_database(session: AsyncSession):
    """Clean up all test data from database."""
    try:
        from app.models import User, Contact, Campaign, Message, WebhookEvent, Property, PropertyList
        from app.models.property import contact_property_association
        from sqlalchemy import text
        
        # Clean up all test data
        
        # Use TRUNCATE for faster cleanup (PostgreSQL specific)
        # TRUNCATE CASCADE will handle foreign key constraints automatically
        table_names = [
            'contact_property_relationships',
            'messages',
            'webhook_events', 
            'campaigns',
            'properties',
            'lists',
            'contacts',
            'users'
        ]
        
        for table_name in table_names:
            # Truncate table
            await session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        
        await session.commit()
        # Cleanup completed
        
    except Exception as e:
        await session.rollback()
        # TRUNCATE failed, falling back to DELETE
        # If TRUNCATE fails, fall back to DELETE
        try:
            await session.execute(contact_property_association.delete())
            await session.execute(Message.__table__.delete())
            await session.execute(WebhookEvent.__table__.delete())
            await session.execute(Campaign.__table__.delete())
            await session.execute(Property.__table__.delete())
            await session.execute(PropertyList.__table__.delete())
            await session.execute(Contact.__table__.delete())
            await session.execute(User.__table__.delete())
            await session.commit()
            # DELETE fallback completed
        except Exception as e2:
            await session.rollback()
            # Database cleanup failed completely
            import logging
            logging.warning(f"Database cleanup failed: {e}")


@pytest_asyncio.fixture
async def db_session_commit(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session that commits (for testing transactions)."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Clean up BEFORE the test
    async with async_session() as cleanup_session:
        await _cleanup_database(cleanup_session)
    
    async with async_session() as session:
        try:
            yield session
        finally:
            # Clean up AFTER the test
            await _cleanup_database(session)


@pytest.fixture
def test_database_url():
    """Provide test database URL for migration tests."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://attackacrack:attackacrack_password@db:5432/attackacrack_test"
    )


# Webhook Testing Fixtures

@pytest.fixture
def openphone_payloads():
    """Provide OpenPhone webhook payload examples."""
    from tests.fixtures.openphone_payloads import OpenPhonePayloads, TEST_SCENARIOS, INVALID_PAYLOADS
    
    class PayloadContainer:
        payloads = OpenPhonePayloads
        scenarios = TEST_SCENARIOS
        invalid = INVALID_PAYLOADS
    
    return PayloadContainer()


@pytest.fixture
def webhook_signature():
    """Provide utility for generating valid webhook signatures."""
    import json
    import hmac
    import hashlib
    
    def sign_payload(payload: dict, secret: str = "test_webhook_secret") -> str:
        """Generate HMAC-SHA256 signature for webhook payload."""
        payload_json = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    return sign_payload


@pytest_asyncio.fixture
async def webhook_test_setup(client: AsyncClient, webhook_signature):
    """Setup for webhook testing with mocked dependencies."""
    class WebhookTester:
        def __init__(self, client, sign_func):
            self.client = client
            self.sign = sign_func
        
        async def send_webhook(self, payload: dict, signature: str = None, headers: dict = None):
            """Send webhook with proper signature."""
            if signature is None:
                signature = self.sign(payload)
            
            test_headers = {
                "X-OpenPhone-Signature": signature,
                "Content-Type": "application/json"
            }
            
            if headers:
                test_headers.update(headers)
            
            return await self.client.post(
                "/api/v1/webhooks/openphone",
                json=payload,
                headers=test_headers
            )
    
    return WebhookTester(client, webhook_signature)


@pytest_asyncio.fixture
async def test_user(db_engine):
    """Create a test user that persists across sessions."""
    from app.models import User
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    import uuid
    
    # Clean database before creating user
    async with sessionmaker(db_engine, class_=AsyncSession)() as cleanup_session:
        # Clean database before creating user
        await _cleanup_database(cleanup_session)
    
    # Create session factory for user creation
    TestSessionLocal = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Create user in its own session so it can be seen by other sessions
    unique_id = str(uuid.uuid4())[:8]
    async with TestSessionLocal() as session:
        user = User(
            email=f"test_{unique_id}@example.com",
            name="Test User",
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        # User created successfully
        return user