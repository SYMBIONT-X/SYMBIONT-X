"""Custom metrics for SYMBIONT-X monitoring."""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import defaultdict
import threading

from prometheus_client import Counter, Histogram, Gauge, Info, REGISTRY


@dataclass
class MetricEvent:
    """A single metric event."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and exposes metrics for SYMBIONT-X agents."""
    
    def __init__(self, agent_name: str = "symbiont-x"):
        self.agent_name = agent_name
        self._lock = threading.Lock()
        
        # Time-series data storage (in-memory)
        self._events: Dict[str, List[MetricEvent]] = defaultdict(list)
        
        # Prometheus metrics
        self._init_prometheus_metrics()
        
        # Custom aggregations
        self._hourly_vulns: Dict[str, int] = defaultdict(int)
        self._remediation_attempts: int = 0
        self._remediation_successes: int = 0
        self._fix_times: List[float] = []
        self._latencies: Dict[str, List[float]] = defaultdict(list)
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        
        # Counters
        self.vulnerabilities_total = Counter(
            'symbiontx_vulnerabilities_total',
            'Total vulnerabilities detected',
            ['severity', 'priority', 'agent']
        )
        
        self.scans_total = Counter(
            'symbiontx_scans_total',
            'Total scans performed',
            ['scan_type', 'status']
        )
        
        self.remediations_total = Counter(
            'symbiontx_remediations_total',
            'Total remediation attempts',
            ['status', 'fix_type']
        )
        
        self.workflows_total = Counter(
            'symbiontx_workflows_total',
            'Total workflows executed',
            ['status']
        )
        
        # Histograms
        self.scan_duration = Histogram(
            'symbiontx_scan_duration_seconds',
            'Scan duration in seconds',
            ['scan_type'],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600]
        )
        
        self.fix_duration = Histogram(
            'symbiontx_fix_duration_seconds',
            'Time to fix vulnerability in seconds',
            ['priority'],
            buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800]
        )
        
        self.agent_latency = Histogram(
            'symbiontx_agent_latency_seconds',
            'Agent-to-agent communication latency',
            ['source_agent', 'target_agent'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        )
        
        # Gauges
        self.active_workflows = Gauge(
            'symbiontx_active_workflows',
            'Number of active workflows'
        )
        
        self.pending_approvals = Gauge(
            'symbiontx_pending_approvals',
            'Number of pending approvals'
        )
        
        self.agent_health = Gauge(
            'symbiontx_agent_health',
            'Agent health status (1=healthy, 0=unhealthy)',
            ['agent']
        )
        
        self.vulnerabilities_by_priority = Gauge(
            'symbiontx_vulnerabilities_by_priority',
            'Current vulnerabilities by priority',
            ['priority']
        )
    
    # ===== Vulnerability Metrics =====
    
    def record_vulnerability(
        self,
        severity: str,
        priority: str,
        agent: str = "security-scanner",
    ):
        """Record a detected vulnerability."""
        
        with self._lock:
            self.vulnerabilities_total.labels(
                severity=severity,
                priority=priority,
                agent=agent,
            ).inc()
            
            # Track hourly
            hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
            self._hourly_vulns[hour_key] += 1
            
            self._events["vulnerabilities"].append(MetricEvent(
                timestamp=datetime.utcnow(),
                value=1,
                labels={"severity": severity, "priority": priority},
            ))
    
    def get_vulnerabilities_per_hour(self, hours: int = 24) -> Dict[str, int]:
        """Get vulnerabilities detected per hour for the last N hours."""
        
        result = {}
        now = datetime.utcnow()
        
        for i in range(hours):
            hour = now - timedelta(hours=i)
            hour_key = hour.strftime("%Y-%m-%d-%H")
            result[hour_key] = self._hourly_vulns.get(hour_key, 0)
        
        return result
    
    # ===== Scan Metrics =====
    
    def record_scan(
        self,
        scan_type: str,
        status: str,
        duration_seconds: float,
    ):
        """Record a scan execution."""
        
        self.scans_total.labels(scan_type=scan_type, status=status).inc()
        self.scan_duration.labels(scan_type=scan_type).observe(duration_seconds)
        
        self._events["scans"].append(MetricEvent(
            timestamp=datetime.utcnow(),
            value=duration_seconds,
            labels={"scan_type": scan_type, "status": status},
        ))
    
    # ===== Remediation Metrics =====
    
    def record_remediation(
        self,
        status: str,
        fix_type: str,
        duration_seconds: Optional[float] = None,
        priority: str = "P2",
    ):
        """Record a remediation attempt."""
        
        with self._lock:
            self.remediations_total.labels(status=status, fix_type=fix_type).inc()
            
            self._remediation_attempts += 1
            if status == "success":
                self._remediation_successes += 1
            
            if duration_seconds is not None:
                self.fix_duration.labels(priority=priority).observe(duration_seconds)
                self._fix_times.append(duration_seconds)
    
    def get_remediation_success_rate(self) -> float:
        """Get auto-remediation success rate."""
        
        if self._remediation_attempts == 0:
            return 0.0
        
        return self._remediation_successes / self._remediation_attempts * 100
    
    def get_average_fix_time(self) -> float:
        """Get average time to fix in seconds."""
        
        if not self._fix_times:
            return 0.0
        
        return sum(self._fix_times) / len(self._fix_times)
    
    # ===== Workflow Metrics =====
    
    def record_workflow(self, status: str):
        """Record a workflow execution."""
        
        self.workflows_total.labels(status=status).inc()
    
    def set_active_workflows(self, count: int):
        """Set the number of active workflows."""
        
        self.active_workflows.set(count)
    
    def set_pending_approvals(self, count: int):
        """Set the number of pending approvals."""
        
        self.pending_approvals.set(count)
    
    # ===== Agent Metrics =====
    
    def record_agent_latency(
        self,
        source_agent: str,
        target_agent: str,
        latency_seconds: float,
    ):
        """Record agent-to-agent communication latency."""
        
        self.agent_latency.labels(
            source_agent=source_agent,
            target_agent=target_agent,
        ).observe(latency_seconds)
        
        key = f"{source_agent}->{target_agent}"
        self._latencies[key].append(latency_seconds)
    
    def set_agent_health(self, agent: str, healthy: bool):
        """Set agent health status."""
        
        self.agent_health.labels(agent=agent).set(1 if healthy else 0)
    
    def get_average_latency(self, source: str, target: str) -> float:
        """Get average latency between two agents."""
        
        key = f"{source}->{target}"
        latencies = self._latencies.get(key, [])
        
        if not latencies:
            return 0.0
        
        return sum(latencies) / len(latencies)
    
    # ===== Summary =====
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        
        return {
            "vulnerabilities_per_hour": self.get_vulnerabilities_per_hour(24),
            "remediation_success_rate": self.get_remediation_success_rate(),
            "average_fix_time_seconds": self.get_average_fix_time(),
            "total_remediation_attempts": self._remediation_attempts,
            "total_remediation_successes": self._remediation_successes,
            "latencies": {
                key: sum(vals) / len(vals) if vals else 0
                for key, vals in self._latencies.items()
            },
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()
