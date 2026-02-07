"""Secret detection patterns for the Sanitizer agent."""

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern

import yaml

from config.settings import get_settings


@dataclass
class SecretPattern:
    """A pattern for detecting secrets."""
    name: str
    pattern: Pattern[str]
    placeholder: str
    severity: str = "high"
    capture_group: Optional[int] = None
    confidence: float = 1.0
    
    def find_matches(self, content: str) -> List[re.Match]:
        """Find all matches of this pattern in content."""
        return list(self.pattern.finditer(content))


@dataclass
class SecretMatch:
    """A detected secret match."""
    pattern_name: str
    match: str
    start: int
    end: int
    line_number: int
    placeholder: str
    severity: str
    confidence: float = 1.0
    

@dataclass
class PatternConfig:
    """Configuration for secret patterns."""
    patterns: List[SecretPattern] = field(default_factory=list)
    entropy_threshold: float = 4.5
    min_entropy_length: int = 16
    scan_patterns: List[str] = field(default_factory=list)
    skip_patterns: List[str] = field(default_factory=list)
    severity_actions: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def calculate_shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string.
    
    Higher entropy indicates more randomness, which is characteristic
    of secrets like API keys and passwords.
    
    Args:
        s: String to analyze
        
    Returns:
        Entropy value (higher = more random)
    """
    if not s:
        return 0.0
    
    # Count character frequencies
    freq: Dict[str, int] = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    
    # Calculate entropy
    length = len(s)
    entropy = 0.0
    for count in freq.values():
        probability = count / length
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy


def is_high_entropy(s: str, threshold: float = 4.5, min_length: int = 16) -> bool:
    """Check if a string has high entropy (likely a secret).
    
    Args:
        s: String to check
        threshold: Entropy threshold (default 4.5)
        min_length: Minimum string length to check
        
    Returns:
        True if string has high entropy
    """
    if len(s) < min_length:
        return False
    
    entropy = calculate_shannon_entropy(s)
    return entropy >= threshold


# Default patterns compiled at module load
DEFAULT_PATTERNS: List[SecretPattern] = [
    # AWS
    SecretPattern(
        name="aws_access_key_id",
        pattern=re.compile(r'(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}'),
        placeholder="<REDACTED_AWS_ACCESS_KEY>",
        severity="critical",
    ),
    SecretPattern(
        name="aws_secret_access_key",
        pattern=re.compile(
            r'(?i)aws[_\-]?secret[_\-]?access[_\-]?key[\s]*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?'
        ),
        placeholder="<REDACTED_AWS_SECRET_KEY>",
        severity="critical",
        capture_group=1,
    ),
    
    # GitHub
    SecretPattern(
        name="github_token",
        pattern=re.compile(r'gh[pousr]_[A-Za-z0-9_]{36}'),
        placeholder="<REDACTED_GITHUB_TOKEN>",
        severity="critical",
    ),
    SecretPattern(
        name="github_oauth",
        pattern=re.compile(r'gho_[A-Za-z0-9]{36}'),
        placeholder="<REDACTED_GITHUB_OAUTH>",
        severity="critical",
    ),
    
    # JWT
    SecretPattern(
        name="jwt_token",
        pattern=re.compile(r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_.+/=]*'),
        placeholder="<REDACTED_JWT_TOKEN>",
        severity="high",
    ),
    
    # Database URLs
    SecretPattern(
        name="postgres_url",
        pattern=re.compile(
            r'postgres(?:ql)?://([^:\s]+):([^@\s]+)@([^/\s:]+)(?::\d+)?/([^\s"\']*)'
        ),
        placeholder="postgresql://<REDACTED_USER>:<REDACTED_PASSWORD>@<REDACTED_HOST>/<REDACTED_DB>",
        severity="critical",
    ),
    SecretPattern(
        name="mysql_url",
        pattern=re.compile(r'mysql://([^:\s]+):([^@\s]+)@([^/\s:]+)(?::\d+)?/([^\s"\']*)'),
        placeholder="mysql://<REDACTED_USER>:<REDACTED_PASSWORD>@<REDACTED_HOST>/<REDACTED_DB>",
        severity="critical",
    ),
    SecretPattern(
        name="mongodb_url",
        pattern=re.compile(r'mongodb(?:\+srv)?://([^:\s]+):([^@\s]+)@([^\s"\']*)'),
        placeholder="mongodb://<REDACTED_USER>:<REDACTED_PASSWORD>@<REDACTED_HOST>/<REDACTED_DB>",
        severity="critical",
    ),
    
    # API Keys
    SecretPattern(
        name="api_key_assignment",
        pattern=re.compile(
            r'(?i)(?:api[_\-]?key|apikey|api_secret|secret[_\-]?key)[\s]*[=:]\s*["\']?([A-Za-z0-9\-_]{20,})["\']?'
        ),
        placeholder="<REDACTED_API_KEY>",
        severity="high",
        capture_group=1,
    ),
    
    # Private Keys
    SecretPattern(
        name="rsa_private_key",
        pattern=re.compile(r'-----BEGIN (?:RSA )?PRIVATE KEY-----'),
        placeholder="<REDACTED_RSA_PRIVATE_KEY>",
        severity="critical",
    ),
    SecretPattern(
        name="ssh_private_key",
        pattern=re.compile(r'-----BEGIN OPENSSH PRIVATE KEY-----'),
        placeholder="<REDACTED_SSH_PRIVATE_KEY>",
        severity="critical",
    ),
    
    # GCP
    SecretPattern(
        name="gcp_api_key",
        pattern=re.compile(r'AIza[0-9A-Za-z\-_]{35}'),
        placeholder="<REDACTED_GCP_API_KEY>",
        severity="high",
    ),
    
    # Stripe
    SecretPattern(
        name="stripe_key",
        pattern=re.compile(r'(?:sk|pk)_(?:live|test)_[0-9a-zA-Z]{24,}'),
        placeholder="<REDACTED_STRIPE_KEY>",
        severity="critical",
    ),
    
    # Slack
    SecretPattern(
        name="slack_token",
        pattern=re.compile(r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*'),
        placeholder="<REDACTED_SLACK_TOKEN>",
        severity="high",
    ),
    
    # Generic password assignment
    SecretPattern(
        name="password_assignment",
        pattern=re.compile(r'(?i)(?:password|passwd|pwd)[\s]*[=:]\s*["\']([^"\']+)["\']'),
        placeholder="<REDACTED_PASSWORD>",
        severity="high",
        capture_group=1,
    ),
]


class PatternMatcher:
    """Matches secrets using compiled patterns."""
    
    def __init__(self, config: Optional[PatternConfig] = None):
        """Initialize with optional config.
        
        Args:
            config: Pattern configuration (loads from file if not provided)
        """
        if config:
            self.config = config
        else:
            self.config = self._load_config()
        
        # Combine default patterns with config patterns
        self.patterns = DEFAULT_PATTERNS + self.config.patterns
    
    def _load_config(self) -> PatternConfig:
        """Load pattern configuration from YAML file."""
        settings = get_settings()
        config_path = Path(settings.REDACTION_PATTERNS_FILE)
        
        if not config_path.exists():
            return PatternConfig()
        
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
            
            patterns = []
            for p in data.get("secret_patterns", []):
                try:
                    patterns.append(SecretPattern(
                        name=p["name"],
                        pattern=re.compile(p["pattern"]),
                        placeholder=p["placeholder"],
                        severity=p.get("severity", "high"),
                        capture_group=p.get("capture_group"),
                    ))
                except re.error:
                    continue  # Skip invalid patterns
            
            return PatternConfig(
                patterns=patterns,
                entropy_threshold=data.get("entropy_threshold", 4.5),
                min_entropy_length=data.get("min_entropy_length", 16),
                scan_patterns=data.get("scan_patterns", []),
                skip_patterns=data.get("skip_patterns", []),
                severity_actions=data.get("severity_actions", {}),
            )
        except Exception:
            return PatternConfig()
    
    def find_secrets(self, content: str, file_path: str = "") -> List[SecretMatch]:
        """Find all secrets in content.
        
        Args:
            content: Text content to scan
            file_path: File path for context
            
        Returns:
            List of secret matches
        """
        matches: List[SecretMatch] = []
        lines = content.split("\n")
        
        # Track positions to avoid duplicate matches
        seen_positions: set = set()
        
        for pattern in self.patterns:
            for match in pattern.find_matches(content):
                # Get matched text
                if pattern.capture_group is not None:
                    try:
                        matched_text = match.group(pattern.capture_group)
                    except IndexError:
                        matched_text = match.group(0)
                else:
                    matched_text = match.group(0)
                
                # Skip if already matched at this position
                pos_key = (match.start(), match.end())
                if pos_key in seen_positions:
                    continue
                seen_positions.add(pos_key)
                
                # Calculate line number
                line_num = content[:match.start()].count("\n") + 1
                
                matches.append(SecretMatch(
                    pattern_name=pattern.name,
                    match=matched_text,
                    start=match.start(),
                    end=match.end(),
                    line_number=line_num,
                    placeholder=pattern.placeholder,
                    severity=pattern.severity,
                    confidence=pattern.confidence,
                ))
        
        return matches
    
    def find_high_entropy_strings(
        self,
        content: str,
        threshold: Optional[float] = None,
        min_length: Optional[int] = None,
    ) -> List[SecretMatch]:
        """Find high-entropy strings that might be secrets.
        
        Args:
            content: Text content to scan
            threshold: Entropy threshold (default from config)
            min_length: Minimum string length (default from config)
            
        Returns:
            List of potential secret matches
        """
        threshold = threshold or self.config.entropy_threshold
        min_length = min_length or self.config.min_entropy_length
        
        matches: List[SecretMatch] = []
        
        # Pattern to find potential secrets (alphanumeric strings with special chars)
        potential_secrets = re.compile(r'[A-Za-z0-9+/=\-_]{20,}')
        
        for match in potential_secrets.finditer(content):
            text = match.group(0)
            
            if is_high_entropy(text, threshold, min_length):
                line_num = content[:match.start()].count("\n") + 1
                
                matches.append(SecretMatch(
                    pattern_name="high_entropy",
                    match=text,
                    start=match.start(),
                    end=match.end(),
                    line_number=line_num,
                    placeholder="<REDACTED_HIGH_ENTROPY>",
                    severity="medium",
                    confidence=0.7,  # Lower confidence for entropy-based detection
                ))
        
        return matches
    
    def should_scan_file(self, file_path: str) -> bool:
        """Check if a file should be scanned based on config patterns.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be scanned
        """
        from fnmatch import fnmatch
        
        # Check skip patterns first
        for pattern in self.config.skip_patterns:
            if fnmatch(file_path, pattern):
                return False
        
        # If no scan patterns defined, scan all non-skipped files
        if not self.config.scan_patterns:
            return True
        
        # Check if file matches any scan pattern
        for pattern in self.config.scan_patterns:
            if fnmatch(file_path, pattern) or fnmatch(Path(file_path).name, pattern):
                return True
        
        return False
