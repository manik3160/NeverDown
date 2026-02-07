"""Tests for the Detective agent."""

import pytest

from agents.agent_1_detective.log_parser import LogParser
from agents.agent_1_detective.diff_analyzer import DiffAnalyzer


class TestLogParser:
    """Tests for log parsing."""
    
    @pytest.fixture
    def parser(self):
        """Create a log parser for testing."""
        return LogParser()
    
    def test_parse_python_traceback(self, parser):
        """Should parse Python traceback and extract error info."""
        traceback = """
Traceback (most recent call last):
  File "/app/main.py", line 42, in process_request
    result = calculate(data)
  File "/app/utils.py", line 15, in calculate
    return value / 0
ZeroDivisionError: division by zero
"""
        errors = parser.parse(traceback)
        
        assert len(errors) == 1
        assert errors[0].error_type == "ZeroDivisionError"
        assert errors[0].message == "division by zero"
        assert errors[0].file_path is not None
        assert "utils.py" in errors[0].file_path
        assert errors[0].line_number == 15
    
    def test_parse_python_multiple_errors(self, parser):
        """Should extract multiple errors from logs."""
        logs = """
ERROR: First error occurred
Traceback (most recent call last):
  File "/app/a.py", line 10, in func_a
    raise ValueError("Invalid value")
ValueError: Invalid value

ERROR: Second error occurred
Traceback (most recent call last):
  File "/app/b.py", line 20, in func_b
    raise KeyError("Missing key")
KeyError: Missing key
"""
        errors = parser.parse(logs)
        
        assert len(errors) >= 2
        error_types = [e.error_type for e in errors]
        assert "ValueError" in error_types
        assert "KeyError" in error_types
    
    def test_parse_javascript_stack(self, parser):
        """Should parse JavaScript stack traces."""
        stack = """
TypeError: Cannot read property 'foo' of undefined
    at processData (/app/src/handler.js:45:12)
    at async Router.handle (/app/node_modules/express/lib/router/index.js:144:7)
"""
        errors = parser.parse(stack)
        
        assert len(errors) >= 1
        assert errors[0].error_type == "TypeError"
        assert "Cannot read property" in errors[0].message
        # Should prioritize user code over node_modules
        if errors[0].file_path:
            assert "handler.js" in errors[0].file_path
    
    def test_parse_generic_error(self, parser):
        """Should parse generic error messages."""
        logs = """
2024-01-15 10:30:45 ERROR: Connection to database failed
2024-01-15 10:30:46 FATAL: Application shutdown due to critical error
"""
        errors = parser.parse(logs)
        
        assert len(errors) >= 1
        assert any("database" in e.message.lower() for e in errors)
    
    def test_parse_json_logs(self, parser):
        """Should parse JSON-formatted logs."""
        logs = """
{"level": "info", "message": "Starting application"}
{"level": "error", "message": "Database connection failed", "exception_type": "ConnectionError", "filename": "db.py", "lineno": 42}
{"level": "info", "message": "Shutting down"}
"""
        errors = parser.parse_json_logs(logs)
        
        assert len(errors) == 1
        assert errors[0].error_type == "ConnectionError"
        assert errors[0].message == "Database connection failed"
        assert errors[0].line_number == 42
    
    def test_categorize_name_error(self, parser):
        """Should categorize NameError correctly."""
        from models.analysis import ErrorInfo
        
        error = ErrorInfo(
            error_type="NameError",
            message="name 'undefined_var' is not defined",
        )
        
        category = parser.categorize_error(error)
        assert category == "name_error"
    
    def test_categorize_timeout(self, parser):
        """Should categorize timeout errors."""
        from models.analysis import ErrorInfo
        
        error = ErrorInfo(
            error_type="Error",
            message="Request timeout after 30 seconds",
        )
        
        category = parser.categorize_error(error)
        assert category == "timeout"


class TestDiffAnalyzer:
    """Tests for git diff analysis."""
    
    def test_parse_simple_diff(self):
        """Should parse a simple unified diff."""
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -10,3 +10,4 @@ def main():
     print("Hello")
+    print("World")
     return 0
"""
        analyzer = DiffAnalyzer("/tmp/fake-repo")
        files = analyzer._parse_diff_output(diff)
        
        assert len(files) == 1
        assert files[0].file_path == "app.py"
        assert files[0].additions >= 1
    
    def test_parse_new_file_diff(self):
        """Should identify new files in diff."""
        diff = """diff --git a/new_file.py b/new_file.py
new file mode 100644
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,3 @@
+def hello():
+    return "world"
+
"""
        analyzer = DiffAnalyzer("/tmp/fake-repo")
        files = analyzer._parse_diff_output(diff)
        
        assert len(files) == 1
        assert files[0].status == "added"
    
    def test_calculate_relatedness_same_dir(self):
        """Files in same directory should have high relatedness."""
        analyzer = DiffAnalyzer("/tmp/fake-repo")
        
        score = analyzer._calculate_relatedness(
            "src/handlers/api.py",
            ["src/handlers/utils.py", "tests/test_api.py"],
        )
        
        assert score >= 0.5
    
    def test_calculate_relatedness_test_file(self):
        """Test files should relate to their source files."""
        analyzer = DiffAnalyzer("/tmp/fake-repo")
        
        score = analyzer._calculate_relatedness(
            "test_user.py",
            ["user.py", "config.py"],
        )
        
        assert score >= 0.3
