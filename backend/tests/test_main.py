"""
Tests for the main FastAPI application.

These tests verify the core FastAPI application setup, middleware configuration,
and overall application structure.
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient


class TestMainApplication:
    """Test cases for the main FastAPI application setup."""

    def test_app_instance_created(self, app):
        """Test that FastAPI application instance is created properly."""
        # Will fail initially - no main.py exists
        assert isinstance(app, FastAPI)
        assert app.title is not None
        assert app.version is not None

    def test_app_title_and_version(self, app):
        """Test that app has proper title and version."""
        # Will fail initially - no app configuration
        assert app.title == "Attack-a-Crack v2"
        assert app.version == "2.0.0"
        assert app.description is not None

    @pytest.mark.asyncio
    async def test_cors_middleware_configured(self, client: AsyncClient):
        """Test that CORS middleware is properly configured."""
        # Test preflight request
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            }
        )
        
        # Will fail initially - no CORS middleware configured
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "access-control-allow-methods" in response.headers
        assert "GET" in response.headers["access-control-allow-methods"]

    @pytest.mark.asyncio
    async def test_cors_origins_from_config(self, client: AsyncClient):
        """Test that CORS origins are loaded from configuration."""
        # Test allowed origin
        response = await client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        # Will fail initially - no health endpoint
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    @pytest.mark.asyncio
    async def test_api_versioning_prefix(self, client: AsyncClient):
        """Test that API endpoints use /api/v1 prefix."""
        # Will fail initially - no versioned routing
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

        # Non-versioned endpoint should not exist
        response = await client.get("/health")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_app_startup_no_errors(self, app):
        """Test that application starts without errors."""
        # Will fail initially - import errors when no main.py
        assert app is not None
        assert len(app.routes) > 0  # Should have at least health route

    def test_app_middleware_order(self, app):
        """Test that middleware is configured in correct order."""
        # Will fail initially - no middleware configured
        middleware_stack = app.user_middleware
        assert len(middleware_stack) > 0
        
        # CORS middleware should be present
        cors_middleware_found = any(
            "CORSMiddleware" in str(middleware.__class__)
            for middleware, _ in middleware_stack
        )
        assert cors_middleware_found

    @pytest.mark.asyncio
    async def test_invalid_endpoint_returns_404(self, client: AsyncClient):
        """Test that invalid endpoints return proper 404 responses."""
        response = await client.get("/api/v1/nonexistent")
        
        # Will fail initially - no app to handle requests
        assert response.status_code == 404
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_root_endpoint_behavior(self, client: AsyncClient):
        """Test behavior of root endpoint."""
        response = await client.get("/")
        
        # Will fail initially - no root endpoint defined
        # Should either redirect to docs or return app info
        assert response.status_code in [200, 404, 307]  # 307 for redirect

    def test_app_debug_mode_from_config(self, app):
        """Test that debug mode is configured from settings."""
        # Will fail initially - no configuration system
        # In test environment, debug should be enabled
        assert app.debug is True or hasattr(app, 'debug_mode')

    @pytest.mark.asyncio
    async def test_exception_handling(self, client: AsyncClient):
        """Test that application handles exceptions gracefully."""
        # This will test once we have error handlers
        # Will fail initially - no exception handlers configured
        response = await client.get("/api/v1/health")
        assert response.status_code != 500  # Should not crash


class TestApplicationStructure:
    """Test cases for application structure and organization."""

    def test_api_router_structure(self, app):
        """Test that API router structure is properly organized."""
        # Will fail initially - no router structure
        routes = [route.path for route in app.routes]
        
        # Should have versioned API routes
        health_route_found = any("/api/v1/health" in route for route in routes)
        assert health_route_found

    def test_route_tags_configured(self, app):
        """Test that routes have proper tags for API documentation."""
        # Will fail initially - no route tags configured
        health_route = None
        for route in app.routes:
            if hasattr(route, 'path') and "/health" in route.path:
                health_route = route
                break
        
        assert health_route is not None
        assert hasattr(health_route, 'tags')
        assert "health" in health_route.tags or "system" in health_route.tags

    @pytest.mark.asyncio
    async def test_openapi_docs_available(self, client: AsyncClient):
        """Test that OpenAPI documentation is available."""
        # Will fail initially - no docs configuration
        response = await client.get("/docs")
        assert response.status_code == 200
        
        # Test alternative docs endpoint
        response = await client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_generation(self, app):
        """Test that OpenAPI schema is properly generated."""
        # Will fail initially - no schema configuration
        schema = app.openapi()
        
        assert schema is not None
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Attack-a-Crack v2"
        assert schema["info"]["version"] == "2.0.0"
        assert "paths" in schema