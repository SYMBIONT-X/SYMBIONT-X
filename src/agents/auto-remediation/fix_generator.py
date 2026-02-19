"""Fix generation logic for vulnerabilities."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from models import (
    GeneratedFix,
    FileChange,
    FixType,
    FixStatus,
    FixConfidence,
)
from templates import TemplateEngine
from config import settings


logger = get_logger("fix-generator")


class FixGenerator:
    """Generates fixes for vulnerabilities."""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self.ai_client = None
        self._initialize_ai_client()
    
    def _initialize_ai_client(self):
        """Initialize AI client for code generation."""
        try:
            if settings.azure_openai_endpoint and settings.azure_openai_key:
                from openai import AzureOpenAI
                self.ai_client = AzureOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_key,
                    api_version="2024-02-15-preview",
                )
                self.ai_model = settings.azure_openai_deployment
                logger.info("AI client initialized (Azure OpenAI)")
            elif settings.openai_api_key:
                from openai import OpenAI
                self.ai_client = OpenAI(api_key=settings.openai_api_key)
                self.ai_model = "gpt-4"
                logger.info("AI client initialized (OpenAI)")
            else:
                logger.warning("No AI credentials - template-only mode")
        except Exception as e:
            logger.warning("AI client initialization failed", error=str(e))
    
    def generate_fix(
        self,
        vulnerability: Dict[str, Any],
        file_content: Optional[str] = None,
        use_ai: bool = True,
    ) -> GeneratedFix:
        """
        Generate a fix for a vulnerability.
        
        Args:
            vulnerability: Vulnerability data
            file_content: Content of affected file
            use_ai: Whether to use AI for generation
            
        Returns:
            Generated fix
        """
        
        fix_id = str(uuid.uuid4())[:8]
        vuln_id = vulnerability.get("id", "unknown")
        
        logger.info("Generating fix", vulnerability_id=vuln_id, fix_id=fix_id)
        
        # Try template-based fix first
        template_fix = self._generate_template_fix(vulnerability, file_content)
        
        if template_fix:
            logger.info("Template fix generated", template_id=template_fix.template_used)
            return template_fix
        
        # Fall back to AI generation
        if use_ai and self.ai_client:
            ai_fix = self._generate_ai_fix(vulnerability, file_content)
            if ai_fix:
                logger.info("AI fix generated")
                return ai_fix
        
        # Return manual fix required
        return GeneratedFix(
            fix_id=fix_id,
            vulnerability_id=vuln_id,
            cve_id=vulnerability.get("cve_id"),
            fix_type=FixType.MANUAL_REQUIRED,
            title=f"Manual fix required for {vulnerability.get('title', vuln_id)}",
            description="No automatic fix available. Manual intervention required.",
            confidence=FixConfidence.LOW,
            status=FixStatus.PENDING,
        )
    
    def _generate_template_fix(
        self,
        vulnerability: Dict[str, Any],
        file_content: Optional[str],
    ) -> Optional[GeneratedFix]:
        """Generate fix using templates."""
        
        fix_id = str(uuid.uuid4())[:8]
        vuln_id = vulnerability.get("id", "unknown")
        
        # Check for dependency update
        if vulnerability.get("fixed_version"):
            return self._generate_dependency_update_fix(vulnerability, fix_id)
        
        # Find matching template
        template = self.template_engine.find_matching_template(
            vulnerability, file_content
        )
        
        if not template:
            return None
        
        # Prepare variables
        variables = self._extract_variables(vulnerability, template)
        
        # Apply template
        changes = []
        if file_content:
            fixed_content, change_list = self.template_engine.apply_template(
                template, file_content, variables
            )
            
            if fixed_content != file_content:
                changes.append(FileChange(
                    file_path=vulnerability.get("file_path", "unknown"),
                    action="modify",
                    original_content=file_content,
                    new_content=fixed_content,
                ))
        
        fix_type = FixType(template.get("fix_type", "config_change"))
        confidence = FixConfidence(template.get("confidence", "medium"))
        
        return GeneratedFix(
            fix_id=fix_id,
            vulnerability_id=vuln_id,
            cve_id=vulnerability.get("cve_id"),
            fix_type=fix_type,
            title=f"Fix: {template.get('name', 'Security fix')}",
            description=template.get("description", ""),
            changes=changes,
            confidence=confidence,
            template_used=template.get("id"),
            ai_generated=False,
            test_commands=template.get("test_commands", []),
            status=FixStatus.READY if changes else FixStatus.PENDING,
        )
    
    def _generate_dependency_update_fix(
        self,
        vulnerability: Dict[str, Any],
        fix_id: str,
    ) -> GeneratedFix:
        """Generate a dependency update fix."""
        
        vuln_id = vulnerability.get("id", "unknown")
        package_name = vulnerability.get("package_name", "unknown")
        old_version = vulnerability.get("package_version", "")
        new_version = vulnerability.get("fixed_version", "")
        file_path = vulnerability.get("file_path", "requirements.txt")
        
        # Determine file type
        if "requirements" in file_path.lower():
            search = f"{package_name}=={old_version}"
            replace = f"{package_name}=={new_version}"
        elif "package.json" in file_path.lower():
            search = f'"{package_name}": "{old_version}"'
            replace = f'"{package_name}": "{new_version}"'
        else:
            search = f"{package_name}=={old_version}"
            replace = f"{package_name}=={new_version}"
        
        return GeneratedFix(
            fix_id=fix_id,
            vulnerability_id=vuln_id,
            cve_id=vulnerability.get("cve_id"),
            fix_type=FixType.DEPENDENCY_UPDATE,
            title=f"Update {package_name} from {old_version} to {new_version}",
            description=f"Security update for {package_name} to fix {vulnerability.get('cve_id', 'vulnerability')}",
            changes=[
                FileChange(
                    file_path=file_path,
                    action="modify",
                    original_content=search,
                    new_content=replace,
                )
            ],
            confidence=FixConfidence.HIGH,
            template_used="dependency_update",
            ai_generated=False,
            test_commands=[
                "pip install -r requirements.txt",
                "pip check",
                "python -m pytest tests/ -v",
            ],
            rollback_steps=[
                f"Revert {package_name} to {old_version}",
                "pip install -r requirements.txt",
            ],
            status=FixStatus.READY,
        )
    
    def _generate_ai_fix(
        self,
        vulnerability: Dict[str, Any],
        file_content: Optional[str],
    ) -> Optional[GeneratedFix]:
        """Generate fix using AI."""
        
        if not self.ai_client:
            return None
        
        fix_id = str(uuid.uuid4())[:8]
        vuln_id = vulnerability.get("id", "unknown")
        
        try:
            prompt = self._build_ai_prompt(vulnerability, file_content)
            
            response = self.ai_client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1500,
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse AI response
            fix = self._parse_ai_response(ai_response, vulnerability, fix_id)
            return fix
            
        except Exception as e:
            logger.error("AI fix generation failed", error=str(e))
            return None
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI fix generation."""
        return """You are a security engineer generating code fixes for vulnerabilities.

Generate precise, minimal fixes that:
1. Address the specific vulnerability
2. Maintain existing functionality
3. Follow security best practices
4. Are production-ready

Respond in this format:
FIX_TYPE: [dependency_update|config_change|code_patch]
CONFIDENCE: [high|medium|low]
DESCRIPTION: Brief description of the fix

FILE: path/to/file
ACTION: [modify|create|delete]
---ORIGINAL---
original code
---FIXED---
fixed code
---END---

TEST_COMMANDS:
- command 1
- command 2"""

    def _build_ai_prompt(
        self,
        vulnerability: Dict[str, Any],
        file_content: Optional[str],
    ) -> str:
        """Build prompt for AI fix generation."""
        
        prompt = f"""Generate a fix for this security vulnerability:

Vulnerability ID: {vulnerability.get('id')}
CVE: {vulnerability.get('cve_id', 'N/A')}
Title: {vulnerability.get('title')}
Severity: {vulnerability.get('severity')}
Description: {vulnerability.get('description', 'N/A')[:500]}

File: {vulnerability.get('file_path', 'N/A')}
Package: {vulnerability.get('package_name', 'N/A')}
Version: {vulnerability.get('package_version', 'N/A')}
Fixed Version: {vulnerability.get('fixed_version', 'N/A')}
"""
        
        if file_content:
            prompt += f"""
Current file content:
```
{file_content[:2000]}
```
"""
        
        prompt += "\nGenerate a minimal, safe fix for this vulnerability."
        
        return prompt
    
    def _parse_ai_response(
        self,
        response: str,
        vulnerability: Dict[str, Any],
        fix_id: str,
    ) -> Optional[GeneratedFix]:
        """Parse AI response into GeneratedFix."""
        
        vuln_id = vulnerability.get("id", "unknown")
        
        # Simple parsing - in production would be more robust
        fix_type = FixType.CODE_PATCH
        confidence = FixConfidence.MEDIUM
        description = "AI-generated security fix"
        
        if "FIX_TYPE: dependency_update" in response:
            fix_type = FixType.DEPENDENCY_UPDATE
        elif "FIX_TYPE: config_change" in response:
            fix_type = FixType.CONFIG_CHANGE
        
        if "CONFIDENCE: high" in response:
            confidence = FixConfidence.HIGH
        elif "CONFIDENCE: low" in response:
            confidence = FixConfidence.LOW
        
        # Extract description
        if "DESCRIPTION:" in response:
            lines = response.split("\n")
            for line in lines:
                if line.startswith("DESCRIPTION:"):
                    description = line.replace("DESCRIPTION:", "").strip()
                    break
        
        return GeneratedFix(
            fix_id=fix_id,
            vulnerability_id=vuln_id,
            cve_id=vulnerability.get("cve_id"),
            fix_type=fix_type,
            title=f"AI Fix: {vulnerability.get('title', vuln_id)[:50]}",
            description=description,
            confidence=confidence,
            ai_generated=True,
            status=FixStatus.READY,
        )
    
    def _extract_variables(
        self,
        vulnerability: Dict[str, Any],
        template: Dict[str, Any],
    ) -> Dict[str, str]:
        """Extract template variables from vulnerability."""
        
        return {
            "package_name": vulnerability.get("package_name", ""),
            "old_version": vulnerability.get("package_version", ""),
            "new_version": vulnerability.get("fixed_version", ""),
            "old_package": vulnerability.get("package_name", ""),
            "new_package": vulnerability.get("package_name", ""),
            "file_path": vulnerability.get("file_path", ""),
            "cve_id": vulnerability.get("cve_id", ""),
        }
    
    def get_fix_stats(self) -> Dict[str, Any]:
        """Get statistics about available fixes."""
        
        templates = self.template_engine.get_all_templates()
        
        by_type = {}
        for t in templates.values():
            fix_type = t.get("fix_type", "unknown")
            by_type[fix_type] = by_type.get(fix_type, 0) + 1
        
        return {
            "total_templates": len(templates),
            "by_type": by_type,
            "ai_enabled": self.ai_client is not None,
        }
