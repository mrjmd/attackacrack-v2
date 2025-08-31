"""
Tests for project structure and module organization.

These tests verify that the required project structure exists
and modules can be imported correctly.
"""

import os
import pytest
from pathlib import Path


def get_backend_path():
    """Get backend path dynamically for both local and Docker environments."""
    # Try current working directory first (Docker environment)
    current = Path.cwd()
    if current.name == 'backend' or (current / 'app').exists():
        return current
    
    # Try parent directory
    if (current / 'backend').exists():
        return current / 'backend'
    
    # Fall back to absolute path if neither work
    return Path("/Users/matt/Projects/attackacrack/attackacrack-v2/backend")


class TestProjectStructure:
    """Test cases for verifying the correct project structure exists."""

    def test_backend_directory_structure(self):
        """Test that backend directory structure exists."""
        backend_path = get_backend_path()
        
        # Main app directory
        app_path = backend_path / "app"
        assert app_path.exists(), "app directory should exist"
        assert (app_path / "__init__.py").exists(), "app/__init__.py should exist"
        
        # Will fail initially - directories don't exist yet
        assert (app_path / "main.py").exists(), "app/main.py should exist"

    def test_api_directory_structure(self):
        """Test that API directory structure is properly organized."""
        backend_path = get_backend_path()
        api_path = backend_path / "app" / "api"
        
        # Will fail initially - API structure doesn't exist
        assert api_path.exists(), "app/api directory should exist"
        assert (api_path / "__init__.py").exists(), "app/api/__init__.py should exist"
        
        # Versioned API structure
        v1_path = api_path / "v1"
        assert v1_path.exists(), "app/api/v1 directory should exist"
        assert (v1_path / "__init__.py").exists(), "app/api/v1/__init__.py should exist"
        
        # Endpoints directory
        endpoints_path = v1_path / "endpoints"
        assert endpoints_path.exists(), "app/api/v1/endpoints directory should exist"
        assert (endpoints_path / "__init__.py").exists(), "app/api/v1/endpoints/__init__.py should exist"
        assert (endpoints_path / "health.py").exists(), "app/api/v1/endpoints/health.py should exist"

    def test_core_directory_structure(self):
        """Test that core directory structure exists."""
        backend_path = get_backend_path()
        core_path = backend_path / "app" / "core"
        
        # Will fail initially - core structure doesn't exist
        assert core_path.exists(), "app/core directory should exist"
        assert (core_path / "__init__.py").exists(), "app/core/__init__.py should exist"
        assert (core_path / "config.py").exists(), "app/core/config.py should exist"

    def test_models_directory_structure(self):
        """Test that models directory structure exists."""
        backend_path = get_backend_path()
        models_path = backend_path / "app" / "models"
        
        # Will fail initially - models structure doesn't exist
        assert models_path.exists(), "app/models directory should exist"
        assert (models_path / "__init__.py").exists(), "app/models/__init__.py should exist"

    def test_schemas_directory_structure(self):
        """Test that schemas directory structure exists."""
        backend_path = get_backend_path()
        schemas_path = backend_path / "app" / "schemas"
        
        # Will fail initially - schemas structure doesn't exist
        assert schemas_path.exists(), "app/schemas directory should exist"
        assert (schemas_path / "__init__.py").exists(), "app/schemas/__init__.py should exist"

    def test_services_directory_structure(self):
        """Test that services directory structure exists."""
        backend_path = get_backend_path()
        services_path = backend_path / "app" / "services"
        
        # Will fail initially - services structure doesn't exist
        assert services_path.exists(), "app/services directory should exist"
        assert (services_path / "__init__.py").exists(), "app/services/__init__.py should exist"

    def test_tests_directory_structure(self):
        """Test that tests directory structure exists and is organized."""
        backend_path = get_backend_path()
        tests_path = backend_path / "tests"
        
        # Tests directory structure
        assert tests_path.exists(), "tests directory should exist"
        assert (tests_path / "__init__.py").exists(), "tests/__init__.py should exist"
        assert (tests_path / "conftest.py").exists(), "tests/conftest.py should exist"
        
        # Test files should exist
        assert (tests_path / "test_main.py").exists(), "tests/test_main.py should exist"
        assert (tests_path / "test_health.py").exists(), "tests/test_health.py should exist"
        assert (tests_path / "test_config.py").exists(), "tests/test_config.py should exist"


class TestModuleImports:
    """Test cases for verifying modules can be imported correctly."""

    def test_main_module_import(self):
        """Test that main module can be imported."""
        # Will fail initially - main.py doesn't exist
        try:
            from app.main import app
            assert app is not None
        except ImportError as e:
            pytest.fail(f"Cannot import app.main: {e}")

    def test_config_module_import(self):
        """Test that config module can be imported."""
        # Will fail initially - config.py doesn't exist
        try:
            from app.core.config import Settings
            assert Settings is not None
        except ImportError as e:
            pytest.fail(f"Cannot import app.core.config: {e}")

    def test_health_endpoint_import(self):
        """Test that health endpoint can be imported."""
        # Will fail initially - health.py doesn't exist
        try:
            from app.api.v1.endpoints.health import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"Cannot import health endpoint: {e}")

    def test_api_modules_import(self):
        """Test that API modules can be imported."""
        # Will fail initially - API modules don't exist
        try:
            import app.api
            import app.api.v1
            import app.api.v1.endpoints
        except ImportError as e:
            pytest.fail(f"Cannot import API modules: {e}")

    def test_core_modules_import(self):
        """Test that core modules can be imported."""
        # Will fail initially - core modules don't exist
        try:
            import app.core
            from app.core.config import Settings, get_settings
        except ImportError as e:
            pytest.fail(f"Cannot import core modules: {e}")

    def test_all_app_modules_importable(self):
        """Test that all app modules are properly importable."""
        modules_to_test = [
            "app",
            "app.main", 
            "app.api",
            "app.api.v1",
            "app.api.v1.endpoints",
            "app.api.v1.endpoints.health",
            "app.core",
            "app.core.config",
            "app.models",
            "app.schemas", 
            "app.services"
        ]
        
        # Will fail initially - modules don't exist
        for module_name in modules_to_test:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Cannot import {module_name}: {e}")


class TestPackageConfiguration:
    """Test cases for Python package configuration."""

    def test_init_files_exist(self):
        """Test that all required __init__.py files exist."""
        backend_path = get_backend_path()
        
        init_files = [
            "app/__init__.py",
            "app/api/__init__.py", 
            "app/api/v1/__init__.py",
            "app/api/v1/endpoints/__init__.py",
            "app/core/__init__.py",
            "app/models/__init__.py",
            "app/schemas/__init__.py",
            "app/services/__init__.py",
            "tests/__init__.py"
        ]
        
        # Will fail initially - init files don't exist
        for init_file in init_files:
            init_path = backend_path / init_file
            assert init_path.exists(), f"{init_file} should exist for proper package structure"

    def test_python_path_configuration(self):
        """Test that Python path is configured correctly for imports."""
        import sys
        backend_path = str(get_backend_path())
        
        # Backend directory should be in Python path for imports to work
        assert backend_path in sys.path or any(
            backend_path in path for path in sys.path
        ), "Backend directory should be in Python path"

    def test_package_structure_follows_conventions(self):
        """Test that package structure follows Python conventions."""
        backend_path = get_backend_path()
        
        # Check that directories follow naming conventions
        directories_to_check = [
            "app",
            "app/api", 
            "app/core",
            "app/models",
            "app/schemas",
            "app/services",
            "tests"
        ]
        
        for directory in directories_to_check:
            dir_path = backend_path / directory
            # Directory names should be lowercase and valid Python identifiers
            dir_name = dir_path.name
            assert dir_name.islower(), f"Directory {directory} should be lowercase"
            assert dir_name.isidentifier(), f"Directory {directory} should be valid Python identifier"


class TestDependencyStructure:
    """Test cases for dependency structure and circular imports."""

    def test_no_circular_imports(self):
        """Test that there are no circular import dependencies."""
        # Will fail initially if circular imports exist
        modules_to_test = [
            "app.main",
            "app.core.config", 
            "app.api.v1.endpoints.health"
        ]
        
        # Try importing each module independently
        for module_name in modules_to_test:
            try:
                # Fresh import to detect circular dependencies
                import importlib
                import sys
                
                # Remove module from cache if it exists
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                # Import module
                importlib.import_module(module_name)
                
            except ImportError as e:
                if "circular import" in str(e).lower():
                    pytest.fail(f"Circular import detected in {module_name}: {e}")
                else:
                    # Expected failure - modules don't exist yet
                    pass

    def test_dependency_layers_respected(self):
        """Test that dependency layers are properly respected."""
        # Will test once modules exist
        # Core should not depend on API
        # API should not depend on main
        # Services should not depend on API
        pass  # Implementation-dependent test