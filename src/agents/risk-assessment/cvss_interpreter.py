"""CVSS Score interpretation and analysis."""

from typing import Optional, Dict, Tuple
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from models import ExploitMaturity


logger = get_logger("cvss-interpreter")


class CVSSInterpreter:
    """Interprets CVSS scores and vectors for risk assessment."""
    
    def __init__(self):
        # CVSS v3.1 severity ranges
        self.severity_ranges = {
            (9.0, 10.0): "critical",
            (7.0, 8.9): "high",
            (4.0, 6.9): "medium",
            (0.1, 3.9): "low",
            (0.0, 0.0): "none",
        }
        
        # Attack Vector values (CVSS v3.1)
        self.attack_vectors = {
            "N": ("Network", 0.85, "Exploitable remotely"),
            "A": ("Adjacent", 0.62, "Requires adjacent network access"),
            "L": ("Local", 0.55, "Requires local access"),
            "P": ("Physical", 0.20, "Requires physical access"),
        }
        
        # Attack Complexity values
        self.attack_complexity = {
            "L": ("Low", 0.77, "No special conditions needed"),
            "H": ("High", 0.44, "Requires specific conditions"),
        }
        
        # Privileges Required values
        self.privileges_required = {
            "N": ("None", 0.85, "No authentication needed"),
            "L": ("Low", 0.62, "Basic user privileges"),
            "H": ("High", 0.27, "Admin privileges needed"),
        }
        
        # User Interaction values
        self.user_interaction = {
            "N": ("None", 0.85, "No user action required"),
            "R": ("Required", 0.62, "User must perform action"),
        }
        
        # Impact values
        self.impact_values = {
            "H": ("High", 0.56, "Complete impact"),
            "L": ("Low", 0.22, "Limited impact"),
            "N": ("None", 0.0, "No impact"),
        }
    
    def get_severity(self, cvss_score: float) -> str:
        """Get severity label from CVSS score."""
        
        if cvss_score is None:
            return "unknown"
        
        for (low, high), severity in self.severity_ranges.items():
            if low <= cvss_score <= high:
                return severity
        
        return "unknown"
    
    def parse_vector(self, vector_string: str) -> Dict[str, Dict]:
        """
        Parse a CVSS v3.x vector string.
        
        Example: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
        """
        
        result = {}
        
        if not vector_string:
            return result
        
        try:
            # Remove CVSS version prefix if present
            if vector_string.startswith("CVSS:"):
                parts = vector_string.split("/")[1:]
            else:
                parts = vector_string.split("/")
            
            for part in parts:
                if ":" not in part:
                    continue
                    
                metric, value = part.split(":")
                
                if metric == "AV" and value in self.attack_vectors:
                    name, score, desc = self.attack_vectors[value]
                    result["attack_vector"] = {
                        "value": value,
                        "name": name,
                        "score": score,
                        "description": desc,
                    }
                elif metric == "AC" and value in self.attack_complexity:
                    name, score, desc = self.attack_complexity[value]
                    result["attack_complexity"] = {
                        "value": value,
                        "name": name,
                        "score": score,
                        "description": desc,
                    }
                elif metric == "PR" and value in self.privileges_required:
                    name, score, desc = self.privileges_required[value]
                    result["privileges_required"] = {
                        "value": value,
                        "name": name,
                        "score": score,
                        "description": desc,
                    }
                elif metric == "UI" and value in self.user_interaction:
                    name, score, desc = self.user_interaction[value]
                    result["user_interaction"] = {
                        "value": value,
                        "name": name,
                        "score": score,
                        "description": desc,
                    }
                elif metric == "C" and value in self.impact_values:
                    name, score, desc = self.impact_values[value]
                    result["confidentiality_impact"] = {
                        "value": value,
                        "name": name,
                        "score": score,
                        "description": desc,
                    }
                elif metric == "I" and value in self.impact_values:
                    name, score, desc = self.impact_values[value]
                    result["integrity_impact"] = {
                        "value": value,
                        "name": name,
                        "score": score,
                        "description": desc,
                    }
                elif metric == "A" and value in self.impact_values:
                    name, score, desc = self.impact_values[value]
                    result["availability_impact"] = {
                        "value": value,
                        "name": name,
                        "score": score,
                        "description": desc,
                    }
                    
        except Exception as e:
            logger.warning("Failed to parse CVSS vector", vector=vector_string, error=str(e))
        
        return result
    
    def calculate_exploitability_score(
        self,
        cvss_score: float,
        vector_string: Optional[str] = None,
        exploit_maturity: ExploitMaturity = ExploitMaturity.NOT_DEFINED,
        is_actively_exploited: bool = False,
        has_public_exploit: bool = False,
    ) -> Tuple[float, list]:
        """
        Calculate exploitability score (0-10) based on multiple factors.
        
        Returns: (score, factors_list)
        """
        
        factors = []
        base_score = 5.0  # Start neutral
        
        # Factor 1: CVSS-based exploitability
        if cvss_score is not None:
            if cvss_score >= 9.0:
                base_score = 8.0
                factors.append("Critical CVSS indicates high exploitability")
            elif cvss_score >= 7.0:
                base_score = 6.5
                factors.append("High CVSS indicates elevated exploitability")
        
        # Factor 2: Vector analysis
        if vector_string:
            vector_data = self.parse_vector(vector_string)
            
            # Network-accessible = more exploitable
            av = vector_data.get("attack_vector", {})
            if av.get("value") == "N":
                base_score += 1.5
                factors.append("Network-accessible attack vector")
            elif av.get("value") == "A":
                base_score += 0.5
                factors.append("Adjacent network attack vector")
            
            # Low complexity = more exploitable
            ac = vector_data.get("attack_complexity", {})
            if ac.get("value") == "L":
                base_score += 0.5
                factors.append("Low attack complexity")
            
            # No privileges = more exploitable
            pr = vector_data.get("privileges_required", {})
            if pr.get("value") == "N":
                base_score += 1.0
                factors.append("No privileges required")
            
            # No user interaction = more exploitable
            ui = vector_data.get("user_interaction", {})
            if ui.get("value") == "N":
                base_score += 0.5
                factors.append("No user interaction required")
        
        # Factor 3: Exploit maturity
        maturity_modifiers = {
            ExploitMaturity.HIGH: 2.0,
            ExploitMaturity.FUNCTIONAL: 1.5,
            ExploitMaturity.POC: 1.0,
            ExploitMaturity.UNPROVEN: 0.0,
            ExploitMaturity.NOT_DEFINED: 0.0,
        }
        
        maturity_mod = maturity_modifiers.get(exploit_maturity, 0.0)
        if maturity_mod > 0:
            base_score += maturity_mod
            factors.append(f"Exploit maturity: {exploit_maturity.value}")
        
        # Factor 4: Active exploitation
        if is_actively_exploited:
            base_score += 2.0
            factors.append("ACTIVELY EXPLOITED IN THE WILD")
        
        # Factor 5: Public exploit
        if has_public_exploit and not is_actively_exploited:
            base_score += 1.0
            factors.append("Public exploit available")
        
        # Normalize to 0-10
        final_score = min(10.0, max(0.0, base_score))
        
        return final_score, factors
    
    def get_impact_summary(self, vector_string: Optional[str]) -> Dict[str, str]:
        """Get a summary of impact from CVSS vector."""
        
        if not vector_string:
            return {
                "confidentiality": "unknown",
                "integrity": "unknown",
                "availability": "unknown",
            }
        
        vector_data = self.parse_vector(vector_string)
        
        return {
            "confidentiality": vector_data.get("confidentiality_impact", {}).get("name", "unknown"),
            "integrity": vector_data.get("integrity_impact", {}).get("name", "unknown"),
            "availability": vector_data.get("availability_impact", {}).get("name", "unknown"),
        }
