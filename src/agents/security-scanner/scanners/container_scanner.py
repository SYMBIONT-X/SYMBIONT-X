"""Container image vulnerability scanner using Trivy."""

import asyncio
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import uuid

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models import ScanResult, ScanType, Vulnerability, Severity
from .base import BaseScanner


class ContainerScanner(BaseScanner):
    """Scans container images for vulnerabilities using Trivy."""
    
    def __init__(self):
        super().__init__(name="container-scanner", scan_type=ScanType.CONTAINER)
        
        self.severity_map = {
            "CRITICAL": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
            "UNKNOWN": Severity.UNKNOWN,
        }
    
    def is_available(self) -> bool:
        """Check if trivy is installed."""
        try:
            result = subprocess.run(
                ["trivy", "--version"],
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
        """Scan for container vulnerabilities (Dockerfiles and images)."""
        
        start_time = datetime.utcnow()
        result = self._create_scan_result(repository, branch, commit_sha)
        
        self.logger.info(
            "Starting container scan",
            repository=repository,
            target_path=str(target_path),
        )
        
        try:
            # Find Dockerfiles
            dockerfiles = list(target_path.rglob("Dockerfile*"))
            dockerfiles = [
                f for f in dockerfiles 
                if not any(x in str(f) for x in ['node_modules', 'venv', '.git'])
            ]
            
            if not dockerfiles:
                self.logger.info("No Dockerfiles found")
                result.completed_at = datetime.utcnow()
                result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
                return result
            
            # Scan each Dockerfile for misconfigurations
            for dockerfile in dockerfiles:
                vulnerabilities = await self._scan_dockerfile(
                    dockerfile, repository, branch, commit_sha
                )
                result.vulnerabilities.extend(vulnerabilities)
            
            result.update_counts()
            result.success = True
            
            self.logger.info(
                "Container scan completed",
                dockerfiles_scanned=len(dockerfiles),
                total_vulnerabilities=result.total_count,
            )
            
        except Exception as e:
            self.logger.error("Container scan failed", error=str(e))
            result.success = False
            result.error_message = str(e)
        
        result.completed_at = datetime.utcnow()
        result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
        
        return result
    
    async def scan_image(
        self,
        image_name: str,
        repository: str,
        branch: str = "main",
        commit_sha: Optional[str] = None,
    ) -> ScanResult:
        """Scan a specific container image."""
        
        start_time = datetime.utcnow()
        result = self._create_scan_result(repository, branch, commit_sha)
        
        self.logger.info("Scanning container image", image=image_name)
        
        try:
            process = await asyncio.create_subprocess_exec(
                "trivy", "image",
                "--format", "json",
                "--severity", "CRITICAL,HIGH,MEDIUM,LOW",
                image_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=600,  # 10 minutes for image scanning
            )
            
            if stdout:
                trivy_output = json.loads(stdout.decode("utf-8"))
                vulnerabilities = self._parse_trivy_results(
                    trivy_output, image_name, repository, branch, commit_sha
                )
                result.vulnerabilities.extend(vulnerabilities)
            
            result.update_counts()
            result.success = True
            
        except Exception as e:
            self.logger.error("Image scan failed", error=str(e))
            result.success = False
            result.error_message = str(e)
        
        result.completed_at = datetime.utcnow()
        result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
        
        return result
    
    async def _scan_dockerfile(
        self,
        dockerfile: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> List[Vulnerability]:
        """Scan a Dockerfile for misconfigurations."""
        
        vulnerabilities = []
        
        try:
            process = await asyncio.create_subprocess_exec(
                "trivy", "config",
                "--format", "json",
                str(dockerfile.parent),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120,
            )
            
            if stdout:
                output = stdout.decode("utf-8").strip()
                if output:
                    trivy_output = json.loads(output)
                    
                    results = trivy_output.get("Results", [])
                    for result in results:
                        misconfigs = result.get("Misconfigurations", [])
                        for misconfig in misconfigs:
                            vuln = self._parse_misconfig(
                                misconfig, dockerfile, repository, branch, commit_sha
                            )
                            if vuln:
                                vulnerabilities.append(vuln)
                                
        except asyncio.TimeoutError:
            self.logger.error("Dockerfile scan timed out", file=str(dockerfile))
        except Exception as e:
            self.logger.error("Error scanning Dockerfile", file=str(dockerfile), error=str(e))
        
        return vulnerabilities
    
    def _parse_trivy_results(
        self,
        trivy_output: dict,
        target: str,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> List[Vulnerability]:
        """Parse Trivy image scan results."""
        
        vulnerabilities = []
        
        results = trivy_output.get("Results", [])
        for result in results:
            target_name = result.get("Target", target)
            vulns = result.get("Vulnerabilities", [])
            
            for vuln_data in vulns:
                vuln = self._parse_vulnerability(
                    vuln_data, target_name, repository, branch, commit_sha
                )
                if vuln:
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _parse_vulnerability(
        self,
        vuln_data: dict,
        target: str,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> Optional[Vulnerability]:
        """Parse a single Trivy vulnerability."""
        
        try:
            vuln_id = vuln_data.get("VulnerabilityID", str(uuid.uuid4()))
            severity_str = vuln_data.get("Severity", "UNKNOWN")
            severity = self.severity_map.get(severity_str, Severity.UNKNOWN)
            
            return Vulnerability(
                id=f"container-{vuln_id}",
                cve_id=vuln_id if vuln_id.startswith("CVE-") else None,
                title=f"{vuln_data.get('PkgName', 'Unknown')}: {vuln_data.get('Title', vuln_id)[:50]}",
                description=vuln_data.get("Description", "Container vulnerability detected")[:500],
                severity=severity,
                cvss_score=vuln_data.get("CVSS", {}).get("nvd", {}).get("V3Score"),
                package_name=vuln_data.get("PkgName"),
                package_version=vuln_data.get("InstalledVersion"),
                fixed_version=vuln_data.get("FixedVersion"),
                file_path=target,
                fix_recommendation=f"Update {vuln_data.get('PkgName')} to {vuln_data.get('FixedVersion', 'latest version')}",
                source=self.name,
                repository=repository,
                branch=branch,
                commit_sha=commit_sha,
            )
        except Exception as e:
            self.logger.warning("Failed to parse vulnerability", error=str(e))
            return None
    
    def _parse_misconfig(
        self,
        misconfig: dict,
        dockerfile: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> Optional[Vulnerability]:
        """Parse a Trivy misconfiguration finding."""
        
        try:
            severity_str = misconfig.get("Severity", "MEDIUM")
            severity = self.severity_map.get(severity_str, Severity.MEDIUM)
            
            return Vulnerability(
                id=f"container-misconfig-{misconfig.get('ID', uuid.uuid4())}",
                title=misconfig.get("Title", "Container misconfiguration"),
                description=misconfig.get("Description", "")[:500],
                severity=severity,
                file_path=str(dockerfile),
                line_number=misconfig.get("CauseMetadata", {}).get("StartLine"),
                fix_recommendation=misconfig.get("Resolution", "Review and fix the misconfiguration"),
                source=self.name,
                repository=repository,
                branch=branch,
                commit_sha=commit_sha,
            )
        except Exception as e:
            self.logger.warning("Failed to parse misconfiguration", error=str(e))
            return None
