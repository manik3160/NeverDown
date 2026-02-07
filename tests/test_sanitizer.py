"""Tests for the Sanitizer agent."""

import pytest

from agents.agent_0_sanitizer.patterns import (
    PatternMatcher,
    SecretMatch,
    calculate_shannon_entropy,
    is_high_entropy,
)
from agents.agent_0_sanitizer.redactor import Redactor


class TestEntropyCalculation:
    """Tests for Shannon entropy calculation."""
    
    def test_empty_string(self):
        """Empty string should have zero entropy."""
        assert calculate_shannon_entropy("") == 0.0
    
    def test_single_character(self):
        """Single character repeated has zero entropy."""
        assert calculate_shannon_entropy("aaaaaaa") == 0.0
    
    def test_high_entropy_string(self):
        """Random-looking string should have high entropy."""
        # A mix of characters should have entropy > 4
        entropy = calculate_shannon_entropy("aB3$kL9!mN2@pQ5#")
        assert entropy > 3.5
    
    def test_is_high_entropy_short(self):
        """Short strings should not be flagged as high entropy."""
        assert not is_high_entropy("abc123", threshold=4.5, min_length=16)
    
    def test_is_high_entropy_api_key(self):
        """API key-like string should be flagged."""
        api_key = "sk_test_FakeKeyForTestingPurposesOnly1234567890"
        assert is_high_entropy(api_key, threshold=4.0, min_length=20)


class TestPatternMatcher:
    """Tests for secret pattern detection."""
    
    @pytest.fixture
    def matcher(self):
        """Create a pattern matcher for testing."""
        return PatternMatcher()
    
    def test_aws_access_key_detection(self, matcher):
        """Should detect AWS access key IDs."""
        content = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        matches = matcher.find_secrets(content)
        
        assert len(matches) >= 1
        assert any(m.pattern_name == "aws_access_key_id" for m in matches)
    
    def test_github_token_detection(self, matcher):
        """Should detect GitHub tokens."""
        content = "GITHUB_TOKEN=ghp_wWA0FEI7Z1234567890123456789012345678"
        matches = matcher.find_secrets(content)
        
        assert len(matches) >= 1
        assert any(m.pattern_name == "github_token" for m in matches)
    
    def test_jwt_detection(self, matcher):
        """Should detect JWT tokens."""
        content = "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        matches = matcher.find_secrets(content)
        
        assert len(matches) >= 1
        assert any(m.pattern_name == "jwt_token" for m in matches)
    
    def test_postgres_url_detection(self, matcher):
        """Should detect PostgreSQL URLs."""
        content = "DATABASE_URL=postgresql://user:password123@localhost:5432/mydb"
        matches = matcher.find_secrets(content)
        
        assert len(matches) >= 1
        assert any(m.pattern_name == "postgres_url" for m in matches)
    
    def test_no_false_positives(self, matcher):
        """Should not detect secrets in regular code."""
        content = """
def hello_world():
    print("Hello, World!")
    return 42
"""
        matches = matcher.find_secrets(content)
        assert len(matches) == 0
    
    def test_stripe_key_detection(self, matcher):
        """Should detect Stripe API keys."""
        content = "STRIPE_KEY=sk_test_FakeTestKey1234567890ABCD"
        matches = matcher.find_secrets(content)
        
        assert len(matches) >= 1
        assert any(m.pattern_name == "stripe_key" for m in matches)


class TestRedactor:
    """Tests for secret redaction."""
    
    @pytest.fixture
    def redactor(self):
        """Create a redactor for testing."""
        return Redactor()
    
    def test_redact_single_secret(self, redactor):
        """Should redact a single secret."""
        matches = [
            SecretMatch(
                pattern_name="api_key",
                match="sk_1234567890abcdef",
                start=8,
                end=26,
                line_number=1,
                placeholder="<REDACTED_API_KEY>",
                severity="high",
            )
        ]
        
        result = redactor.redact("API_KEY=sk_1234567890abcdef", matches)
        
        assert "<REDACTED_API_KEY>" in result.redacted_content
        assert "sk_1234567890abcdef" not in result.redacted_content
        assert result.redaction_count == 1
    
    def test_redact_multiple_secrets(self, redactor):
        """Should redact multiple secrets."""
        content = "KEY1=secret1\nKEY2=secret2"
        matches = [
            SecretMatch(
                pattern_name="api_key",
                match="secret1",
                start=5,
                end=12,
                line_number=1,
                placeholder="<REDACTED>",
                severity="high",
            ),
            SecretMatch(
                pattern_name="api_key",
                match="secret2",
                start=18,
                end=25,
                line_number=2,
                placeholder="<REDACTED>",
                severity="high",
            ),
        ]
        
        result = redactor.redact(content, matches)
        
        assert "secret1" not in result.redacted_content
        assert "secret2" not in result.redacted_content
        assert result.redaction_count == 2
    
    def test_redact_env_file(self, redactor):
        """Should redact .env file content."""
        content = """
# Database config
DATABASE_PASSWORD=supersecret123
API_KEY="my-api-key-value"
DEBUG=true
"""
        redacted, entries = redactor.redact_env_file(content)
        
        assert "supersecret123" not in redacted
        assert "my-api-key-value" not in redacted
        assert "DEBUG=true" in redacted  # Non-secret value preserved
        assert "<REDACTED>" in redacted
    
    def test_database_url_redaction(self, redactor):
        """Should redact database URL preserving structure."""
        url = "postgresql://admin:secretpass@db.example.com:5432/production"
        redacted = redactor.redact_database_url(url)
        
        assert "secretpass" not in redacted
        assert "admin" not in redacted
        assert "<REDACTED_PASSWORD>" in redacted
        assert "postgresql://" in redacted
