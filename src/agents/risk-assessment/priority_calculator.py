"""Priority calculation engine for vulnerabilities."""

from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from models import (
    Priority,
    RiskScore,
    RiskAssessment,
    BusinessContext,
    ExploitMaturity,
)
from cvss_interpreter import CVSSInterpreter
from business_analyzer import BusinessContextAnalyzer
from config import settings


logger = get_logger("priority-calculator")


class PriorityCalculator:
    """Calculates vulnerability priority based on multiple risk factors."""
    
    def __init__(self):
        self.cvss_interpreter = CVSSInterpreter()
        self.business_analyzer = BusinessContextAnalyzer()
        
        # Weights from config
        self.weight_cvss = settings.weight_cvss
        self.weight_exploitability = settings.weight_exploitability
        self.weight_business_impact = settings.weight_business_impact
        self.weight_data_sensitivity = settings.weight_data_sensitivity
        
        # Priority thresholds (total score 0-10)
        self.priority_thresholds = {
            Priority.P0: 9.0,   # >= 9.0 = P0 (Critical)
            Priority.P1: 7.0,   # >= 7.0 = P1 (High)
            Priority.P2: 4.0,   # >= 4.0 = P2 (Medium)
            Priority.P3: 2.0,   # >= 2.0 = P3 (Low)
            Priority.P4: 0.0,   # < 2.0 = P4 (Informational)
        }
    
    def calculate(
        self,
        vulnerability: Dict[str, Any],
        business_context: Optional[BusinessContext] = None,
        exploit_maturity: ExploitMaturity = ExploitMaturity.NOT_DEFINED,
        is_actively_exploited: bool = False,
        has_public_exploit: bool = False,
        ai_analysis: Optional[str] = None,
    ) -> RiskAssessment:
        """
        Calculate priority for a single vulnerability.
        
        Args:
            vulnerability: Vulnerability data dict
            business_context: Business context for the service
            exploit_maturity: Known exploit maturity level
            is_actively_exploited: Is this being exploited in the wild?
            has_public_exploit: Is there a public exploit available?
            ai_analysis: Optional AI-generated analysis
            
        Returns:
            Complete RiskAssessment with priority
        """
        
        vuln_id = vulnerability.get("id", "unknown")
        cve_id = vulnerability.get("cve_id")
        title = vulnerability.get("title", "Unknown vulnerability")
        severity = vulnerability.get("severity", "medium")
        cvss_score = vulnerability.get("cvss_score")
        cvss_vector = vulnerability.get("cvss_vector")
        repository = vulnerability.get("repository", "unknown")
        
        logger.info(
            "Calculating priority",
            vulnerability_id=vuln_id,
            severity=severity,
            cvss_score=cvss_score,
        )
        
        all_factors = []
        
        # 1. CVSS Score (0-10)
        if cvss_score is not None:
            cvss_normalized = float(cvss_score)
        else:
            # Estimate from severity if no CVSS
            cvss_normalized = self._estimate_cvss_from_severity(severity)
            all_factors.append(f"CVSS estimated from severity: {severity}")
        
        all_factors.append(f"CVSS Score: {cvss_normalized}")
        
        # 2. Exploitability Score (0-10)
        exploitability_score, exploit_factors = self.cvss_interpreter.calculate_exploitability_score(
            cvss_score=cvss_normalized,
            vector_string=cvss_vector,
            exploit_maturity=exploit_maturity,
            is_actively_exploited=is_actively_exploited,
            has_public_exploit=has_public_exploit,
        )
        all_factors.extend(exploit_factors)
        
        # 3. Business Impact Score (0-10)
        if business_context:
            business_score, business_factors = self.business_analyzer.analyze(business_context)
            all_factors.extend(business_factors)
        else:
            # Infer context if not provided
            inferred_context = self.business_analyzer.infer_context_from_repository(repository)
            business_score, business_factors = self.business_analyzer.analyze(inferred_context)
            all_factors.append("Business context inferred from repository name")
            all_factors.extend(business_factors)
            business_context = inferred_context
        
        # 4. Data Sensitivity Score (0-10)
        data_sensitivity_score = self._calculate_data_sensitivity_score(business_context)
        all_factors.append(f"Data sensitivity score: {data_sensitivity_score:.1f}")
        
        # Calculate weighted total score
        total_score = (
            (cvss_normalized * self.weight_cvss) +
            (exploitability_score * self.weight_exploitability) +
            (business_score * self.weight_business_impact) +
            (data_sensitivity_score * self.weight_data_sensitivity)
        )
        
        # Apply critical modifiers
        total_score = self._apply_critical_modifiers(
            total_score,
            is_actively_exploited=is_actively_exploited,
            cvss_score=cvss_normalized,
            business_context=business_context,
            factors=all_factors,
        )
        
        # Normalize to 0-10
        total_score = min(10.0, max(0.0, total_score))
        
        # Determine priority
        priority = self._score_to_priority(total_score)
        
        # Create risk score
        risk_score = RiskScore(
            cvss_score=cvss_normalized,
            exploitability_score=exploitability_score,
            business_impact_score=business_score,
            data_sensitivity_score=data_sensitivity_score,
            total_score=total_score,
            priority=priority,
            factors=all_factors,
            ai_analysis=ai_analysis,
        )
        
        # Determine urgency and action
        urgency, action = self._determine_action(priority, vulnerability, business_context)
        
        # Create full assessment
        assessment = RiskAssessment(
            vulnerability_id=vuln_id,
            cve_id=cve_id,
            title=title,
            severity=severity,
            cvss_score=cvss_normalized,
            business_context=business_context,
            risk_score=risk_score,
            remediation_urgency=urgency,
            recommended_action=action,
            estimated_effort=self._estimate_effort(vulnerability),
        )
        
        logger.info(
            "Priority calculated",
            vulnerability_id=vuln_id,
            priority=priority.value,
            total_score=total_score,
        )
        
        return assessment
    
    def calculate_batch(
        self,
        vulnerabilities: List[Dict[str, Any]],
        business_context: Optional[BusinessContext] = None,
    ) -> List[RiskAssessment]:
        """Calculate priorities for multiple vulnerabilities."""
        
        assessments = []
        
        for vuln in vulnerabilities:
            assessment = self.calculate(
                vulnerability=vuln,
                business_context=business_context,
            )
            assessments.append(assessment)
        
        # Sort by priority (P0 first) and then by total score (highest first)
        assessments.sort(
            key=lambda a: (
                list(Priority).index(a.risk_score.priority),
                -a.risk_score.total_score,
            )
        )
        
        return assessments
    
    def _estimate_cvss_from_severity(self, severity: str) -> float:
        """Estimate CVSS score from severity label."""
        
        severity_cvss_map = {
            "critical": 9.5,
            "high": 7.5,
            "medium": 5.5,
            "low": 2.5,
            "unknown": 5.0,
        }
        
        return severity_cvss_map.get(severity.lower(), 5.0)
    
    def _calculate_data_sensitivity_score(self, context: BusinessContext) -> float:
        """Calculate data sensitivity score from business context."""
        
        from models import DataSensitivity
        
        sensitivity_scores = {
            DataSensitivity.PUBLIC: 1.0,
            DataSensitivity.INTERNAL: 3.0,
            DataSensitivity.CONFIDENTIAL: 5.0,
            DataSensitivity.PII: 8.0,
            DataSensitivity.PHI: 9.0,
            DataSensitivity.PCI: 9.0,
            DataSensitivity.CRITICAL: 10.0,
        }
        
        base_score = sensitivity_scores.get(context.data_sensitivity, 5.0)
        
        # Modifiers
        if context.handles_pii:
            base_score = max(base_score, 8.0)
        if context.handles_financial_data:
            base_score = max(base_score, 8.5)
        if context.handles_health_data:
            base_score = max(base_score, 9.0)
        
        return min(10.0, base_score)
    
    def _apply_critical_modifiers(
        self,
        score: float,
        is_actively_exploited: bool,
        cvss_score: float,
        business_context: BusinessContext,
        factors: List[str],
    ) -> float:
        """Apply modifiers that can force higher priority."""
        
        modified_score = score
        
        # Actively exploited vulnerabilities are always critical
        if is_actively_exploited:
            modified_score = max(modified_score, 9.5)
            factors.append("CRITICAL: Actively exploited - automatic P0")
        
        # Critical CVSS on public-facing services
        if cvss_score >= 9.0 and business_context.is_public_facing:
            modified_score = max(modified_score, 9.0)
            factors.append("Critical CVSS on public-facing service")
        
        # PCI/PHI compliance with high severity
        if business_context.compliance_requirements:
            high_compliance = any(
                c.upper() in ["PCI-DSS", "HIPAA", "PCI", "PHI"]
                for c in business_context.compliance_requirements
            )
            if high_compliance and cvss_score >= 7.0:
                modified_score = max(modified_score, 8.0)
                factors.append("High severity in compliance-regulated service")
        
        return modified_score
    
    def _score_to_priority(self, score: float) -> Priority:
        """Convert total score to priority level."""
        
        if score >= self.priority_thresholds[Priority.P0]:
            return Priority.P0
        elif score >= self.priority_thresholds[Priority.P1]:
            return Priority.P1
        elif score >= self.priority_thresholds[Priority.P2]:
            return Priority.P2
        elif score >= self.priority_thresholds[Priority.P3]:
            return Priority.P3
        else:
            return Priority.P4
    
    def _determine_action(
        self,
        priority: Priority,
        vulnerability: Dict[str, Any],
        business_context: BusinessContext,
    ) -> Tuple[str, str]:
        """Determine urgency and recommended action."""
        
        actions = {
            Priority.P0: (
                "immediate",
                "IMMEDIATE ACTION REQUIRED: Escalate to security team. "
                "Consider emergency patch or mitigation. "
                "Notify stakeholders within 1 hour."
            ),
            Priority.P1: (
                "urgent",
                "Fix within 24 hours. Create high-priority ticket. "
                "Assign to senior developer. Consider temporary mitigation."
            ),
            Priority.P2: (
                "normal",
                "Fix within 1 week. Add to current sprint if possible. "
                "Standard code review and testing required."
            ),
            Priority.P3: (
                "low",
                "Fix within 1 month. Add to backlog. "
                "Can be addressed in regular maintenance cycle."
            ),
            Priority.P4: (
                "informational",
                "Track for awareness. No immediate action required. "
                "Review during next security assessment."
            ),
        }
        
        urgency, base_action = actions.get(priority, ("normal", "Review and address"))
        
        # Add specific recommendations based on vulnerability type
        fix_recommendation = vulnerability.get("fix_recommendation", "")
        if fix_recommendation:
            base_action += f" Recommended fix: {fix_recommendation}"
        
        return urgency, base_action
    
    def _estimate_effort(self, vulnerability: Dict[str, Any]) -> str:
        """Estimate remediation effort."""
        
        # This is a simplified estimation
        # In reality, this would consider:
        # - Type of vulnerability
        # - Complexity of fix
        # - Test coverage required
        # - Number of affected files
        
        severity = vulnerability.get("severity", "medium").lower()
        
        effort_estimates = {
            "critical": "2-4 hours (emergency)",
            "high": "4-8 hours",
            "medium": "2-4 hours",
            "low": "1-2 hours",
        }
        
        return effort_estimates.get(severity, "2-4 hours")
    
    def get_summary(self, assessments: List[RiskAssessment]) -> Dict[str, Any]:
        """Generate summary statistics for a batch of assessments."""
        
        summary = {
            "total": len(assessments),
            "by_priority": {
                "P0": 0,
                "P1": 0,
                "P2": 0,
                "P3": 0,
                "P4": 0,
            },
            "average_score": 0.0,
            "highest_score": 0.0,
            "immediate_action_required": 0,
        }
        
        if not assessments:
            return summary
        
        total_score = 0.0
        
        for assessment in assessments:
            priority = assessment.risk_score.priority.value
            summary["by_priority"][priority] += 1
            total_score += assessment.risk_score.total_score
            
            if assessment.risk_score.total_score > summary["highest_score"]:
                summary["highest_score"] = assessment.risk_score.total_score
            
            if assessment.remediation_urgency == "immediate":
                summary["immediate_action_required"] += 1
        
        summary["average_score"] = total_score / len(assessments)
        
        return summary
