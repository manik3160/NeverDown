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
        
        # Verify that verification passed
        if input_data.verification.status != VerificationStatus.PASSED:
            if input_data.verification.status == VerificationStatus.NO_TESTS:
                self.logger.warning("Creating PR without test verification")
            else:
                return AgentResult.fail(
                    f"Cannot create PR: verification status is {input_data.verification.status.value}",
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
            
            # Log the PR creation
            audit_logger.log_security_event(
                event_name="pr_created",
                severity="info",
                details={
                    "incident_id": str(incident_id),
                    "pr_number": pr.number,
                    "pr_url": pr.url,
                    "auto_merge": False,  # Always false
                },
            )
            
            return AgentResult.ok(
                pr,
                metadata={
                    "pr_number": pr.number,
                    "pr_url": pr.url,
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
        # Parse files from patch
        for file_change in patch.files_changed:
            if file_change.action == 'deleted':
                continue  # Handle deletions separately
            
            file_path = Path(original_repo_path) / file_change.path
            
            if not file_path.exists():
                logger.warning("File not found, skipping", path=file_change.path)
                continue
            
            # Read file content and apply patch locally
            try:
                # Apply patch using git apply
                result = subprocess.run(
                    ["git", "apply", "--check"],
                    input=patch.diff.encode(),
                    cwd=original_repo_path,
                    capture_output=True,
                    timeout=30,
                )
                
                if result.returncode == 0:
                    subprocess.run(
                        ["git", "apply"],
                        input=patch.diff.encode(),
                        cwd=original_repo_path,
                        capture_output=True,
                        timeout=30,
                    )
                
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
                
            except Exception as e:
                logger.warning(
                    "Failed to push file",
                    path=file_change.path,
                    error=str(e),
                )
    
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
