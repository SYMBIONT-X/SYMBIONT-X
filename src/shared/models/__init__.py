"""Shared data models for SYMBIONT-X agents."""

from .vulnerability import Vulnerability, Severity, VulnerabilityStatus
from .scan_result import ScanResult, ScanType

__all__ = [
    "Vulnerability",
    "Severity", 
    "VulnerabilityStatus",
    "ScanResult",
    "ScanType",
]
