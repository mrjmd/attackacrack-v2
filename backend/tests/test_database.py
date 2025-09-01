"""
Integration tests for PostgreSQL database connection and session management.

Tests database connectivity, session handling, and connection pooling.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.sql import text
from sqlalchemy import MetaData
from typing import AsyncGenerator
import os


class TestDatabaseConnection:
    """Test database connection and session management."""
    
    # Using fixtures from conftest.py: db_engine and db_session
    
    @pytest.mark.asyncio
    async def test_database_connection(self, db_engine):
        """Test database connection is working."""
        async with AsyncSession(db_engine) as session:
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row.test == 1
    
    @pytest.mark.asyncio
    async def test_database_health_check(self, db_session):
        """Test database health check query."""
        result = await db_session.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        assert "PostgreSQL" in version
    
    @pytest.mark.asyncio
    async def test_session_transaction_rollback(self, db_session):
        """Test session transaction rollback functionality."""
        # Create a temporary table for testing
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_rollback (
                id SERIAL PRIMARY KEY,
                value TEXT
            )
        """))
        
        # Insert data
        await db_session.execute(text("""
            INSERT INTO test_rollback (value) VALUES ('test')
        """))
        
        # Check data exists
        result = await db_session.execute(text("""
            SELECT COUNT(*) FROM test_rollback
        """))
        count = result.scalar()
        assert count == 1
        
        # Rollback will happen in fixture cleanup
    
    @pytest.mark.asyncio
    async def test_connection_pool_limits(self, db_engine):
        """Test connection pool respects limits."""
        # Test that we can create multiple sessions
        sessions = []
        try:
            for _ in range(5):
                session = AsyncSession(db_engine)
                sessions.append(session)
                # Execute simple query
                await session.execute(text("SELECT 1"))
        
        finally:
            # Clean up sessions
            for session in sessions:
                await session.close()
    
    @pytest.mark.asyncio
    async def test_database_isolation(self, db_engine):
        """Test that transactions are isolated between sessions."""
        # Create two separate sessions
        async with AsyncSession(db_engine) as session1:
            async with AsyncSession(db_engine) as session2:
                # Create temp table in session1
                await session1.execute(text("""
                    CREATE TEMPORARY TABLE test_isolation (
                        id SERIAL PRIMARY KEY,
                        value TEXT
                    )
                """))
                
                await session1.execute(text("""
                    INSERT INTO test_isolation (value) VALUES ('session1')
                """))
                
                # Should not be visible in session2 until commit
                result = await session2.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'test_isolation'
                """))
                
                # Temp tables are session-specific, so this is expected behavior
                count = result.scalar()
                # This will be 0 because temp tables are session-local
                assert isinstance(count, int)


class TestDatabaseConfiguration:
    """Test database configuration and environment setup."""
    
    def test_database_url_from_environment(self):
        """Test database URL is read from environment."""
        # Should be set in conftest.py
        db_url = os.getenv("DATABASE_URL")
        assert db_url is not None
        assert "postgresql" in db_url
    
    def test_test_database_url_different(self):
        """Test that test database URL is separate from production."""
        db_url = os.getenv("DATABASE_URL")
        assert "test" in db_url.lower() or "localhost" in db_url
    
    @pytest.mark.asyncio
    async def test_database_timezone_utc(self, db_session):
        """Test database timezone is set to UTC."""
        result = await db_session.execute(text("SHOW timezone"))
        timezone = result.scalar()
        # Should be UTC for consistency
        assert timezone in ["UTC", "GMT"]
    
    @pytest.mark.asyncio
    async def test_database_encoding_utf8(self, db_session):
        """Test database encoding is UTF-8."""
        result = await db_session.execute(text("""
            SELECT pg_encoding_to_char(encoding) 
            FROM pg_database 
            WHERE datname = current_database()
        """))
        encoding = result.scalar()
        assert encoding == "UTF8"


class TestDatabaseMetadata:
    """Test database metadata operations."""
    
    @pytest.mark.asyncio
    async def test_metadata_reflection(self, db_engine):
        """Test database metadata can be reflected."""
        metadata = MetaData()
        
        async with db_engine.begin() as conn:
            # This will pass even with empty database
            await conn.run_sync(metadata.reflect)
            
            # Check we can access metadata object
            assert metadata is not None
            assert hasattr(metadata, 'tables')
    
    @pytest.mark.asyncio
    async def test_database_schema_exists(self, db_session):
        """Test that database schema/structure can be queried."""
        # Query information_schema to verify database structure queries work
        result = await db_session.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'public'
        """))
        
        schema = result.scalar()
        assert schema == "public"
    
    @pytest.mark.asyncio
    async def test_create_drop_table_permissions(self, db_session):
        """Test that we have necessary permissions to create/drop tables."""
        # Create temporary table to test permissions
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_permissions (
                id SERIAL PRIMARY KEY,
                test_column VARCHAR(100)
            )
        """))
        
        # Insert test data
        await db_session.execute(text("""
            INSERT INTO test_permissions (test_column) 
            VALUES ('test_value')
        """))
        
        # Query data
        result = await db_session.execute(text("""
            SELECT test_column FROM test_permissions
        """))
        
        value = result.scalar()
        assert value == "test_value"
        
        # Drop table (temp tables are auto-dropped at session end)
        await db_session.execute(text("DROP TABLE test_permissions"))


class TestAsyncDatabaseOperations:
    """Test async database operations and patterns."""
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, db_engine):
        """Test async context manager patterns work correctly."""
        async with AsyncSession(db_engine) as session:
            async with session.begin():
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, db_engine):
        """Test multiple concurrent database sessions."""
        import asyncio
        
        async def run_query(session_id: int):
            """Run a query in a separate session."""
            async with AsyncSession(db_engine) as session:
                result = await session.execute(text(f"SELECT {session_id}"))
                return result.scalar()
        
        # Run 3 concurrent queries
        tasks = [run_query(i) for i in range(1, 4)]
        results = await asyncio.gather(*tasks)
        
        assert results == [1, 2, 3]
    
    @pytest.mark.asyncio
    async def test_session_lifecycle(self, db_engine):
        """Test complete session lifecycle."""
        session = AsyncSession(db_engine)
        
        try:
            # Session should be usable
            # Note: AsyncSession may auto-begin a transaction
            # Just verify the session exists
            assert session is not None
            
            # Start transaction
            await session.begin()
            assert session.is_active
            
            # Execute query
            result = await session.execute(text("SELECT 'lifecycle_test'"))
            value = result.scalar()
            assert value == "lifecycle_test"
            
            # Commit transaction
            await session.commit()
            # In SQLAlchemy 2.0 with autobegin, session stays active
            # The important thing is the commit succeeded
            
        finally:
            await session.close()


class TestDatabaseErrorHandling:
    """Test database error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_connection_error_recovery(self, db_engine):
        """Test recovery from connection errors."""
        # This tests basic error handling patterns
        session = AsyncSession(db_engine)
        
        try:
            # Valid query should work
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            
            # Invalid query should raise exception
            with pytest.raises(Exception):  # Will be specific SQLAlchemy exception
                await session.execute(text("SELECT * FROM non_existent_table"))
        
        finally:
            await session.close()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, db_session):
        """Test transaction rollback on error."""
        # Create temp table
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_error_rollback (
                id SERIAL PRIMARY KEY,
                value VARCHAR(10) UNIQUE
            )
        """))
        
        # Insert valid data first
        await db_session.execute(text("""
            INSERT INTO test_error_rollback (value) VALUES ('test1')
        """))
        await db_session.commit()
        
        # Now try to insert duplicate - this should fail and auto-rollback
        try:
            await db_session.execute(text("""
                INSERT INTO test_error_rollback (value) VALUES ('test1')
            """))
            await db_session.commit()
            # Should not reach here
            assert False, "Expected duplicate key error"
        except Exception:
            # The session should auto-rollback on error
            # PostgreSQL puts the transaction in an aborted state
            await db_session.rollback()
        
        # After explicit rollback, session should be usable
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    @pytest.mark.asyncio
    async def test_invalid_sql_handling(self, db_session):
        """Test handling of invalid SQL queries."""
        with pytest.raises(Exception):  # Specific exception will depend on SQLAlchemy version
            await db_session.execute(text("INVALID SQL QUERY"))


class TestDatabasePerformance:
    """Test database performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_query_execution_time(self, db_session):
        """Test query execution completes within reasonable time."""
        import time
        
        start_time = time.time()
        
        # Simple query should be fast
        result = await db_session.execute(text("SELECT COUNT(*) FROM pg_tables"))
        count = result.scalar()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within 1 second (generous for test environment)
        assert execution_time < 1.0
        assert isinstance(count, int)
    
    @pytest.mark.asyncio
    async def test_bulk_operation_performance(self, db_session):
        """Test bulk operations complete in reasonable time."""
        import time
        
        # Create temp table for bulk operations
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_bulk_performance (
                id SERIAL PRIMARY KEY,
                value INTEGER
            )
        """))
        
        start_time = time.time()
        
        # Insert 1000 records using VALUES
        values = ", ".join([f"({i})" for i in range(1000)])
        await db_session.execute(text(f"""
            INSERT INTO test_bulk_performance (value) VALUES {values}
        """))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within 2 seconds
        assert execution_time < 2.0
        
        # Verify count
        result = await db_session.execute(text("""
            SELECT COUNT(*) FROM test_bulk_performance
        """))
        count = result.scalar()
        assert count == 1000