"""Secret redaction logic for the Sanitizer agent."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from agents.agent_0_sanitizer.patterns import SecretMatch


@dataclass
class RedactionResult:
    """Result of redacting content."""
    original_content: str
    redacted_content: str
    redactions: List["RedactionEntry"]
    
    @property
    def redaction_count(self) -> int:
        """Number of redactions made."""
        return len(self.redactions)


@dataclass
class RedactionEntry:
    """A single redaction made to content."""
    original_text: str
    replacement: str
    start: int
    end: int
    line_number: int
    pattern_name: str
    severity: str


class Redactor:
    """Redacts secrets from content using semantic placeholders."""
    
    def __init__(self):
        # Cache for consistent redaction of same secrets
        self._redaction_cache: Dict[str, str] = {}
    
    def redact(
        self,
        content: str,
        matches: List[SecretMatch],
    ) -> RedactionResult:
        """Redact all matched secrets from content.
        
        Args:
            content: Original content
            matches: List of secret matches to redact
            
        Returns:
            RedactionResult with redacted content and entries
        """
        if not matches:
            return RedactionResult(
                original_content=content,
                redacted_content=content,
                redactions=[],
            )
        
        # Sort matches by position (reverse order for replacement)
        sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)
        
        redacted = content
        entries: List[RedactionEntry] = []
        
        for match in sorted_matches:
            replacement = self._get_replacement(match)
            
            # Replace in content
            redacted = redacted[:match.start] + replacement + redacted[match.end:]
            
            entries.append(RedactionEntry(
                original_text=match.match,
                replacement=replacement,
                start=match.start,
                end=match.end,
                line_number=match.line_number,
                pattern_name=match.pattern_name,
                severity=match.severity,
            ))
        
        # Reverse entries to match original order
        entries.reverse()
        
        return RedactionResult(
            original_content=content,
            redacted_content=redacted,
            redactions=entries,
        )
    
    def _get_replacement(self, match: SecretMatch) -> str:
        """Get replacement text for a match.
        
        Uses caching to ensure consistent replacement of same secrets.
        
        Args:
            match: Secret match to get replacement for
            
        Returns:
            Replacement placeholder text
        """
        # Check cache first
        cache_key = f"{match.pattern_name}:{match.match}"
        if cache_key in self._redaction_cache:
            return self._redaction_cache[cache_key]
        
        # Generate semantic placeholder
        replacement = match.placeholder
        
        # Cache for consistency
        self._redaction_cache[cache_key] = replacement
        
        return replacement
    
    def redact_database_url(self, url: str) -> str:
        """Redact a database URL preserving structure.
        
        Handles:
        - postgresql://user:password@host:port/database
        - mysql://user:password@host:port/database
        - mongodb://user:password@host:port/database
        
        Args:
            url: Database URL to redact
            
        Returns:
            Redacted URL with placeholders
        """
        # PostgreSQL pattern
        pg_pattern = re.compile(
            r'(postgres(?:ql)?://)([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(.+)'
        )
        match = pg_pattern.match(url)
        if match:
            scheme, user, password, host, port, db = match.groups()
            port_str = f":{port}" if port else ""
            return f"{scheme}<REDACTED_USER>:<REDACTED_PASSWORD>@<REDACTED_HOST>{port_str}/<REDACTED_DB>"
        
        # MySQL pattern
        mysql_pattern = re.compile(
            r'(mysql://)([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(.+)'
        )
        match = mysql_pattern.match(url)
        if match:
            scheme, user, password, host, port, db = match.groups()
            port_str = f":{port}" if port else ""
            return f"{scheme}<REDACTED_USER>:<REDACTED_PASSWORD>@<REDACTED_HOST>{port_str}/<REDACTED_DB>"
        
        # MongoDB pattern
        mongo_pattern = re.compile(
            r'(mongodb(?:\+srv)?://)([^:]+):([^@]+)@(.+)'
        )
        match = mongo_pattern.match(url)
        if match:
            scheme, user, password, rest = match.groups()
            return f"{scheme}<REDACTED_USER>:<REDACTED_PASSWORD>@<REDACTED_HOST>/<REDACTED_DB>"
        
        # Fallback
        return "<REDACTED_DATABASE_URL>"
    
    def redact_env_file(self, content: str) -> Tuple[str, List[RedactionEntry]]:
        """Redact an entire .env file content.
        
        Preserves key names but redacts values.
        
        Args:
            content: .env file content
            
        Returns:
            Tuple of (redacted content, list of redaction entries)
        """
        lines = content.split("\n")
        redacted_lines = []
        entries: List[RedactionEntry] = []
        
        for i, line in enumerate(lines):
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                redacted_lines.append(line)
                continue
            
            # Parse KEY=VALUE or KEY="VALUE"
            env_pattern = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$')
            match = env_pattern.match(stripped)
            
            if not match:
                redacted_lines.append(line)
                continue
            
            key, value = match.groups()
            
            # Check if value looks like a secret
            if self._is_likely_secret_key(key) or self._is_likely_secret_value(value):
                # Preserve quotes if present
                if value.startswith('"') and value.endswith('"'):
                    redacted_value = '"<REDACTED>"'
                elif value.startswith("'") and value.endswith("'"):
                    redacted_value = "'<REDACTED>'"
                else:
                    redacted_value = "<REDACTED>"
                
                redacted_lines.append(f"{key}={redacted_value}")
                
                entries.append(RedactionEntry(
                    original_text=value,
                    replacement=redacted_value,
                    start=0,  # Position not relevant for line-based
                    end=len(value),
                    line_number=i + 1,
                    pattern_name="env_file_value",
                    severity="high",
                ))
            else:
                redacted_lines.append(line)
        
        return "\n".join(redacted_lines), entries
    
    def _is_likely_secret_key(self, key: str) -> bool:
        """Check if an env var key name suggests it's a secret."""
        secret_indicators = [
            "password", "passwd", "pwd", "secret", "token", "key",
            "api_key", "apikey", "auth", "credential", "private",
            "access_key", "secret_key", "db_pass", "database_password",
        ]
        key_lower = key.lower()
        return any(indicator in key_lower for indicator in secret_indicators)
    
    def _is_likely_secret_value(self, value: str) -> bool:
        """Check if a value looks like a secret."""
        # Remove quotes
        value = value.strip("\"'")
        
        # Empty or placeholder values are not secrets
        if not value or value.startswith("<") or value == "xxx":
            return False
        
        # Database URLs
        if any(value.startswith(prefix) for prefix in ["postgresql://", "mysql://", "mongodb://"]):
            return True
        
        # Long alphanumeric strings
        if len(value) > 20 and re.match(r'^[A-Za-z0-9+/=\-_]+$', value):
            from agents.agent_0_sanitizer.patterns import is_high_entropy
            return is_high_entropy(value)
        
        return False
    
    def clear_cache(self) -> None:
        """Clear the redaction cache."""
        self._redaction_cache.clear()
