"""Content Safety filters for AI-generated code in SYMBIONT-X."""

import re
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class SafetyLevel(str, Enum):
    """Safety levels for content."""
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


@dataclass
class SafetyIssue:
    """A detected safety issue."""
    category: str
    severity: SafetyLevel
    description: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class ContentSafetyFilter:
    """Filter AI-generated code for safety issues."""
    
    # Dangerous code patterns
    DANGEROUS_PATTERNS = {
        # Command execution
        "shell_execution": [
            (r"os\.system\s*\(", "Direct OS command execution"),
            (r"subprocess\.(call|run|Popen)\s*\(.*shell\s*=\s*True", "Shell command with shell=True"),
            (r"exec\s*\(", "Dynamic code execution with exec()"),
            (r"eval\s*\(", "Dynamic code execution with eval()"),
        ],
        
        # File system dangers
        "file_system": [
            (r"open\s*\([^)]*['\"]w['\"]", "File write operation"),
            (r"shutil\.rmtree\s*\(", "Recursive directory deletion"),
            (r"os\.remove\s*\(", "File deletion"),
            (r"os\.unlink\s*\(", "File unlinking"),
        ],
        
        # Network dangers
        "network": [
            (r"socket\.socket\s*\(", "Raw socket creation"),
            (r"0\.0\.0\.0", "Binding to all interfaces"),
            (r"requests\.(get|post)\s*\([^)]*verify\s*=\s*False", "SSL verification disabled"),
        ],
        
        # Credential exposure
        "credentials": [
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
            (r"AWS_SECRET_ACCESS_KEY\s*=\s*['\"]", "Hardcoded AWS credentials"),
            (r"PRIVATE_KEY\s*=\s*['\"]", "Hardcoded private key"),
        ],
        
        # SQL injection risks
        "sql_injection": [
            (r"execute\s*\([^)]*%s", "Potential SQL injection with string formatting"),
            (r"execute\s*\([^)]*\.format\(", "Potential SQL injection with .format()"),
            (r"execute\s*\([^)]*f['\"]", "Potential SQL injection with f-string"),
        ],
        
        # Deserialization risks
        "deserialization": [
            (r"pickle\.loads?\s*\(", "Unsafe pickle deserialization"),
            (r"yaml\.load\s*\([^)]*Loader\s*=\s*None", "Unsafe YAML loading"),
            (r"yaml\.unsafe_load\s*\(", "Unsafe YAML loading"),
        ],
        
        # Crypto weaknesses
        "weak_crypto": [
            (r"md5\s*\(", "Weak MD5 hash"),
            (r"sha1\s*\(", "Weak SHA1 hash"),
            (r"DES\s*\(", "Weak DES encryption"),
            (r"random\.random\s*\(", "Non-cryptographic random for security"),
        ],
    }
    
    # Patterns that should trigger warnings but not blocks
    WARNING_PATTERNS = {
        "input_handling": [
            (r"input\s*\(", "User input without validation"),
            (r"request\.(args|form|data)", "Direct request data access"),
        ],
        
        "logging": [
            (r"print\s*\(.*password", "Potential password in print statement"),
            (r"logging\.(info|debug)\s*\(.*secret", "Potential secret in log"),
        ],
        
        "error_handling": [
            (r"except\s*:", "Bare except clause"),
            (r"pass\s*$", "Empty except block"),
        ],
    }
    
    # Safe replacement suggestions
    SAFE_ALTERNATIVES = {
        "os.system": "Use subprocess.run() with shell=False and explicit arguments",
        "eval": "Use ast.literal_eval() for safe evaluation of literals",
        "pickle.load": "Use json for data serialization when possible",
        "md5": "Use hashlib.sha256() or stronger for security purposes",
        "random.random": "Use secrets module for cryptographic randomness",
        "0.0.0.0": "Bind to specific interface or 127.0.0.1 for local only",
    }
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
    
    def analyze_code(self, code: str) -> Tuple[SafetyLevel, List[SafetyIssue]]:
        """Analyze code for safety issues."""
        
        issues: List[SafetyIssue] = []
        lines = code.split("\n")
        
        # Check dangerous patterns (blocked)
        for category, patterns in self.DANGEROUS_PATTERNS.items():
            for pattern, description in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        # Find suggestion
                        suggestion = None
                        for key, alt in self.SAFE_ALTERNATIVES.items():
                            if key.lower() in line.lower():
                                suggestion = alt
                                break
                        
                        issues.append(SafetyIssue(
                            category=category,
                            severity=SafetyLevel.BLOCKED,
                            description=description,
                            line_number=i,
                            suggestion=suggestion,
                        ))
        
        # Check warning patterns
        for category, patterns in self.WARNING_PATTERNS.items():
            for pattern, description in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(SafetyIssue(
                            category=category,
                            severity=SafetyLevel.WARNING,
                            description=description,
                            line_number=i,
                        ))
        
        # Determine overall safety level
        if any(i.severity == SafetyLevel.BLOCKED for i in issues):
            return SafetyLevel.BLOCKED, issues
        elif any(i.severity == SafetyLevel.WARNING for i in issues):
            return SafetyLevel.WARNING, issues
        else:
            return SafetyLevel.SAFE, issues
    
    def filter_code(self, code: str) -> Tuple[str, List[SafetyIssue]]:
        """Filter code, removing or commenting dangerous patterns."""
        
        safety_level, issues = self.analyze_code(code)
        
        if safety_level == SafetyLevel.SAFE:
            return code, issues
        
        if self.strict_mode and safety_level == SafetyLevel.BLOCKED:
            # Return code with dangerous lines commented out
            lines = code.split("\n")
            blocked_lines = {i.line_number for i in issues if i.severity == SafetyLevel.BLOCKED}
            
            filtered_lines = []
            for i, line in enumerate(lines, 1):
                if i in blocked_lines:
                    filtered_lines.append(f"# BLOCKED (security): {line}")
                else:
                    filtered_lines.append(line)
            
            return "\n".join(filtered_lines), issues
        
        return code, issues
    
    def get_safety_report(self, code: str) -> Dict[str, Any]:
        """Generate a safety report for code."""
        
        safety_level, issues = self.analyze_code(code)
        
        return {
            "safety_level": safety_level.value,
            "total_issues": len(issues),
            "blocked_count": sum(1 for i in issues if i.severity == SafetyLevel.BLOCKED),
            "warning_count": sum(1 for i in issues if i.severity == SafetyLevel.WARNING),
            "issues": [
                {
                    "category": i.category,
                    "severity": i.severity.value,
                    "description": i.description,
                    "line_number": i.line_number,
                    "suggestion": i.suggestion,
                }
                for i in issues
            ],
            "is_safe": safety_level == SafetyLevel.SAFE,
            "can_execute": safety_level != SafetyLevel.BLOCKED,
        }


# Global filter instance
content_filter = ContentSafetyFilter(strict_mode=True)


def filter_ai_content(code: str) -> Tuple[str, Dict[str, Any]]:
    """Filter AI-generated code and return filtered code with report."""
    
    filtered_code, issues = content_filter.filter_code(code)
    report = content_filter.get_safety_report(code)
    
    return filtered_code, report
