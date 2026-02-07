"""Tests for the Reasoner agent."""

import pytest

from agents.agent_2_reasoner.patch_generator import PatchGenerator, LLMResponse


class TestPatchGenerator:
    """Tests for patch generation and validation."""
    
    @pytest.fixture
    def generator(self):
        """Create a patch generator for testing."""
        return PatchGenerator()
    
    def test_parse_valid_llm_response(self, generator):
        """Should parse well-formatted LLM response."""
        response = """
## Root Cause
Missing null check in user validation function

## Explanation
The function `validate_user` does not check if the user object is None
before accessing its properties, causing an AttributeError.

## Confidence
0.85

## Assumptions
- The user object can be None when coming from the database
- The fix should handle None gracefully

## Fix
```diff
--- a/app/validators.py
+++ b/app/validators.py
@@ -10,3 +10,5 @@ def validate_user(user):
+    if user is None:
+        return False
     return user.is_active
```

## Risks
None identified - this is a straightforward null check.
"""
        
        parsed = generator.parse_llm_response(response)
        
        assert parsed.root_cause_summary == "Missing null check in user validation function"
        assert "null check" in parsed.explanation.lower() or "None" in parsed.explanation
        assert parsed.confidence == 0.85
        assert len(parsed.assumptions) == 2
        assert "validate_user" in parsed.diff or "validators.py" in parsed.diff
        assert parsed.risks != ""
    
    def test_parse_response_clamps_confidence(self, generator):
        """Should clamp confidence to [0, 1] range."""
        response = """
## Root Cause
Test

## Confidence
1.5

## Fix
```diff
- old
+ new
```
"""
        parsed = generator.parse_llm_response(response)
        assert parsed.confidence == 1.0
        
        response2 = """
## Root Cause
Test

## Confidence
-0.5

## Fix
```diff
- old
+ new
```
"""
        parsed2 = generator.parse_llm_response(response2)
        assert parsed2.confidence == 0.0
    
    def test_validate_valid_diff(self, generator):
        """Should validate a properly formatted diff."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 line 1
+line 2
 line 3
"""
        result = generator.validate_diff(diff)
        
        assert result.is_valid
        assert len(result.validation_errors) == 0
    
    def test_validate_empty_diff(self, generator):
        """Should reject empty diff."""
        result = generator.validate_diff("")
        
        assert not result.is_valid
        assert "Empty diff" in result.validation_errors[0]
    
    def test_validate_missing_hunks(self, generator):
        """Should reject diff without hunks."""
        diff = """--- a/file.py
+++ b/file.py
some random text
"""
        result = generator.validate_diff(diff)
        
        assert not result.is_valid
        assert any("hunk" in e.lower() for e in result.validation_errors)
    
    def test_normalize_diff(self, generator):
        """Should normalize diff format."""
        diff = "\n\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n\n\n"
        normalized = generator.normalize_diff(diff)
        
        # Should start with file header, not blank lines
        assert normalized.startswith("---")
        # Should end with single newline
        assert normalized.endswith("\n")
        assert not normalized.endswith("\n\n")


class TestLLMResponseParsing:
    """Tests for edge cases in LLM response parsing."""
    
    @pytest.fixture
    def generator(self):
        return PatchGenerator()
    
    def test_missing_sections(self, generator):
        """Should handle missing sections gracefully."""
        response = """
## Root Cause
The bug

## Confidence
0.7
"""
        parsed = generator.parse_llm_response(response)
        
        assert parsed.root_cause_summary == "The bug"
        assert parsed.confidence == 0.7
        assert parsed.diff == ""  # Missing
        assert len(parsed.assumptions) == 0  # Missing
    
    def test_malformed_confidence(self, generator):
        """Should handle non-numeric confidence."""
        response = """
## Root Cause
Test

## Confidence
high
"""
        parsed = generator.parse_llm_response(response)
        
        assert "confidence" in parsed.parse_errors[0].lower()
    
    def test_diff_without_code_block(self, generator):
        """Should extract diff even without code block markers."""
        response = """
## Root Cause
Test

## Confidence
0.8

## Fix
--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-old line
+new line
"""
        parsed = generator.parse_llm_response(response)
        
        # Should still extract the diff
        assert "old line" in parsed.diff or "new line" in parsed.diff
