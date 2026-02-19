"""Agent-to-Agent (A2A) communication client."""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import get_logger
from models import AgentInfo, AgentStatus
from config import settings


logger = get_logger("agent-client")


class AgentClient:
    """Client for communicating with other SYMBIONT-X agents."""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {
            "security-scanner": AgentInfo(
                name="security-scanner",
                url=settings.security_scanner_url,
                capabilities=["scan", "dependency", "code", "secret", "container", "iac"],
            ),
            "risk-assessment": AgentInfo(
                name="risk-assessment",
                url=settings.risk_assessment_url,
                capabilities=["assess", "prioritize", "context"],
            ),
            "auto-remediation": AgentInfo(
                name="auto-remediation",
                url=settings.auto_remediation_url,
                capabilities=["remediate", "pr", "templates"],
            ),
        }
        self.timeout = settings.agent_timeout_seconds
    
    async def check_agent_health(self, agent_name: str) -> AgentInfo:
        """Check health of a specific agent."""
        
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent = self.agents[agent_name]
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{agent.url}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    agent.status = AgentStatus.HEALTHY
                    agent.version = data.get("version")
                    agent.last_check = datetime.utcnow()
                    
                    logger.info(
                        "Agent health check passed",
                        agent=agent_name,
                        version=agent.version,
                    )
                else:
                    agent.status = AgentStatus.UNHEALTHY
                    agent.last_check = datetime.utcnow()
                    
        except Exception as e:
            logger.warning(
                "Agent health check failed",
                agent=agent_name,
                error=str(e),
            )
            agent.status = AgentStatus.UNHEALTHY
            agent.last_check = datetime.utcnow()
        
        return agent
    
    async def check_all_agents(self) -> Dict[str, AgentInfo]:
        """Check health of all agents."""
        
        tasks = [
            self.check_agent_health(name)
            for name in self.agents.keys()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return self.agents
    
    async def trigger_scan(
        self,
        repository: str,
        branch: str = "main",
        scan_types: Optional[List[str]] = None,
        target_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger a security scan."""
        
        agent = self.agents["security-scanner"]
        
        if agent.status == AgentStatus.UNHEALTHY:
            await self.check_agent_health("security-scanner")
        
        payload = {
            "repository": repository,
            "branch": branch,
            "scan_types": scan_types or ["dependency", "code", "secret", "container", "iac"],
        }
        
        if target_path:
            payload["target_path"] = target_path
        
        logger.info("Triggering scan", repository=repository, branch=branch)
        
        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{agent.url}/scan",
                    json=payload,
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(
                        "Scan trigger failed",
                        status=response.status_code,
                        response=response.text,
                    )
                    return {"error": f"Status {response.status_code}"}
                    
        except Exception as e:
            logger.error("Scan trigger error", error=str(e))
            return {"error": str(e)}
    
    async def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
        """Get scan results."""
        
        agent = self.agents["security-scanner"]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{agent.url}/scan/{scan_id}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Status {response.status_code}"}
                    
        except Exception as e:
            logger.error("Get scan results error", error=str(e))
            return {"error": str(e)}
    
    async def poll_scan_completion(
        self,
        scan_id: str,
        max_wait: int = 600,
        poll_interval: int = 5,
    ) -> Dict[str, Any]:
        """Poll for scan completion."""
        
        elapsed = 0
        
        while elapsed < max_wait:
            result = await self.get_scan_results(scan_id)
            
            status = result.get("status", "unknown")
            
            if status == "completed":
                logger.info("Scan completed", scan_id=scan_id)
                return result
            elif status == "failed":
                logger.error("Scan failed", scan_id=scan_id)
                return result
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        logger.warning("Scan polling timeout", scan_id=scan_id)
        return {"error": "Polling timeout", "status": "timeout"}
    
    async def assess_vulnerabilities(
        self,
        vulnerabilities: List[Dict[str, Any]],
        repository: str,
        business_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send vulnerabilities for risk assessment."""
        
        agent = self.agents["risk-assessment"]
        
        if agent.status == AgentStatus.UNHEALTHY:
            await self.check_agent_health("risk-assessment")
        
        payload = {
            "vulnerabilities": vulnerabilities,
            "repository": repository,
            "use_ai_analysis": False,  # Skip AI for speed
        }
        
        if business_context:
            payload["business_context"] = business_context
        
        logger.info(
            "Assessing vulnerabilities",
            count=len(vulnerabilities),
            repository=repository,
        )
        
        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{agent.url}/assess",
                    json=payload,
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(
                        "Assessment failed",
                        status=response.status_code,
                    )
                    return {"error": f"Status {response.status_code}"}
                    
        except Exception as e:
            logger.error("Assessment error", error=str(e))
            return {"error": str(e)}
    
    async def remediate_vulnerability(
        self,
        vulnerability: Dict[str, Any],
        repository: str,
        branch: str = "main",
        auto_create_pr: bool = True,
    ) -> Dict[str, Any]:
        """Request remediation for a vulnerability."""
        
        agent = self.agents["auto-remediation"]
        
        if agent.status == AgentStatus.UNHEALTHY:
            await self.check_agent_health("auto-remediation")
        
        payload = {
            "vulnerability": vulnerability,
            "repository": repository,
            "branch": branch,
            "auto_create_pr": auto_create_pr,
        }
        
        logger.info(
            "Requesting remediation",
            vulnerability_id=vulnerability.get("id"),
            repository=repository,
        )
        
        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{agent.url}/remediate",
                    json=payload,
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(
                        "Remediation failed",
                        status=response.status_code,
                    )
                    return {"error": f"Status {response.status_code}"}
                    
        except Exception as e:
            logger.error("Remediation error", error=str(e))
            return {"error": str(e)}
    
    async def remediate_batch(
        self,
        vulnerabilities: List[Dict[str, Any]],
        repository: str,
        branch: str = "main",
        auto_create_pr: bool = True,
        priority_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Request batch remediation."""
        
        agent = self.agents["auto-remediation"]
        
        payload = {
            "vulnerabilities": vulnerabilities,
            "repository": repository,
            "branch": branch,
            "auto_create_pr": auto_create_pr,
        }
        
        if priority_filter:
            payload["priority_filter"] = priority_filter
        
        logger.info(
            "Requesting batch remediation",
            count=len(vulnerabilities),
            repository=repository,
        )
        
        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{agent.url}/remediate/batch",
                    json=payload,
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Status {response.status_code}"}
                    
        except Exception as e:
            logger.error("Batch remediation error", error=str(e))
            return {"error": str(e)}
    
    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get summary of all agent statuses."""
        
        return {
            name: {
                "status": agent.status.value,
                "url": agent.url,
                "version": agent.version,
                "last_check": agent.last_check.isoformat() if agent.last_check else None,
            }
            for name, agent in self.agents.items()
        }
