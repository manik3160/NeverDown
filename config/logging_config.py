"""Structured logging configuration for NeverDown."""

import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor

from config.settings import get_settings


def add_timestamp(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add ISO timestamp to log events."""
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_service_info(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add service metadata to log events."""
    settings = get_settings()
    event_dict["service"] = settings.APP_NAME
    event_dict["version"] = settings.APP_VERSION
    return event_dict


def redact_secrets(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Redact sensitive fields from log output."""
    sensitive_keys = {
        "password", "secret", "token", "api_key", "apikey",
        "authorization", "auth", "credential", "private_key",
    }
    
    def _redact(obj: Any, depth: int = 0) -> Any:
        if depth > 10:
            return obj
        if isinstance(obj, dict):
            return {
                k: "<REDACTED>" if any(s in k.lower() for s in sensitive_keys) else _redact(v, depth + 1)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [_redact(item, depth + 1) for item in obj]
        return obj
    
    return _redact(event_dict)


def configure_logging(
    log_level: Optional[str] = None,
    json_logs: bool = True,
) -> None:
    """Configure structured logging for the application.
    
    Args:
        log_level: Override log level (default from settings)
        json_logs: Whether to output JSON format (default True for production)
    """
    settings = get_settings()
    level = log_level or settings.LOG_LEVEL
    
    # Shared processors for all loggers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_timestamp,
        add_service_info,
        redact_secrets,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_logs:
        # Production: JSON output
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()
    else:
        # Development: colored console output
        shared_processors.append(structlog.dev.set_exc_info)
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())
    
    # Quiet noisy third-party loggers
    for logger_name in ["httpx", "httpcore", "urllib3", "docker"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


class AuditLogger:
    """Specialized logger for audit trail events."""
    
    def __init__(self):
        self._logger = get_logger("neverdown.audit")
    
    def log_state_transition(
        self,
        incident_id: str,
        from_state: str,
        to_state: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a state machine transition."""
        self._logger.info(
            "state_transition",
            event_type="state_transition",
            incident_id=incident_id,
            from_state=from_state,
            to_state=to_state,
            metadata=metadata or {},
        )
    
    def log_agent_execution(
        self,
        incident_id: str,
        agent_name: str,
        action: str,
        success: bool,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an agent execution event."""
        self._logger.info(
            "agent_execution",
            event_type="agent_execution",
            incident_id=incident_id,
            agent=agent_name,
            action=action,
            success=success,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
    
    def log_api_call(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: Optional[str] = None,
    ) -> None:
        """Log an API request."""
        self._logger.info(
            "api_call",
            event_type="api_call",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
        )
    
    def log_security_event(
        self,
        event_name: str,
        severity: str,
        details: Dict[str, Any],
    ) -> None:
        """Log a security-related event."""
        self._logger.warning(
            "security_event",
            event_type="security_event",
            event_name=event_name,
            severity=severity,
            details=details,
        )


# Global audit logger instance
audit_logger = AuditLogger()
