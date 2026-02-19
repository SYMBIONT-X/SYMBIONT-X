"""Workflow orchestration engine."""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import uuid

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from models import (
    Workflow,
    WorkflowStatus,
    WorkflowAction,
    WorkflowRequest,
)
from agent_client import AgentClient
from state_manager import StateManager
from config import settings


logger = get_logger("workflow-engine")


class WorkflowEngine:
    """Orchestrates the complete vulnerability management workflow."""
    
    def __init__(self):
        self.agent_client = AgentClient()
        self.state_manager = StateManager()
    
    async def start_workflow(
        self,
        request: WorkflowRequest,
        triggered_by: str = "manual",
    ) -> Workflow:
        """
        Start a new workflow.
        
        Flow:
        1. Scanner detects vulnerabilities
        2. Orchestrator receives results
        3. Risk Assessment determines priority
        4. Orchestrator decides: auto-fix or human-in-loop
        5. Auto-Remediation executes or waits for approval
        """
        
        workflow_id = str(uuid.uuid4())
        
        logger.info(
            "Starting workflow",
            workflow_id=workflow_id,
            repository=request.repository,
            branch=request.branch,
        )
        
        # Create workflow
        workflow = await self.state_manager.create_workflow(
            workflow_id=workflow_id,
            repository=request.repository,
            branch=request.branch,
            triggered_by=triggered_by,
            metadata={
                "scan_types": request.scan_types,
                "auto_remediate": request.auto_remediate,
                "notify": request.notify,
            },
        )
        
        # Execute workflow asynchronously
        asyncio.create_task(self._execute_workflow(workflow))
        
        return workflow
    
    async def _execute_workflow(self, workflow: Workflow):
        """Execute the workflow steps."""
        
        try:
            # Step 1: Scan
            workflow = await self._execute_scan(workflow)
            
            if workflow.status == WorkflowStatus.FAILED:
                return
            
            # Step 2: Assess
            workflow = await self._execute_assessment(workflow)
            
            if workflow.status == WorkflowStatus.FAILED:
                return
            
            # Step 3: Decide and Remediate
            workflow = await self._execute_remediation_decisions(workflow)
            
            # Step 4: Complete
            await self._complete_workflow(workflow)
            
        except Exception as e:
            logger.error(
                "Workflow execution failed",
                workflow_id=workflow.workflow_id,
                error=str(e),
            )
            
            workflow.status = WorkflowStatus.FAILED
            await self.state_manager.update_workflow(workflow)
    
    async def _execute_scan(self, workflow: Workflow) -> Workflow:
        """Execute scanning step."""
        
        logger.info("Executing scan step", workflow_id=workflow.workflow_id)
        
        workflow.status = WorkflowStatus.SCANNING
        await self.state_manager.update_step(
            workflow.workflow_id,
            "scan",
            WorkflowStatus.SCANNING,
        )
        
        # Trigger scan
        scan_types = workflow.metadata.get("scan_types", [])
        
        scan_result = await self.agent_client.trigger_scan(
            repository=workflow.repository,
            branch=workflow.branch,
            scan_types=scan_types,
        )
        
        if "error" in scan_result:
            logger.error("Scan failed", error=scan_result["error"])
            workflow.status = WorkflowStatus.FAILED
            await self.state_manager.update_step(
                workflow.workflow_id,
                "scan",
                WorkflowStatus.FAILED,
                error_message=scan_result["error"],
            )
            return workflow
        
        # Get scan ID and poll for completion
        scan_id = scan_result.get("scan_id")
        workflow.scan_id = scan_id
        
        # Poll for completion
        final_result = await self.agent_client.poll_scan_completion(
            scan_id=scan_id,
            max_wait=settings.workflow_timeout_seconds,
        )
        
        if final_result.get("status") == "completed":
            # Extract vulnerabilities
            vulnerabilities = self._extract_vulnerabilities(final_result)
            
            workflow.total_vulnerabilities = len(vulnerabilities)
            
            await self.state_manager.update_step(
                workflow.workflow_id,
                "scan",
                WorkflowStatus.COMPLETED,
                output_data={
                    "scan_id": scan_id,
                    "vulnerability_count": len(vulnerabilities),
                    "vulnerabilities": vulnerabilities,
                },
            )
            
            logger.info(
                "Scan completed",
                workflow_id=workflow.workflow_id,
                vulnerabilities=len(vulnerabilities),
            )
        else:
            workflow.status = WorkflowStatus.FAILED
            await self.state_manager.update_step(
                workflow.workflow_id,
                "scan",
                WorkflowStatus.FAILED,
                error_message=final_result.get("error", "Scan failed"),
            )
        
        return await self.state_manager.update_workflow(workflow)
    
    async def _execute_assessment(self, workflow: Workflow) -> Workflow:
        """Execute risk assessment step."""
        
        logger.info("Executing assessment step", workflow_id=workflow.workflow_id)
        
        workflow.status = WorkflowStatus.ASSESSING
        await self.state_manager.update_step(
            workflow.workflow_id,
            "assess",
            WorkflowStatus.SCANNING,  # Using SCANNING as "in progress"
        )
        
        # Get vulnerabilities from scan step
        scan_step = next(
            (s for s in workflow.steps if s.step_id == "scan"),
            None
        )
        
        if not scan_step or not scan_step.output_data:
            logger.error("No scan data found")
            workflow.status = WorkflowStatus.FAILED
            return workflow
        
        vulnerabilities = scan_step.output_data.get("vulnerabilities", [])
        
        if not vulnerabilities:
            logger.info("No vulnerabilities to assess")
            await self.state_manager.update_step(
                workflow.workflow_id,
                "assess",
                WorkflowStatus.COMPLETED,
                output_data={"assessments": [], "message": "No vulnerabilities"},
            )
            return await self.state_manager.update_workflow(workflow)
        
        # Call Risk Assessment
        assessment_result = await self.agent_client.assess_vulnerabilities(
            vulnerabilities=vulnerabilities,
            repository=workflow.repository,
        )
        
        if "error" in assessment_result:
            logger.error("Assessment failed", error=assessment_result["error"])
            workflow.status = WorkflowStatus.FAILED
            await self.state_manager.update_step(
                workflow.workflow_id,
                "assess",
                WorkflowStatus.FAILED,
                error_message=assessment_result["error"],
            )
            return workflow
        
        # Store assessment results
        workflow.assessment_id = assessment_result.get("assessment_id")
        
        assessments = assessment_result.get("assessments", [])
        summary = assessment_result.get("summary", {})
        
        workflow.critical_count = summary.get("P0", 0)
        workflow.high_count = summary.get("P1", 0)
        
        await self.state_manager.update_step(
            workflow.workflow_id,
            "assess",
            WorkflowStatus.COMPLETED,
            output_data={
                "assessment_id": workflow.assessment_id,
                "assessments": assessments,
                "summary": summary,
            },
        )
        
        logger.info(
            "Assessment completed",
            workflow_id=workflow.workflow_id,
            p0=workflow.critical_count,
            p1=workflow.high_count,
        )
        
        return await self.state_manager.update_workflow(workflow)
    
    async def _execute_remediation_decisions(self, workflow: Workflow) -> Workflow:
        """Make remediation decisions based on priority."""
        
        logger.info(
            "Making remediation decisions",
            workflow_id=workflow.workflow_id,
        )
        
        workflow.status = WorkflowStatus.REMEDIATING
        
        # Get assessments
        assess_step = next(
            (s for s in workflow.steps if s.step_id == "assess"),
            None
        )
        
        if not assess_step or not assess_step.output_data:
            return workflow
        
        assessments = assess_step.output_data.get("assessments", [])
        
        if not assessments:
            return workflow
        
        auto_remediate_config = workflow.metadata.get("auto_remediate", True)
        
        # Categorize by priority
        to_auto_remediate = []
        to_await_approval = []
        
        for assessment in assessments:
            priority = assessment.get("risk_score", {}).get("priority", "P2")
            vuln_id = assessment.get("vulnerability_id")
            
            # Build vulnerability object for remediation
            vuln = {
                "id": vuln_id,
                "cve_id": assessment.get("cve_id"),
                "title": assessment.get("title"),
                "severity": assessment.get("severity"),
                "priority": priority,
                "cvss_score": assessment.get("cvss_score"),
            }
            
            # Decision logic
            if priority in ["P0", "P1"]:
                if settings.require_approval_p0_p1:
                    to_await_approval.append(vuln)
                else:
                    to_auto_remediate.append(vuln)
            elif priority == "P2":
                if settings.auto_remediate_p2:
                    to_auto_remediate.append(vuln)
                else:
                    to_await_approval.append(vuln)
            elif priority in ["P3", "P4"]:
                if settings.auto_remediate_p3_p4 and auto_remediate_config:
                    to_auto_remediate.append(vuln)
        
        # Execute auto-remediation
        if to_auto_remediate:
            remediation_result = await self.agent_client.remediate_batch(
                vulnerabilities=to_auto_remediate,
                repository=workflow.repository,
                branch=workflow.branch,
                auto_create_pr=False,  # Don't create PRs without GitHub token
            )
            
            if "error" not in remediation_result:
                workflow.auto_remediated = remediation_result.get("fixes_generated", 0)
                workflow.remediation_ids.append(
                    remediation_result.get("batch_id", "")
                )
        
        # Handle items needing approval
        if to_await_approval:
            workflow.awaiting_approval = len(to_await_approval)
            
            if workflow.awaiting_approval > 0:
                workflow.status = WorkflowStatus.AWAITING_APPROVAL
                
                # Send notification if configured
                if workflow.metadata.get("notify", True):
                    await self._send_notification(workflow, to_await_approval)
        
        await self.state_manager.update_step(
            workflow.workflow_id,
            "remediate",
            WorkflowStatus.COMPLETED if not to_await_approval else WorkflowStatus.AWAITING_APPROVAL,
            output_data={
                "auto_remediated": len(to_auto_remediate),
                "awaiting_approval": len(to_await_approval),
            },
        )
        
        logger.info(
            "Remediation decisions made",
            workflow_id=workflow.workflow_id,
            auto_remediated=workflow.auto_remediated,
            awaiting_approval=workflow.awaiting_approval,
        )
        
        return await self.state_manager.update_workflow(workflow)
    
    async def _complete_workflow(self, workflow: Workflow):
        """Complete the workflow."""
        
        if workflow.status != WorkflowStatus.AWAITING_APPROVAL:
            await self.state_manager.complete_workflow(
                workflow.workflow_id,
                WorkflowStatus.COMPLETED,
            )
        
        logger.info(
            "Workflow finished",
            workflow_id=workflow.workflow_id,
            status=workflow.status.value,
            vulnerabilities=workflow.total_vulnerabilities,
            auto_remediated=workflow.auto_remediated,
            awaiting_approval=workflow.awaiting_approval,
        )
    
    async def approve_remediation(
        self,
        workflow_id: str,
        vulnerability_ids: List[str],
        approver: str,
    ) -> Optional[Workflow]:
        """Approve pending remediations."""
        
        workflow = await self.state_manager.get_workflow(workflow_id)
        
        if not workflow:
            return None
        
        if workflow.status != WorkflowStatus.AWAITING_APPROVAL:
            logger.warning(
                "Workflow not awaiting approval",
                workflow_id=workflow_id,
            )
            return workflow
        
        logger.info(
            "Processing approval",
            workflow_id=workflow_id,
            approver=approver,
            count=len(vulnerability_ids),
        )
        
        # Get vulnerabilities to remediate
        assess_step = next(
            (s for s in workflow.steps if s.step_id == "assess"),
            None
        )
        
        if assess_step and assess_step.output_data:
            assessments = assess_step.output_data.get("assessments", [])
            
            to_remediate = [
                {
                    "id": a.get("vulnerability_id"),
                    "cve_id": a.get("cve_id"),
                    "title": a.get("title"),
                    "severity": a.get("severity"),
                }
                for a in assessments
                if a.get("vulnerability_id") in vulnerability_ids
            ]
            
            if to_remediate:
                await self.agent_client.remediate_batch(
                    vulnerabilities=to_remediate,
                    repository=workflow.repository,
                    branch=workflow.branch,
                    auto_create_pr=False,
                )
        
        # Update workflow
        workflow.awaiting_approval = 0
        workflow.status = WorkflowStatus.COMPLETED
        workflow.completed_at = datetime.utcnow()
        
        return await self.state_manager.update_workflow(workflow)
    
    async def _send_notification(
        self,
        workflow: Workflow,
        vulnerabilities: List[Dict[str, Any]],
    ):
        """Send notification for vulnerabilities needing approval."""
        
        if not settings.slack_webhook_url:
            logger.debug("Slack webhook not configured, skipping notification")
            return
        
        # TODO: Implement Slack notification
        logger.info(
            "Would send notification",
            workflow_id=workflow.workflow_id,
            vulnerabilities=len(vulnerabilities),
        )
    
    def _extract_vulnerabilities(
        self,
        scan_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract vulnerabilities from scan result."""
        
        vulnerabilities = []
        
        results = scan_result.get("results", [])
        
        for result in results:
            if isinstance(result, dict):
                vulns = result.get("vulnerabilities", [])
                for v in vulns:
                    if isinstance(v, dict):
                        vulnerabilities.append(v)
        
        return vulnerabilities
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Workflow]:
        """Get current workflow status."""
        return await self.state_manager.get_workflow(workflow_id)
    
    async def cancel_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Cancel a running workflow."""
        
        workflow = await self.state_manager.get_workflow(workflow_id)
        
        if not workflow:
            return None
        
        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.utcnow()
        
        return await self.state_manager.update_workflow(workflow)
