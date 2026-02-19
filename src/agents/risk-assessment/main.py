"""Risk Assessment Agent - Main entry point."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import uuid

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from shared.utils import setup_logging, get_logger
from config import settings
from models import (
    BusinessContext,
    RiskAssessment,
    AssessmentRequest,
    AssessmentResponse,
    Priority,
    ServiceType,
    DataSensitivity,
)
from priority_calculator import PriorityCalculator
from ai_analyzer import AIAnalyzer


# Setup logging
setup_logging(level=settings.log_level, json_format=settings.log_json)
logger = get_logger("risk-assessment")


# Initialize FastAPI app
app = FastAPI(
    title="SYMBIONT-X Risk Assessment Agent",
    description="AI-powered vulnerability prioritization and risk analysis",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
priority_calculator = PriorityCalculator()
ai_analyzer = AIAnalyzer()


# ----- Request/Response Models -----

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent: str
    version: str
    ai_enabled: bool
    timestamp: str


class SingleVulnerabilityRequest(BaseModel):
    """Request to assess a single vulnerability."""
    vulnerability: dict = Field(..., description="Vulnerability data")
    repository: str = Field(..., description="Repository name")
    business_context: Optional[BusinessContext] = Field(None)
    use_ai_analysis: bool = Field(default=True)


class BusinessContextRequest(BaseModel):
    """Request to register/update business context."""
    repository: str
    service_name: Optional[str] = None
    service_type: ServiceType = ServiceType.UNKNOWN
    is_public_facing: bool = False
    is_internet_exposed: bool = False
    data_sensitivity: DataSensitivity = DataSensitivity.INTERNAL
    handles_pii: bool = False
    handles_financial_data: bool = False
    handles_health_data: bool = False
    business_criticality: int = Field(default=5, ge=1, le=10)
    revenue_impact: bool = False
    customer_facing: bool = False
    compliance_requirements: List[str] = Field(default_factory=list)
    dependent_services: List[str] = Field(default_factory=list)


class SummaryRequest(BaseModel):
    """Request for executive summary."""
    assessments: List[dict] = Field(..., description="List of assessment results")
    repository: str
    business_context: Optional[BusinessContext] = None


# ----- In-memory storage (would be Cosmos DB in production) -----

assessments_store: dict = {}
business_contexts_store: dict = {}


# ----- API Endpoints -----

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check agent health and capabilities."""
    return HealthResponse(
        status="healthy",
        agent=settings.agent_name,
        version=settings.agent_version,
        ai_enabled=ai_analyzer.is_available(),
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/assess", response_model=AssessmentResponse)
async def assess_vulnerabilities(request: AssessmentRequest):
    """
    Assess a batch of vulnerabilities and calculate priorities.
    
    This is the main endpoint for vulnerability risk assessment.
    """
    
    assessment_id = str(uuid.uuid4())
    
    logger.info(
        "Assessment requested",
        assessment_id=assessment_id,
        repository=request.repository,
        vulnerability_count=len(request.vulnerabilities),
    )
    
    try:
        # Get or create business context
        business_context = request.business_context
        if not business_context:
            # Check if we have stored context
            if request.repository in business_contexts_store:
                business_context = business_contexts_store[request.repository]
            else:
                # Infer from repository name
                business_context = priority_calculator.business_analyzer.infer_context_from_repository(
                    request.repository
                )
        
        # Get AI analysis if enabled
        ai_analyses = {}
        if request.use_ai_analysis and ai_analyzer.is_available():
            ai_analyses = await ai_analyzer.analyze_batch(
                request.vulnerabilities,
                business_context,
            )
        
        # Calculate priorities
        assessments = []
        for vuln in request.vulnerabilities:
            vuln_id = vuln.get("id", "unknown")
            ai_analysis = ai_analyses.get(vuln_id)
            
            assessment = priority_calculator.calculate(
                vulnerability=vuln,
                business_context=business_context,
                ai_analysis=ai_analysis,
            )
            assessments.append(assessment)
        
        # Sort by priority
        assessments.sort(
            key=lambda a: (
                list(Priority).index(a.risk_score.priority),
                -a.risk_score.total_score,
            )
        )
        
        # Generate summary
        summary = priority_calculator.get_summary(assessments)
        
        # Store results
        response = AssessmentResponse(
            assessment_id=assessment_id,
            repository=request.repository,
            total_assessed=len(assessments),
            assessments=assessments,
            summary=summary["by_priority"],
        )
        
        assessments_store[assessment_id] = response
        
        logger.info(
            "Assessment completed",
            assessment_id=assessment_id,
            total=len(assessments),
            p0_count=summary["by_priority"]["P0"],
            p1_count=summary["by_priority"]["P1"],
        )
        
        return response
        
    except Exception as e:
        logger.error("Assessment failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assess/single", response_model=RiskAssessment)
async def assess_single_vulnerability(request: SingleVulnerabilityRequest):
    """Assess a single vulnerability."""
    
    logger.info(
        "Single assessment requested",
        vulnerability_id=request.vulnerability.get("id"),
        repository=request.repository,
    )
    
    try:
        # Get business context
        business_context = request.business_context
        if not business_context and request.repository in business_contexts_store:
            business_context = business_contexts_store[request.repository]
        
        # Get AI analysis if enabled
        ai_analysis = None
        if request.use_ai_analysis and ai_analyzer.is_available():
            ai_analysis = await ai_analyzer.analyze_vulnerability(
                request.vulnerability,
                business_context,
            )
        
        # Calculate priority
        assessment = priority_calculator.calculate(
            vulnerability=request.vulnerability,
            business_context=business_context,
            ai_analysis=ai_analysis,
        )
        
        return assessment
        
    except Exception as e:
        logger.error("Single assessment failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assessment/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(assessment_id: str):
    """Get a previous assessment result."""
    
    if assessment_id not in assessments_store:
        raise HTTPException(status_code=404, detail=f"Assessment not found: {assessment_id}")
    
    return assessments_store[assessment_id]


@app.post("/context", response_model=BusinessContext)
async def register_business_context(request: BusinessContextRequest):
    """
    Register or update business context for a repository.
    
    This context will be used for all future assessments of this repository.
    """
    
    context = BusinessContext(
        repository=request.repository,
        service_name=request.service_name,
        service_type=request.service_type,
        is_public_facing=request.is_public_facing,
        is_internet_exposed=request.is_internet_exposed,
        data_sensitivity=request.data_sensitivity,
        handles_pii=request.handles_pii,
        handles_financial_data=request.handles_financial_data,
        handles_health_data=request.handles_health_data,
        business_criticality=request.business_criticality,
        revenue_impact=request.revenue_impact,
        customer_facing=request.customer_facing,
        compliance_requirements=request.compliance_requirements,
        dependent_services=request.dependent_services,
        dependency_count=len(request.dependent_services),
    )
    
    business_contexts_store[request.repository] = context
    
    logger.info(
        "Business context registered",
        repository=request.repository,
        service_type=context.service_type,
    )
    
    return context


@app.get("/context/{repository}")
async def get_business_context(repository: str):
    """Get business context for a repository."""
    
    if repository in business_contexts_store:
        return business_contexts_store[repository]
    
    # Return inferred context
    return priority_calculator.business_analyzer.infer_context_from_repository(repository)


@app.post("/summary")
async def generate_executive_summary(request: SummaryRequest):
    """Generate an executive summary for assessments."""
    
    if not ai_analyzer.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI analysis not available - no API key configured",
        )
    
    # Convert dicts back to RiskAssessment objects
    assessments = []
    for a in request.assessments:
        try:
            assessment = RiskAssessment(**a)
            assessments.append(assessment)
        except Exception:
            pass
    
    summary = await ai_analyzer.generate_executive_summary(
        assessments,
        request.business_context,
    )
    
    return {
        "summary": summary,
        "repository": request.repository,
        "generated_at": datetime.utcnow().isoformat(),
    }


@app.post("/remediation/{vulnerability_id}")
async def get_remediation_suggestions(vulnerability_id: str, vulnerability: dict):
    """Get AI-powered remediation suggestions for a vulnerability."""
    
    if not ai_analyzer.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI analysis not available - no API key configured",
        )
    
    suggestion = await ai_analyzer.suggest_remediation(vulnerability)
    
    return {
        "vulnerability_id": vulnerability_id,
        "remediation": suggestion,
        "generated_at": datetime.utcnow().isoformat(),
    }


@app.get("/priorities")
async def get_priority_definitions():
    """Get priority level definitions and thresholds."""
    
    return {
        "priorities": [
            {
                "level": "P0",
                "name": "Critical",
                "description": "Immediate action required",
                "sla": "Fix within 4 hours",
                "threshold": "Score >= 9.0",
            },
            {
                "level": "P1",
                "name": "High",
                "description": "Urgent attention needed",
                "sla": "Fix within 24 hours",
                "threshold": "Score >= 7.0",
            },
            {
                "level": "P2",
                "name": "Medium",
                "description": "Standard priority",
                "sla": "Fix within 1 week",
                "threshold": "Score >= 4.0",
            },
            {
                "level": "P3",
                "name": "Low",
                "description": "Can be scheduled",
                "sla": "Fix within 1 month",
                "threshold": "Score >= 2.0",
            },
            {
                "level": "P4",
                "name": "Informational",
                "description": "Track only",
                "sla": "No SLA",
                "threshold": "Score < 2.0",
            },
        ],
        "weights": {
            "cvss": settings.weight_cvss,
            "exploitability": settings.weight_exploitability,
            "business_impact": settings.weight_business_impact,
            "data_sensitivity": settings.weight_data_sensitivity,
        },
    }


# ----- Main Entry Point -----

def main():
    """Start the Risk Assessment Agent."""
    logger.info(
        "Starting Risk Assessment Agent",
        host=settings.host,
        port=settings.port,
        ai_enabled=ai_analyzer.is_available(),
    )
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
