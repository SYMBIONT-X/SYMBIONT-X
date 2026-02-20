"""Monitoring Dashboard for SYMBIONT-X."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

from .metrics import metrics_collector


@dataclass
class Alert:
    """An alert notification."""
    id: str
    severity: str  # critical, warning, info
    title: str
    message: str
    source: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class MonitoringDashboard:
    """Dashboard for monitoring SYMBIONT-X system health."""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self._alert_rules: List[Dict[str, Any]] = []
        self._setup_default_alert_rules()
    
    def _setup_default_alert_rules(self):
        """Setup default alerting rules."""
        
        self._alert_rules = [
            {
                "id": "agent_unhealthy",
                "name": "Agent Unhealthy",
                "severity": "critical",
                "condition": "agent_health == 0",
                "message": "Agent {agent} is unhealthy",
            },
            {
                "id": "high_latency",
                "name": "High Agent Latency",
                "severity": "warning",
                "condition": "latency > 5",
                "message": "High latency detected: {latency}s",
            },
            {
                "id": "remediation_failures",
                "name": "Remediation Failure Rate",
                "severity": "warning",
                "condition": "success_rate < 50",
                "message": "Remediation success rate below 50%: {rate}%",
            },
            {
                "id": "critical_vulnerability",
                "name": "Critical Vulnerability Detected",
                "severity": "critical",
                "condition": "priority == P0",
                "message": "Critical vulnerability detected requiring immediate attention",
            },
        ]
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get complete system overview."""
        
        metrics_summary = metrics_collector.get_summary()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": self._calculate_system_status(),
            "metrics": {
                "vulnerabilities": {
                    "per_hour": metrics_summary["vulnerabilities_per_hour"],
                    "total_last_24h": sum(metrics_summary["vulnerabilities_per_hour"].values()),
                },
                "remediation": {
                    "success_rate": round(metrics_summary["remediation_success_rate"], 2),
                    "average_fix_time_seconds": round(metrics_summary["average_fix_time_seconds"], 2),
                    "total_attempts": metrics_summary["total_remediation_attempts"],
                    "total_successes": metrics_summary["total_remediation_successes"],
                },
                "latencies": metrics_summary["latencies"],
            },
            "active_alerts": [a for a in self.alerts if not a.resolved],
            "recent_alerts": self.alerts[-10:],
        }
    
    def _calculate_system_status(self) -> str:
        """Calculate overall system status."""
        
        active_critical = sum(
            1 for a in self.alerts
            if not a.resolved and a.severity == "critical"
        )
        
        active_warnings = sum(
            1 for a in self.alerts
            if not a.resolved and a.severity == "warning"
        )
        
        if active_critical > 0:
            return "critical"
        elif active_warnings > 0:
            return "warning"
        else:
            return "healthy"
    
    def get_vulnerability_dashboard(self) -> Dict[str, Any]:
        """Get vulnerability-focused dashboard data."""
        
        hourly_data = metrics_collector.get_vulnerabilities_per_hour(24)
        
        return {
            "title": "Vulnerability Dashboard",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_24h": sum(hourly_data.values()),
                "hourly_average": round(sum(hourly_data.values()) / max(len(hourly_data), 1), 2),
                "peak_hour": max(hourly_data.items(), key=lambda x: x[1])[0] if hourly_data else None,
            },
            "hourly_trend": hourly_data,
            "by_priority": self._get_vulnerabilities_by_priority(),
        }
    
    def _get_vulnerabilities_by_priority(self) -> Dict[str, int]:
        """Get vulnerability counts by priority."""
        
        # This would normally query the actual data
        # For now, return placeholder structure
        return {
            "P0": 0,
            "P1": 0,
            "P2": 0,
            "P3": 0,
            "P4": 0,
        }
    
    def get_remediation_dashboard(self) -> Dict[str, Any]:
        """Get remediation-focused dashboard data."""
        
        success_rate = metrics_collector.get_remediation_success_rate()
        avg_fix_time = metrics_collector.get_average_fix_time()
        
        return {
            "title": "Remediation Dashboard",
            "timestamp": datetime.utcnow().isoformat(),
            "kpis": {
                "success_rate": {
                    "value": round(success_rate, 2),
                    "unit": "%",
                    "status": "good" if success_rate >= 80 else "warning" if success_rate >= 50 else "critical",
                },
                "average_fix_time": {
                    "value": round(avg_fix_time / 60, 2),  # Convert to minutes
                    "unit": "minutes",
                    "status": "good" if avg_fix_time < 3600 else "warning",
                },
                "total_fixed": {
                    "value": metrics_collector._remediation_successes,
                    "unit": "vulnerabilities",
                },
            },
            "fix_time_distribution": self._get_fix_time_distribution(),
        }
    
    def _get_fix_time_distribution(self) -> Dict[str, int]:
        """Get distribution of fix times."""
        
        fix_times = metrics_collector._fix_times
        
        distribution = {
            "< 1 hour": 0,
            "1-4 hours": 0,
            "4-8 hours": 0,
            "8-24 hours": 0,
            "> 24 hours": 0,
        }
        
        for time_seconds in fix_times:
            hours = time_seconds / 3600
            if hours < 1:
                distribution["< 1 hour"] += 1
            elif hours < 4:
                distribution["1-4 hours"] += 1
            elif hours < 8:
                distribution["4-8 hours"] += 1
            elif hours < 24:
                distribution["8-24 hours"] += 1
            else:
                distribution["> 24 hours"] += 1
        
        return distribution
    
    def get_agent_dashboard(self) -> Dict[str, Any]:
        """Get agent health dashboard data."""
        
        latencies = metrics_collector._latencies
        
        return {
            "title": "Agent Health Dashboard",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {
                "orchestrator": {"status": "healthy", "port": 8000},
                "security-scanner": {"status": "healthy", "port": 8001},
                "risk-assessment": {"status": "healthy", "port": 8002},
                "auto-remediation": {"status": "healthy", "port": 8003},
            },
            "latencies": {
                key: {
                    "average_ms": round(sum(vals) / len(vals) * 1000, 2) if vals else 0,
                    "max_ms": round(max(vals) * 1000, 2) if vals else 0,
                    "min_ms": round(min(vals) * 1000, 2) if vals else 0,
                }
                for key, vals in latencies.items()
            },
        }
    
    # ===== Alerting =====
    
    def create_alert(
        self,
        severity: str,
        title: str,
        message: str,
        source: str,
    ) -> Alert:
        """Create a new alert."""
        
        alert = Alert(
            id=f"alert-{len(self.alerts)+1:04d}",
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=datetime.utcnow(),
        )
        
        self.alerts.append(alert)
        
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                return True
        
        return False
    
    def check_alert_rules(self, context: Dict[str, Any]):
        """Check alert rules against current context."""
        
        # Check agent health
        for agent, health in context.get("agent_health", {}).items():
            if not health:
                self.create_alert(
                    severity="critical",
                    title="Agent Unhealthy",
                    message=f"Agent {agent} is not responding",
                    source="health_monitor",
                )
        
        # Check remediation success rate
        success_rate = context.get("remediation_success_rate", 100)
        if success_rate < 50 and metrics_collector._remediation_attempts > 5:
            self.create_alert(
                severity="warning",
                title="Low Remediation Success Rate",
                message=f"Success rate is {success_rate:.1f}%",
                source="metrics_monitor",
            )
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[Alert]:
        """Get alerts with optional filters."""
        
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return alerts
    
    def export_dashboard_json(self) -> str:
        """Export dashboard data as JSON."""
        
        data = {
            "overview": self.get_system_overview(),
            "vulnerabilities": self.get_vulnerability_dashboard(),
            "remediation": self.get_remediation_dashboard(),
            "agents": self.get_agent_dashboard(),
        }
        
        # Convert datetime objects to strings
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Alert):
                return {
                    "id": obj.id,
                    "severity": obj.severity,
                    "title": obj.title,
                    "message": obj.message,
                    "source": obj.source,
                    "timestamp": obj.timestamp.isoformat(),
                    "resolved": obj.resolved,
                }
            return obj
        
        return json.dumps(data, default=serialize, indent=2)
