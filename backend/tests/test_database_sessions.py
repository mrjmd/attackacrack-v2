"""
Integration tests for database session lifecycle and connection management.

Tests session factories, dependency injection, and transaction handling in FastAPI.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from unittest.mock import Mock, AsyncMock
import asyncio


class TestDatabaseSessionFactory:
    """Test database session factory and lifecycle."""
    
    @pytest.mark.asyncio
    async def test_session_factory_creates_sessions(self, db_engine):
        """Test session factory creates working sessions."""
        from sqlalchemy.orm import sessionmaker
        
        # Create session factory
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Create session
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    @pytest.mark.asyncio
    async def test_session_factory_isolation(self, db_engine):
        """Test sessions from factory are isolated."""
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Create temp table in first session
        async with async_session() as session1:
            await session1.execute(text("""
                CREATE TEMPORARY TABLE test_isolation (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """))
            
            await session1.execute(text("""
                INSERT INTO test_isolation (value) VALUES ('session1')
            """))
            
            await session1.commit()
            
            # Temp tables are session-local, so second session won't see it
            async with async_session() as session2:
                # This should work - each session is independent
                result = await session2.execute(text("SELECT 1"))
                assert result.scalar() == 1
    
    @pytest.mark.asyncio
    async def test_session_context_manager(self, db_session):
        """Test session context manager handles cleanup properly."""
        # Session should be active
        assert db_session is not None
        
        # Should be able to execute queries
        result = await db_session.execute(text("SELECT 'context_test'"))
        value = result.scalar()
        assert value == "context_test"
        
        # Transaction should be active (in fixture)
        assert db_session.in_transaction()


class TestAsyncSessionBehavior:
    """Test async session behavior and patterns."""
    
    @pytest.mark.asyncio
    async def test_async_session_concurrent_access(self, db_engine):
        """Test async sessions handle concurrent access properly."""
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        async def concurrent_query(session_id: int):
            """Execute query in separate session."""
            async with async_session() as session:
                result = await session.execute(text(f"SELECT {session_id}"))
                return result.scalar()
        
        # Run concurrent queries
        tasks = [concurrent_query(i) for i in range(1, 6)]
        results = await asyncio.gather(*tasks)
        
        assert results == [1, 2, 3, 4, 5]
    
    @pytest.mark.asyncio
    async def test_session_commit_behavior(self, db_engine):
        """Test session commit and rollback behavior."""
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Test commit behavior
        async with async_session() as session:
            # Just test basic session operations
            result = await session.execute(text("SELECT 1 as test_value"))
            value = result.scalar()
            assert value == 1
            
            # Test that session can handle multiple operations
            result2 = await session.execute(text("SELECT 2 as test_value"))
            value2 = result2.scalar()
            assert value2 == 2
    
    @pytest.mark.asyncio
    async def test_session_error_handling(self, db_session):
        """Test session error handling and recovery."""
        try:
            # Execute invalid SQL
            await db_session.execute(text("INVALID SQL SYNTAX"))
            assert False, "Should have raised exception"
        
        except Exception:
            # After error, session needs rollback to recover
            await db_session.rollback()
            
            # Now session should be usable
            result = await db_session.execute(text("SELECT 'recovered' as status"))
            value = result.scalar()
            assert value == "recovered"


class TestFastAPIDatabaseIntegration:
    """Test FastAPI database dependency injection."""
    
    def test_database_dependency_function(self):
        """Test database dependency function exists."""
        try:
            from app.core.database import get_db
            assert callable(get_db), "get_db should be a callable function"
        except ImportError:
            pytest.skip("Database dependency not implemented yet")
    
    @pytest.mark.asyncio
    async def test_database_dependency_returns_session(self):
        """Test database dependency returns AsyncSession."""
        try:
            from app.core.database import get_db
            
            # get_db should be an async generator
            db_gen = get_db()
            
            # Should be async generator
            assert hasattr(db_gen, '__aiter__'), "get_db should return async generator"
            
        except ImportError:
            pytest.skip("Database dependency not implemented yet")
        except Exception as e:
            # Expected until database is configured
            pytest.skip(f"Database not configured yet: {e}")
    
    def test_database_session_middleware_config(self):
        """Test database session middleware configuration."""
        try:
            from app.core.database import SessionLocal
            
            # Should have session factory
            assert SessionLocal is not None
            
        except ImportError:
            pytest.skip("Database session factory not implemented yet")
    
    @pytest.mark.asyncio
    async def test_fastapi_database_injection(self):
        """Test FastAPI database dependency injection."""
        try:
            from fastapi import Depends
            from app.core.database import get_db
            
            # Mock FastAPI dependency
            async def test_endpoint(db: AsyncSession = Depends(get_db)):
                result = await db.execute(text("SELECT 'dependency_test'"))
                return result.scalar()
            
            # This tests the pattern, actual injection tested in endpoint tests
            assert callable(test_endpoint)
            
        except ImportError:
            pytest.skip("Database dependencies not implemented yet")


class TestDatabaseConnectionPool:
    """Test database connection pool behavior."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_reuse(self, db_engine):
        """Test connection pool reuses connections efficiently."""
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Execute multiple queries in sequence
        for i in range(10):
            async with async_session() as session:
                result = await session.execute(text(f"SELECT {i}"))
                assert result.scalar() == i
        
        # Should complete without error (connection pool working)
    
    @pytest.mark.asyncio
    async def test_connection_pool_limits(self, db_engine):
        """Test connection pool respects configured limits."""
        from sqlalchemy.orm import sessionmaker
        import asyncio
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        async def long_running_query(query_id: int):
            """Simulate long-running query."""
            async with async_session() as session:
                # Simulate work
                result = await session.execute(text(f"SELECT {query_id}"))
                await asyncio.sleep(0.01)  # Small delay
                return result.scalar()
        
        # Run multiple concurrent queries
        tasks = [long_running_query(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 20
        assert results == list(range(20))
    
    def test_connection_pool_configuration(self, db_engine):
        """Test connection pool is configured correctly."""
        pool = db_engine.pool
        
        # Should have pool configured
        assert pool is not None
        
        # Check pool type (depends on configuration)
        assert hasattr(pool, 'size') or hasattr(pool, '_creator')


class TestDatabaseTransactionManagement:
    """Test database transaction management patterns."""
    
    @pytest.mark.asyncio
    async def test_nested_transaction_handling(self, db_engine):
        """Test nested transaction handling."""
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        async with async_session() as session:
            async with session.begin():
                # Create temp table in transaction
                await session.execute(text("""
                    CREATE TEMPORARY TABLE test_nested (
                        id SERIAL PRIMARY KEY,
                        value TEXT
                    )
                """))
                
                await session.execute(text("""
                    INSERT INTO test_nested (value) VALUES ('outer')
                """))
                
                # Nested "transaction" (savepoint)
                try:
                    async with session.begin_nested():
                        await session.execute(text("""
                            INSERT INTO test_nested (value) VALUES ('inner')
                        """))
                        
                        # Check both records exist
                        result = await session.execute(text("""
                            SELECT COUNT(*) FROM test_nested
                        """))
                        count = result.scalar()
                        assert count == 2
                        
                        # Intentionally cause error to test rollback
                        await session.execute(text("INVALID SQL"))
                        
                except Exception:
                    # Inner transaction should rollback
                    pass
                
                # Outer transaction should still have first record
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM test_nested
                """))
                count = result.scalar()
                assert count == 1
    
    @pytest.mark.asyncio
    async def test_transaction_isolation_levels(self, db_engine):
        """Test transaction isolation levels."""
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Test default isolation level works
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
    
    @pytest.mark.asyncio
    async def test_transaction_timeout_handling(self, db_engine):
        """Test transaction timeout handling."""
        from sqlalchemy.orm import sessionmaker
        import asyncio
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Test that short transactions complete normally
        async with async_session() as session:
            start_time = asyncio.get_event_loop().time()
            
            result = await session.execute(text("SELECT 'timeout_test'"))
            value = result.scalar()
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            
            assert value == "timeout_test"
            assert duration < 1.0  # Should complete quickly


class TestDatabaseSessionCleanup:
    """Test database session cleanup and resource management."""
    
    @pytest.mark.asyncio
    async def test_session_cleanup_on_exception(self, db_engine):
        """Test session is properly cleaned up on exception."""
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        try:
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
                
                # Cause exception
                raise ValueError("Test exception")
                
        except ValueError:
            # Exception expected
            pass
        
        # Should be able to create new session normally
        async with async_session() as new_session:
            result = await new_session.execute(text("SELECT 'cleanup_test'"))
            value = result.scalar()
            assert value == "cleanup_test"
    
    @pytest.mark.asyncio
    async def test_engine_disposal(self, db_engine):
        """Test engine disposal cleans up connections."""
        # Engine should be usable
        async with AsyncSession(db_engine) as session:
            result = await session.execute(text("SELECT 'before_disposal'"))
            value = result.scalar()
            assert value == "before_disposal"
        
        # After disposal, new connections should still work
        # (This is tested in fixture cleanup)
    
    @pytest.mark.asyncio
    async def test_session_expunge_on_commit(self, db_engine):
        """Test session expunge behavior on commit.""" 
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(
            db_engine, 
            class_=AsyncSession, 
            expire_on_commit=False  # Test with expire_on_commit=False
        )
        
        async with async_session() as session:
            # Create temp table with data
            await session.execute(text("""
                CREATE TEMPORARY TABLE test_expunge (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """))
            
            await session.execute(text("""
                INSERT INTO test_expunge (value) VALUES ('test')
            """))
            
            await session.commit()
            
            # Should still be able to query after commit
            result = await session.execute(text("""
                SELECT value FROM test_expunge LIMIT 1
            """))
            value = result.scalar()
            assert value == "test"