/**
 * Hook for dashboard metrics with real data
 */

import { useState, useEffect, useCallback } from 'react';
import { orchestratorService } from '../services';
import type { Workflow } from '../types/api.types';

interface VulnerabilitySummary {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  byPriority: {
    P0: number;
    P1: number;
    P2: number;
    P3: number;
    P4: number;
  };
}

interface RemediationStats {
  totalAttempts: number;
  totalSuccesses: number;
  successRate: number;
  averageFixTimeMinutes: number;
  timeSavedHours: number;
}

interface TrendData {
  time: string;
  detected: number;
  fixed: number;
}

interface DashboardMetrics {
  vulnerabilities: VulnerabilitySummary;
  remediation: RemediationStats;
  workflows: {
    total: number;
    active: number;
    completed: number;
    failed: number;
    awaitingApproval: number;
  };
  trends: TrendData[];
  lastUpdated: string;
}

const MANUAL_FIX_TIME_HOURS = 4; // Estimated manual fix time per vulnerability

export function useDashboardMetrics(refreshInterval = 10000) {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const calculateMetrics = useCallback((workflows: Workflow[]): DashboardMetrics => {
    // Initialize counters
    const vulnSummary: VulnerabilitySummary = {
      total: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      byPriority: { P0: 0, P1: 0, P2: 0, P3: 0, P4: 0 },
    };

    let totalFixed = 0;
    let totalAttempts = 0;
    const hourlyData: Record<string, { detected: number; fixed: number }> = {};

    // Process each workflow
    workflows.forEach((workflow) => {
      // Get assessment data
      const assessStep = workflow.steps.find((s) => s.step_id === 'assess');
      if (assessStep?.output_data?.assessments) {
        const assessments = assessStep.output_data.assessments as Array<{
          severity: string;
          risk_score: { priority: string };
        }>;

        assessments.forEach((assessment) => {
          vulnSummary.total += 1;

          // Count by severity
          const severity = assessment.severity?.toLowerCase() || 'unknown';
          if (severity === 'critical') vulnSummary.critical += 1;
          else if (severity === 'high') vulnSummary.high += 1;
          else if (severity === 'medium') vulnSummary.medium += 1;
          else if (severity === 'low') vulnSummary.low += 1;

          // Count by priority
          const priority = assessment.risk_score?.priority || 'P2';
          if (priority in vulnSummary.byPriority) {
            vulnSummary.byPriority[priority as keyof typeof vulnSummary.byPriority] += 1;
          }
        });
      }

      // Track remediation
      totalFixed += workflow.auto_remediated || 0;
      totalAttempts += workflow.total_vulnerabilities || 0;

      // Build hourly trend
      const hour = new Date(workflow.created_at).toISOString().slice(0, 13);
      if (!hourlyData[hour]) {
        hourlyData[hour] = { detected: 0, fixed: 0 };
      }
      hourlyData[hour].detected += workflow.total_vulnerabilities || 0;
      hourlyData[hour].fixed += workflow.auto_remediated || 0;
    });

    // Calculate remediation stats
    const successRate = totalAttempts > 0 ? (totalFixed / totalAttempts) * 100 : 0;
    const avgFixTimeMinutes = 5; // Automated fix time
    const timeSavedHours = totalFixed * (MANUAL_FIX_TIME_HOURS - avgFixTimeMinutes / 60);

    // Build trend data (last 12 hours)
    const trends: TrendData[] = [];
    const now = new Date();
    for (let i = 11; i >= 0; i--) {
      const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hourKey = hour.toISOString().slice(0, 13);
      const hourLabel = hour.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      trends.push({
        time: hourLabel,
        detected: hourlyData[hourKey]?.detected || 0,
        fixed: hourlyData[hourKey]?.fixed || 0,
      });
    }

    // Calculate workflow stats
    const workflowStats = {
      total: workflows.length,
      active: workflows.filter((w) => ['scanning', 'assessing', 'remediating'].includes(w.status)).length,
      completed: workflows.filter((w) => w.status === 'completed').length,
      failed: workflows.filter((w) => w.status === 'failed').length,
      awaitingApproval: workflows.filter((w) => w.status === 'awaiting_approval').length,
    };

    return {
      vulnerabilities: vulnSummary,
      remediation: {
        totalAttempts,
        totalSuccesses: totalFixed,
        successRate,
        averageFixTimeMinutes: avgFixTimeMinutes,
        timeSavedHours: Math.max(0, timeSavedHours),
      },
      workflows: workflowStats,
      trends,
      lastUpdated: new Date().toISOString(),
    };
  }, []);

  const fetchMetrics = useCallback(async () => {
    try {
      const workflowsResponse = await orchestratorService.listWorkflows({ limit: 50 });
      const calculatedMetrics = calculateMetrics(workflowsResponse.workflows);
      setMetrics(calculatedMetrics);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  }, [calculateMetrics]);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMetrics, refreshInterval]);

  return { metrics, loading, error, refresh: fetchMetrics };
}
