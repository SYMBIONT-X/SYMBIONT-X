"""Base scanner interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models import ScanResult, ScanType
from shared.utils import get_logger


class BaseScanner(ABC):
    """Abstract base class for all security scanners."""
    
    def __init__(self, name: str, scan_type: ScanType):
        self.name = name
        self.scan_type = scan_type
        self.logger = get_logger(f"scanner.{name}")
    
    @abstractmethod
    async def scan(
        self,
        target_path: Path,
        repository: str,
        branch: str = "main",
        commit_sha: Optional[str] = None,
    ) -> ScanResult:
        """
        Perform a security scan on the target.
        
        Args:
            target_path: Path to the code/files to scan
            repository: Repository name
            branch: Git branch name
            commit_sha: Git commit SHA
            
        Returns:
            ScanResult with any vulnerabilities found
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the scanner dependencies are available."""
        pass
    
    def _create_scan_result(
        self,
        repository: str,
        branch: str,
        commit_sha: Optional[str] = None,
    ) -> ScanResult:
        """Create a new ScanResult instance."""
        import uuid
        return ScanResult(
            scan_id=str(uuid.uuid4()),
            scan_type=self.scan_type,
            repository=repository,
            branch=branch,
            commit_sha=commit_sha,
            scanner_name=self.name,
        )
