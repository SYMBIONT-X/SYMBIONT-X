"""Data models for Risk Assessment Agent."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Vulnerability priority levels."""
    P0 = "P0"  # Critical - Immediate action required
    P1 = "P1"  # High - Fix within 24 hours
    P2 = "P2"  # Medium - Fix within 1 week
    P3 = "P3"  # Low - Fix within 1 month
    P4 = "P4"  # Informational - Track only


class ServiceType(str, Enum):
    """Type of service affected."""
    PUBLIC_API = "public_api"
    INTERNAL_API = "internal_api"
    WEB_APPLICATION = "web_application"
    BACKEND_SERVICE = "backend_service"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    UNKNOWN = "unknown"


class DataSensitivity(str, Enum):
    """Data sensitivity classification."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PII = "pii"  # Personally Identifiable Information
    PHI = "phi"  # Protected Health Information
    PCI = "pci"  # Payment Card Industry data
    CRITICAL = "critical"


class ExploitMaturity(str, Enum):
    """Exploit maturity level."""
    NOT_DEFINED = "not_defined"
    UNPROVEN = "unproven"
    POC = "proof_of_concept"
    FUNCTIONAL = "functional"
    HIGH = "high"


class BusinessContext(BaseModel):
    """Business context for a service/repository."""
    
    repository: str = Field(..., description="Repository name")
    service_name: Optional[str] = Field(None, description="Service name")
    service_type: ServiceType = Field(default=ServiceType.UNKNOWN)
    
    # Exposure
    is_public_facing: bool = Field(default=False)
    is_internet_exposed: bool = Field(default=False)
    
    # Data classification
    data_sensitivity: DataSensitivity = Field(default=DataSensitivity.INTERNAL)
    handles_pii: bool = Field(default=False)
    handles_financial_data: bool = Field(default=False)
    handles_health_data: bool = Field(default=False)
    
    # Business impact
    business_criticality: int = Field(default=5, ge=1, le=10, description="1-10 scale")
    revenue_impact: bool = Field(default=False, description="Direct revenue impact if down")
    customer_facing: bool = Field(default=False)
    
    # Compliance
    compliance_requirements: List[str] = Field(default_factory=list)
    
    # Dependencies
    dependent_services: List[str] = Field(default_factory=list)
    dependency_count: int = Field(default=0)
    
    class Config:
        use_enum_values = True


class RiskScore(BaseModel):
    """Calculated risk score for a vulnerability."""
    
    # Component scores (0-10)
    cvss_score: float = Field(..., ge=0, le=10)
    exploitability_score: float = Field(default=5.0, ge=0, le=10)
    business_impact_score: float = Field(default=5.0, ge=0, le=10)
    data_sensitivity_score: float = Field(default=5.0, ge=0, le=10)
    
    # Calculated total (0-10)
    total_score: float = Field(..., ge=0, le=10)
    
    # Final priority
    priority: Priority
    
    # Reasoning
    factors: List[str] = Field(default_factory=list)
    ai_analysis: Optional[str] = Field(None)


class RiskAssessment(BaseModel):
    """Complete risk assessment for a vulnerability."""
    
    # Vulnerability info
    vulnerability_id: str
    cve_id: Optional[str] = None
    title: str
    severity: str
    
    # Original CVSS
    cvss_score: Optional[float] = None
    
    # Business context
    business_context: Optional[BusinessContext] = None
    
    # Calculated risk
    risk_score: RiskScore
    
    # Recommendations
    remediation_urgency: str = Field(default="normal")
    recommended_action: str = Field(default="")
    estimated_effort: Optional[str] = Field(None)
    
    # Metadata
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    assessed_by: str = Field(default="risk-assessment-agent")
    
    class Config:
        use_enum_values = True


class AssessmentRequest(BaseModel):
    """Request to assess vulnerabilities."""
    
    vulnerabilities: List[Dict[str, Any]] = Field(..., description="List of vulnerabilities to assess")
    repository: str = Field(..., description="Repository name")
    business_context: Optional[BusinessContext] = Field(None)
    use_ai_analysis: bool = Field(default=True)


class AssessmentResponse(BaseModel):
    """Response with risk assessments."""
    
    assessment_id: str
    repository: str
    total_assessed: int
    assessments: List[RiskAssessment]
    summary: Dict[str, int]  # Priority counts
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
