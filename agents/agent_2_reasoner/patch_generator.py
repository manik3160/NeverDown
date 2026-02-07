"""Patch generator and validator for the Reasoner agent."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from models.patch import FileChange


@dataclass
class ParsedPatch:
    """Parsed patch information."""
    raw_diff: str
    files: List[FileChange]
    is_valid: bool
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class LLMResponse:
    """Parsed LLM response."""
    root_cause_summary: str = ""
    explanation: str = ""
    confidence: float = 0.0
    assumptions: List[str] = field(default_factory=list)
    diff: str = ""
    risks: str = ""
    parse_errors: List[str] = field(default_factory=list)


class PatchGenerator:
    """Generates and validates patches from LLM output."""
    
    # Pattern to extract diff from markdown code blocks
    DIFF_BLOCK = re.compile(r'```(?:diff)?\s*\n(.*?)```', re.DOTALL)
    
    # Unified diff patterns
    DIFF_HEADER = re.compile(r'^diff --git a/(.+) b/(.+)$', re.MULTILINE)
    FILE_HEADER = re.compile(r'^(?:---|\+\+\+) (?:a/|b/)?(.+)$', re.MULTILINE)
    HUNK_HEADER = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', re.MULTILINE)
    
    def __init__(self, repo_path: Optional[str] = None):
        """Initialize with optional repository path for validation.
        
        Args:
            repo_path: Path to repository for file existence checks
        """
        self.repo_path = Path(repo_path) if repo_path else None
    
    def parse_llm_response(self, response: str) -> LLMResponse:
        """Parse structured response from LLM.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Parsed response with extracted fields
        """
        result = LLMResponse()
        
        try:
            # Extract Root Cause
            root_cause_match = re.search(
                r'## Root Cause\s*\n(.+?)(?=\n##|\Z)',
                response,
                re.DOTALL
            )
            if root_cause_match:
                result.root_cause_summary = root_cause_match.group(1).strip()
            
            # Extract Explanation
            explanation_match = re.search(
                r'## Explanation\s*\n(.+?)(?=\n##|\Z)',
                response,
                re.DOTALL
            )
            if explanation_match:
                result.explanation = explanation_match.group(1).strip()
            
            # Extract Confidence
            confidence_match = re.search(
                r'## Confidence\s*\n\s*([0-9.]+)',
                response
            )
            if confidence_match:
                try:
                    result.confidence = float(confidence_match.group(1))
                    result.confidence = max(0.0, min(1.0, result.confidence))
                except ValueError:
                    result.parse_errors.append("Could not parse confidence value")
            
            # Extract Assumptions
            assumptions_match = re.search(
                r'## Assumptions\s*\n(.+?)(?=\n##|\Z)',
                response,
                re.DOTALL
            )
            if assumptions_match:
                assumptions_text = assumptions_match.group(1)
                for line in assumptions_text.split('\n'):
                    line = line.strip()
                    if line.startswith('- '):
                        result.assumptions.append(line[2:])
                    elif line and not line.startswith('#'):
                        result.assumptions.append(line)
            
            # Extract Fix/Diff
            fix_match = re.search(
                r'## Fix\s*\n(.+?)(?=\n##|\Z)',
                response,
                re.DOTALL
            )
            if fix_match:
                fix_content = fix_match.group(1)
                # Extract from code block
                diff_blocks = self.DIFF_BLOCK.findall(fix_content)
                if diff_blocks:
                    result.diff = diff_blocks[0].strip()
                else:
                    result.diff = fix_content.strip()
            
            # Extract Risks
            risks_match = re.search(
                r'## Risks\s*\n(.+?)(?=\n##|\Z)',
                response,
                re.DOTALL
            )
            if risks_match:
                result.risks = risks_match.group(1).strip()
        
        except Exception as e:
            result.parse_errors.append(f"Parse error: {str(e)}")
        
        return result
    
    def validate_diff(self, diff_content: str) -> ParsedPatch:
        """Validate a unified diff.
        
        Args:
            diff_content: Diff content to validate
            
        Returns:
            ParsedPatch with validation results
        """
        errors: List[str] = []
        files: List[FileChange] = []
        
        if not diff_content.strip():
            return ParsedPatch(
                raw_diff=diff_content,
                files=[],
                is_valid=False,
                validation_errors=["Empty diff content"],
            )
        
        # Check for basic diff structure
        has_hunks = bool(self.HUNK_HEADER.search(diff_content))
        has_file_headers = bool(self.FILE_HEADER.search(diff_content))
        
        if not has_hunks:
            errors.append("No hunk headers (@@ ... @@) found in diff")
        
        if not has_file_headers:
            errors.append("No file headers (--- / +++) found in diff")
        
        # Parse files from diff
        files = self._parse_files_from_diff(diff_content)
        
        if not files:
            errors.append("Could not identify any files in diff")
        
        # Validate file paths if repo path available
        if self.repo_path:
            for file_change in files:
                if file_change.action not in ('added', 'deleted'):
                    file_path = self.repo_path / file_change.path
                    if not file_path.exists():
                        errors.append(f"File not found: {file_change.path}")
        
        # Validate hunk syntax
        hunk_errors = self._validate_hunks(diff_content)
        errors.extend(hunk_errors)
        
        return ParsedPatch(
            raw_diff=diff_content,
            files=files,
            is_valid=len(errors) == 0,
            validation_errors=errors,
        )
    
    def _parse_files_from_diff(self, diff_content: str) -> List[FileChange]:
        """Parse file information from diff content."""
        files: List[FileChange] = []
        
        # Try to find git diff headers first
        git_headers = self.DIFF_HEADER.findall(diff_content)
        if git_headers:
            for old_path, new_path in git_headers:
                if old_path == '/dev/null':
                    action = 'added'
                    path = new_path
                elif new_path == '/dev/null':
                    action = 'deleted'
                    path = old_path
                else:
                    action = 'modified'
                    path = new_path
                
                # Count additions/deletions for this file
                additions, deletions = self._count_changes_for_file(diff_content, new_path)
                
                files.append(FileChange(
                    path=path,
                    action=action,
                    additions=additions,
                    deletions=deletions,
                ))
            return files
        
        # Fallback to simple file headers
        file_headers = self.FILE_HEADER.findall(diff_content)
        seen_paths = set()
        
        for path in file_headers:
            if path in seen_paths or path == '/dev/null':
                continue
            seen_paths.add(path)
            
            additions, deletions = self._count_changes_for_file(diff_content, path)
            
            files.append(FileChange(
                path=path,
                action='modified',
                additions=additions,
                deletions=deletions,
            ))
        
        return files
    
    def _count_changes_for_file(
        self,
        diff_content: str,
        file_path: str,
    ) -> Tuple[int, int]:
        """Count additions and deletions for a file in diff."""
        additions = 0
        deletions = 0
        
        # Simple counting - count + and - lines
        in_file_section = False
        
        for line in diff_content.split('\n'):
            # Check if we're entering this file's section
            if f'+++ b/{file_path}' in line or f'+++ {file_path}' in line:
                in_file_section = True
                continue
            
            # Check if we're leaving to another file
            if line.startswith('+++ ') and in_file_section:
                if file_path not in line:
                    in_file_section = False
                    continue
            
            if in_file_section or not self.DIFF_HEADER.search(diff_content):
                if line.startswith('+') and not line.startswith('+++'):
                    additions += 1
                elif line.startswith('-') and not line.startswith('---'):
                    deletions += 1
        
        return additions, deletions
    
    def _validate_hunks(self, diff_content: str) -> List[str]:
        """Validate hunk headers and content."""
        errors: List[str] = []
        
        lines = diff_content.split('\n')
        current_hunk = None
        additions_seen = 0
        deletions_seen = 0
        
        for i, line in enumerate(lines):
            hunk_match = self.HUNK_HEADER.match(line)
            
            if hunk_match:
                # Validate previous hunk if exists
                if current_hunk:
                    old_count = int(current_hunk.group(2) or 1)
                    new_count = int(current_hunk.group(4) or 1)
                    
                    # Rough validation - counts should be reasonable
                    if deletions_seen > old_count * 2:
                        errors.append(f"Hunk deletions ({deletions_seen}) exceeds expected ({old_count})")
                    if additions_seen > new_count * 2:
                        errors.append(f"Hunk additions ({additions_seen}) exceeds expected ({new_count})")
                
                current_hunk = hunk_match
                additions_seen = 0
                deletions_seen = 0
            elif current_hunk:
                if line.startswith('+') and not line.startswith('+++'):
                    additions_seen += 1
                elif line.startswith('-') and not line.startswith('---'):
                    deletions_seen += 1
        
        return errors
    
    def normalize_diff(self, diff_content: str) -> str:
        """Normalize diff format for consistency.
        
        Args:
            diff_content: Raw diff content
            
        Returns:
            Normalized diff content
        """
        lines = diff_content.split('\n')
        normalized = []
        
        for line in lines:
            # Ensure proper line endings
            line = line.rstrip()
            
            # Skip empty lines at start
            if not normalized and not line:
                continue
            
            normalized.append(line)
        
        # Remove trailing empty lines
        while normalized and not normalized[-1]:
            normalized.pop()
        
        return '\n'.join(normalized) + '\n'
