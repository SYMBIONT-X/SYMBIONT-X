"""Scan result data model."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from .vulnerability import Vulnerability


class ScanType(str, Enum):
    """Types of security scans."""
    DEPENDENCY = "dependency"
    CODE = "code"
    SECRET = "secret"
    CONTAINER = "container"
    IAC = "iac"
    FULL = "full"


class ScanResult(BaseModel):
    """Result of a security scan."""
    
    scan_id: str = Field(..., description="Unique scan identifier")
    scan_type: ScanType = Field(..., description="Type of scan performed")
    repository: str = Field(..., description="Repository scanned")
    branch: str = Field(default="main", description="Branch scanned")
    commit_sha: Optional[str] = Field(None, description="Commit SHA scanned")
    
    # Results
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)
    total_count: int = Field(default=0, description="Total vulnerabilities found")
    critical_count: int = Field(default=0)
    high_count: int = Field(default=0)
    medium_count: int = Field(default=0)
    low_count: int = Field(default=0)
    
    # Scan metadata
    scanner_name: str = Field(..., description="Name of scanner used")
    scanner_version: Optional[str] = Field(None)
    scan_duration_seconds: Optional[float] = Field(None)
    
    # Status
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(None)
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    
    class Config:
        use_enum_values = True
    
    def update_counts(self) -> None:
        """Update vulnerability counts based on the vulnerabilities list."""
        from .vulnerability import Severity
        
        self.total_count = len(self.vulnerabilities)
        self.critical_count = sum(1 for v in self.vulnerabilities if v.severity == Severity.CRITICAL)
        self.high_count = sum(1 for v in self.vulnerabilities if v.severity == Severity.HIGH)
        self.medium_count = sum(1 for v in self.vulnerabilities if v.severity == Severity.MEDIUM)
        self.low_count = sum(1 for v in self.vulnerabilities if v.severity == Severity.LOW)
