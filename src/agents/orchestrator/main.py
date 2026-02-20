"""Orchestrator Agent - Main entry point."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from shared.utils import setup_logging, get_logger
from config import settings
from models import (
    Workflow,
    WorkflowStatus,
    WorkflowRequest,
    WorkflowResponse,
    ApprovalRequest,
    AgentStatus,
)
from workflow_engine import WorkflowEngine
from agent_client import AgentClient


# Setup logging
setup_logging(level=settings.log_level, json_format=settings.log_json)
logger = get_logger("orchestrator")


# Initialize FastAPI
app = FastAPI(
    title="SYMBIONT-X Orchestrator Agent",
    description="Coordinates all SYMBIONT-X security agents",
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
workflow_engine = WorkflowEngine()
agent_client = AgentClient()


# ----- Request/Response Models -----

class HealthResponse(BaseModel):
    status: str
    agent: str
    version: str
    agents: dict
    timestamp: str


class AgentStatusResponse(BaseModel):
    agents: dict
    all_healthy: bool


class WorkflowListResponse(BaseModel):
    total: int
    workflows: List[Workflow]


class StatsResponse(BaseModel):
    workflows: dict
    agents: dict


# ----- API Endpoints -----

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check orchestrator and all agent health."""
    
    # Check all agents
    await agent_client.check_all_agents()
    
    agent_statuses = {
        name: agent.status.value
        for name, agent in agent_client.agents.items()
    }
    
    return HealthResponse(
        status="healthy",
        agent=settings.agent_name,
        version=settings.agent_version,
        agents=agent_statuses,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/agents", response_model=AgentStatusResponse)
async def get_agent_status():
    """Get detailed status of all agents."""
    
    await agent_client.check_all_agents()
    
    agents = agent_client.get_agent_status_summary()
    
    all_healthy = all(
        a["status"] == AgentStatus.HEALTHY.value
        for a in agents.values()
    )
    
    return AgentStatusResponse(
        agents=agents,
        all_healthy=all_healthy,
    )


@app.post("/workflow", response_model=WorkflowResponse)
async def start_workflow(request: WorkflowRequest):
    """
    Start a new security workflow.
    
    This initiates the full pipeline:
    1. Security Scanner scans the repository
    2. Risk Assessment prioritizes vulnerabilities
    3. Orchestrator decides on auto-fix vs approval
    4. Auto-Remediation generates fixes
    """
    
    logger.info(
        "Workflow start requested",
        repository=request.repository,
        branch=request.branch,
    )
    
    try:
        workflow = await workflow_engine.start_workflow(
            request=request,
            triggered_by="api",
        )
        
        return WorkflowResponse(
            workflow_id=workflow.workflow_id,
            status=workflow.status,
            message=f"Workflow started for {request.repository}",
            workflow=workflow,
        )
        
    except Exception as e:
        logger.error("Workflow start failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get workflow status and details."""
    
    workflow = await workflow_engine.get_workflow_status(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return WorkflowResponse(
        workflow_id=workflow.workflow_id,
        status=workflow.status,
        message=f"Workflow status: {workflow.status.value}",
        workflow=workflow,
    )


@app.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    status: Optional[WorkflowStatus] = None,
    repository: Optional[str] = None,
    limit: int = 50,
):
    """List workflows with optional filters."""
    
    workflows = await workflow_engine.state_manager.list_workflows(
        status=status,
        repository=repository,
        limit=limit,
    )
    
    return WorkflowListResponse(
        total=len(workflows),
        workflows=workflows,
    )


@app.post("/workflow/{workflow_id}/cancel", response_model=WorkflowResponse)
async def cancel_workflow(workflow_id: str):
    """Cancel a running workflow."""
    
    workflow = await workflow_engine.cancel_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return WorkflowResponse(
        workflow_id=workflow.workflow_id,
        status=workflow.status,
        message="Workflow cancelled",
        workflow=workflow,
    )


@app.post("/approve", response_model=WorkflowResponse)
async def approve_remediation(request: ApprovalRequest):
    """Approve pending remediations in a workflow."""
    
    if not request.approved:
        # Handle rejection
        workflow = await workflow_engine.state_manager.get_workflow(
            request.workflow_id
        )
        
        if workflow:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.awaiting_approval = 0
            await workflow_engine.state_manager.update_workflow(workflow)
        
        return WorkflowResponse(
            workflow_id=request.workflow_id,
            status=WorkflowStatus.COMPLETED,
            message="Remediation rejected",
            workflow=workflow,
        )
    
    workflow = await workflow_engine.approve_remediation(
        workflow_id=request.workflow_id,
        vulnerability_ids=request.vulnerability_ids,
        approver=request.approver,
    )
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return WorkflowResponse(
        workflow_id=workflow.workflow_id,
        status=workflow.status,
        message=f"Approved {len(request.vulnerability_ids)} remediations",
        workflow=workflow,
    )


@app.get("/approvals", response_model=WorkflowListResponse)
async def get_pending_approvals():
    """Get all workflows awaiting approval."""
    
    workflows = await workflow_engine.state_manager.get_pending_approvals()
    
    return WorkflowListResponse(
        total=len(workflows),
        workflows=workflows,
    )


@app.post("/webhook/scan-complete")
async def webhook_scan_complete(payload: dict):
    """
    Webhook endpoint for Security Scanner to notify scan completion.
    
    This enables event-driven workflow progression.
    """
    
    scan_id = payload.get("scan_id")
    status = payload.get("status")
    repository = payload.get("repository")
    
    logger.info(
        "Scan complete webhook received",
        scan_id=scan_id,
        status=status,
        repository=repository,
    )
    
    # Find workflow waiting for this scan
    workflows = await workflow_engine.state_manager.list_workflows(
        status=WorkflowStatus.SCANNING,
        repository=repository,
    )
    
    for workflow in workflows:
        if workflow.scan_id == scan_id:
            # Workflow engine will handle progression
            logger.info(
                "Found matching workflow",
                workflow_id=workflow.workflow_id,
            )
            break
    
    return {"status": "received", "scan_id": scan_id}


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get orchestrator statistics."""
    
    workflow_stats = workflow_engine.state_manager.get_stats()
    agent_stats = agent_client.get_agent_status_summary()
    
    return StatsResponse(
        workflows=workflow_stats,
        agents=agent_stats,
    )


@app.post("/scan")
async def quick_scan(
    repository: str,
    branch: str = "main",
):
    """
    Trigger a quick scan without full workflow.
    
    Useful for testing scanner connectivity.
    """
    
    result = await agent_client.trigger_scan(
        repository=repository,
        branch=branch,
    )
    
    return result


@app.post("/assess")
async def quick_assess(
    vulnerabilities: List[dict],
    repository: str,
):
    """
    Quick risk assessment without full workflow.
    
    Useful for testing risk assessment connectivity.
    """
    
    result = await agent_client.assess_vulnerabilities(
        vulnerabilities=vulnerabilities,
        repository=repository,
    )
    
    return result


# ----- Startup Events -----

@app.on_event("startup")
async def startup_event():
    """Check agent connectivity on startup."""
    
    logger.info("Orchestrator starting, checking agent connectivity...")
    
    await agent_client.check_all_agents()
    
    for name, agent in agent_client.agents.items():
        logger.info(
            f"Agent {name}: {agent.status.value}",
            url=agent.url,
        )


# ----- Main -----

def main():
    """Start the Orchestrator Agent."""
    
    logger.info(
        "Starting Orchestrator Agent",
        host=settings.host,
        port=settings.port,
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


# Import and include monitoring router
from monitoring import router as monitoring_router
app.include_router(monitoring_router)


# Import and include HITL router
from hitl_api import router as hitl_router
app.include_router(hitl_router)
