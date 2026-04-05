"""Generates fake credentials and environment variables for sandbox testing.

Provides deterministic fake values for common environment variables
to ensure tests that expect .env files can run safely without
requiring real credentials.
"""

import os
from pathlib import Path
from typing import Dict, List

from config.logging_config import get_logger

logger = get_logger(__name__)


class EnvGenerator:
    """Generates fake .env files for sandbox testing."""
    
    # Common environment variables that might be needed by tests
    FAKE_CREDENTIALS = {
        # Databases
        "DATABASE_URL": "postgresql://test_user:test_pass@localhost:5432/test_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "MONGO_URI": "mongodb://localhost:27017/test_db",
        
        # APIs / Auth
        "API_KEY": "test_api_key_12345",
        "OPENAI_API_KEY": "sk-test-1234567890abcdef1234567890abcdef",
        "GITHUB_TOKEN": "ghp_test1234567890abcdef1234567890abcdef",
        "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
        "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "JWT_SECRET": "test_jwt_secret_should_be_long_enough",
        
        # App config
        "ENVIRONMENT": "testing",
        "DEBUG": "True",
        "LOG_LEVEL": "DEBUG",
        "PORT": "8080",
    }
    
    # Common .env file names to generate
    ENV_FILES = [".env", ".env.test", ".env.local"]
    
    @classmethod
    def generate(cls, target_dir: Path) -> List[Path]:
        """Generate fake .env files in the target directory.
        
        Args:
            target_dir: Directory where .env files should be created
            
        Returns:
            List of paths to the created files
        """
        created_files = []
        
        env_content = "\n".join(
            f"{k}={v}" for k, v in cls.FAKE_CREDENTIALS.items()
        )
        
        for env_name in cls.ENV_FILES:
            env_path = target_dir / env_name
            try:
                # Don't overwrite existing files (they might be valid test fixtures)
                if not env_path.exists():
                    env_path.write_text(env_content)
                    created_files.append(env_path)
            except Exception as e:
                logger.warning(
                    f"Failed to generate fake credentials for {env_name}",
                    error=str(e)
                )
                
        if created_files:
            logger.info(
                "Injected fake credentials for sandbox testing",
                files=[f.name for f in created_files]
            )
            
        return created_files
    
    @classmethod
    def get_env_dict(cls) -> Dict[str, str]:
        """Get the fake credentials as a dictionary.
        
        Can be used to pass environment variables directly to
        subprocess/docker if not relying on .env files.
        """
        return cls.FAKE_CREDENTIALS.copy()
