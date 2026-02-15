"""Code vulnerability scanner using Bandit."""

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


class CodeScanner(BaseScanner):
    """Scans Python code for security issues using Bandit."""
    
    def __init__(self):
        super().__init__(name="code-scanner", scan_type=ScanType.CODE)
        
        # Bandit severity mapping
        self.severity_map = {
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
        }
        
        # Bandit confidence mapping for adjusting severity
        self.confidence_map = {
            "HIGH": 1.0,
            "MEDIUM": 0.7,
            "LOW": 0.4,
        }
    
    def is_available(self) -> bool:
        """Check if bandit is installed."""
        try:
            result = subprocess.run(
                ["bandit", "--version"],
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
        """Scan Python code for security vulnerabilities."""
        
        start_time = datetime.utcnow()
        result = self._create_scan_result(repository, branch, commit_sha)
        
        self.logger.info(
            "Starting code scan",
            repository=repository,
            target_path=str(target_path),
        )
        
        try:
            # Find Python files
            python_files = list(target_path.rglob("*.py"))
            
            if not python_files:
                self.logger.info("No Python files found")
                result.completed_at = datetime.utcnow()
                result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
                return result
            
            # Run Bandit
            vulnerabilities = await self._run_bandit(
                target_path, repository, branch, commit_sha
            )
            result.vulnerabilities.extend(vulnerabilities)
            
            result.update_counts()
            result.success = True
            
            self.logger.info(
                "Code scan completed",
                files_scanned=len(python_files),
                total_vulnerabilities=result.total_count,
            )
            
        except Exception as e:
            self.logger.error("Code scan failed", error=str(e))
            result.success = False
            result.error_message = str(e)
        
        result.completed_at = datetime.utcnow()
        result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
        
        return result
    
    async def _run_bandit(
        self,
        target_path: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> List[Vulnerability]:
        """Run Bandit scanner and parse results."""
        
        vulnerabilities = []
        
        try:
            # Run bandit with JSON output
            process = await asyncio.create_subprocess_exec(
                "bandit",
                "-r",  # Recursive
                "-f", "json",  # JSON output
                "-ll",  # Only medium and higher severity
                "--exclude", ".venv,venv,node_modules,__pycache__",
                str(target_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300,
            )
            
            if stdout:
                bandit_output = json.loads(stdout.decode("utf-8"))
                results = bandit_output.get("results", [])
                
                for issue in results:
                    vuln = self._parse_bandit_issue(
                        issue, target_path, repository, branch, commit_sha
                    )
                    if vuln:
                        vulnerabilities.append(vuln)
                        
        except asyncio.TimeoutError:
            self.logger.error("Bandit scan timed out")
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse Bandit output", error=str(e))
        except Exception as e:
            self.logger.error("Error running Bandit", error=str(e))
        
        return vulnerabilities
    
    def _parse_bandit_issue(
        self,
        issue: dict,
        target_path: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> Optional[Vulnerability]:
        """Parse a Bandit issue into a Vulnerability."""
        
        try:
            severity_str = issue.get("issue_severity", "MEDIUM")
            confidence_str = issue.get("issue_confidence", "MEDIUM")
            
            severity = self.severity_map.get(severity_str, Severity.MEDIUM)
            
            # Adjust severity based on confidence
            confidence = self.confidence_map.get(confidence_str, 0.7)
            if confidence < 0.5 and severity == Severity.HIGH:
                severity = Severity.MEDIUM
            
            # Make file path relative
            file_path = issue.get("filename", "")
            try:
                file_path = str(Path(file_path).relative_to(target_path))
            except ValueError:
                pass
            
            return Vulnerability(
                id=f"code-{issue.get('test_id', uuid.uuid4())}-{issue.get('line_number', 0)}",
                title=f"{issue.get('test_name', 'Security Issue')}: {issue.get('issue_text', '')[:50]}",
                description=issue.get("issue_text", "Code security issue detected"),
                severity=severity,
                file_path=file_path,
                line_number=issue.get("line_number"),
                fix_recommendation=f"Review and fix {issue.get('test_name', 'security issue')} in {file_path}",
                source=self.name,
                repository=repository,
                branch=branch,
                commit_sha=commit_sha,
            )
        except Exception as e:
            self.logger.warning("Failed to parse Bandit issue", error=str(e))
            return None
