from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Union, Literal
from functools import lru_cache

class Settings(BaseSettings):
    # App metadata
    app_title: str = "Attack-a-Crack v2"
    app_version: str = "2.0.0"
    app_description: str = "SMS campaign management system"
    
    # Environment configuration
    environment: str = Field(default="development")
    debug: bool = Field(default=None)
    
    # API configuration
    api_v1_prefix: str = "/api/v1"
    
    # Database configuration
    database_url: str = Field(
        default="postgresql://app:password@localhost:5432/attackacrack"
    )
    
    # CORS configuration  
    cors_origins_str: str = Field(default="http://localhost:3000,http://localhost:5173", alias="cors_origins")
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins_str.split(',')]
    
    @field_validator('debug', mode='before')
    @classmethod
    def set_debug_mode(cls, v, info):
        if v is not None:
            return v
        environment = info.data.get('environment', 'development')
        return environment == 'development'
    
    @field_validator('environment', mode='after')
    @classmethod
    def validate_environment(cls, v):
        valid_environments = ["development", "staging", "production", "test"]
        if v not in valid_environments:
            return "development"  # Default to development for invalid values
        return v
    
        
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        if not (v.startswith('postgresql://') or v.startswith('postgresql+asyncpg://')):
            raise ValueError('Database URL must be PostgreSQL')
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_file_encoding": "utf-8"
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()