"""State management for workflows."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from models import Workflow, WorkflowStatus, WorkflowStep, WorkflowAction
from config import settings


logger = get_logger("state-manager")


class StateManager:
    """Manages workflow state (in-memory or Cosmos DB)."""
    
    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._cosmos_client = None
        self._container = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage backend."""
        
        if settings.cosmos_endpoint and settings.cosmos_key:
            try:
                from azure.cosmos import CosmosClient
                
                self._cosmos_client = CosmosClient(
                    settings.cosmos_endpoint,
                    settings.cosmos_key,
                )
                
                database = self._cosmos_client.get_database_client(
                    settings.cosmos_database
                )
                self._container = database.get_container_client(
                    settings.cosmos_container
                )
                
                logger.info("Cosmos DB storage initialized")
                
            except Exception as e:
                logger.warning(
                    "Cosmos DB initialization failed, using in-memory",
                    error=str(e),
                )
        else:
            logger.info("Using in-memory storage (Cosmos DB not configured)")
    
    async def create_workflow(
        self,
        workflow_id: str,
        repository: str,
        branch: str = "main",
        triggered_by: str = "manual",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """Create a new workflow."""
        
        workflow = Workflow(
            workflow_id=workflow_id,
            repository=repository,
            branch=branch,
            triggered_by=triggered_by,
            metadata=metadata or {},
        )
        
        # Add initial steps
        workflow.steps = [
            WorkflowStep(
                step_id="scan",
                action=WorkflowAction.SCAN,
                agent="security-scanner",
            ),
            WorkflowStep(
                step_id="assess",
                action=WorkflowAction.ASSESS,
                agent="risk-assessment",
            ),
            WorkflowStep(
                step_id="decide",
                action=WorkflowAction.AUTO_REMEDIATE,
                agent="orchestrator",
            ),
            WorkflowStep(
                step_id="remediate",
                action=WorkflowAction.AUTO_REMEDIATE,
                agent="auto-remediation",
            ),
            WorkflowStep(
                step_id="complete",
                action=WorkflowAction.COMPLETE,
                agent="orchestrator",
            ),
        ]
        
        workflow.current_step = "scan"
        
        await self._save_workflow(workflow)
        
        logger.info(
            "Workflow created",
            workflow_id=workflow_id,
            repository=repository,
        )
        
        return workflow
    
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        
        # Try Cosmos DB first
        if self._container:
            try:
                item = self._container.read_item(
                    item=workflow_id,
                    partition_key=workflow_id,
                )
                return Workflow(**item)
            except Exception:
                pass
        
        # Fall back to in-memory
        return self._workflows.get(workflow_id)
    
    async def update_workflow(self, workflow: Workflow) -> Workflow:
        """Update a workflow."""
        
        workflow.updated_at = datetime.utcnow()
        await self._save_workflow(workflow)
        
        logger.debug("Workflow updated", workflow_id=workflow.workflow_id)
        
        return workflow
    
    async def update_step(
        self,
        workflow_id: str,
        step_id: str,
        status: WorkflowStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Workflow]:
        """Update a specific step in a workflow."""
        
        workflow = await self.get_workflow(workflow_id)
        
        if not workflow:
            logger.warning("Workflow not found", workflow_id=workflow_id)
            return None
        
        for step in workflow.steps:
            if step.step_id == step_id:
                step.status = status
                
                if output_data:
                    step.output_data = output_data
                
                if error_message:
                    step.error_message = error_message
                
                if status == WorkflowStatus.SCANNING:
                    step.started_at = datetime.utcnow()
                elif status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                    step.completed_at = datetime.utcnow()
                
                break
        
        return await self.update_workflow(workflow)
    
    async def advance_workflow(
        self,
        workflow_id: str,
        next_step: str,
    ) -> Optional[Workflow]:
        """Advance workflow to next step."""
        
        workflow = await self.get_workflow(workflow_id)
        
        if not workflow:
            return None
        
        workflow.current_step = next_step
        
        return await self.update_workflow(workflow)
    
    async def complete_workflow(
        self,
        workflow_id: str,
        status: WorkflowStatus = WorkflowStatus.COMPLETED,
    ) -> Optional[Workflow]:
        """Mark workflow as complete."""
        
        workflow = await self.get_workflow(workflow_id)
        
        if not workflow:
            return None
        
        workflow.status = status
        workflow.completed_at = datetime.utcnow()
        workflow.current_step = None
        
        logger.info(
            "Workflow completed",
            workflow_id=workflow_id,
            status=status.value,
        )
        
        return await self.update_workflow(workflow)
    
    async def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
        repository: Optional[str] = None,
        limit: int = 50,
    ) -> List[Workflow]:
        """List workflows with optional filters."""
        
        workflows = list(self._workflows.values())
        
        if status:
            workflows = [w for w in workflows if w.status == status]
        
        if repository:
            workflows = [w for w in workflows if w.repository == repository]
        
        # Sort by created_at descending
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        
        return workflows[:limit]
    
    async def get_pending_approvals(self) -> List[Workflow]:
        """Get workflows awaiting approval."""
        
        return await self.list_workflows(status=WorkflowStatus.AWAITING_APPROVAL)
    
    async def _save_workflow(self, workflow: Workflow):
        """Save workflow to storage."""
        
        # Save to Cosmos DB if available
        if self._container:
            try:
                item = workflow.model_dump()
                item["id"] = workflow.workflow_id
                
                self._container.upsert_item(item)
                
            except Exception as e:
                logger.warning(
                    "Cosmos DB save failed",
                    error=str(e),
                )
        
        # Always save to in-memory
        self._workflows[workflow.workflow_id] = workflow
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
        
        if self._container:
            try:
                self._container.delete_item(
                    item=workflow_id,
                    partition_key=workflow_id,
                )
            except Exception:
                pass
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        
        workflows = list(self._workflows.values())
        
        by_status = {}
        for w in workflows:
            status = w.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total": len(workflows),
            "by_status": by_status,
            "storage": "cosmos_db" if self._container else "in_memory",
        }
