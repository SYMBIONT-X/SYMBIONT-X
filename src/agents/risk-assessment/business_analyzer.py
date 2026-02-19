"""Business context analysis for risk assessment."""

from typing import Optional, Dict, List, Tuple
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from models import BusinessContext, DataSensitivity, ServiceType


logger = get_logger("business-analyzer")


class BusinessContextAnalyzer:
    """Analyzes business context to determine risk impact."""
    
    def __init__(self):
        # Data sensitivity scores (0-10)
        self.sensitivity_scores = {
            DataSensitivity.PUBLIC: 1.0,
            DataSensitivity.INTERNAL: 3.0,
            DataSensitivity.CONFIDENTIAL: 5.0,
            DataSensitivity.PII: 8.0,
            DataSensitivity.PHI: 9.0,
            DataSensitivity.PCI: 9.0,
            DataSensitivity.CRITICAL: 10.0,
        }
        
        # Service type exposure scores (0-10)
        self.service_exposure_scores = {
            ServiceType.PUBLIC_API: 9.0,
            ServiceType.WEB_APPLICATION: 8.0,
            ServiceType.INTERNAL_API: 5.0,
            ServiceType.BACKEND_SERVICE: 4.0,
            ServiceType.DATABASE: 7.0,
            ServiceType.INFRASTRUCTURE: 6.0,
            ServiceType.UNKNOWN: 5.0,
        }
        
        # Compliance penalty multipliers
        self.compliance_penalties = {
            "PCI-DSS": 1.3,
            "HIPAA": 1.3,
            "GDPR": 1.2,
            "SOC2": 1.1,
            "ISO27001": 1.1,
            "FedRAMP": 1.2,
        }
    
    def analyze(self, context: BusinessContext) -> Tuple[float, List[str]]:
        """
        Analyze business context and return impact score.
        
        Returns: (score 0-10, list of factors)
        """
        
        factors = []
        scores = []
        
        # 1. Data sensitivity analysis
        sensitivity_score = self._analyze_data_sensitivity(context)
        scores.append(("data_sensitivity", sensitivity_score[0], 0.3))
        factors.extend(sensitivity_score[1])
        
        # 2. Service exposure analysis
        exposure_score = self._analyze_exposure(context)
        scores.append(("exposure", exposure_score[0], 0.25))
        factors.extend(exposure_score[1])
        
        # 3. Business criticality analysis
        criticality_score = self._analyze_criticality(context)
        scores.append(("criticality", criticality_score[0], 0.25))
        factors.extend(criticality_score[1])
        
        # 4. Compliance impact analysis
        compliance_score = self._analyze_compliance(context)
        scores.append(("compliance", compliance_score[0], 0.2))
        factors.extend(compliance_score[1])
        
        # Calculate weighted average
        total_score = sum(score * weight for _, score, weight in scores)
        
        # Normalize to 0-10
        final_score = min(10.0, max(0.0, total_score))
        
        logger.info(
            "Business context analyzed",
            repository=context.repository,
            score=final_score,
            factors_count=len(factors),
        )
        
        return final_score, factors
    
    def _analyze_data_sensitivity(self, context: BusinessContext) -> Tuple[float, List[str]]:
        """Analyze data sensitivity factors."""
        
        factors = []
        base_score = self.sensitivity_scores.get(context.data_sensitivity, 5.0)
        
        factors.append(f"Data sensitivity: {context.data_sensitivity}")
        
        # Additional modifiers
        if context.handles_pii:
            base_score = max(base_score, 8.0)
            factors.append("Handles PII (Personally Identifiable Information)")
        
        if context.handles_financial_data:
            base_score = max(base_score, 8.5)
            factors.append("Handles financial data")
        
        if context.handles_health_data:
            base_score = max(base_score, 9.0)
            factors.append("Handles health data (PHI)")
        
        return base_score, factors
    
    def _analyze_exposure(self, context: BusinessContext) -> Tuple[float, List[str]]:
        """Analyze service exposure factors."""
        
        factors = []
        base_score = self.service_exposure_scores.get(context.service_type, 5.0)
        
        factors.append(f"Service type: {context.service_type}")
        
        if context.is_public_facing:
            base_score = max(base_score, 8.0)
            factors.append("Public-facing service")
        
        if context.is_internet_exposed:
            base_score += 1.0
            factors.append("Internet-exposed")
        
        if context.customer_facing:
            base_score += 0.5
            factors.append("Customer-facing application")
        
        return min(10.0, base_score), factors
    
    def _analyze_criticality(self, context: BusinessContext) -> Tuple[float, List[str]]:
        """Analyze business criticality factors."""
        
        factors = []
        
        # Start with defined criticality (1-10)
        base_score = float(context.business_criticality)
        factors.append(f"Business criticality rating: {context.business_criticality}/10")
        
        # Revenue impact
        if context.revenue_impact:
            base_score += 1.5
            factors.append("Direct revenue impact if compromised")
        
        # Dependent services
        if context.dependency_count > 10:
            base_score += 1.0
            factors.append(f"High dependency count: {context.dependency_count} services depend on this")
        elif context.dependency_count > 5:
            base_score += 0.5
            factors.append(f"Moderate dependency count: {context.dependency_count} services")
        
        return min(10.0, base_score), factors
    
    def _analyze_compliance(self, context: BusinessContext) -> Tuple[float, List[str]]:
        """Analyze compliance requirement factors."""
        
        factors = []
        base_score = 3.0  # Default low compliance concern
        
        if not context.compliance_requirements:
            factors.append("No specific compliance requirements identified")
            return base_score, factors
        
        # Apply compliance penalties
        max_penalty = 1.0
        for compliance in context.compliance_requirements:
            penalty = self.compliance_penalties.get(compliance.upper(), 1.0)
            if penalty > max_penalty:
                max_penalty = penalty
            factors.append(f"Compliance requirement: {compliance}")
        
        # Higher compliance = higher risk if vulnerability exists
        base_score = 5.0 * max_penalty
        
        if len(context.compliance_requirements) > 2:
            base_score += 1.0
            factors.append("Multiple compliance frameworks apply")
        
        return min(10.0, base_score), factors
    
    def infer_context_from_repository(self, repository: str) -> BusinessContext:
        """
        Infer basic business context from repository name/path.
        This is a fallback when no explicit context is provided.
        """
        
        repo_lower = repository.lower()
        
        # Default context
        context = BusinessContext(
            repository=repository,
            service_type=ServiceType.UNKNOWN,
            data_sensitivity=DataSensitivity.INTERNAL,
            business_criticality=5,
        )
        
        # Infer service type from name
        if any(x in repo_lower for x in ["api", "service", "backend"]):
            if any(x in repo_lower for x in ["public", "external", "gateway"]):
                context.service_type = ServiceType.PUBLIC_API
                context.is_public_facing = True
            else:
                context.service_type = ServiceType.INTERNAL_API
        elif any(x in repo_lower for x in ["web", "frontend", "ui", "portal"]):
            context.service_type = ServiceType.WEB_APPLICATION
            context.is_public_facing = True
            context.customer_facing = True
        elif any(x in repo_lower for x in ["db", "database", "data"]):
            context.service_type = ServiceType.DATABASE
        elif any(x in repo_lower for x in ["infra", "terraform", "deploy"]):
            context.service_type = ServiceType.INFRASTRUCTURE
        
        # Infer data sensitivity
        if any(x in repo_lower for x in ["payment", "billing", "finance"]):
            context.data_sensitivity = DataSensitivity.PCI
            context.handles_financial_data = True
        elif any(x in repo_lower for x in ["health", "medical", "patient"]):
            context.data_sensitivity = DataSensitivity.PHI
            context.handles_health_data = True
        elif any(x in repo_lower for x in ["user", "customer", "profile", "auth"]):
            context.data_sensitivity = DataSensitivity.PII
            context.handles_pii = True
        
        # Infer criticality
        if any(x in repo_lower for x in ["core", "critical", "main", "platform"]):
            context.business_criticality = 8
        elif any(x in repo_lower for x in ["internal", "tool", "util"]):
            context.business_criticality = 4
        
        logger.info(
            "Inferred business context",
            repository=repository,
            service_type=context.service_type,
            data_sensitivity=context.data_sensitivity,
        )
        
        return context
    
    def calculate_financial_impact_estimate(
        self,
        context: BusinessContext,
        severity: str,
    ) -> Dict[str, str]:
        """
        Estimate potential financial impact of a vulnerability.
        This is a rough estimate for prioritization purposes.
        """
        
        base_impacts = {
            "critical": {"low": "$100K", "medium": "$500K", "high": "$1M+"},
            "high": {"low": "$50K", "medium": "$200K", "high": "$500K"},
            "medium": {"low": "$10K", "medium": "$50K", "high": "$100K"},
            "low": {"low": "$1K", "medium": "$10K", "high": "$25K"},
        }
        
        severity_impacts = base_impacts.get(severity.lower(), base_impacts["medium"])
        
        # Determine impact level based on context
        if context.handles_pii or context.handles_financial_data:
            impact_level = "high"
        elif context.is_public_facing or context.revenue_impact:
            impact_level = "medium"
        else:
            impact_level = "low"
        
        estimate = severity_impacts.get(impact_level, "$50K")
        
        return {
            "estimate": estimate,
            "level": impact_level,
            "factors": [
                f"Severity: {severity}",
                f"Public facing: {context.is_public_facing}",
                f"Handles sensitive data: {context.handles_pii or context.handles_financial_data}",
            ],
        }
