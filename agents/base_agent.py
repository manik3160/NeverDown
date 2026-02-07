"""Base agent abstract class for all NeverDown agents."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar
from uuid import UUID
import time

from config.logging_config import audit_logger, get_logger

# Type variables for input/output
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class AgentResult(Generic[OutputT]):
    """Result wrapper for agent execution."""
    
    def __init__(
        self,
        success: bool,
        output: Optional[OutputT] = None,
        error: Optional[str] = None,
        duration_ms: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.duration_ms = duration_ms
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
    
    @classmethod
    def ok(
        cls,
        output: OutputT,
        duration_ms: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AgentResult[OutputT]":
        """Create a successful result."""
        return cls(
            success=True,
            output=output,
            duration_ms=duration_ms,
            metadata=metadata,
        )
    
    @classmethod
    def fail(
        cls,
        error: str,
        duration_ms: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "AgentResult[OutputT]":
        """Create a failed result."""
        return cls(
            success=False,
            error=error,
            duration_ms=duration_ms,
            metadata=metadata,
        )


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all NeverDown agents.
    
    All agents must implement the `execute` method and define their
    input/output types.
    
    Example:
        class MySanitizerAgent(BaseAgent[SanitizeInput, SanitizeOutput]):
            name = "sanitizer"
            
            async def execute(self, input: SanitizeInput) -> AgentResult[SanitizeOutput]:
                # Implementation here
                return AgentResult.ok(output)
    """
    
    # Agent name - must be set by subclasses
    name: str = "base"
    
    def __init__(self):
        self.logger = get_logger(f"neverdown.agents.{self.name}")
    
    @abstractmethod
    async def execute(
        self,
        input_data: InputT,
        incident_id: Optional[UUID] = None,
    ) -> AgentResult[OutputT]:
        """Execute the agent's main task.
        
        Args:
            input_data: Input data for the agent
            incident_id: Optional incident ID for logging
            
        Returns:
            AgentResult containing output or error
        """
        pass
    
    async def run(
        self,
        input_data: InputT,
        incident_id: Optional[UUID] = None,
    ) -> AgentResult[OutputT]:
        """Run the agent with timing and logging.
        
        This is the main entry point - it wraps execute() with
        timing, logging, and error handling.
        
        Args:
            input_data: Input data for the agent
            incident_id: Optional incident ID for logging
            
        Returns:
            AgentResult containing output or error
        """
        start_time = time.perf_counter()
        
        self.logger.info(
            f"Starting {self.name} agent",
            incident_id=str(incident_id) if incident_id else None,
        )
        
        try:
            result = await self.execute(input_data, incident_id)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            result.duration_ms = duration_ms
            
            # Log execution
            if incident_id:
                audit_logger.log_agent_execution(
                    incident_id=str(incident_id),
                    agent_name=self.name,
                    action="execute",
                    success=result.success,
                    duration_ms=duration_ms,
                    metadata=result.metadata,
                )
            
            if result.success:
                self.logger.info(
                    f"Agent {self.name} completed successfully",
                    incident_id=str(incident_id) if incident_id else None,
                    duration_ms=duration_ms,
                )
            else:
                self.logger.warning(
                    f"Agent {self.name} failed",
                    incident_id=str(incident_id) if incident_id else None,
                    error=result.error,
                    duration_ms=duration_ms,
                )
            
            return result
            
        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            self.logger.exception(
                f"Agent {self.name} raised exception",
                incident_id=str(incident_id) if incident_id else None,
                error=str(e),
            )
            
            if incident_id:
                audit_logger.log_agent_execution(
                    incident_id=str(incident_id),
                    agent_name=self.name,
                    action="execute",
                    success=False,
                    duration_ms=duration_ms,
                    metadata={"exception": str(e)},
                )
            
            return AgentResult.fail(
                error=str(e),
                duration_ms=duration_ms,
                metadata={"exception_type": type(e).__name__},
            )
    
    def validate_input(self, input_data: InputT) -> Optional[str]:
        """Validate input data before execution.
        
        Override in subclasses to add validation.
        
        Args:
            input_data: Input to validate
            
        Returns:
            Error message if invalid, None if valid
        """
        return None
