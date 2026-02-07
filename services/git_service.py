"""Git service for repository cloning and management."""

import asyncio
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from config.settings import get_settings

logger = get_logger(__name__)


@dataclass
class CloneResult:
    """Result of cloning a repository."""
    success: bool
    path: Optional[str] = None
    error: Optional[str] = None


class GitService:
    """Service for git operations.
    
    SECURITY:
    - Uses GitHub token for private repo access
    - Clones to isolated directories
    - Cleans up on failure
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_clone_dir = Path(self.settings.CLONE_DIR)
        self.base_clone_dir.mkdir(parents=True, exist_ok=True)
    
    async def clone_repository(
        self,
        repo_url: str,
        incident_id: str,
        branch: Optional[str] = None,
        depth: int = 1,
    ) -> CloneResult:
        """Clone a repository.
        
        Args:
            repo_url: Repository URL (https or ssh)
            incident_id: Incident ID for directory naming
            branch: Optional specific branch to clone
            depth: Clone depth (default: 1 for shallow)
            
        Returns:
            CloneResult with path or error
        """
        # Prepare clone directory
        clone_path = self.base_clone_dir / f"repo-{incident_id}"
        
        # Clean if exists
        if clone_path.exists():
            shutil.rmtree(clone_path)
        
        # Prepare URL with token if needed
        clone_url = self._prepare_clone_url(repo_url)
        
        # Build clone command
        cmd = ["git", "clone"]
        
        if depth > 0:
            cmd.extend(["--depth", str(depth)])
        
        if branch:
            cmd.extend(["--branch", branch])
        
        cmd.extend([clone_url, str(clone_path)])
        
        try:
            # Try async subprocess first (preferred)
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=self._get_git_env(),
                )
                
                _, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=120,
                )
                
                returncode = proc.returncode
            except NotImplementedError:
                # Fallback for Windows SelectorEventLoop
                logger.info("Async subprocess not supported, falling back to threaded subprocess")
                import subprocess
                
                def _run_git():
                    return subprocess.run(
                        cmd,
                        capture_output=True,
                        env=self._get_git_env(),
                        timeout=120,
                    )
                
                result = await asyncio.to_thread(_run_git)
                returncode = result.returncode
                stderr = result.stderr
            
            if returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                # Redact any token from error message
                error_msg = self._redact_token(error_msg)
                
                return CloneResult(
                    success=False,
                    error=f"Git clone failed: {error_msg[:500]}",
                )
            
            logger.info("Repository cloned", path=str(clone_path))
            
            return CloneResult(
                success=True,
                path=str(clone_path),
            )
        
        except asyncio.TimeoutError:
            # Cleanup on timeout
            if clone_path.exists():
                shutil.rmtree(clone_path, ignore_errors=True)
            
            return CloneResult(
                success=False,
                error="Git clone timed out",
            )
        
        except Exception as e:
            # Cleanup on error
            if clone_path.exists():
                shutil.rmtree(clone_path, ignore_errors=True)
            
            return CloneResult(
                success=False,
                error=f"Clone error: {type(e).__name__}: {str(e)}",
            )
    
    def _prepare_clone_url(self, url: str) -> str:
        """Prepare clone URL with authentication if needed."""
        if not self.settings.GITHUB_TOKEN:
            return url
        
        token = self.settings.GITHUB_TOKEN.get_secret_value()
        
        # Skip dummy tokens
        if token.lower() in ["dummy_token", "your_token_here", ""]:
            return url
        
        # Handle HTTPS URLs
        if url.startswith("https://github.com/"):
            # Insert token into URL
            return url.replace(
                "https://github.com/",
                f"https://x-access-token:{token}@github.com/",
            )
        
        return url
    
    def _get_git_env(self) -> dict:
        """Get environment for git commands."""
        env = os.environ.copy()
        
        # Disable interactive prompts
        env["GIT_TERMINAL_PROMPT"] = "0"
        
        return env
    
    def _redact_token(self, message: str) -> str:
        """Redact any tokens from error messages."""
        if self.settings.GITHUB_TOKEN:
            token = self.settings.GITHUB_TOKEN.get_secret_value()
            message = message.replace(token, "<REDACTED_TOKEN>")
        return message
    
    def cleanup_clone(self, path: str) -> None:
        """Remove a cloned repository.
        
        Args:
            path: Path to repository to remove
        """
        try:
            clone_path = Path(path)
            if clone_path.exists():
                shutil.rmtree(clone_path)
                logger.info("Cleaned up clone", path=path)
        except Exception as e:
            logger.warning("Failed to cleanup clone", path=path, error=str(e))
    
    def checkout_branch(
        self,
        repo_path: str,
        branch: str,
        create: bool = False,
    ) -> bool:
        """Checkout a branch in a repository.
        
        Args:
            repo_path: Path to repository
            branch: Branch name
            create: Whether to create the branch if it doesn't exist
            
        Returns:
            True if successful
        """
        try:
            cmd = ["git", "checkout"]
            if create:
                cmd.append("-b")
            cmd.append(branch)
            
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                timeout=30,
            )
            
            return result.returncode == 0
        
        except Exception:
            return False
    
    def get_current_branch(self, repo_path: str) -> Optional[str]:
        """Get the current branch of a repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Current branch name or None
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        
        except Exception:
            return None
    
    def get_commit_sha(self, repo_path: str, ref: str = "HEAD") -> Optional[str]:
        """Get the SHA of a commit.
        
        Args:
            repo_path: Path to repository
            ref: Git reference (default: HEAD)
            
        Returns:
            Commit SHA or None
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", ref],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        
        except Exception:
            return None
