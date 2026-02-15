"""GitHub API integration."""

import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path

import aiohttp

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.utils import get_logger


class GitHubClient:
    """Client for GitHub API interactions."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.logger = get_logger("github-client")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SYMBIONT-X-Scanner",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers
    
    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(
                        "Failed to get repository info",
                        status=response.status,
                        owner=owner,
                        repo=repo,
                    )
                    return {}
    
    async def get_security_alerts(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get Dependabot security alerts for a repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/dependabot/alerts"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(
                        "Could not fetch security alerts",
                        status=response.status,
                        message="May require GitHub Advanced Security",
                    )
                    return []
    
    async def get_code_scanning_alerts(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get code scanning alerts from GitHub Advanced Security."""
        url = f"{self.base_url}/repos/{owner}/{repo}/code-scanning/alerts"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(
                        "Could not fetch code scanning alerts",
                        status=response.status,
                    )
                    return []
    
    async def get_secret_scanning_alerts(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get secret scanning alerts from GitHub Advanced Security."""
        url = f"{self.base_url}/repos/{owner}/{repo}/secret-scanning/alerts"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self._get_headers()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(
                        "Could not fetch secret scanning alerts",
                        status=response.status,
                    )
                    return []
    
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create an issue for a vulnerability."""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        
        payload = {
            "title": title,
            "body": body,
            "labels": labels or ["security", "vulnerability"],
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                headers=self._get_headers(), 
                json=payload
            ) as response:
                if response.status == 201:
                    self.logger.info("Issue created", title=title)
                    return await response.json()
                else:
                    self.logger.error(
                        "Failed to create issue",
                        status=response.status,
                    )
                    return None
