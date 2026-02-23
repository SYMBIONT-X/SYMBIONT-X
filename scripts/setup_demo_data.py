#!/usr/bin/env python3
"""Setup demo data for SYMBIONT-X demo video."""

import json
import httpx
import asyncio
from datetime import datetime, timedelta


ORCHESTRATOR_URL = "http://localhost:8000"


DEMO_VULNERABILITIES = [
    {
        "id": "vuln-demo-001",
        "cve_id": "CVE-2026-1234",
        "title": "SQL Injection in User Authentication",
        "description": "User input not sanitized in login query",
        "severity": "critical",
        "cvss_score": 9.8,
        "package_name": None,
        "file_path": "src/auth/login.py",
        "line_number": 42,
        "source": "code-scanner",
        "repository": "SYMBIONT-X/demo-app",
        "branch": "main",
    },
    {
        "id": "vuln-demo-002",
        "cve_id": None,
        "title": "Exposed AWS Secret Access Key",
        "description": "AWS credentials hardcoded in configuration file",
        "severity": "high",
        "cvss_score": 8.5,
        "package_name": None,
        "file_path": "config/aws_settings.py",
        "line_number": 15,
        "source": "secret-scanner",
        "repository": "SYMBIONT-X/demo-app",
        "branch": "main",
    },
    {
        "id": "vuln-demo-003",
        "cve_id": None,
        "title": "Hardcoded Database Password",
        "description": "Database password visible in source code",
        "severity": "high",
        "cvss_score": 7.5,
        "package_name": None,
        "file_path": "src/db/connection.py",
        "line_number": 8,
        "source": "secret-scanner",
        "repository": "SYMBIONT-X/demo-app",
        "branch": "main",
    },
    {
        "id": "vuln-demo-004",
        "cve_id": "CVE-2025-9876",
        "title": "Prototype Pollution in lodash",
        "description": "lodash before 4.17.21 allows prototype pollution",
        "severity": "medium",
        "cvss_score": 6.5,
        "package_name": "lodash",
        "package_version": "4.17.15",
        "fixed_version": "4.17.21",
        "file_path": "package.json",
        "source": "dependency-scanner",
        "repository": "SYMBIONT-X/demo-app",
        "branch": "main",
    },
    {
        "id": "vuln-demo-005",
        "cve_id": None,
        "title": "Insecure Bind to All Interfaces",
        "description": "Server binding to 0.0.0.0 exposes service",
        "severity": "medium",
        "cvss_score": 5.5,
        "package_name": None,
        "file_path": "src/server/config.py",
        "line_number": 24,
        "source": "code-scanner",
        "repository": "SYMBIONT-X/demo-app",
        "branch": "main",
    },
    {
        "id": "vuln-demo-006",
        "cve_id": None,
        "title": "Missing HTTPS Redirect",
        "description": "HTTP traffic not redirected to HTTPS",
        "severity": "low",
        "cvss_score": 3.5,
        "package_name": None,
        "file_path": "src/middleware/security.py",
        "line_number": 12,
        "source": "code-scanner",
        "repository": "SYMBIONT-X/demo-app",
        "branch": "main",
    },
]


DEMO_METRICS = {
    "total_scans": 47,
    "total_vulnerabilities": 156,
    "critical_count": 3,
    "high_count": 12,
    "medium_count": 45,
    "low_count": 96,
    "auto_remediated": 142,
    "awaiting_approval": 8,
    "success_rate": 94.5,
    "avg_fix_time_minutes": 3.2,
    "time_saved_hours": 156,
}


async def check_health():
    """Check if orchestrator is running."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/health")
            return response.status_code == 200
    except Exception:
        return False


async def create_demo_approval():
    """Create a demo approval request."""
    
    approval_data = {
        "workflow_id": "demo-workflow-001",
        "title": "Critical SQL Injection Remediation",
        "description": "AI-generated fix for SQL injection vulnerability in login.py. The fix parameterizes the query to prevent injection attacks.",
        "vulnerability_ids": ["vuln-demo-001"],
        "priority": "P0",
        "risk_summary": "This vulnerability allows unauthenticated attackers to bypass login and access any user account. CVSS 9.8 - Critical severity.",
        "recommended_action": "Apply the parameterized query fix immediately. The AI has generated a safe replacement that uses prepared statements.",
        "requested_by": "security-scanner",
        "expires_in_hours": 24,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/hitl/approvals",
                json=approval_data,
            )
            if response.status_code == 200:
                print("✅ Created demo approval request")
                return response.json()
            else:
                print(f"❌ Failed to create approval: {response.text}")
    except Exception as e:
        print(f"❌ Error creating approval: {e}")


async def add_demo_comments(approval_id: str):
    """Add demo comments to approval."""
    
    comments = [
        {
            "target_type": "approval",
            "target_id": approval_id,
            "author": "security-bot",
            "content": "AI Analysis: This SQL injection is exploitable via the username field. Attack payload: ' OR '1'='1' -- would bypass authentication.",
        },
        {
            "target_type": "approval",
            "target_id": approval_id,
            "author": "alice@company.com",
            "content": "Reviewing the fix now. The parameterized query approach looks correct.",
        },
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            for comment in comments:
                response = await client.post(
                    f"{ORCHESTRATOR_URL}/hitl/comments",
                    json=comment,
                )
                if response.status_code == 200:
                    print(f"✅ Added comment from {comment['author']}")
    except Exception as e:
        print(f"❌ Error adding comments: {e}")


async def record_demo_metrics():
    """Record demo metrics for impressive dashboard."""
    
    try:
        async with httpx.AsyncClient() as client:
            # Record vulnerabilities
            for vuln in DEMO_VULNERABILITIES:
                await client.post(
                    f"{ORCHESTRATOR_URL}/monitoring/record/vulnerability",
                    params={
                        "severity": vuln["severity"],
                        "priority": "P0" if vuln["severity"] == "critical" else "P1" if vuln["severity"] == "high" else "P2",
                        "agent": vuln["source"],
                    },
                )
            
            # Record some remediations
            for i in range(10):
                await client.post(
                    f"{ORCHESTRATOR_URL}/monitoring/record/remediation",
                    params={
                        "status": "success",
                        "fix_type": "dependency_upgrade",
                        "duration_seconds": 45.0 + i * 10,
                        "priority": "P2",
                    },
                )
            
            # Record latencies
            agents = ["security-scanner", "risk-assessment", "auto-remediation"]
            for agent in agents:
                await client.post(
                    f"{ORCHESTRATOR_URL}/monitoring/record/latency",
                    params={
                        "source_agent": "orchestrator",
                        "target_agent": agent,
                        "latency_seconds": 0.05 + 0.02 * agents.index(agent),
                    },
                )
            
            print("✅ Recorded demo metrics")
    except Exception as e:
        print(f"❌ Error recording metrics: {e}")


async def main():
    print("\n🎬 SYMBIONT-X Demo Data Setup")
    print("=" * 50)
    
    # Check health
    print("\n📡 Checking orchestrator health...")
    if not await check_health():
        print("❌ Orchestrator not running! Start it first:")
        print("   cd src/agents/orchestrator && python main.py")
        return
    print("✅ Orchestrator is healthy")
    
    # Create approval
    print("\n📝 Creating demo approval request...")
    result = await create_demo_approval()
    
    if result and "approval_id" in result:
        # Add comments
        print("\n💬 Adding demo comments...")
        await add_demo_comments(result["approval_id"])
    
    # Record metrics
    print("\n📊 Recording demo metrics...")
    await record_demo_metrics()
    
    print("\n" + "=" * 50)
    print("✅ Demo data setup complete!")
    print("\nNow you can:")
    print("1. Open http://localhost:5173")
    print("2. Navigate through Dashboard, Vulnerabilities, Approvals")
    print("3. Start recording your demo video")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
