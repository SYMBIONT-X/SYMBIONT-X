"""Infrastructure as Code scanner using Checkov."""

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


class IaCScanner(BaseScanner):
    """Scans Infrastructure as Code (Bicep, Terraform, CloudFormation) using Checkov."""
    
    def __init__(self):
        super().__init__(name="iac-scanner", scan_type=ScanType.IAC)
        
        self.severity_map = {
            "CRITICAL": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
        }
        
        # Supported IaC file patterns
        self.supported_patterns = [
            "*.bicep",
            "*.tf",
            "*.json",  # ARM templates, CloudFormation
            "*.yaml",  # CloudFormation, Kubernetes
            "*.yml",
        ]
    
    def is_available(self) -> bool:
        """Check if checkov is installed."""
        try:
            result = subprocess.run(
                ["checkov", "--version"],
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
        """Scan Infrastructure as Code for security issues."""
        
        start_time = datetime.utcnow()
        result = self._create_scan_result(repository, branch, commit_sha)
        
        self.logger.info(
            "Starting IaC scan",
            repository=repository,
            target_path=str(target_path),
        )
        
        try:
            # Find infrastructure directories
            infra_dirs = self._find_infrastructure_dirs(target_path)
            
            if not infra_dirs:
                self.logger.info("No infrastructure directories found")
                result.completed_at = datetime.utcnow()
                result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
                return result
            
            # Scan each infrastructure directory
            for infra_dir in infra_dirs:
                vulnerabilities = await self._scan_directory(
                    infra_dir, target_path, repository, branch, commit_sha
                )
                result.vulnerabilities.extend(vulnerabilities)
            
            result.update_counts()
            result.success = True
            
            self.logger.info(
                "IaC scan completed",
                directories_scanned=len(infra_dirs),
                total_vulnerabilities=result.total_count,
            )
            
        except Exception as e:
            self.logger.error("IaC scan failed", error=str(e))
            result.success = False
            result.error_message = str(e)
        
        result.completed_at = datetime.utcnow()
        result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
        
        return result
    
    def _find_infrastructure_dirs(self, target_path: Path) -> List[Path]:
        """Find directories containing infrastructure code."""
        
        infra_dirs = set()
        
        # Common infrastructure directory names
        infra_names = ['infrastructure', 'infra', 'terraform', 'bicep', 'cloudformation', 'arm']
        
        # Find by directory name
        for name in infra_names:
            for dir_path in target_path.rglob(name):
                if dir_path.is_dir() and not any(x in str(dir_path) for x in ['node_modules', 'venv', '.git']):
                    infra_dirs.add(dir_path)
        
        # Find by file extensions
        for pattern in ['*.bicep', '*.tf']:
            for file_path in target_path.rglob(pattern):
                if not any(x in str(file_path) for x in ['node_modules', 'venv', '.git']):
                    infra_dirs.add(file_path.parent)
        
        return list(infra_dirs)
    
    async def _scan_directory(
        self,
        infra_dir: Path,
        target_path: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> List[Vulnerability]:
        """Scan a directory with Checkov."""
        
        vulnerabilities = []
        
        self.logger.info("Scanning IaC directory", directory=str(infra_dir))
        
        try:
            # Determine framework based on files present
            frameworks = self._detect_frameworks(infra_dir)
            
            if not frameworks:
                return vulnerabilities
            
            # Run Checkov
            process = await asyncio.create_subprocess_exec(
                "checkov",
                "--directory", str(infra_dir),
                "--framework", ",".join(frameworks),
                "--output", "json",
                "--quiet",
                "--compact",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300,
            )
            
            if stdout:
                output = stdout.decode("utf-8").strip()
                if output:
                    try:
                        checkov_results = json.loads(output)
                        vulnerabilities = self._parse_checkov_results(
                            checkov_results, target_path, repository, branch, commit_sha
                        )
                    except json.JSONDecodeError:
                        # Checkov sometimes outputs multiple JSON objects
                        self.logger.warning("Could not parse Checkov output as JSON")
                        
        except asyncio.TimeoutError:
            self.logger.error("Checkov scan timed out", directory=str(infra_dir))
        except Exception as e:
            self.logger.error("Error scanning directory", directory=str(infra_dir), error=str(e))
        
        return vulnerabilities
    
    def _detect_frameworks(self, infra_dir: Path) -> List[str]:
        """Detect which IaC frameworks are used in a directory."""
        
        frameworks = []
        
        # Check for Bicep
        if list(infra_dir.rglob("*.bicep")):
            frameworks.append("bicep")
        
        # Check for Terraform
        if list(infra_dir.rglob("*.tf")):
            frameworks.append("terraform")
        
        # Check for ARM templates
        arm_files = list(infra_dir.rglob("*.json"))
        for f in arm_files:
            try:
                with open(f) as file:
                    content = json.load(file)
                    if "$schema" in content and "azure" in content.get("$schema", "").lower():
                        frameworks.append("arm")
                        break
            except:
                pass
        
        # Check for CloudFormation/Kubernetes YAML
        yaml_files = list(infra_dir.rglob("*.yaml")) + list(infra_dir.rglob("*.yml"))
        for f in yaml_files:
            try:
                with open(f) as file:
                    content = file.read()
                    if "AWSTemplateFormatVersion" in content:
                        frameworks.append("cloudformation")
                    elif "apiVersion" in content and "kind" in content:
                        frameworks.append("kubernetes")
            except:
                pass
        
        return list(set(frameworks))
    
    def _parse_checkov_results(
        self,
        checkov_results: dict,
        target_path: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> List[Vulnerability]:
        """Parse Checkov scan results."""
        
        vulnerabilities = []
        
        # Handle both list and dict formats
        if isinstance(checkov_results, list):
            results_list = checkov_results
        else:
            results_list = [checkov_results]
        
        for result_set in results_list:
            if not isinstance(result_set, dict):
                continue
                
            # Get failed checks
            failed_checks = result_set.get("results", {}).get("failed_checks", [])
            
            for check in failed_checks:
                vuln = self._parse_failed_check(
                    check, target_path, repository, branch, commit_sha
                )
                if vuln:
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _parse_failed_check(
        self,
        check: dict,
        target_path: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> Optional[Vulnerability]:
        """Parse a single Checkov failed check."""
        
        try:
            check_id = check.get("check_id", str(uuid.uuid4()))
            severity_str = check.get("severity", "MEDIUM")
            
            if severity_str:
                severity = self.severity_map.get(severity_str.upper(), Severity.MEDIUM)
            else:
                severity = Severity.MEDIUM
            
            # Make file path relative
            file_path = check.get("file_path", "")
            try:
                file_path = str(Path(file_path).relative_to(target_path))
            except ValueError:
                pass
            
            return Vulnerability(
                id=f"iac-{check_id}-{check.get('resource', '')[:20]}",
                title=f"[{check_id}] {check.get('check_name', 'IaC Security Issue')[:60]}",
                description=check.get("guideline", check.get("check_name", "Infrastructure security issue detected"))[:500],
                severity=severity,
                file_path=file_path,
                line_number=check.get("file_line_range", [0])[0] if check.get("file_line_range") else None,
                fix_recommendation=check.get("guideline", f"Review and fix {check_id} in your infrastructure code"),
                source=self.name,
                repository=repository,
                branch=branch,
                commit_sha=commit_sha,
            )
        except Exception as e:
            self.logger.warning("Failed to parse Checkov check", error=str(e))
            return None
