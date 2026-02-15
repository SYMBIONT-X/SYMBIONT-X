"""Secret scanner using detect-secrets."""

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


class SecretScanner(BaseScanner):
    """Scans code for leaked secrets and credentials using detect-secrets."""
    
    def __init__(self):
        super().__init__(name="secret-scanner", scan_type=ScanType.SECRET)
        
        # Secret types that are critical
        self.critical_secret_types = [
            "AWS",
            "Azure",
            "PrivateKey",
            "BasicAuth",
            "Stripe",
            "Twilio",
            "SendGrid",
        ]
        
        # Secret types that are high severity
        self.high_secret_types = [
            "Slack",
            "Discord",
            "GitHub",
            "GitLab",
            "Npm",
            "PyPI",
            "JWT",
        ]
    
    def is_available(self) -> bool:
        """Check if detect-secrets is installed."""
        try:
            result = subprocess.run(
                ["detect-secrets", "--version"],
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
        """Scan for leaked secrets and credentials."""
        
        start_time = datetime.utcnow()
        result = self._create_scan_result(repository, branch, commit_sha)
        
        self.logger.info(
            "Starting secret scan",
            repository=repository,
            target_path=str(target_path),
        )
        
        try:
            vulnerabilities = await self._run_detect_secrets(
                target_path, repository, branch, commit_sha
            )
            result.vulnerabilities.extend(vulnerabilities)
            
            result.update_counts()
            result.success = True
            
            self.logger.info(
                "Secret scan completed",
                total_secrets_found=result.total_count,
                critical=result.critical_count,
            )
            
        except Exception as e:
            self.logger.error("Secret scan failed", error=str(e))
            result.success = False
            result.error_message = str(e)
        
        result.completed_at = datetime.utcnow()
        result.scan_duration_seconds = (result.completed_at - start_time).total_seconds()
        
        return result
    
    async def _run_detect_secrets(
        self,
        target_path: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> List[Vulnerability]:
        """Run detect-secrets and parse results."""
        
        vulnerabilities = []
        
        try:
            # Run detect-secrets scan
            process = await asyncio.create_subprocess_exec(
                "detect-secrets", "scan",
                "--all-files",
                str(target_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300,
            )
            
            if stdout:
                scan_results = json.loads(stdout.decode("utf-8"))
                results = scan_results.get("results", {})
                
                for file_path, secrets in results.items():
                    for secret in secrets:
                        vuln = self._parse_secret(
                            secret, file_path, target_path, repository, branch, commit_sha
                        )
                        if vuln:
                            vulnerabilities.append(vuln)
                            
        except asyncio.TimeoutError:
            self.logger.error("Secret scan timed out")
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse detect-secrets output", error=str(e))
        except Exception as e:
            self.logger.error("Error running detect-secrets", error=str(e))
        
        return vulnerabilities
    
    def _parse_secret(
        self,
        secret: dict,
        file_path: str,
        target_path: Path,
        repository: str,
        branch: str,
        commit_sha: Optional[str],
    ) -> Optional[Vulnerability]:
        """Parse a detected secret into a Vulnerability."""
        
        try:
            secret_type = secret.get("type", "Unknown")
            line_number = secret.get("line_number", 0)
            
            # Determine severity based on secret type
            severity = self._determine_severity(secret_type)
            
            # Make file path relative
            try:
                relative_path = str(Path(file_path).relative_to(target_path))
            except ValueError:
                relative_path = file_path
            
            return Vulnerability(
                id=f"secret-{uuid.uuid4().hex[:8]}-{line_number}",
                title=f"Exposed {secret_type} detected",
                description=f"A potential {secret_type} secret was found in the codebase. "
                           f"Exposed secrets can lead to unauthorized access and data breaches.",
                severity=severity,
                file_path=relative_path,
                line_number=line_number,
                fix_recommendation=(
                    f"1. Immediately rotate/revoke this {secret_type} credential\n"
                    f"2. Remove the secret from code\n"
                    f"3. Use environment variables or a secrets manager\n"
                    f"4. Add the file to .gitignore if appropriate"
                ),
                source=self.name,
                repository=repository,
                branch=branch,
                commit_sha=commit_sha,
            )
        except Exception as e:
            self.logger.warning("Failed to parse secret", error=str(e))
            return None
    
    def _determine_severity(self, secret_type: str) -> Severity:
        """Determine severity based on secret type."""
        
        for critical_type in self.critical_secret_types:
            if critical_type.lower() in secret_type.lower():
                return Severity.CRITICAL
        
        for high_type in self.high_secret_types:
            if high_type.lower() in secret_type.lower():
                return Severity.HIGH
        
        # Default to HIGH for any secret
        return Severity.HIGH
