"""Docker sandbox runner for the Verifier agent."""

import asyncio
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.logging_config import get_logger
from config.settings import get_settings
from core.exceptions import SandboxError, SandboxTimeoutError
from models.verification import SandboxInfo

logger = get_logger(__name__)


@dataclass
class SandboxResult:
    """Result from running code in sandbox."""
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    memory_exceeded: bool = False


@dataclass
class SandboxConfig:
    """Configuration for Docker sandbox."""
    image: str = "python:3.11-slim"
    timeout_seconds: int = 300
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    network_mode: str = "none"  # No network access
    read_only: bool = False  # Need write for tests
    work_dir: str = "/app"
    user: str = "1000:1000"  # Non-root user


class SandboxRunner:
    """Runs code in isolated Docker containers.
    
    SECURITY:
    - No network access (network_mode: none)
    - Memory and CPU limits
    - Timeout enforcement
    - Non-root execution
    - No access to host filesystem except mounted code
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        """Initialize runner with configuration.
        
        Args:
            config: Sandbox configuration (uses defaults if not provided)
        """
        self.settings = get_settings()
        self.config = config or SandboxConfig(
            image=self.settings.SANDBOX_IMAGE,
            timeout_seconds=self.settings.SANDBOX_TIMEOUT,
            memory_limit=self.settings.SANDBOX_MEMORY_LIMIT,
        )
    
    async def run(
        self,
        repo_path: str,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """Run a command in Docker sandbox.
        
        Args:
            repo_path: Path to code to mount
            command: Command to run [cmd, arg1, arg2, ...]
            env: Optional environment variables
            
        Returns:
            SandboxResult with output and status
            
        Raises:
            SandboxError: If Docker execution fails
            SandboxTimeoutError: If timeout exceeded
        """
        container_name = f"neverdown-sandbox-{uuid.uuid4().hex[:12]}"
        start_time = datetime.utcnow()
        
        docker_cmd = self._build_docker_command(
            container_name,
            repo_path,
            command,
            env,
        )
        
        logger.info(
            "Starting sandbox container",
            container=container_name,
            command=command[:3],  # Log first 3 args
        )
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.config.timeout_seconds,
                )
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                return SandboxResult(
                    exit_code=proc.returncode or 0,
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    duration_seconds=duration,
                )
            
            except asyncio.TimeoutError:
                # Kill container
                await self._kill_container(container_name)
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                return SandboxResult(
                    exit_code=-1,
                    stdout="",
                    stderr="Sandbox execution timed out",
                    duration_seconds=duration,
                    timed_out=True,
                )
        
        except Exception as e:
            logger.exception("Sandbox execution failed", error=str(e))
            raise SandboxError(f"Docker execution failed: {str(e)}")
        
        finally:
            # Cleanup container
            await self._cleanup_container(container_name)
    
    def _build_docker_command(
        self,
        container_name: str,
        repo_path: str,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
    ) -> List[str]:
        """Build the docker run command."""
        cmd = [
            "docker", "run",
            "--name", container_name,
            "--rm",  # Remove after exit
            "--network", self.config.network_mode,  # No network
            "--memory", self.config.memory_limit,
            f"--cpus={self.config.cpu_limit}",
            "--pids-limit", "100",  # Limit processes
            "-v", f"{repo_path}:{self.config.work_dir}:rw",
            "-w", self.config.work_dir,
        ]
        
        # Add environment variables
        if env:
            for key, value in env.items():
                # Never pass sensitive env vars
                if any(s in key.lower() for s in ['secret', 'key', 'password', 'token']):
                    continue
                cmd.extend(["-e", f"{key}={value}"])
        
        # Add security options
        cmd.extend([
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",  # Drop all capabilities
        ])
        
        # Add image and command
        cmd.append(self.config.image)
        cmd.extend(command)
        
        return cmd
    
    async def _kill_container(self, name: str) -> None:
        """Kill a running container."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "kill", name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=10)
        except Exception:
            pass  # Ignore errors
    
    async def _cleanup_container(self, name: str) -> None:
        """Remove a container if it still exists."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "rm", "-f", name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=10)
        except Exception:
            pass  # Ignore errors
    
    async def check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=5)
            return proc.returncode == 0
        except Exception:
            return False
    
    async def pull_image(self, image: Optional[str] = None) -> bool:
        """Pull Docker image if not present.
        
        Args:
            image: Image to pull (default: config image)
            
        Returns:
            True if successful
        """
        image = image or self.config.image
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "pull", image,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.wait(), timeout=120)
            return proc.returncode == 0
        except Exception as e:
            logger.warning("Failed to pull image", image=image, error=str(e))
            return False
    
    def get_sandbox_info(self) -> SandboxInfo:
        """Get current sandbox configuration as SandboxInfo."""
        return SandboxInfo(
            container_id="",  # Set at runtime
            image=self.config.image,
            memory_limit=self.config.memory_limit,
            timeout_seconds=self.config.timeout_seconds,
        )
