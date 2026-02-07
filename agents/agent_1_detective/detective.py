"""Detective agent - Failure analyzer for NeverDown."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from agents.base_agent import AgentResult, BaseAgent
from agents.agent_1_detective.diff_analyzer import DiffAnalyzer
from agents.agent_1_detective.log_parser import LogParser
from config.logging_config import get_logger
from models.analysis import (
    DetectiveReport,
    ErrorInfo,
    FailureCategory,
    RecentChange,
    SuspectedFile,
    SuspectedFunction,
)

logger = get_logger(__name__)


@dataclass
class DetectiveInput:
    """Input for the Detective agent."""
    incident_id: UUID
    sanitized_repo_path: str
    logs: Optional[str] = None
    stack_trace: Optional[str] = None
    ci_output: Optional[str] = None


@dataclass
class DetectiveOutput:
    """Output from the Detective agent."""
    report: DetectiveReport


class DetectiveAgent(BaseAgent[DetectiveInput, DetectiveOutput]):
    """Agent 1: Failure Analyzer.
    
    Responsibilities:
    - Parse logs and stack traces to extract error information
    - Analyze git history to find recent relevant changes
    - Localize failures to specific files and functions
    - Rank suspects by confidence
    - Use deterministic tools before any LLM calls
    """
    
    name = "detective"
    
    def __init__(self):
        super().__init__()
        self.log_parser = LogParser()
    
    async def execute(
        self,
        input_data: DetectiveInput,
        incident_id: Optional[UUID] = None,
    ) -> AgentResult[DetectiveOutput]:
        """Analyze failure and produce localization report.
        
        Args:
            input_data: Detective input with repo path and logs
            incident_id: Incident ID for logging
            
        Returns:
            AgentResult with detective report
        """
        incident_id = incident_id or input_data.incident_id
        repo_path = Path(input_data.sanitized_repo_path)
        
        if not repo_path.exists():
            return AgentResult.fail(
                f"Repository path does not exist: {repo_path}",
            )
        
        # Parse errors from all available sources
        errors: List[ErrorInfo] = []
        
        if input_data.logs:
            errors.extend(self.log_parser.parse(input_data.logs))
        
        if input_data.stack_trace:
            errors.extend(self.log_parser.parse(input_data.stack_trace))
        
        if input_data.ci_output:
            errors.extend(self.log_parser.parse(input_data.ci_output))
        
        if not errors:
            self.logger.warning("No errors found in provided logs")
            return AgentResult.ok(
                DetectiveOutput(
                    report=DetectiveReport(
                        incident_id=incident_id,
                        errors=[],
                        failure_category=FailureCategory.UNKNOWN,
                        suspected_files=[],
                        evidence=["No errors found in logs"],
                        overall_confidence=0.0,
                    ),
                ),
                metadata={"error_count": 0},
            )
        
        # Determine failure category
        primary_error = errors[0]
        failure_category = self._determine_failure_category(primary_error)
        
        # Analyze git history
        diff_analyzer = DiffAnalyzer(str(repo_path))
        recent_commits = diff_analyzer.get_recent_commits(count=10)
        
        # Build list of suspected files
        suspected_files: List[SuspectedFile] = []
        suspected_functions: List[SuspectedFunction] = []
        
        for error in errors:
            if error.file_path:
                # Find or update suspected file entry
                existing = next(
                    (f for f in suspected_files if f.path == error.file_path),
                    None,
                )
                
                if existing:
                    # Increase confidence for multiple errors in same file
                    existing.confidence = min(1.0, existing.confidence + 0.2)
                    if error.line_number and error.line_number not in existing.line_numbers:
                        existing.line_numbers.append(error.line_number)
                    existing.evidence.append(f"{error.error_type}: {error.message}")
                else:
                    # Calculate confidence based on error type
                    confidence = self._calculate_file_confidence(error)
                    
                    suspected_files.append(SuspectedFile(
                        path=error.file_path,
                        confidence=confidence,
                        line_numbers=[error.line_number] if error.line_number else [],
                        evidence=[f"{error.error_type}: {error.message}"],
                    ))
                
                # Try to extract function name from stack trace
                if error.stack_trace:
                    func_info = self._extract_function_from_trace(error)
                    if func_info:
                        suspected_functions.append(func_info)
        
        # Enhance with git history analysis
        relevant_changes: List[RecentChange] = []
        for sf in suspected_files:
            changes = diff_analyzer.find_relevant_changes(
                sf.path,
                sf.line_numbers[0] if sf.line_numbers else None,
                recent_commits,
            )
            
            # Boost confidence if file was recently changed
            if changes:
                sf.confidence = min(1.0, sf.confidence + 0.2)
                sf.evidence.append(
                    f"Recently changed in commit: {changes[0].message[:50]}"
                )
            
            relevant_changes.extend(changes)
        
        # Deduplicate and sort changes
        seen_shas = set()
        unique_changes = []
        for change in relevant_changes:
            if change.commit_sha not in seen_shas:
                seen_shas.add(change.commit_sha)
                unique_changes.append(change)
        unique_changes.sort(key=lambda c: c.relevance_score, reverse=True)
        
        # Sort suspected files by confidence
        suspected_files.sort(key=lambda f: f.confidence, reverse=True)
        
        # Calculate overall confidence
        overall_confidence = suspected_files[0].confidence if suspected_files else 0.0
        
        # Build evidence list
        evidence = [
            f"Found {len(errors)} error(s) in logs",
            f"Primary error: {primary_error.error_type}: {primary_error.message}",
        ]
        if suspected_files:
            evidence.append(f"Top suspect: {suspected_files[0].path} (confidence: {suspected_files[0].confidence:.2f})")
        if unique_changes:
            evidence.append(f"Found {len(unique_changes)} potentially relevant recent commit(s)")
        
        report = DetectiveReport(
            incident_id=incident_id,
            errors=errors,
            failure_category=FailureCategory(failure_category),
            suspected_files=suspected_files[:10],  # Top 10
            suspected_functions=suspected_functions[:10],
            recent_changes=unique_changes[:5],
            evidence=evidence,
            overall_confidence=overall_confidence,
        )
        
        return AgentResult.ok(
            DetectiveOutput(report=report),
            metadata={
                "error_count": len(errors),
                "suspected_file_count": len(suspected_files),
                "failure_category": failure_category,
                "overall_confidence": overall_confidence,
            },
        )
    
    def _determine_failure_category(self, error: ErrorInfo) -> str:
        """Determine the failure category from the primary error."""
        return self.log_parser.categorize_error(error)
    
    def _calculate_file_confidence(self, error: ErrorInfo) -> float:
        """Calculate confidence that a file contains the bug.
        
        Higher confidence for:
        - Specific line numbers
        - User code (not libraries)
        - Certain error types
        """
        confidence = 0.5  # Base confidence
        
        # Boost for line number
        if error.line_number:
            confidence += 0.2
        
        # Boost/reduce based on error type
        definite_bugs = ['nameerror', 'typeerror', 'syntaxerror', 'attributeerror']
        if error.error_type.lower() in definite_bugs:
            confidence += 0.2
        
        # Reduce for library code
        if error.file_path:
            if any(lib in error.file_path.lower() for lib in [
                'site-packages', 'node_modules', '/usr/lib', 'venv/'
            ]):
                confidence -= 0.3
        
        return max(0.1, min(1.0, confidence))
    
    def _extract_function_from_trace(self, error: ErrorInfo) -> Optional[SuspectedFunction]:
        """Try to extract function information from stack trace."""
        if not error.stack_trace or not error.file_path:
            return None
        
        import re
        
        # Python function pattern
        py_pattern = re.compile(r'File "([^"]+)", line (\d+), in (\w+)')
        matches = list(py_pattern.finditer(error.stack_trace))
        
        if matches:
            # Get the last frame (most specific)
            match = matches[-1]
            return SuspectedFunction(
                name=match.group(3),
                file_path=match.group(1),
                start_line=int(match.group(2)),
                confidence=0.8,
            )
        
        # JavaScript function pattern
        js_pattern = re.compile(r'at (\w+) \(([^:]+):(\d+)')
        matches = list(js_pattern.finditer(error.stack_trace))
        
        if matches:
            match = matches[-1]
            return SuspectedFunction(
                name=match.group(1),
                file_path=match.group(2),
                start_line=int(match.group(3)),
                confidence=0.8,
            )
        
        return None
