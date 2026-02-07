"""Prompt builder for the Reasoner agent."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from models.analysis import DetectiveReport, ErrorInfo, SuspectedFile


class PromptBuilder:
    """Builds LLM prompts from sanitized context."""
    
    # System prompt for root cause analysis
    SYSTEM_PROMPT = """You are an expert software engineer analyzing a bug in a codebase.
You are given SANITIZED code where all secrets have been replaced with placeholders like <REDACTED_PASSWORD>.
This is intentional - do NOT try to guess or replace these placeholders.

Your task:
1. Analyze the error and code to identify the root cause
2. Propose a minimal fix as a unified diff patch
3. Explain your reasoning clearly
4. Provide a confidence score (0.0-1.0) for your analysis

IMPORTANT RULES:
- Only propose changes to files mentioned in the analysis
- Keep fixes minimal - change only what's necessary
- Do NOT modify any <REDACTED_*> placeholders
- Include the complete fix, not partial changes
- If you're uncertain, express that in your confidence score

Output your response in this EXACT format:

## Root Cause
<One-line summary of the root cause>

## Explanation
<Detailed explanation of why this bug occurs>

## Confidence
<A decimal number between 0.0 and 1.0>

## Assumptions
<List any assumptions you made, one per line, starting with - >

## Fix
```diff
<Your unified diff patch here>
```

## Risks
<Any potential risks or side effects of this fix>
"""

    def __init__(self, repo_path: str):
        """Initialize with repository path for code reading.
        
        Args:
            repo_path: Path to sanitized repository
        """
        self.repo_path = Path(repo_path)
    
    def build_analysis_prompt(
        self,
        report: DetectiveReport,
        max_code_lines: int = 200,
    ) -> str:
        """Build the main analysis prompt for the LLM.
        
        Args:
            report: Detective report with errors and suspects
            max_code_lines: Maximum lines of code to include
            
        Returns:
            Formatted prompt string
        """
        sections = []
        
        # Error information section
        sections.append("# Error Information\n")
        for i, error in enumerate(report.errors[:5], 1):  # Max 5 errors
            sections.append(f"## Error {i}")
            sections.append(f"**Type**: {error.error_type}")
            sections.append(f"**Message**: {error.message}")
            if error.file_path:
                sections.append(f"**File**: {error.file_path}")
            if error.line_number:
                sections.append(f"**Line**: {error.line_number}")
            if error.stack_trace:
                # Truncate long stack traces
                trace = error.stack_trace[:1000]
                sections.append(f"**Stack Trace**:\n```\n{trace}\n```")
            sections.append("")
        
        # Failure category
        sections.append(f"**Failure Category**: {report.failure_category.value}")
        sections.append("")
        
        # Suspected files with code
        total_lines = 0
        
        if report.suspected_files:
            sections.append("# Suspected Files\n")
            for sf in report.suspected_files[:5]:  # Top 5 suspects
                if total_lines >= max_code_lines:
                    break
                
                sections.append(f"## {sf.path} (Confidence: {sf.confidence:.2f})")
                
                if sf.line_numbers:
                    sections.append(f"Suspected lines: {sf.line_numbers}")
                
                if sf.evidence:
                    sections.append("Evidence:")
                    for ev in sf.evidence[:3]:
                        sections.append(f"- {ev[:200]}")  # Truncate long evidence
                
                # Read and include file content
                code = self._read_file_content(sf)
                if code:
                    lines_added = code.count('\n') + 1
                    total_lines += lines_added
                    sections.append(f"```\n{code}\n```")
                
                sections.append("")
        else:
            # No suspected files - provide project file listing and sample code
            sections.append("# Project Overview\n")
            sections.append("No specific files identified from error logs. Here is the project structure:\n")
            
            # Get file listing
            file_listing = self._get_project_file_listing()
            sections.append(f"```\n{file_listing}\n```\n")
            
            # Include key source files
            sections.append("# Key Source Files\n")
            key_files = self._get_key_source_files(max_lines=max_code_lines)
            for file_path, content in key_files:
                sections.append(f"## {file_path}")
                sections.append(f"```\n{content}\n```")
                sections.append("")
        
        # Recent changes
        if report.recent_changes:
            sections.append("# Recent Changes\n")
            for change in report.recent_changes[:3]:
                sections.append(f"- **{change.commit_sha[:8]}**: {change.message}")
                sections.append(f"  Files: {', '.join(change.files_changed[:5])}")
            sections.append("")
        
        # Evidence summary
        sections.append("# Evidence Summary")
        for ev in report.evidence:
            sections.append(f"- {ev}")
        
        # Final instruction
        sections.append("\n---")
        sections.append("Analyze this information and provide your response in the specified format.")
        sections.append("IMPORTANT: Only reference files that actually exist in the project structure shown above.")
        
        return "\n".join(sections)
    
    def _get_project_file_listing(self, max_files: int = 50) -> str:
        """Get a listing of project files.
        
        Args:
            max_files: Maximum number of files to list
            
        Returns:
            File listing as a string
        """
        files = []
        extensions = {'.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go', '.rb', 
                      '.php', '.c', '.cpp', '.h', '.cs', '.swift', '.kt', '.rs',
                      '.vue', '.svelte', '.json', '.yml', '.yaml'}
        
        for f in self.repo_path.rglob('*'):
            if f.is_file():
                # Skip common non-source directories
                rel_path = str(f.relative_to(self.repo_path))
                if any(skip in rel_path for skip in ['node_modules/', '.git/', 
                        'vendor/', '__pycache__/', 'venv/', '.venv/', 'dist/', 'build/']):
                    continue
                
                # Check extension
                if f.suffix in extensions or f.name in ['package.json', 'Dockerfile', 
                        'Makefile', 'requirements.txt', 'Cargo.toml', 'go.mod']:
                    files.append(rel_path)
        
        files.sort()
        if len(files) > max_files:
            files = files[:max_files] + [f"... and {len(files) - max_files} more files"]
        
        return '\n'.join(files)
    
    def _get_key_source_files(self, max_lines: int = 200) -> list:
        """Get content of key source files.
        
        Args:
            max_lines: Maximum total lines to include
            
        Returns:
            List of (file_path, content) tuples
        """
        result = []
        total_lines = 0
        
        # Priority patterns for common entry points
        priority_patterns = [
            'index.js', 'index.ts', 'main.js', 'main.ts', 'main.py', 'app.py',
            'server.js', 'server.ts', 'src/index.js', 'src/index.ts',
            'src/App.js', 'src/App.jsx', 'src/App.tsx',
        ]
        
        # Find all source files
        all_files = []
        for f in self.repo_path.rglob('*'):
            if f.is_file() and f.suffix in {'.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go'}:
                rel_path = str(f.relative_to(self.repo_path))
                if not any(skip in rel_path for skip in ['node_modules/', '.git/', 
                        'vendor/', '__pycache__/', 'venv/', 'test', 'spec']):
                    all_files.append((rel_path, f))
        
        # Sort by priority
        def priority_key(item):
            rel_path, f = item
            for i, pattern in enumerate(priority_patterns):
                if rel_path.endswith(pattern) or pattern in rel_path:
                    return i
            return 100
        
        all_files.sort(key=priority_key)
        
        # Read top files
        for rel_path, file_path in all_files[:5]:  # Top 5 files
            if total_lines >= max_lines:
                break
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='replace')
                lines = content.split('\n')
                
                # Limit lines per file
                max_per_file = min(50, max_lines - total_lines)
                if len(lines) > max_per_file:
                    content = '\n'.join(lines[:max_per_file]) + '\n... (truncated)'
                    total_lines += max_per_file
                else:
                    total_lines += len(lines)
                
                result.append((rel_path, content))
            except Exception:
                continue
        
        return result
    
    def _read_file_content(
        self,
        suspect: SuspectedFile,
        context_lines: int = 20,
    ) -> Optional[str]:
        """Read relevant content from a suspected file.
        
        Args:
            suspect: Suspected file info
            context_lines: Lines of context around suspected lines
            
        Returns:
            File content with line context, or None
        """
        file_path = self.repo_path / suspect.path
        
        if not file_path.exists():
            return None
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            return None
        
        lines = content.split('\n')
        
        # If specific lines are suspected, extract just those with context
        if suspect.line_numbers:
            # Find range to extract
            min_line = max(1, min(suspect.line_numbers) - context_lines)
            max_line = min(len(lines), max(suspect.line_numbers) + context_lines)
            
            result_lines = []
            for i in range(min_line - 1, max_line):
                line_num = i + 1
                marker = ">>> " if line_num in suspect.line_numbers else "    "
                result_lines.append(f"{line_num:4d}{marker}{lines[i]}")
            
            return '\n'.join(result_lines)
        else:
            # Return first N lines
            max_lines = 100
            if len(lines) > max_lines:
                return '\n'.join([f"{i+1:4d}    {line}" for i, line in enumerate(lines[:max_lines])])
            return '\n'.join([f"{i+1:4d}    {line}" for i, line in enumerate(lines)])
    
    def build_retry_prompt(
        self,
        original_prompt: str,
        previous_response: str,
        error_message: str,
    ) -> str:
        """Build a retry prompt after a failed attempt.
        
        Args:
            original_prompt: The original analysis prompt
            previous_response: The LLM's previous response
            error_message: Why the previous attempt failed
            
        Returns:
            Updated prompt for retry
        """
        retry_section = f"""
# Previous Attempt Failed

Your previous response could not be used. Error: {error_message}

## Your Previous Response
{previous_response[:1000]}

## Instructions for Retry
Please provide a new response that addresses this issue. Make sure:
1. Your diff is valid unified diff format
2. File paths in the diff match the actual files
3. The patch can be applied with standard tools

---

{original_prompt}
"""
        return retry_section
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return self.SYSTEM_PROMPT
