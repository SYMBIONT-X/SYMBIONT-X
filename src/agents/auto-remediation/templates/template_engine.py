"""Template engine for applying fix templates."""

import re
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.utils import get_logger

from .dependency_templates import DEPENDENCY_TEMPLATES
from .config_templates import CONFIG_TEMPLATES
from .dockerfile_templates import DOCKERFILE_TEMPLATES


logger = get_logger("template-engine")


class TemplateEngine:
    """Engine for matching and applying fix templates."""
    
    def __init__(self):
        self.templates = {
            **DEPENDENCY_TEMPLATES,
            **CONFIG_TEMPLATES,
            **DOCKERFILE_TEMPLATES,
        }
    
    def find_matching_template(
        self,
        vulnerability: Dict[str, Any],
        file_content: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find a template that matches the vulnerability.
        
        Args:
            vulnerability: Vulnerability data
            file_content: Content of the affected file
            
        Returns:
            Matching template or None
        """
        
        vuln_type = vulnerability.get("source", "").lower()
        package_name = vulnerability.get("package_name", "").lower()
        file_path = vulnerability.get("file_path", "").lower()
        title = vulnerability.get("title", "").lower()
        description = vulnerability.get("description", "").lower()
        
        # Combine searchable text
        search_text = f"{vuln_type} {package_name} {file_path} {title} {description}"
        
        best_match = None
        best_score = 0
        
        for template_id, template in self.templates.items():
            score = self._calculate_match_score(template, search_text, file_path)
            
            if score > best_score:
                best_score = score
                best_match = template
        
        if best_match and best_score > 0:
            logger.info(
                "Found matching template",
                template_id=best_match["id"],
                score=best_score,
            )
            return best_match
        
        return None
    
    def _calculate_match_score(
        self,
        template: Dict[str, Any],
        search_text: str,
        file_path: str,
    ) -> int:
        """Calculate how well a template matches."""
        
        score = 0
        
        # Check applicable_to keywords
        for keyword in template.get("applicable_to", []):
            if keyword.lower() in search_text:
                score += 2
            if keyword.lower() in file_path:
                score += 3
        
        # Check file pattern
        if "file_pattern" in template:
            pattern = template["file_pattern"]
            if pattern.lower() in file_path:
                score += 5
        
        return score
    
    def apply_template(
        self,
        template: Dict[str, Any],
        file_content: str,
        variables: Dict[str, str],
    ) -> Tuple[str, List[str]]:
        """
        Apply a template to fix file content.
        
        Args:
            template: The fix template
            file_content: Original file content
            variables: Variable values for the template
            
        Returns:
            Tuple of (fixed_content, list_of_changes)
        """
        
        changes = []
        fixed_content = file_content
        
        # Apply pattern replacements
        if "patterns" in template:
            for old_pattern, new_pattern in template["patterns"]:
                # Substitute variables in patterns
                old_filled = self._fill_variables(old_pattern, variables)
                new_filled = self._fill_variables(new_pattern, variables)
                
                if old_filled in fixed_content:
                    fixed_content = fixed_content.replace(old_filled, new_filled)
                    changes.append(f"Replaced: {old_filled[:50]}... -> {new_filled[:50]}...")
        
        # Apply template/replacement
        if "template" in template and "replacement" in template:
            old_filled = self._fill_variables(template["template"], variables)
            new_filled = self._fill_variables(template["replacement"], variables)
            
            if old_filled in fixed_content:
                fixed_content = fixed_content.replace(old_filled, new_filled)
                changes.append(f"Applied template replacement")
        
        # Apply regex pattern
        if "pattern_regex" in template:
            pattern = template["pattern_regex"]
            replacement = self._fill_variables(
                template.get("replacement", ""),
                variables
            )
            
            fixed_content, count = re.subn(pattern, replacement, fixed_content)
            if count > 0:
                changes.append(f"Applied regex replacement ({count} matches)")
        
        # Add imports if needed
        if "imports_needed" in template:
            for import_stmt in template["imports_needed"]:
                if import_stmt not in fixed_content:
                    fixed_content = import_stmt + "\n" + fixed_content
                    changes.append(f"Added import: {import_stmt}")
        
        # Add additions
        if "additions" in template:
            for addition in template["additions"]:
                if addition not in fixed_content:
                    fixed_content += "\n" + addition
                    changes.append(f"Added: {addition[:50]}...")
        
        # Add addition after specific content
        if "addition_after" in template:
            # Find last occurrence and add after
            addition = template["addition_after"]
            # This is simplified - in production would need smarter insertion
            if addition not in fixed_content:
                changes.append(f"Note: Manual addition may be needed: {addition}")
        
        return fixed_content, changes
    
    def _fill_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Fill template variables in text."""
        
        result = text
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{var_name}}}", var_value)
        
        return result
    
    def generate_dependency_fix(
        self,
        package_name: str,
        old_version: str,
        new_version: str,
        file_type: str = "requirements.txt",
    ) -> Dict[str, Any]:
        """
        Generate a dependency update fix.
        
        Args:
            package_name: Name of the package
            old_version: Current vulnerable version
            new_version: Fixed version
            file_type: Type of dependency file
            
        Returns:
            Fix details
        """
        
        # Select appropriate template
        if "requirements" in file_type.lower():
            template_id = "python_requirements_update"
        elif "pipfile" in file_type.lower():
            template_id = "python_pipfile_update"
        elif "package.json" in file_type.lower():
            template_id = "npm_package_update"
        elif "go.mod" in file_type.lower():
            template_id = "go_mod_update"
        else:
            template_id = "python_requirements_update"
        
        template = self.templates.get(template_id, {})
        
        return {
            "template_id": template_id,
            "template": template,
            "variables": {
                "package_name": package_name,
                "old_package": package_name,
                "new_package": package_name,
                "old_version": old_version,
                "new_version": new_version,
            },
            "search_pattern": f"{package_name}=={old_version}",
            "replacement": f"{package_name}=={new_version}",
            "test_commands": template.get("test_commands", []),
        }
    
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available templates."""
        return self.templates
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID."""
        return self.templates.get(template_id)
