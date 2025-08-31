"""
Database configuration and session management for Attack-a-Crack v2.

This module provides async SQLAlchemy engine, session factory, and FastAPI dependency.
Following database specialist patterns for connection pooling and transaction management.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:password@localhost:5432/attackacrack_v2"
)

# Force asyncpg by ensuring URL uses asyncpg driver
if DATABASE_URL.startswith('postgresql://') and '+asyncpg' not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Create async engine with proper pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",  # SQL logging in debug mode
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,   # Recycle connections every hour
    pool_size=5,         # Base pool size
    max_overflow=10,     # Maximum overflow connections
    # Use StaticPool for SQLite testing
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    connect_args={
        "check_same_thread": False,  # For SQLite compatibility
    } if "sqlite" in DATABASE_URL else {},
)

# Session factory with proper configuration
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects accessible after commit
    autoflush=True,          # Auto-flush before queries
    autocommit=False,        # Explicit transaction control
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to provide database session.
    
    Ensures proper session cleanup and transaction management.
    Each request gets its own session that's automatically closed.
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            # Rollback on any exception
            await session.rollback()
            raise
        finally:
            # Session cleanup happens automatically via context manager
            pass


async def init_db() -> None:
    """
    Initialize database with all tables.
    
    Used for development and testing. In production, use Alembic migrations.
    """
    from app.models.base import Base
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database engine and cleanup connections.
    
    Call this on application shutdown to ensure clean shutdown.
    """
    await engine.dispose()


# Health check function for database connectivity
async def check_database_health() -> dict:
    """
    Check database connectivity and return health status.
    
    Returns:
        dict: Health status with connection info
    """
    try:
        async with SessionLocal() as session:
            from sqlalchemy import text
            
            # Simple connectivity test
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
            # Get connection pool stats
            pool = engine.pool
            try:
                pool_stats = {
                    "size": getattr(pool, 'size', lambda: 0)(),
                    "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                    "overflow": getattr(pool, 'overflow', lambda: 0)(),
                    "invalid": getattr(pool, 'invalid', lambda: 0)() if hasattr(pool, 'invalid') else 0,
                }
            except AttributeError:
                pool_stats = {"status": "unknown"}
            
            return {
                "status": "healthy",
                "database_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "unknown",
                "pool": pool_stats
            }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "unknown"
        }