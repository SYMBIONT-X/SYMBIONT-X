"""GitHub Pull Request creator for auto-remediation."""

import asyncio
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from models import GeneratedFix, PullRequestInfo, FileChange
from config import settings


logger = get_logger("github-pr-creator")


class GitHubPRCreator:
    """Creates Pull Requests on GitHub for fixes."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SYMBIONT-X-AutoRemediation",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def is_available(self) -> bool:
        """Check if GitHub integration is available."""
        return self.token is not None
    
    async def create_pr_for_fix(
        self,
        fix: GeneratedFix,
        repository: str,
        base_branch: str = "main",
    ) -> Optional[PullRequestInfo]:
        """
        Create a Pull Request for a generated fix.
        
        Args:
            fix: The generated fix
            repository: Repository name (owner/repo)
            base_branch: Base branch for the PR
            
        Returns:
            PR info or None if failed
        """
        
        if not self.is_available():
            logger.error("GitHub token not configured")
            return None
        
        if not fix.changes:
            logger.warning("No file changes in fix", fix_id=fix.fix_id)
            return None
        
        logger.info(
            "Creating PR for fix",
            fix_id=fix.fix_id,
            repository=repository,
        )
        
        try:
            # Create branch name
            branch_name = f"{settings.pr_branch_prefix}{fix.fix_id}"
            
            # Get base branch SHA
            base_sha = await self._get_branch_sha(repository, base_branch)
            if not base_sha:
                logger.error("Failed to get base branch SHA")
                return None
            
            # Create new branch
            branch_created = await self._create_branch(
                repository, branch_name, base_sha
            )
            if not branch_created:
                logger.error("Failed to create branch")
                return None
            
            # Apply file changes
            for change in fix.changes:
                success = await self._commit_file_change(
                    repository, branch_name, change, fix
                )
                if not success:
                    logger.error("Failed to commit change", file=change.file_path)
                    return None
            
            # Create Pull Request
            pr_info = await self._create_pull_request(
                repository, branch_name, base_branch, fix
            )
            
            if pr_info:
                # Add labels
                await self._add_labels(
                    repository,
                    pr_info.pr_number,
                    [settings.pr_label_auto, settings.pr_label_security],
                )
                
                logger.info(
                    "PR created successfully",
                    pr_number=pr_info.pr_number,
                    pr_url=pr_info.pr_url,
                )
            
            return pr_info
            
        except Exception as e:
            logger.error("PR creation failed", error=str(e))
            return None
    
    async def _get_branch_sha(
        self,
        repository: str,
        branch: str,
    ) -> Optional[str]:
        """Get the SHA of a branch."""
        
        url = f"{self.base_url}/repos/{repository}/git/ref/heads/{branch}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()["object"]["sha"]
            
            logger.warning(
                "Failed to get branch SHA",
                status=response.status_code,
                branch=branch,
            )
            return None
    
    async def _create_branch(
        self,
        repository: str,
        branch_name: str,
        base_sha: str,
    ) -> bool:
        """Create a new branch."""
        
        url = f"{self.base_url}/repos/{repository}/git/refs"
        
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=self.headers, json=data
            )
            
            if response.status_code == 201:
                return True
            
            # Branch might already exist
            if response.status_code == 422:
                logger.info("Branch already exists", branch=branch_name)
                return True
            
            logger.warning(
                "Failed to create branch",
                status=response.status_code,
                response=response.text,
            )
            return False
    
    async def _commit_file_change(
        self,
        repository: str,
        branch: str,
        change: FileChange,
        fix: GeneratedFix,
    ) -> bool:
        """Commit a file change to a branch."""
        
        url = f"{self.base_url}/repos/{repository}/contents/{change.file_path}"
        
        # Get current file (if modifying)
        current_sha = None
        if change.action == "modify":
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params={"ref": branch},
                )
                if response.status_code == 200:
                    current_sha = response.json().get("sha")
        
        # Prepare content
        if change.new_content:
            content_bytes = change.new_content.encode("utf-8")
        else:
            content_bytes = b""
        
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")
        
        data = {
            "message": f"fix: {fix.title}\n\n{fix.description}",
            "content": content_base64,
            "branch": branch,
        }
        
        if current_sha:
            data["sha"] = current_sha
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url, headers=self.headers, json=data
            )
            
            if response.status_code in [200, 201]:
                return True
            
            logger.warning(
                "Failed to commit file",
                status=response.status_code,
                file=change.file_path,
            )
            return False
    
    async def _create_pull_request(
        self,
        repository: str,
        head_branch: str,
        base_branch: str,
        fix: GeneratedFix,
    ) -> Optional[PullRequestInfo]:
        """Create the Pull Request."""
        
        url = f"{self.base_url}/repos/{repository}/pulls"
        
        body = self._generate_pr_body(fix)
        
        data = {
            "title": f"🔒 {fix.title}",
            "head": head_branch,
            "base": base_branch,
            "body": body,
            "maintainer_can_modify": True,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=self.headers, json=data
            )
            
            if response.status_code == 201:
                pr_data = response.json()
                return PullRequestInfo(
                    pr_number=pr_data["number"],
                    pr_url=pr_data["html_url"],
                    branch_name=head_branch,
                    title=data["title"],
                    status="open",
                )
            
            logger.warning(
                "Failed to create PR",
                status=response.status_code,
                response=response.text,
            )
            return None
    
    async def _add_labels(
        self,
        repository: str,
        pr_number: int,
        labels: List[str],
    ) -> bool:
        """Add labels to a PR."""
        
        url = f"{self.base_url}/repos/{repository}/issues/{pr_number}/labels"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=self.headers, json={"labels": labels}
            )
            
            return response.status_code == 200
    
    def _generate_pr_body(self, fix: GeneratedFix) -> str:
        """Generate PR description body."""
        
        body = f"""## 🤖 Auto-Remediation by SYMBIONT-X

### Vulnerability Details
- **Vulnerability ID:** {fix.vulnerability_id}
- **CVE:** {fix.cve_id or 'N/A'}
- **Fix Type:** {fix.fix_type.value}
- **Confidence:** {fix.confidence.value}

### Description
{fix.description}

### Changes
"""
        
        for change in fix.changes:
            body += f"- `{change.file_path}` ({change.action})\n"
        
        body += "\n### Verification Steps\n"
        
        if fix.test_commands:
            body += "```bash\n"
            for cmd in fix.test_commands:
                body += f"{cmd}\n"
            body += "```\n"
        else:
            body += "- Review the changes\n- Run existing test suite\n"
        
        if fix.rollback_steps:
            body += "\n### Rollback Steps\n"
            for step in fix.rollback_steps:
                body += f"- {step}\n"
        
        body += f"""
---
*Generated by SYMBIONT-X Auto-Remediation Agent*
*Template: {fix.template_used or 'AI-generated'}*
*Timestamp: {datetime.utcnow().isoformat()}*
"""
        
        return body
    
    async def get_pr_status(
        self,
        repository: str,
        pr_number: int,
    ) -> Optional[Dict[str, Any]]:
        """Get status of a PR."""
        
        url = f"{self.base_url}/repos/{repository}/pulls/{pr_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "number": data["number"],
                    "state": data["state"],
                    "merged": data.get("merged", False),
                    "mergeable": data.get("mergeable"),
                    "url": data["html_url"],
                }
            
            return None
    
    async def merge_pr(
        self,
        repository: str,
        pr_number: int,
        merge_method: str = "squash",
    ) -> bool:
        """Merge a PR."""
        
        url = f"{self.base_url}/repos/{repository}/pulls/{pr_number}/merge"
        
        data = {
            "merge_method": merge_method,
            "commit_title": f"fix: Auto-remediation #{pr_number}",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url, headers=self.headers, json=data
            )
            
            if response.status_code == 200:
                logger.info("PR merged successfully", pr_number=pr_number)
                return True
            
            logger.warning(
                "Failed to merge PR",
                status=response.status_code,
                pr_number=pr_number,
            )
            return False
