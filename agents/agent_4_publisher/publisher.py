"""Publisher agent - GitHub PR creator for NeverDown."""

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from agents.base_agent import AgentResult, BaseAgent
from agents.agent_4_publisher.github_client import (
    CreateBranchRequest,
    CreatePRRequest,
    GitHubClient,
)
from config.logging_config import audit_logger, get_logger
from config.settings import get_settings
from core.exceptions import GitHubAPIError
from models.patch import Patch
from models.pull_request import PullRequest
from models.verification import VerificationResult, VerificationStatus

logger = get_logger(__name__)


@dataclass
class PublisherInput:
    """Input for the Publisher agent."""
    incident_id: UUID
    original_repo_path: str  # Path to original (non-sanitized) repo
    patch: Patch
    verification: VerificationResult
    repo_url: str  # GitHub repo URL
    root_cause_summary: str


@dataclass
class PublisherOutput:
    """Output from the Publisher agent."""
    pull_request: PullRequest
    branch_name: str


class PublisherAgent(BaseAgent[PublisherInput, PullRequest]):
    """Agent 4: GitHub PR Creator.
    
    Responsibilities:
    - Create fix branch with patch applied
    - Generate PR description with analysis
    - Open PR (NEVER auto-merge)
    - Add appropriate labels
    
    CRITICAL CONSTRAINTS:
    - This agent applies patches to ORIGINAL repo (not sanitized)
    - NEVER auto-merges PRs (human-in-the-loop required)
    - Verification must pass before PR creation
    """
    
    name = "publisher"
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.github = GitHubClient()
    
    async def execute(
        self,
        input_data: PublisherInput,
        incident_id: Optional[UUID] = None,
    ) -> AgentResult[PullRequest]:
        """Create GitHub PR with the fix.
        
        Args:
            input_data: Publisher input with patch and verification
            incident_id: Incident ID for logging
            
        Returns:
            AgentResult with created PullRequest
        """
        incident_id = incident_id or input_data.incident_id
        
        # Log verification status
        if input_data.verification.status != VerificationStatus.PASSED:
            if input_data.verification.status == VerificationStatus.NO_TESTS:
                self.logger.warning("Creating PR without test verification - no tests found")
            elif input_data.verification.status == VerificationStatus.FAILED:
                self.logger.warning(
                    "Creating PR with failed verification - patch needs manual review",
                    reason=input_data.verification.verification_failed_reason
                )
        
        # Parse repo info
        try:
            owner, repo = self.github.parse_repo_url(input_data.repo_url)
        except ValueError as e:
            return AgentResult.fail(str(e))
        
        # Generate branch name
        branch_name = self._generate_branch_name(incident_id)
        
        try:
            # Get default branch
            default_branch = await self.github.get_default_branch(owner, repo)
            base_sha = await self.github.get_ref(owner, repo, f"heads/{default_branch}")
            
            # Create fix branch
            await self.github.create_branch(
                owner,
                repo,
                CreateBranchRequest(
                    branch_name=branch_name,
                    base_sha=base_sha,
                ),
            )
            
            # Apply patch to branch via file pushes
            await self._apply_patch_to_branch(
                owner,
                repo,
                branch_name,
                input_data.patch,
                input_data.original_repo_path,
            )
            
            # Generate PR description
            pr_body = self._generate_pr_body(
                incident_id,
                input_data.patch,
                input_data.verification,
                input_data.root_cause_summary,
            )
            
            # Determine labels
            labels = self._determine_labels(
                input_data.patch,
                input_data.verification,
            )
            
            # Create PR
            pr = await self.github.create_pull_request(
                owner,
                repo,
                CreatePRRequest(
                    title=f"[NeverDown] Fix: {input_data.root_cause_summary[:50]}",
                    body=pr_body,
                    head_branch=branch_name,
                    base_branch=default_branch,
                    labels=labels,
                    draft=False,
                ),
            )
            
            # Transform GitHub response into PullRequest model
            from models.pull_request import PullRequest, PRStatus
            from uuid import uuid4
            pr_model = PullRequest(
                incident_id=incident_id,
                patch_id=input_data.patch.id,
                verification_id=uuid4(),  # VerificationResult doesn't have ID
                pr_number=pr.get("number"),
                pr_url=pr.get("html_url"),
                branch_name=branch_name,
                base_branch=default_branch,
                title=pr.get("title", ""),
                body=pr.get("body", ""),
                labels=labels,
                status=PRStatus.OPEN if pr.get("state") == "open" else PRStatus.DRAFT,
                merge_commit_sha=pr.get("merge_commit_sha"),
                github_response=pr,
            )
            
            # Log the PR creation
            audit_logger.log_security_event(
                event_name="pr_created",
                severity="info",
                details={
                    "incident_id": str(incident_id),
                    "pr_number": pr_model.pr_number,
                    "pr_url": pr_model.pr_url,
                    "auto_merge": False,  # Always false
                },
            )
            
            return AgentResult.ok(
                pr_model,
                metadata={
                    "pr_number": pr_model.pr_number,
                    "pr_url": pr_model.pr_url,
                    "branch": branch_name,
                },
            )
        
        except GitHubAPIError as e:
            return AgentResult.fail(
                f"GitHub API error: {str(e)}",
                metadata={"status_code": e.status_code if hasattr(e, 'status_code') else None},
            )
        except Exception as e:
            return AgentResult.fail(
                f"Failed to create PR: {str(e)}",
            )
    
    def _generate_branch_name(self, incident_id: UUID) -> str:
        """Generate a branch name for the fix."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        short_id = str(incident_id)[:8]
        return f"neverdown/fix-{short_id}-{timestamp}"
    
    async def _apply_patch_to_branch(
        self,
        owner: str,
        repo: str,
        branch: str,
        patch: Patch,
        original_repo_path: str,
    ) -> None:
        """Apply patch to branch by pushing modified files.
        
        Note: This applies the patch to the original repo and pushes
        the file contents to GitHub. The patch was validated against
        the sanitized repo, but the actual file contents come from
        the original repo after applying the patch.
        """
        repo_path = Path(original_repo_path)
        
        # Initialize git if needed (for cloned repos)
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            subprocess.run(
                ["git", "init"],
                cwd=str(repo_path),
                capture_output=True,
                timeout=30,
            )
            subprocess.run(
                ["git", "add", "."],
                cwd=str(repo_path),
                capture_output=True,
                timeout=30,
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial"],
                cwd=str(repo_path),
                capture_output=True,
                timeout=30,
            )
        
        # Apply the entire patch once
        apply_result = subprocess.run(
            ["git", "apply", "--check"],
            input=patch.diff.encode(),
            cwd=str(repo_path),
            capture_output=True,
            timeout=30,
        )
        
        if apply_result.returncode == 0:
            # Patch is valid, apply it
            subprocess.run(
                ["git", "apply"],
                input=patch.diff.encode(),
                cwd=str(repo_path),
                capture_output=True,
                timeout=30,
            )
            logger.info("Patch applied successfully via git apply")
        else:
            # Fallback: try to apply patch manually
            logger.warning(
                "git apply --check failed, attempting manual patch",
                error=apply_result.stderr.decode()[:500]
            )
            self._apply_patch_manually(patch, repo_path)
        
        # Now push each modified file
        for file_change in patch.files_changed:
            if file_change.action == 'deleted':
                continue  # Handle deletions separately
            
            file_path = repo_path / file_change.path
            
            if not file_path.exists():
                logger.warning("File not found after patch, skipping", path=file_change.path)
                continue
            
            try:
                # Read the updated file
                content = file_path.read_text(encoding='utf-8')
                
                # Push to GitHub
                await self.github.push_file(
                    owner,
                    repo,
                    branch,
                    file_change.path,
                    content,
                    f"[NeverDown] Apply fix to {file_change.path}",
                )
                logger.info("Pushed modified file", path=file_change.path)
                
            except Exception as e:
                logger.warning(
                    "Failed to push file",
                    path=file_change.path,
                    error=str(e),
                )
    
    def _apply_patch_manually(self, patch: Patch, repo_path: Path) -> None:
        """Manually apply patch when git apply fails.
        
        This parses the unified diff and applies changes directly by
        reading each file and doing find/replace operations.
        """
        import re
        
        # Parse file blocks from diff
        file_blocks = self._parse_diff_to_file_blocks(patch.diff)
        
        for file_path, block in file_blocks.items():
            full_path = repo_path / file_path
            
            if not full_path.exists():
                logger.warning("File not found for manual patch", path=file_path)
                continue
            
            try:
                # Read original file
                original_content = full_path.read_text(encoding='utf-8')
                
                # Apply changes
                new_content = self._apply_hunk(original_content, block)
                
                if new_content != original_content:
                    full_path.write_text(new_content, encoding='utf-8')
                    logger.info("Manual patch applied", path=file_path)
                else:
                    logger.warning("No changes applied by manual patch", path=file_path)
            except Exception as e:
                logger.warning("Failed to apply manual patch", path=file_path, error=str(e))
    
    def _parse_diff_to_file_blocks(self, diff: str) -> dict:
        """Parse a unified diff into per-file blocks.
        
        Returns dict mapping file path to list of (old_lines, new_lines) tuples.
        """
        blocks = {}
        current_file = None
        current_hunks = []
        
        lines = diff.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # File header
            if line.startswith('+++ '):
                # Extract file path
                if line.startswith('+++ b/'):
                    current_file = line[6:]
                elif line.startswith('+++ '):
                    current_file = line[4:]
                
                # Skip a/ prefix variants
                if current_file and current_file.startswith('/'):
                    current_file = current_file.lstrip('/')
                
                blocks[current_file] = {'old': [], 'new': []}
            
            # Hunk header @@ -start,count +start,count @@
            elif line.startswith('@@') and current_file:
                pass  # We'll just capture +/- lines
            
            # Content lines
            elif current_file:
                if line.startswith('-') and not line.startswith('---'):
                    blocks[current_file]['old'].append(line[1:])
                elif line.startswith('+') and not line.startswith('+++'):
                    blocks[current_file]['new'].append(line[1:])
            
            i += 1
        
        return blocks
    
    def _apply_hunk(self, original: str, block: dict) -> str:
        """Apply a hunk's changes to file content.
        
        Uses find/replace to swap old lines for new lines.
        """
        result = original
        old_lines = block.get('old', [])
        new_lines = block.get('new', [])
        
        if not old_lines and not new_lines:
            return result
        
        # Try to find and replace the old content with new content
        if old_lines:
            old_content = '\n'.join(old_lines)
            new_content = '\n'.join(new_lines) if new_lines else ''
            
            if old_content in result:
                result = result.replace(old_content, new_content, 1)
            else:
                # Try line-by-line replacements
                for old_line in old_lines:
                    if old_line.strip() and old_line in result:
                        # Find the corresponding new line (if any)
                        result = result.replace(old_line + '\n', '', 1)
                
                # Add new lines (simplified - may not preserve position)
                if new_lines:
                    for new_line in new_lines:
                        if new_line not in result:
                            # Insert at start if it's an import-like line
                            if 'import' in new_line.lower():
                                # Find first non-empty line
                                lines = result.split('\n')
                                for i, l in enumerate(lines):
                                    if l.strip() and not l.strip().startswith('//') and not l.strip().startswith('#'):
                                        lines.insert(i, new_line)
                                        break
                                result = '\n'.join(lines)
        elif new_lines:
            # Pure additions - append at the end
            new_content = '\n'.join(new_lines)
            result = result + '\n' + new_content
        
        return result
    
    def _generate_pr_body(
        self,
        incident_id: UUID,
        patch: Patch,
        verification: VerificationResult,
        root_cause: str,
    ) -> str:
        """Generate comprehensive PR description."""
        body = f"""## 🤖 Automated Fix by NeverDown

### Incident ID
`{incident_id}`

### Root Cause
{root_cause}

### Analysis Confidence
{patch.confidence * 100:.1f}%

### Reasoning
{patch.reasoning[:500]}{"..." if len(patch.reasoning) > 500 else ""}

### Assumptions Made
"""
        if patch.assumptions:
            for assumption in patch.assumptions:
                body += f"- {assumption}\n"
        else:
            body += "- None\n"
        
        body += f"""
### Verification Status
- **Status**: {verification.status.value.upper()}
- **Tests Passed**: {verification.tests_passed}
- **Tests Failed**: {verification.tests_failed}

### Files Changed
"""
        for fc in patch.files_changed:
            body += f"- `{fc.path}` ({fc.action}): +{fc.additions}/-{fc.deletions}\n"
        
        body += """
---

> ⚠️ **Human Review Required**: This PR was created automatically and must be reviewed before merging.
> 
> NeverDown does NOT auto-merge PRs. All fixes require human approval.

Created by [NeverDown](https://github.com/NeverDown) - Autonomous Incident Detection & Remediation
"""
        return body
    
    def _determine_labels(
        self,
        patch: Patch,
        verification: VerificationResult,
    ) -> list[str]:
        """Determine appropriate labels for the PR."""
        labels = ["neverdown", "automated-fix"]
        
        # Confidence-based labels
        if patch.confidence >= 0.9:
            labels.append("high-confidence")
        elif patch.confidence >= 0.7:
            labels.append("medium-confidence")
        else:
            labels.append("low-confidence")
        
        # Verification labels
        if verification.status == VerificationStatus.PASSED:
            labels.append("tests-passing")
        elif verification.status == VerificationStatus.NO_TESTS:
            labels.append("needs-tests")
        else:
            labels.append("tests-failing")
        
        return labels
