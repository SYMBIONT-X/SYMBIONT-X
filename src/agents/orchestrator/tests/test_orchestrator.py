"""Unit tests for Orchestrator Agent."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    Workflow,
    WorkflowStatus,
    WorkflowRequest,
    AgentInfo,
    AgentStatus,
)
from state_manager import StateManager
from agent_client import AgentClient


class TestStateManager:
    """Tests for state manager."""
    
    @pytest.fixture
    def state_manager(self):
        return StateManager()
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, state_manager):
        workflow = await state_manager.create_workflow(
            workflow_id="test-123",
            repository="test/repo",
            branch="main",
        )
        
        assert workflow.workflow_id == "test-123"
        assert workflow.repository == "test/repo"
        assert workflow.status == WorkflowStatus.PENDING
        assert len(workflow.steps) == 5
    
    @pytest.mark.asyncio
    async def test_get_workflow(self, state_manager):
        await state_manager.create_workflow(
            workflow_id="test-456",
            repository="test/repo",
        )
        
        workflow = await state_manager.get_workflow("test-456")
        
        assert workflow is not None
        assert workflow.workflow_id == "test-456"
    
    @pytest.mark.asyncio
    async def test_get_workflow_not_found(self, state_manager):
        workflow = await state_manager.get_workflow("nonexistent")
        
        assert workflow is None
    
    @pytest.mark.asyncio
    async def test_update_workflow(self, state_manager):
        workflow = await state_manager.create_workflow(
            workflow_id="test-789",
            repository="test/repo",
        )
        
        workflow.total_vulnerabilities = 5
        updated = await state_manager.update_workflow(workflow)
        
        assert updated.total_vulnerabilities == 5
    
    @pytest.mark.asyncio
    async def test_update_step(self, state_manager):
        await state_manager.create_workflow(
            workflow_id="test-step",
            repository="test/repo",
        )
        
        workflow = await state_manager.update_step(
            workflow_id="test-step",
            step_id="scan",
            status=WorkflowStatus.COMPLETED,
            output_data={"vulnerabilities": []},
        )
        
        assert workflow is not None
        scan_step = next(s for s in workflow.steps if s.step_id == "scan")
        assert scan_step.status == WorkflowStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, state_manager):
        await state_manager.create_workflow(
            workflow_id="test-complete",
            repository="test/repo",
        )
        
        workflow = await state_manager.complete_workflow("test-complete")
        
        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, state_manager):
        await state_manager.create_workflow(
            workflow_id="list-1",
            repository="test/repo",
        )
        await state_manager.create_workflow(
            workflow_id="list-2",
            repository="test/repo",
        )
        
        workflows = await state_manager.list_workflows()
        
        assert len(workflows) >= 2
    
    @pytest.mark.asyncio
    async def test_list_workflows_by_repository(self, state_manager):
        await state_manager.create_workflow(
            workflow_id="repo-1",
            repository="specific/repo",
        )
        await state_manager.create_workflow(
            workflow_id="repo-2",
            repository="other/repo",
        )
        
        workflows = await state_manager.list_workflows(repository="specific/repo")
        
        assert len(workflows) == 1
        assert workflows[0].repository == "specific/repo"
    
    def test_get_stats(self, state_manager):
        stats = state_manager.get_stats()
        
        assert "total" in stats
        assert "by_status" in stats
        assert "storage" in stats


class TestAgentClient:
    """Tests for agent client."""
    
    @pytest.fixture
    def agent_client(self):
        return AgentClient()
    
    def test_agents_configured(self, agent_client):
        assert "security-scanner" in agent_client.agents
        assert "risk-assessment" in agent_client.agents
        assert "auto-remediation" in agent_client.agents
    
    def test_agent_urls(self, agent_client):
        assert agent_client.agents["security-scanner"].url == "http://localhost:8001"
        assert agent_client.agents["risk-assessment"].url == "http://localhost:8002"
        assert agent_client.agents["auto-remediation"].url == "http://localhost:8003"
    
    def test_get_agent_status_summary(self, agent_client):
        summary = agent_client.get_agent_status_summary()
        
        assert "security-scanner" in summary
        assert "risk-assessment" in summary
        assert "auto-remediation" in summary
        
        for agent_info in summary.values():
            assert "status" in agent_info
            assert "url" in agent_info


class TestAPIEndpoints:
    """Tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agent"] == "orchestrator"
        assert "agents" in data
    
    def test_get_agents(self, client):
        response = client.get("/agents")
        
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "all_healthy" in data
    
    def test_list_workflows_empty(self, client):
        response = client.get("/workflows")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "workflows" in data
    
    def test_get_workflow_not_found(self, client):
        response = client.get("/workflow/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_get_pending_approvals(self, client):
        response = client.get("/approvals")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "workflows" in data
    
    def test_get_stats(self, client):
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert "agents" in data
    
    def test_start_workflow(self, client):
        response = client.post("/workflow", json={
            "repository": "test/repo",
            "branch": "main",
            "scan_types": ["dependency", "code"],
            "auto_remediate": True,
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert data["status"] in ["pending", "scanning"]


class TestWorkflowModels:
    """Tests for workflow models."""
    
    def test_workflow_creation(self):
        workflow = Workflow(
            workflow_id="model-test",
            repository="test/repo",
            branch="main",
        )
        
        assert workflow.workflow_id == "model-test"
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.total_vulnerabilities == 0
    
    def test_workflow_request(self):
        request = WorkflowRequest(
            repository="test/repo",
            branch="develop",
            scan_types=["dependency"],
            auto_remediate=False,
        )
        
        assert request.repository == "test/repo"
        assert request.branch == "develop"
        assert request.auto_remediate is False
    
    def test_agent_info(self):
        agent = AgentInfo(
            name="test-agent",
            url="http://localhost:9999",
        )
        
        assert agent.name == "test-agent"
        assert agent.status == AgentStatus.UNKNOWN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
