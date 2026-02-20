"""Monitoring endpoints for SYMBIONT-X."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.telemetry import metrics_collector, MonitoringDashboard


router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Initialize dashboard
dashboard = MonitoringDashboard()


# ===== Response Models =====

class MetricsSummary(BaseModel):
    vulnerabilities_per_hour: Dict[str, int]
    remediation_success_rate: float
    average_fix_time_seconds: float
    total_remediation_attempts: int
    total_remediation_successes: int
    latencies: Dict[str, float]


class AlertResponse(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    source: str
    timestamp: str
    resolved: bool


class DashboardOverview(BaseModel):
    timestamp: str
    system_status: str
    metrics: Dict[str, Any]
    active_alerts: List[Dict[str, Any]]


# ===== Endpoints =====

@router.get("/health")
async def monitoring_health():
    """Check monitoring system health."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics/summary")
async def get_metrics_summary() -> MetricsSummary:
    """Get summary of all metrics."""
    
    summary = metrics_collector.get_summary()
    
    return MetricsSummary(
        vulnerabilities_per_hour=summary["vulnerabilities_per_hour"],
        remediation_success_rate=summary["remediation_success_rate"],
        average_fix_time_seconds=summary["average_fix_time_seconds"],
        total_remediation_attempts=summary["total_remediation_attempts"],
        total_remediation_successes=summary["total_remediation_successes"],
        latencies=summary["latencies"],
    )


@router.get("/dashboard/overview")
async def get_dashboard_overview():
    """Get system overview dashboard."""
    
    return dashboard.get_system_overview()


@router.get("/dashboard/vulnerabilities")
async def get_vulnerability_dashboard():
    """Get vulnerability-focused dashboard."""
    
    return dashboard.get_vulnerability_dashboard()


@router.get("/dashboard/remediation")
async def get_remediation_dashboard():
    """Get remediation-focused dashboard."""
    
    return dashboard.get_remediation_dashboard()


@router.get("/dashboard/agents")
async def get_agent_dashboard():
    """Get agent health dashboard."""
    
    return dashboard.get_agent_dashboard()


@router.get("/dashboard/export")
async def export_dashboard():
    """Export complete dashboard as JSON."""
    
    return dashboard.export_dashboard_json()


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
):
    """Get alerts with optional filters."""
    
    alerts = dashboard.get_alerts(severity=severity, resolved=resolved)
    
    return {
        "total": len(alerts),
        "alerts": [
            {
                "id": a.id,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "source": a.source,
                "timestamp": a.timestamp.isoformat(),
                "resolved": a.resolved,
            }
            for a in alerts
        ],
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    
    success = dashboard.resolve_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"status": "resolved", "alert_id": alert_id}


@router.post("/record/vulnerability")
async def record_vulnerability(
    severity: str,
    priority: str,
    agent: str = "security-scanner",
):
    """Record a vulnerability detection (for testing)."""
    
    metrics_collector.record_vulnerability(
        severity=severity,
        priority=priority,
        agent=agent,
    )
    
    return {"status": "recorded"}


@router.post("/record/remediation")
async def record_remediation(
    status: str,
    fix_type: str,
    duration_seconds: Optional[float] = None,
    priority: str = "P2",
):
    """Record a remediation attempt (for testing)."""
    
    metrics_collector.record_remediation(
        status=status,
        fix_type=fix_type,
        duration_seconds=duration_seconds,
        priority=priority,
    )
    
    return {"status": "recorded"}


@router.post("/record/latency")
async def record_latency(
    source_agent: str,
    target_agent: str,
    latency_seconds: float,
):
    """Record agent latency (for testing)."""
    
    metrics_collector.record_agent_latency(
        source_agent=source_agent,
        target_agent=target_agent,
        latency_seconds=latency_seconds,
    )
    
    return {"status": "recorded"}
