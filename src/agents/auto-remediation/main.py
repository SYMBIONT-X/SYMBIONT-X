"""Auto-Remediation Agent - Main entry point."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from shared.utils import setup_logging, get_logger
from config import settings
from models import (
    GeneratedFix,
    RemediationRequest,
    RemediationResponse,
    PullRequestInfo,
    FixStatus,
    FixType,
)
from fix_generator import FixGenerator
from github_pr_creator import GitHubPRCreator


# Setup logging
setup_logging(level=settings.log_level, json_format=settings.log_json)
logger = get_logger("auto-remediation")


# Initialize FastAPI
app = FastAPI(
    title="SYMBIONT-X Auto-Remediation Agent",
    description="Automated vulnerability fixes and PR creation",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
fix_generator = FixGenerator()
pr_creator = GitHubPRCreator()


# ----- Request/Response Models -----

class HealthResponse(BaseModel):
    status: str
    agent: str
    version: str
    github_enabled: bool
    ai_enabled: bool
    templates_count: int
    timestamp: str


class BatchRemediationRequest(BaseModel):
    vulnerabilities: List[Dict[str, Any]]
    repository: str
    branch: str = "main"
    auto_create_pr: bool = True
    priority_filter: Optional[List[str]] = None


class BatchRemediationResponse(BaseModel):
    batch_id: str
    total_vulnerabilities: int
    fixes_generated: int
    prs_created: int
    results: List[RemediationResponse]


class TemplateListResponse(BaseModel):
    total: int
    templates: List[Dict[str, Any]]


# ----- In-memory storage -----

remediation_store: Dict[str, RemediationResponse] = {}
batch_store: Dict[str, BatchRemediationResponse] = {}


# ----- API Endpoints -----

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check agent health and capabilities."""
    
    stats = fix_generator.get_fix_stats()
    
    return HealthResponse(
        status="healthy",
        agent=settings.agent_name,
        version=settings.agent_version,
        github_enabled=pr_creator.is_available(),
        ai_enabled=stats["ai_enabled"],
        templates_count=stats["total_templates"],
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/remediate", response_model=RemediationResponse)
async def remediate_vulnerability(
    request: RemediationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Generate a fix for a single vulnerability.
    
    Optionally creates a PR if auto_create_pr is True.
    """
    
    remediation_id = str(uuid.uuid4())
    vuln_id = request.vulnerability.get("id", "unknown")
    
    logger.info(
        "Remediation requested",
        remediation_id=remediation_id,
        vulnerability_id=vuln_id,
        repository=request.repository,
    )
    
    try:
        # Generate fix
        fix = fix_generator.generate_fix(
            vulnerability=request.vulnerability,
            use_ai=True,
        )
        
        # Create response
        response = RemediationResponse(
            remediation_id=remediation_id,
            vulnerability_id=vuln_id,
            status=fix.status,
            fix=fix,
            message=f"Fix generated: {fix.title}",
        )
        
        # Create PR if requested
        if request.auto_create_pr and fix.status == FixStatus.READY:
            if pr_creator.is_available():
                background_tasks.add_task(
                    create_pr_background,
                    remediation_id=remediation_id,
                    fix=fix,
                    repository=request.repository,
                    branch=request.branch,
                )
                response.message += " (PR creation in progress)"
            else:
                response.message += " (GitHub not configured - PR not created)"
        
        # Store result
        remediation_store[remediation_id] = response
        
        return response
        
    except Exception as e:
        logger.error("Remediation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/remediate/batch", response_model=BatchRemediationResponse)
async def remediate_batch(
    request: BatchRemediationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Generate fixes for multiple vulnerabilities.
    """
    
    batch_id = str(uuid.uuid4())
    
    logger.info(
        "Batch remediation requested",
        batch_id=batch_id,
        vulnerability_count=len(request.vulnerabilities),
        repository=request.repository,
    )
    
    results = []
    prs_created = 0
    
    for vuln in request.vulnerabilities:
        # Filter by priority if specified
        if request.priority_filter:
            vuln_priority = vuln.get("priority", "P2")
            if vuln_priority not in request.priority_filter:
                continue
        
        remediation_id = str(uuid.uuid4())
        vuln_id = vuln.get("id", "unknown")
        
        try:
            # Generate fix
            fix = fix_generator.generate_fix(vulnerability=vuln)
            
            response = RemediationResponse(
                remediation_id=remediation_id,
                vulnerability_id=vuln_id,
                status=fix.status,
                fix=fix,
                message=f"Fix generated: {fix.title}",
            )
            
            # Create PR if requested and fix is ready
            if (request.auto_create_pr and 
                fix.status == FixStatus.READY and 
                pr_creator.is_available()):
                
                pr_info = await pr_creator.create_pr_for_fix(
                    fix=fix,
                    repository=request.repository,
                    base_branch=request.branch,
                )
                
                if pr_info:
                    response.pr_info = pr_info
                    response.status = FixStatus.PR_CREATED
                    prs_created += 1
            
            results.append(response)
            
        except Exception as e:
            logger.error("Fix generation failed", vuln_id=vuln_id, error=str(e))
            results.append(RemediationResponse(
                remediation_id=remediation_id,
                vulnerability_id=vuln_id,
                status=FixStatus.FAILED,
                message=str(e),
            ))
    
    batch_response = BatchRemediationResponse(
        batch_id=batch_id,
        total_vulnerabilities=len(request.vulnerabilities),
        fixes_generated=sum(1 for r in results if r.fix is not None),
        prs_created=prs_created,
        results=results,
    )
    
    batch_store[batch_id] = batch_response
    
    logger.info(
        "Batch remediation completed",
        batch_id=batch_id,
        fixes_generated=batch_response.fixes_generated,
        prs_created=prs_created,
    )
    
    return batch_response


@app.get("/remediation/{remediation_id}", response_model=RemediationResponse)
async def get_remediation(remediation_id: str):
    """Get status of a remediation."""
    
    if remediation_id not in remediation_store:
        raise HTTPException(status_code=404, detail="Remediation not found")
    
    return remediation_store[remediation_id]


@app.get("/batch/{batch_id}", response_model=BatchRemediationResponse)
async def get_batch(batch_id: str):
    """Get status of a batch remediation."""
    
    if batch_id not in batch_store:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return batch_store[batch_id]


@app.get("/templates", response_model=TemplateListResponse)
async def list_templates():
    """List all available fix templates."""
    
    templates = fix_generator.template_engine.get_all_templates()
    
    template_list = []
    for tid, template in templates.items():
        template_list.append({
            "id": tid,
            "name": template.get("name", tid),
            "description": template.get("description", ""),
            "fix_type": template.get("fix_type", "unknown"),
            "confidence": template.get("confidence", "medium"),
            "applicable_to": template.get("applicable_to", []),
        })
    
    return TemplateListResponse(
        total=len(template_list),
        templates=template_list,
    )


@app.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get a specific template."""
    
    template = fix_generator.template_engine.get_template_by_id(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@app.post("/preview")
async def preview_fix(request: RemediationRequest):
    """
    Preview a fix without creating a PR.
    
    Useful for reviewing changes before applying.
    """
    
    fix = fix_generator.generate_fix(
        vulnerability=request.vulnerability,
        use_ai=True,
    )
    
    return {
        "fix": fix,
        "preview_only": True,
        "message": "This is a preview. Use /remediate to create a PR.",
    }


@app.get("/stats")
async def get_stats():
    """Get agent statistics."""
    
    fix_stats = fix_generator.get_fix_stats()
    
    return {
        "fix_generator": fix_stats,
        "remediations": {
            "total": len(remediation_store),
            "by_status": _count_by_status(remediation_store),
        },
        "batches": {
            "total": len(batch_store),
        },
        "github": {
            "enabled": pr_creator.is_available(),
        },
    }


# ----- Background Tasks -----

async def create_pr_background(
    remediation_id: str,
    fix: GeneratedFix,
    repository: str,
    branch: str,
):
    """Create PR in background."""
    
    try:
        pr_info = await pr_creator.create_pr_for_fix(
            fix=fix,
            repository=repository,
            base_branch=branch,
        )
        
        if remediation_id in remediation_store:
            remediation_store[remediation_id].pr_info = pr_info
            if pr_info:
                remediation_store[remediation_id].status = FixStatus.PR_CREATED
                
    except Exception as e:
        logger.error("Background PR creation failed", error=str(e))


# ----- Helpers -----

def _count_by_status(store: Dict[str, RemediationResponse]) -> Dict[str, int]:
    """Count remediations by status."""
    
    counts = {}
    for item in store.values():
        status = item.status.value if item.status else "unknown"
        counts[status] = counts.get(status, 0) + 1
    
    return counts


# ----- Main -----

def main():
    """Start the Auto-Remediation Agent."""
    
    logger.info(
        "Starting Auto-Remediation Agent",
        host=settings.host,
        port=settings.port,
        github_enabled=pr_creator.is_available(),
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
