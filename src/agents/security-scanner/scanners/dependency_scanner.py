"""Dependency vulnerability scanner using pip-audit."""

import asyncio
import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models import ScanResult, ScanType, Vulnerability, Severity
from .base import BaseScanner


class DependencyScanner(BaseScanner):
    """Scans Python dependencies for known vulnerabilities using pip-audit."""
    
    def __init__(self):
        super().__init__(name="dependency-scanner", scan_type=ScanType.DEPENDENCY)
        self.supported_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-prod.txt",
        ]
    
    def is_available(self) -> bool:
        """Check if pip-audit is installed."""
        try:
            result = subprocess.run(
                ["pip-audit", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    async def scan(
        self,
        target_path: Path,
        repository: str,
        branch: str = "main",
        commit_sha: Optional[str] = None,
    ) -> ScanResult:
        """Scan dependencies for vulnerabilities."""
        
        start_time = datetime.utcnow()
        result = self._create_scan_result(repository, branch, commit_sha)
        
        self.logger.info(
            "Starting dependency scan",
            repository=repository,
            target_path=str(target_path),
        )
        
        try:
            # Find requirements files
            requirements_files = self._find_requirements_files(target_path)
            
            if not requirements_files:
                self.logger.info("No requirements files found")
                result.completed_at = datetime.utcnow()
                result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
                return result
            
            # Scan each requirements file
            for req_file in requirements_files:
                vulnerabilities = await self._scan_requirements_file(
                    req_file, repository, branch, commit_sha
                )
                result.vulnerabilities.extend(vulnerabilities)
            
            result.update_counts()
            result.success = True
            
            self.logger.info(
                "Dependency scan completed",
                total_vulnerabilities=result.total_count,
                critical=result.critical_count,
                high=result.high_count,
            )
            
        except Exception as e:
            self.logger.error("Dependency scan failed", error=str(e))
            result.success = False
            result.error_message = str(e)
        
        result.completed_at = datetime.utcnow()
        result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
        
        return result
    
    def _find_requirements_files(self, target_path: Path) -> List[Path]:
        """Find all requirements files in the target path."""
        found_files = []
        
        for pattern in self.supported_files:
            found_files.extend(target_path.rglob(pattern))
        
        # Filter out files in venv, node_modules, etc.
        filtered = [
            f for f in found_files 
            if not any(exclude in str(f) for exclude in ['venv', 'node_modules', '.git', '__pycache__'])
        ]
        
        return filtered
    
    async def _scan_requirements_file(
        self,
        req_file: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> List[Vulnerability]:
        """Scan a single requirements file with pip-audit."""
        
        vulnerabilities = []
        
        self.logger.info("Scanning requirements file", file=str(req_file))
        
        try:
            # Run pip-audit with JSON output
            process = await asyncio.create_subprocess_exec(
                "pip-audit",
                "--requirement", str(req_file),
                "--format", "json",
                "--progress-spinner", "off",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=180,
            )
            
            # Parse results
            if stdout:
                try:
                    output = stdout.decode("utf-8").strip()
                    if output:
                        audit_results = json.loads(output)
                        
                        # pip-audit returns a list of dependencies with their vulnerabilities
                        if isinstance(audit_results, list):
                            for dep in audit_results:
                                vulns = dep.get("vulns", [])
                                for vuln_data in vulns:
                                    vuln = self._parse_vulnerability(
                                        dep, vuln_data, req_file, repository, branch, commit_sha
                                    )
                                    if vuln:
                                        vulnerabilities.append(vuln)
                                        
                except json.JSONDecodeError as e:
                    self.logger.warning(
                        "Could not parse pip-audit output as JSON",
                        file=str(req_file),
                        error=str(e),
                    )
            
            # Check stderr for any issues
            if stderr:
                stderr_text = stderr.decode("utf-8")
                if "error" in stderr_text.lower():
                    self.logger.warning("pip-audit stderr", message=stderr_text[:200])
                    
        except asyncio.TimeoutError:
            self.logger.error("pip-audit scan timed out", file=str(req_file))
        except Exception as e:
            self.logger.error("Error scanning file", file=str(req_file), error=str(e))
        
        return vulnerabilities
    
    def _parse_vulnerability(
        self,
        dep: dict,
        vuln_data: dict,
        req_file: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> Optional[Vulnerability]:
        """Parse a pip-audit vulnerability into our Vulnerability model."""
        
        try:
            package_name = dep.get("name", "unknown")
            package_version = dep.get("version", "unknown")
            
            vuln_id = vuln_data.get("id", str(uuid.uuid4()))
            description = vuln_data.get("description", "Vulnerability detected")
            fix_versions = vuln_data.get("fix_versions", [])
            
            # Determine severity based on vuln_id prefix or default to HIGH
            severity = self._determine_severity(vuln_id, description)
            
            # Get CVE if the ID is a CVE
            cve_id = vuln_id if vuln_id.startswith("CVE-") else None
            
            return Vulnerability(
                id=f"dep-{vuln_id}-{package_name}",
                cve_id=cve_id,
                title=f"Vulnerable dependency: {package_name}@{package_version}",
                description=description[:500] if description else "Vulnerability detected in dependency",
                severity=severity,
                package_name=package_name,
                package_version=package_version,
                file_path=str(req_file.name),
                fixed_version=fix_versions[0] if fix_versions else None,
                fix_recommendation=f"Update {package_name} to version {fix_versions[0]}" if fix_versions else f"Update {package_name} to a patched version",
                source=self.name,
                repository=repository,
                branch=branch,
                commit_sha=commit_sha,
            )
        except Exception as e:
            self.logger.warning("Failed to parse vulnerability", error=str(e))
            return None
    
    def _determine_severity(self, vuln_id: str, description: str) -> Severity:
        """Determine severity from vulnerability data."""
        
        # Check description for severity hints
        desc_lower = description.lower() if description else ""
        
        if any(word in desc_lower for word in ["critical", "remote code execution", "rce", "arbitrary code"]):
            return Severity.CRITICAL
        elif any(word in desc_lower for word in ["high", "denial of service", "sql injection", "xss"]):
            return Severity.HIGH
        elif any(word in desc_lower for word in ["medium", "moderate"]):
            return Severity.MEDIUM
        elif any(word in desc_lower for word in ["low", "minor"]):
            return Severity.LOW
        
        # Default to HIGH for dependencies (conservative approach)
        return Severity.HIGH
