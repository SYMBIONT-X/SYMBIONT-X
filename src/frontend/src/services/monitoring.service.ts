/**
 * Monitoring Service for SYMBIONT-X
 */

import { api } from './api';

export interface MetricsSummary {
  vulnerabilities_per_hour: Record<string, number>;
  remediation_success_rate: number;
  average_fix_time_seconds: number;
  total_remediation_attempts: number;
  total_remediation_successes: number;
  latencies: Record<string, number>;
}

export interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  source: string;
  timestamp: string;
  resolved: boolean;
}

export interface DashboardOverview {
  timestamp: string;
  system_status: 'healthy' | 'warning' | 'critical';
  metrics: {
    vulnerabilities: {
      per_hour: Record<string, number>;
      total_last_24h: number;
    };
    remediation: {
      success_rate: number;
      average_fix_time_seconds: number;
      total_attempts: number;
      total_successes: number;
    };
    latencies: Record<string, number>;
  };
  active_alerts: Alert[];
}

export const monitoringService = {
  /**
   * Get metrics summary
   */
  async getMetricsSummary(): Promise<MetricsSummary> {
    return api.get('orchestrator', '/monitoring/metrics/summary');
  },

  /**
   * Get dashboard overview
   */
  async getDashboardOverview(): Promise<DashboardOverview> {
    return api.get('orchestrator', '/monitoring/dashboard/overview');
  },

  /**
   * Get vulnerability dashboard
   */
  async getVulnerabilityDashboard(): Promise<{
    title: string;
    timestamp: string;
    summary: {
      total_24h: number;
      hourly_average: number;
      peak_hour: string | null;
    };
    hourly_trend: Record<string, number>;
  }> {
    return api.get('orchestrator', '/monitoring/dashboard/vulnerabilities');
  },

  /**
   * Get remediation dashboard
   */
  async getRemediationDashboard(): Promise<{
    title: string;
    timestamp: string;
    kpis: {
      success_rate: { value: number; unit: string; status: string };
      average_fix_time: { value: number; unit: string; status: string };
      total_fixed: { value: number; unit: string };
    };
  }> {
    return api.get('orchestrator', '/monitoring/dashboard/remediation');
  },

  /**
   * Get agent dashboard
   */
  async getAgentDashboard(): Promise<{
    title: string;
    timestamp: string;
    agents: Record<string, { status: string; port: number }>;
    latencies: Record<string, { average_ms: number; max_ms: number; min_ms: number }>;
  }> {
    return api.get('orchestrator', '/monitoring/dashboard/agents');
  },

  /**
   * Get alerts
   */
  async getAlerts(params?: {
    severity?: string;
    resolved?: boolean;
  }): Promise<{ total: number; alerts: Alert[] }> {
    const query = new URLSearchParams();
    if (params?.severity) query.set('severity', params.severity);
    if (params?.resolved !== undefined) query.set('resolved', String(params.resolved));
    
    const queryString = query.toString();
    return api.get('orchestrator', `/monitoring/alerts${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Resolve an alert
   */
  async resolveAlert(alertId: string): Promise<{ status: string }> {
    return api.post('orchestrator', `/monitoring/alerts/${alertId}/resolve`);
  },
};
