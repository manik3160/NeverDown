"""Log parser for the Detective agent."""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from models.analysis import ErrorInfo


@dataclass
class ParsedStackTrace:
    """Parsed stack trace information."""
    error_type: str
    error_message: str
    frames: List["StackFrame"]
    raw_trace: str
    language: str = "python"


@dataclass
class StackFrame:
    """A single frame in a stack trace."""
    file_path: str
    line_number: int
    function_name: str
    code_context: Optional[str] = None
    is_user_code: bool = True


class LogParser:
    """Multi-format log parser for error extraction."""
    
    # Patterns for different log formats
    PYTHON_TRACEBACK = re.compile(
        r'Traceback \(most recent call last\):\n(.*?)(?:^(\w+(?:Error|Exception|Warning)): (.+))$',
        re.MULTILINE | re.DOTALL
    )
    
    PYTHON_FRAME = re.compile(
        r'^\s*File "([^"]+)", line (\d+), in (\w+)\n\s*(.+)?$',
        re.MULTILINE
    )
    
    PYTHON_ERROR_LINE = re.compile(
        r'^(\w+(?:Error|Exception|Warning)): (.+)$',
        re.MULTILINE
    )
    
    # Node.js/JavaScript patterns
    JS_STACK_FRAME = re.compile(
        r'^\s+at (?:(.+?) \()?((?:[A-Za-z]:)?[^:]+):(\d+):\d+\)?$',
        re.MULTILINE
    )
    
    JS_ERROR = re.compile(
        r'^((?:\w+)?Error): (.+)$',
        re.MULTILINE
    )
    
    # Generic error patterns
    GENERIC_ERROR = re.compile(
        r'(?:ERROR|Error|error|FATAL|Fatal|fatal)[:\s]+(.+)',
        re.MULTILINE
    )
    
    HTTP_ERROR = re.compile(
        r'(?:HTTP[/\s]?\d+\.\d+\s+)?(\d{3})\s+(.+)',
    )
    
    def parse(self, log_content: str) -> List[ErrorInfo]:
        """Parse log content and extract errors.
        
        Args:
            log_content: Raw log content
            
        Returns:
            List of extracted error information
        """
        errors: List[ErrorInfo] = []
        
        # Try Python traceback parsing first
        python_errors = self._parse_python_traceback(log_content)
        
        # Try JavaScript stack trace
        js_errors = self._parse_js_stack(log_content)
        
        # Prefer the parser that found file paths
        if python_errors and any(e.file_path for e in python_errors):
            errors.extend(python_errors)
        elif js_errors and any(e.file_path for e in js_errors):
            errors.extend(js_errors)
        elif python_errors:
            errors.extend(python_errors)
        elif js_errors:
            errors.extend(js_errors)
        
        # Try generic error patterns if no structured errors found
        if not errors:
            generic_errors = self._parse_generic_errors(log_content)
            errors.extend(generic_errors)
        
        return errors
    
    def _parse_python_traceback(self, content: str) -> List[ErrorInfo]:
        """Parse Python traceback format."""
        errors: List[ErrorInfo] = []
        
        # Find error lines
        for match in self.PYTHON_ERROR_LINE.finditer(content):
            error_type = match.group(1)
            error_message = match.group(2)
            
            # Try to find associated stack trace
            stack_start = content.rfind('Traceback (most recent call last):', 0, match.start())
            
            file_path = None
            line_number = None
            stack_trace = None
            
            if stack_start != -1:
                stack_trace = content[stack_start:match.end()]
                
                # Parse frames to find the last user code frame
                frames = list(self.PYTHON_FRAME.finditer(stack_trace))
                
                # Find the most relevant frame (last non-library frame)
                for frame in reversed(frames):
                    frame_path = frame.group(1)
                    # Skip standard library and site-packages
                    if not any(skip in frame_path for skip in [
                        'site-packages', 'lib/python', '/usr/lib/',
                        'venv/', '.venv/', 'anaconda', 'miniconda'
                    ]):
                        file_path = frame_path
                        line_number = int(frame.group(2))
                        break
                
                # Fallback to last frame if no user code found
                if file_path is None and frames:
                    file_path = frames[-1].group(1)
                    line_number = int(frames[-1].group(2))
            
            errors.append(ErrorInfo(
                error_type=error_type,
                message=error_message,
                file_path=file_path,
                line_number=line_number,
                stack_trace=stack_trace,
            ))
        
        return errors
    
    def _parse_js_stack(self, content: str) -> List[ErrorInfo]:
        """Parse JavaScript stack trace format."""
        errors: List[ErrorInfo] = []
        
        for match in self.JS_ERROR.finditer(content):
            error_type = match.group(1)
            error_message = match.group(2)
            
            # Look for stack frames after this error
            stack_start = match.end()
            remaining = content[stack_start:]
            
            # Collect stack frames
            frames: List[Tuple[str, str, int]] = []
            for frame_match in self.JS_STACK_FRAME.finditer(remaining):
                func_name = frame_match.group(1) or "<anonymous>"
                file_path = frame_match.group(2)
                line_num = int(frame_match.group(3))
                frames.append((func_name, file_path, line_num))
                
                # Stop after finding frames (before next error or end)
                if len(frames) > 20:
                    break
            
            # Find first non-node_modules frame
            file_path = None
            line_number = None
            for func, path, line in frames:
                if 'node_modules' not in path:
                    # Normalize path: strip leading slash for relative paths
                    file_path = path.lstrip('/')
                    line_number = line
                    break
            
            if file_path is None and frames:
                _, path, line_number = frames[0]
                file_path = path.lstrip('/')
            
            errors.append(ErrorInfo(
                error_type=error_type,
                message=error_message,
                file_path=file_path,
                line_number=line_number,
                stack_trace=remaining[:500] if frames else None,
            ))
        
        return errors
    
    def _parse_generic_errors(self, content: str) -> List[ErrorInfo]:
        """Parse generic error patterns."""
        errors: List[ErrorInfo] = []
        
        for match in self.GENERIC_ERROR.finditer(content):
            message = match.group(1).strip()
            
            # Try to extract file/line from message
            file_match = re.search(r'([^\s:]+):(\d+)', message)
            file_path = file_match.group(1) if file_match else None
            line_number = int(file_match.group(2)) if file_match else None
            
            errors.append(ErrorInfo(
                error_type="Error",
                message=message,
                file_path=file_path,
                line_number=line_number,
            ))
        
        # Deduplicate by message
        seen_messages = set()
        unique_errors = []
        for error in errors:
            if error.message not in seen_messages:
                seen_messages.add(error.message)
                unique_errors.append(error)
        
        return unique_errors
    
    def parse_json_logs(self, content: str) -> List[ErrorInfo]:
        """Parse JSON-formatted logs (e.g., structured logging output).
        
        Args:
            content: JSON log content (one JSON object per line)
            
        Returns:
            List of extracted errors
        """
        errors: List[ErrorInfo] = []
        
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # Check if this is an error log
            level = data.get('level', data.get('levelname', '')).lower()
            if level not in ('error', 'critical', 'fatal', 'exception'):
                continue
            
            # Extract error information
            error_type = data.get('exception_type', data.get('exc_type', 'Error'))
            message = data.get('message', data.get('msg', data.get('error', '')))
            
            # Try to get file/line
            file_path = data.get('filename', data.get('file', data.get('pathname')))
            line_number = data.get('lineno', data.get('line_number', data.get('line')))
            
            if isinstance(line_number, str):
                try:
                    line_number = int(line_number)
                except ValueError:
                    line_number = None
            
            # Get stack trace if available
            stack_trace = data.get('traceback', data.get('stack_trace', data.get('exc_info')))
            if isinstance(stack_trace, list):
                stack_trace = '\n'.join(stack_trace)
            
            errors.append(ErrorInfo(
                error_type=error_type,
                message=message,
                file_path=file_path,
                line_number=line_number,
                stack_trace=stack_trace,
            ))
        
        return errors
    
    def categorize_error(self, error: ErrorInfo) -> str:
        """Categorize an error by type.
        
        Args:
            error: Error to categorize
            
        Returns:
            Category string (maps to FailureCategory enum)
        """
        error_type = error.error_type.lower()
        message = error.message.lower()
        
        # Python-specific errors
        if 'nameerror' in error_type:
            return 'name_error'
        if 'typeerror' in error_type:
            return 'type_error'
        if 'syntaxerror' in error_type:
            return 'syntax_error'
        if 'importerror' in error_type or 'modulenotfounderror' in error_type:
            return 'import_error'
        if 'attributeerror' in error_type:
            return 'logic_error'
        if 'keyerror' in error_type or 'indexerror' in error_type:
            return 'logic_error'
        
        # Database errors
        if any(db in error_type for db in ['database', 'sql', 'postgres', 'mysql', 'mongo']):
            return 'database_query'
        if 'connection' in message or 'connect' in message:
            return 'connection_error'
        
        # Timeout errors
        if 'timeout' in error_type or 'timeout' in message:
            return 'timeout'
        
        # Permission errors
        if 'permission' in error_type or 'permission denied' in message:
            return 'permission_error'
        
        # Config errors
        if 'config' in message or 'configuration' in message:
            return 'config_mismatch'
        if 'environment' in message or 'env' in message:
            return 'config_mismatch'
        
        return 'logic_error'  # Default
