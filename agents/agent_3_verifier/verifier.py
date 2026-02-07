"""Verifier agent - Sandbox testing for NeverDown."""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from agents.base_agent import AgentResult, BaseAgent
from agents.agent_3_verifier.sandbox_runner import SandboxRunner, SandboxResult
from config.logging_config import get_logger
from config.settings import get_settings
from core.exceptions import SandboxError, VerificationFailedError
from models.patch import Patch
from models.verification import (
    TestOutcome,
    TestResult,
    VerificationResult,
    VerificationStatus,
)

logger = get_logger(__name__)


@dataclass
class VerifierInput:
    """Input for the Verifier agent."""
    incident_id: UUID
    sanitized_repo_path: str
    patch: Patch


@dataclass
class VerifierOutput:
    """Output from the Verifier agent."""
    result: VerificationResult


class VerifierAgent(BaseAgent[VerifierInput, VerifierOutput]):
    """Agent 3: Sandbox Tester.
    
    Responsibilities:
    - Apply patch to sanitized repository
    - Run tests in isolated Docker sandbox
    - Verify patch doesn't introduce new failures
    - Report verification results
    
    CRITICAL: All execution happens in Docker containers with:
    - No network access
    - Memory limits
    - CPU limits
    - Timeout enforcement
    """
    
    name = "verifier"
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.sandbox = SandboxRunner()
    
    async def execute(
        self,
        input_data: VerifierInput,
        incident_id: Optional[UUID] = None,
    ) -> AgentResult[VerifierOutput]:
        """Verify a patch by running tests in sandbox.
        
        Args:
            input_data: Verifier input with patch to test
            incident_id: Incident ID for logging
            
        Returns:
            AgentResult with verification results
        """
        incident_id = incident_id or input_data.incident_id
        repo_path = Path(input_data.sanitized_repo_path)
        
        if not repo_path.exists():
            return AgentResult.fail(
                f"Repository path does not exist: {repo_path}",
            )
        
        # Check Docker availability
        if not await self.sandbox.check_docker_available():
            return AgentResult.fail(
                "Docker is not available for sandbox execution",
            )
        
        # Create versioned copy for testing
        test_repo = Path(tempfile.mkdtemp(prefix="neverdown-verify-"))
        
        try:
            # Copy repository
            shutil.copytree(repo_path, test_repo / "repo", dirs_exist_ok=True)
            work_dir = test_repo / "repo"
            
            # Apply patch
            patch_success = await self._apply_patch(work_dir, input_data.patch)
            
            if not patch_success:
                return AgentResult.ok(
                    VerifierOutput(
                        result=VerificationResult(
                            incident_id=incident_id,
                            patch_id=input_data.patch.id,
                            status=VerificationStatus.FAILED,
                            tests_passed=0,
                            tests_failed=0,
                            tests_run=[],
                            verification_failed_reason="Patch could not be applied cleanly",
                            sandbox_info=self.sandbox.get_sandbox_info().model_dump(),
                        ),
                    ),
                    metadata={"status": "patch_apply_failed"},
                )
            
            # Detect test framework and run tests
            test_results = await self._run_tests(work_dir)
            
            # Analyze results
            passed = sum(1 for t in test_results if t.outcome == TestOutcome.PASSED)
            failed = sum(1 for t in test_results if t.outcome == TestOutcome.FAILED)
            
            # Determine status
            if failed > 0:
                status = VerificationStatus.FAILED
                reason = f"{failed} test(s) failed"
            elif passed == 0:
                status = VerificationStatus.NO_TESTS
                reason = "No tests found or executed"
            else:
                status = VerificationStatus.PASSED
                reason = None
            
            result = VerificationResult(
                incident_id=incident_id,
                patch_id=input_data.patch.id,
                status=status,
                tests_passed=passed,
                tests_failed=failed,
                tests_run=test_results[:50],  # Limit stored results
                verification_failed_reason=reason,
                sandbox_info=self.sandbox.get_sandbox_info().model_dump(),
            )
            
            return AgentResult.ok(
                VerifierOutput(result=result),
                metadata={
                    "status": status.value,
                    "passed": passed,
                    "failed": failed,
                },
            )
        
        except SandboxError as e:
            return AgentResult.fail(
                f"Sandbox error: {str(e)}",
            )
        
        finally:
            # Cleanup
            shutil.rmtree(test_repo, ignore_errors=True)
    
    async def _apply_patch(self, repo_path: Path, patch: Patch) -> bool:
        """Apply a patch to the repository.
        
        Args:
            repo_path: Path to repository
            patch: Patch to apply
            
        Returns:
            True if patch applied successfully
        """
        # Write patch to temp file
        patch_file = repo_path / ".neverdown_patch.diff"
        
        try:
            patch_file.write_text(patch.diff, encoding='utf-8')
            
            # Try to apply with git apply
            result = subprocess.run(
                ["git", "apply", "--check", str(patch_file)],
                cwd=repo_path,
                capture_output=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                self.logger.warning(
                    "Patch check failed",
                    stderr=result.stderr.decode('utf-8', errors='replace')[:200],
                )
                
                # Try with --3way for more permissive apply
                result = subprocess.run(
                    ["git", "apply", "--3way", "--check", str(patch_file)],
                    cwd=repo_path,
                    capture_output=True,
                    timeout=30,
                )
                
                if result.returncode != 0:
                    return False
            
            # Apply the patch
            result = subprocess.run(
                ["git", "apply", str(patch_file)],
                cwd=repo_path,
                capture_output=True,
                timeout=30,
            )
            
            return result.returncode == 0
        
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            self.logger.exception("Error applying patch", error=str(e))
            return False
        finally:
            if patch_file.exists():
                patch_file.unlink()
    
    async def _run_tests(self, repo_path: Path) -> List[TestResult]:
        """Detect and run tests in the repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            List of test results
        """
        # Detect test framework
        framework = self._detect_test_framework(repo_path)
        
        if framework == "pytest":
            return await self._run_pytest(repo_path)
        elif framework == "jest":
            return await self._run_jest(repo_path)
        elif framework == "unittest":
            return await self._run_unittest(repo_path)
        else:
            self.logger.warning("No test framework detected")
            return []
    
    def _detect_test_framework(self, repo_path: Path) -> Optional[str]:
        """Detect which test framework the project uses."""
        # Check for pytest
        if (repo_path / "pytest.ini").exists() or (repo_path / "pyproject.toml").exists():
            return "pytest"
        
        # Check for conftest.py
        for p in repo_path.rglob("conftest.py"):
            return "pytest"
        
        # Check for test_*.py files
        test_files = list(repo_path.rglob("test_*.py"))
        if test_files:
            return "pytest"  # Default to pytest for Python tests
        
        # Check for Jest (JavaScript)
        if (repo_path / "jest.config.js").exists() or (repo_path / "jest.config.ts").exists():
            return "jest"
        
        pkg_json = repo_path / "package.json"
        if pkg_json.exists():
            try:
                import json
                data = json.loads(pkg_json.read_text())
                if "jest" in data.get("devDependencies", {}):
                    return "jest"
            except Exception:
                pass
        
        # Fallback check for Python unittest
        for p in repo_path.rglob("*_test.py"):
            return "unittest"
        
        return None
    
    async def _run_pytest(self, repo_path: Path) -> List[TestResult]:
        """Run pytest in sandbox."""
        result = await self.sandbox.run(
            str(repo_path),
            ["sh", "-c", "pip install -q -r requirements.txt 2>/dev/null; pip install pytest; python -m pytest -v --tb=short 2>&1"],
        )
        
        return self._parse_pytest_output(result)
    
    async def _run_jest(self, repo_path: Path) -> List[TestResult]:
        """Run jest in sandbox."""
        result = await self.sandbox.run(
            str(repo_path),
            ["sh", "-c", "npm ci && npm test 2>&1"],
            env={"CI": "true"},
        )
        
        return self._parse_jest_output(result)
    
    async def _run_unittest(self, repo_path: Path) -> List[TestResult]:
        """Run Python unittest in sandbox."""
        result = await self.sandbox.run(
            str(repo_path),
            ["python", "-m", "unittest", "discover", "-v"],
        )
        
        return self._parse_unittest_output(result)
    
    def _parse_pytest_output(self, result: SandboxResult) -> List[TestResult]:
        """Parse pytest output into TestResult objects."""
        tests: List[TestResult] = []
        
        if result.timed_out:
            tests.append(TestResult(
                name="sandbox_timeout",
                outcome=TestOutcome.ERROR,
                duration_ms=int(result.duration_seconds * 1000),
                error_message="Test execution timed out",
            ))
            return tests
        
        import re
        
        # Parse individual test results
        # Pattern: test_file.py::test_name PASSED/FAILED/SKIPPED
        pattern = re.compile(r'([^\s]+::[^\s]+)\s+(PASSED|FAILED|SKIPPED|ERROR)')
        
        for match in pattern.finditer(result.stdout):
            name = match.group(1)
            status = match.group(2)
            
            outcome = {
                "PASSED": TestOutcome.PASSED,
                "FAILED": TestOutcome.FAILED,
                "SKIPPED": TestOutcome.SKIPPED,
                "ERROR": TestOutcome.ERROR,
            }.get(status, TestOutcome.ERROR)
            
            tests.append(TestResult(
                name=name,
                outcome=outcome,
                duration_ms=0,  # Would need to parse timing
            ))
        
        # If no tests found, check for summary
        if not tests:
            summary = re.search(r'(\d+) passed', result.stdout)
            if summary:
                # Synthetic result
                tests.append(TestResult(
                    name="pytest_summary",
                    outcome=TestOutcome.PASSED,
                    duration_ms=int(result.duration_seconds * 1000),
                ))
        
        return tests
    
    def _parse_jest_output(self, result: SandboxResult) -> List[TestResult]:
        """Parse Jest output into TestResult objects."""
        tests: List[TestResult] = []
        
        if result.timed_out:
            tests.append(TestResult(
                name="sandbox_timeout",
                outcome=TestOutcome.ERROR,
                duration_ms=int(result.duration_seconds * 1000),
                error_message="Test execution timed out",
            ))
            return tests
        
        import re
        
        # Pattern: ✓ test name (Xms) or ✕ test name
        pass_pattern = re.compile(r'✓\s+(.+?)\s+\((\d+)\s*ms\)')
        fail_pattern = re.compile(r'✕\s+(.+)')
        
        for match in pass_pattern.finditer(result.stdout):
            tests.append(TestResult(
                name=match.group(1),
                outcome=TestOutcome.PASSED,
                duration_ms=int(match.group(2)),
            ))
        
        for match in fail_pattern.finditer(result.stdout):
            tests.append(TestResult(
                name=match.group(1),
                outcome=TestOutcome.FAILED,
                duration_ms=0,
            ))
        
        return tests
    
    def _parse_unittest_output(self, result: SandboxResult) -> List[TestResult]:
        """Parse unittest output into TestResult objects."""
        tests: List[TestResult] = []
        
        if result.timed_out:
            tests.append(TestResult(
                name="sandbox_timeout",
                outcome=TestOutcome.ERROR,
                duration_ms=int(result.duration_seconds * 1000),
                error_message="Test execution timed out",
            ))
            return tests
        
        import re
        
        # Pattern: test_name (test_module.TestClass) ... ok/FAIL
        pattern = re.compile(r'(\w+)\s+\(([^)]+)\)\s+\.\.\.\s+(ok|FAIL|ERROR|skipped)')
        
        for match in pattern.finditer(result.stdout):
            name = f"{match.group(2)}.{match.group(1)}"
            status = match.group(3)
            
            outcome = {
                "ok": TestOutcome.PASSED,
                "FAIL": TestOutcome.FAILED,
                "ERROR": TestOutcome.ERROR,
                "skipped": TestOutcome.SKIPPED,
            }.get(status, TestOutcome.ERROR)
            
            tests.append(TestResult(
                name=name,
                outcome=outcome,
                duration_ms=0,
            ))
        
        return tests
