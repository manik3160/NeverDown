"""Git diff analyzer for the Detective agent."""

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.logging_config import get_logger
from models.analysis import RecentChange

logger = get_logger(__name__)


@dataclass
class DiffHunk:
    """A single hunk from a git diff."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    content: str
    additions: List[str] = field(default_factory=list)
    deletions: List[str] = field(default_factory=list)


@dataclass
class FileDiff:
    """Diff for a single file."""
    file_path: str
    old_path: Optional[str]  # For renames
    status: str  # 'modified', 'added', 'deleted', 'renamed'
    hunks: List[DiffHunk] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    binary: bool = False


@dataclass
class CommitInfo:
    """Information about a git commit."""
    sha: str
    author: str
    email: str
    timestamp: datetime
    message: str
    files_changed: List[str] = field(default_factory=list)


class DiffAnalyzer:
    """Analyzes git diffs to find changes related to failures."""
    
    # Patterns for parsing git diff output
    DIFF_HEADER = re.compile(r'^diff --git a/(.+) b/(.+)$')
    HUNK_HEADER = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
    FILE_STATUS = re.compile(r'^(new file mode|deleted file mode|rename from|rename to|Binary files)')
    
    def __init__(self, repo_path: str):
        """Initialize with repository path.
        
        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path)
    
    def get_recent_commits(
        self,
        count: int = 10,
        branch: Optional[str] = None,
    ) -> List[CommitInfo]:
        """Get recent commits from the repository.
        
        Args:
            count: Number of commits to retrieve
            branch: Branch to check (default: current branch)
            
        Returns:
            List of commit information
        """
        try:
            cmd = [
                'git', 'log',
                f'-n{count}',
                '--format=%H|%an|%ae|%at|%s',
            ]
            if branch:
                cmd.append(branch)
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 4)
                if len(parts) < 5:
                    continue
                
                sha, author, email, timestamp, message = parts
                
                # Get files changed in this commit
                files = self._get_commit_files(sha)
                
                commits.append(CommitInfo(
                    sha=sha,
                    author=author,
                    email=email,
                    timestamp=datetime.fromtimestamp(int(timestamp)),
                    message=message,
                    files_changed=files,
                ))
            
            return commits
            
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to get git log", error=str(e))
            return []
    
    def _get_commit_files(self, sha: str) -> List[str]:
        """Get list of files changed in a commit."""
        try:
            result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', sha],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return [f for f in result.stdout.strip().split('\n') if f]
        except subprocess.CalledProcessError:
            return []
    
    def get_diff(
        self,
        from_ref: str = 'HEAD~5',
        to_ref: str = 'HEAD',
    ) -> List[FileDiff]:
        """Get diff between two references.
        
        Args:
            from_ref: Starting reference (default: 5 commits ago)
            to_ref: Ending reference (default: HEAD)
            
        Returns:
            List of file diffs
        """
        try:
            result = subprocess.run(
                ['git', 'diff', '--stat', from_ref, to_ref],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            
            # Get detailed diff
            result = subprocess.run(
                ['git', 'diff', from_ref, to_ref],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            
            return self._parse_diff_output(result.stdout)
            
        except subprocess.CalledProcessError as e:
            logger.warning("Failed to get git diff", error=str(e))
            return []
    
    def _parse_diff_output(self, diff_output: str) -> List[FileDiff]:
        """Parse git diff output into structured format."""
        diffs: List[FileDiff] = []
        lines = diff_output.split('\n')
        
        current_file: Optional[FileDiff] = None
        current_hunk: Optional[DiffHunk] = None
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for new file diff
            header_match = self.DIFF_HEADER.match(line)
            if header_match:
                # Save previous file if exists
                if current_file:
                    if current_hunk:
                        current_file.hunks.append(current_hunk)
                    diffs.append(current_file)
                
                current_file = FileDiff(
                    file_path=header_match.group(2),
                    old_path=header_match.group(1) if header_match.group(1) != header_match.group(2) else None,
                    status='modified',
                )
                current_hunk = None
                i += 1
                continue
            
            # Check for file status
            status_match = self.FILE_STATUS.match(line)
            if status_match and current_file:
                status = status_match.group(1)
                if 'new file' in status:
                    current_file.status = 'added'
                elif 'deleted file' in status:
                    current_file.status = 'deleted'
                elif 'rename' in status:
                    current_file.status = 'renamed'
                elif 'Binary' in status:
                    current_file.binary = True
                i += 1
                continue
            
            # Check for hunk header
            hunk_match = self.HUNK_HEADER.match(line)
            if hunk_match and current_file:
                # Save previous hunk
                if current_hunk:
                    current_file.hunks.append(current_hunk)
                
                current_hunk = DiffHunk(
                    old_start=int(hunk_match.group(1)),
                    old_count=int(hunk_match.group(2) or 1),
                    new_start=int(hunk_match.group(3)),
                    new_count=int(hunk_match.group(4) or 1),
                    content=line,
                )
                i += 1
                continue
            
            # Parse diff lines
            if current_hunk and current_file:
                if line.startswith('+') and not line.startswith('+++'):
                    current_hunk.additions.append(line[1:])
                    current_file.additions += 1
                elif line.startswith('-') and not line.startswith('---'):
                    current_hunk.deletions.append(line[1:])
                    current_file.deletions += 1
            
            i += 1
        
        # Add last file
        if current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            diffs.append(current_file)
        
        return diffs
    
    def find_relevant_changes(
        self,
        file_path: str,
        line_number: Optional[int] = None,
        commits: Optional[List[CommitInfo]] = None,
    ) -> List[RecentChange]:
        """Find changes to a specific file that might be relevant.
        
        Args:
            file_path: Path to file to check
            line_number: Specific line number (optional)
            commits: Pre-fetched commits (optional)
            
        Returns:
            List of relevant changes with relevance scores
        """
        if commits is None:
            commits = self.get_recent_commits()
        
        relevant: List[RecentChange] = []
        
        for commit in commits:
            # Check if file was changed in this commit
            if file_path in commit.files_changed:
                relevance = 1.0  # High relevance for direct changes
            else:
                # Check for changes to related files
                related_score = self._calculate_relatedness(
                    file_path,
                    commit.files_changed,
                )
                if related_score < 0.3:
                    continue
                relevance = related_score
            
            relevant.append(RecentChange(
                commit_sha=commit.sha,
                author=commit.author,
                message=commit.message,
                timestamp=commit.timestamp,
                files_changed=commit.files_changed,
                relevance_score=relevance,
            ))
        
        # Sort by relevance
        relevant.sort(key=lambda c: c.relevance_score, reverse=True)
        
        return relevant[:5]  # Return top 5
    
    def _calculate_relatedness(
        self,
        target_file: str,
        changed_files: List[str],
    ) -> float:
        """Calculate how related a set of changed files is to a target file.
        
        Factors:
        - Same directory: high relatedness
        - Similar file type: medium relatedness
        - Common prefix: medium relatedness
        """
        target_path = Path(target_file)
        target_dir = target_path.parent
        target_ext = target_path.suffix
        
        max_score = 0.0
        
        for changed in changed_files:
            changed_path = Path(changed)
            score = 0.0
            
            # Same directory
            if changed_path.parent == target_dir:
                score = 0.6
            # Same parent directory
            elif changed_path.parent.parent == target_dir.parent:
                score = 0.4
            
            # Same file type
            if changed_path.suffix == target_ext:
                score += 0.2
            
            # Check for test file relationship
            if 'test' in str(target_path).lower() and str(target_path.stem).replace('test_', '') in str(changed_path.stem):
                score += 0.3
            elif 'test' in str(changed_path).lower() and str(changed_path.stem).replace('test_', '') in str(target_path.stem):
                score += 0.3
            
            max_score = max(max_score, score)
        
        return min(1.0, max_score)
    
    def get_blame(
        self,
        file_path: str,
        line_number: int,
    ) -> Optional[CommitInfo]:
        """Get blame information for a specific line.
        
        Args:
            file_path: Path to file
            line_number: Line number to check
            
        Returns:
            Commit information for the line, or None
        """
        try:
            result = subprocess.run(
                [
                    'git', 'blame',
                    f'-L{line_number},{line_number}',
                    '--porcelain',
                    file_path,
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            
            lines = result.stdout.strip().split('\n')
            if not lines:
                return None
            
            sha = lines[0].split()[0]
            
            # Parse porcelain output
            data: Dict[str, str] = {}
            for line in lines[1:]:
                if ' ' in line:
                    key, value = line.split(' ', 1)
                    data[key] = value
            
            return CommitInfo(
                sha=sha,
                author=data.get('author', 'Unknown'),
                email=data.get('author-mail', '').strip('<>'),
                timestamp=datetime.fromtimestamp(int(data.get('author-time', '0'))),
                message=data.get('summary', ''),
            )
            
        except subprocess.CalledProcessError:
            return None
