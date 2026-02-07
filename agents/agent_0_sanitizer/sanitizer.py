"""Sanitizer agent - Security gatekeeper for NeverDown."""

import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from agents.base_agent import AgentResult, BaseAgent
from agents.agent_0_sanitizer.patterns import PatternMatcher, SecretMatch
from agents.agent_0_sanitizer.redactor import Redactor, RedactionEntry
from config.logging_config import audit_logger, get_logger
from config.settings import get_settings
from core.exceptions import SanitizationFailedError, TooManySecretsError
from models.analysis import SanitizationEntry, SanitizationReport

logger = get_logger(__name__)


@dataclass
class SanitizeInput:
    """Input for the Sanitizer agent."""
    repo_path: str  # Path to cloned repository
    incident_id: UUID
    include_entropy_detection: bool = True


@dataclass
class SanitizeOutput:
    """Output from the Sanitizer agent."""
    sanitized_repo_path: str
    report: SanitizationReport
    success: bool = True
    halted: bool = False


class SanitizerAgent(BaseAgent[SanitizeInput, SanitizeOutput]):
    """Agent 0: Security Gatekeeper.
    
    Responsibilities:
    - Scan repository for secrets (API keys, passwords, tokens, etc.)
    - Redact secrets with semantic placeholders
    - Create sanitized shadow repository
    - Generate sanitization report
    - HALT if too many secrets found (requires human review)
    
    CRITICAL: This agent is the first line of defense. No secrets
    must ever reach downstream agents (especially the LLM).
    """
    
    name = "sanitizer"
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.pattern_matcher = PatternMatcher()
        self.redactor = Redactor()
    
    async def execute(
        self,
        input_data: SanitizeInput,
        incident_id: Optional[UUID] = None,
    ) -> AgentResult[SanitizeOutput]:
        """Execute sanitization on a repository.
        
        Args:
            input_data: Sanitization input with repo path
            incident_id: Incident ID for logging
            
        Returns:
            AgentResult with sanitized repo path and report
        """
        incident_id = incident_id or input_data.incident_id
        repo_path = Path(input_data.repo_path)
        
        if not repo_path.exists():
            return AgentResult.fail(
                f"Repository path does not exist: {repo_path}",
                metadata={"repo_path": str(repo_path)},
            )
        
        # Create sanitized copy directory
        sanitized_path = Path(self.settings.SANITIZED_REPO_DIR) / f"sanitized-{incident_id}"
        
        try:
            # Copy repository to sanitized location
            self.logger.info("Copying repository for sanitization", 
                           source=str(repo_path), dest=str(sanitized_path))
            
            if sanitized_path.exists():
                shutil.rmtree(sanitized_path)
            
            shutil.copytree(repo_path, sanitized_path, ignore=shutil.ignore_patterns('.git'))
            
            # Scan and sanitize files
            report = await self._sanitize_directory(
                sanitized_path,
                incident_id,
                input_data.include_entropy_detection,
            )
            
            # Check if we should halt due to too many secrets
            max_secrets = self.settings.SANITIZER_MAX_SECRETS
            if report.total_secrets_found > max_secrets:
                report.halted = True
                
                # Log security event
                audit_logger.log_security_event(
                    event_name="too_many_secrets",
                    severity="critical",
                    details={
                        "incident_id": str(incident_id),
                        "secret_count": report.total_secrets_found,
                        "threshold": max_secrets,
                    },
                )
                
                return AgentResult.fail(
                    f"Too many secrets found ({report.total_secrets_found}), halting for human review",
                    metadata={
                        "secret_count": report.total_secrets_found,
                        "threshold": max_secrets,
                        "by_severity": report.by_severity,
                    },
                )
            
            output = SanitizeOutput(
                sanitized_repo_path=str(sanitized_path),
                report=report,
                success=True,
                halted=False,
            )
            
            return AgentResult.ok(
                output,
                metadata={
                    "files_scanned": report.total_files_scanned,
                    "secrets_found": report.total_secrets_found,
                    "by_severity": report.by_severity,
                },
            )
            
        except TooManySecretsError as e:
            return AgentResult.fail(
                str(e),
                metadata={"secret_count": e.details.get("secret_count")},
            )
        except Exception as e:
            # Clean up on error
            if sanitized_path.exists():
                shutil.rmtree(sanitized_path, ignore_errors=True)
            
            return AgentResult.fail(
                f"Sanitization failed: {str(e)}",
                metadata={"exception_type": type(e).__name__},
            )
    
    async def _sanitize_directory(
        self,
        directory: Path,
        incident_id: UUID,
        include_entropy: bool,
    ) -> SanitizationReport:
        """Recursively sanitize all files in directory.
        
        Args:
            directory: Directory to sanitize (in place)
            incident_id: Incident ID for report
            include_entropy: Whether to include high-entropy detection
            
        Returns:
            Sanitization report
        """
        all_entries: List[SanitizationEntry] = []
        files_scanned = 0
        by_severity: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        entropy_detections = 0
        pattern_matches = 0
        
        # Walk directory
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(directory)
                
                # Check if we should scan this file
                if not self.pattern_matcher.should_scan_file(str(rel_path)):
                    continue
                
                # Skip binary files
                if self._is_binary_file(file_path):
                    continue
                
                try:
                    entries = await self._sanitize_file(
                        file_path,
                        str(rel_path),
                        include_entropy,
                    )
                    
                    files_scanned += 1
                    all_entries.extend(entries)
                    
                    # Update counts
                    for entry in entries:
                        by_severity[entry.severity] = by_severity.get(entry.severity, 0) + 1
                        by_type[entry.secret_type] = by_type.get(entry.secret_type, 0) + 1
                        
                        if entry.secret_type == "high_entropy":
                            entropy_detections += 1
                        else:
                            pattern_matches += 1
                
                except Exception as e:
                    self.logger.warning(
                        "Failed to sanitize file",
                        file=str(rel_path),
                        error=str(e),
                    )
        
        return SanitizationReport(
            incident_id=incident_id,
            sanitized_repo_path=str(directory),
            total_files_scanned=files_scanned,
            total_secrets_found=len(all_entries),
            entries=all_entries,
            high_entropy_detections=entropy_detections,
            pattern_matches=pattern_matches,
            by_severity=by_severity,
            by_type=by_type,
            halted=False,
        )
    
    async def _sanitize_file(
        self,
        file_path: Path,
        rel_path: str,
        include_entropy: bool,
    ) -> List[SanitizationEntry]:
        """Sanitize a single file.
        
        Args:
            file_path: Absolute path to file
            rel_path: Relative path for reporting
            include_entropy: Whether to include entropy detection
            
        Returns:
            List of sanitization entries for this file
        """
        entries: List[SanitizationEntry] = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            return entries
        
        # Special handling for .env files
        if file_path.name.startswith('.env') or file_path.suffix == '.env':
            redacted_content, env_entries = self.redactor.redact_env_file(content)
            
            if env_entries:
                file_path.write_text(redacted_content, encoding='utf-8')
                
                for entry in env_entries:
                    entries.append(SanitizationEntry(
                        file_path=rel_path,
                        line_number=entry.line_number,
                        secret_type="env_file_value",
                        placeholder=entry.replacement,
                        severity=entry.severity,
                    ))
            
            return entries
        
        # Pattern-based detection
        matches = self.pattern_matcher.find_secrets(content, rel_path)
        
        # Add entropy-based detection if enabled
        if include_entropy:
            entropy_matches = self.pattern_matcher.find_high_entropy_strings(content)
            # Filter out entropy matches that overlap with pattern matches
            existing_ranges = {(m.start, m.end) for m in matches}
            for em in entropy_matches:
                if not any(self._ranges_overlap((em.start, em.end), r) for r in existing_ranges):
                    matches.append(em)
        
        if not matches:
            return entries
        
        # Redact all matches
        result = self.redactor.redact(content, matches)
        
        # Write redacted content
        file_path.write_text(result.redacted_content, encoding='utf-8')
        
        # Create entries
        for redaction in result.redactions:
            entries.append(SanitizationEntry(
                file_path=rel_path,
                line_number=redaction.line_number,
                secret_type=redaction.pattern_name,
                placeholder=redaction.replacement,
                severity=redaction.severity,
            ))
        
        return entries
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is binary."""
        binary_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.ico', '.bmp', '.webp',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.exe', '.dll', '.so', '.dylib',
            '.pyc', '.pyo', '.class',
            '.woff', '.woff2', '.ttf', '.eot',
            '.mp3', '.mp4', '.wav', '.avi', '.mov',
        }
        
        if file_path.suffix.lower() in binary_extensions:
            return True
        
        # Check file content for binary data
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except Exception:
            return True
    
    def _ranges_overlap(self, r1: tuple, r2: tuple) -> bool:
        """Check if two ranges overlap."""
        return r1[0] < r2[1] and r2[0] < r1[1]
