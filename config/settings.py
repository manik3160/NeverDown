"""Centralized configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Application
    APP_NAME: str = "NeverDown"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    API_KEY: Optional[SecretStr] = None
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://neverdown:neverdown@localhost:5432/neverdown"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis (for task queue)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # GitHub
    GITHUB_TOKEN: Optional[SecretStr] = None
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_APP_PRIVATE_KEY: Optional[SecretStr] = None
    GITHUB_WEBHOOK_SECRET: Optional[SecretStr] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[SecretStr] = None
    
    # LLM Configuration
    LLM_PROVIDER: str = "anthropic"  # or "openai"
    LLM_API_KEY: Optional[SecretStr] = None
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.1
    
    # Docker / Sandbox
    DOCKER_HOST: Optional[str] = None
    SANDBOX_IMAGE: str = "python:3.11-slim"
    SANDBOX_TIMEOUT: int = 300
    SANDBOX_TIMEOUT_SECONDS: int = 600
    SANDBOX_MEMORY_LIMIT: str = "512m"
    SANDBOX_CPU_LIMIT: float = 1.0
    SANDBOX_NETWORK_DISABLED: bool = True
    
    # Agent Configuration
    SANITIZER_CONFIDENCE_THRESHOLD: float = 0.9
    SANITIZER_MAX_SECRETS: int = 100
    REASONER_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 2.0
    
    # Security
    ALLOWED_REPOS: List[str] = Field(default_factory=list)
    REDACTION_PATTERNS_FILE: str = "config/security_rules.yaml"
    
    # Paths
    WORKSPACE_DIR: str = "/tmp/neverdown-workspaces"
    SANITIZED_REPO_DIR: str = "/tmp/neverdown-sanitized"
    CLONE_DIR: str = "/tmp/neverdown-clones"
    
    @field_validator("ALLOWED_REPOS", mode="before")
    @classmethod
    def parse_allowed_repos(cls, v):
        """Parse comma-separated repos list."""
        if isinstance(v, str):
            return [r.strip() for r in v.split(",") if r.strip()]
        return v or []


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
