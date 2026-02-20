import { useState } from 'react';
import {
  Card,
  Title1 as Title,
  Text,
  Button,
  Spinner,
  Badge,
  Dropdown,
  Option,
} from '@fluentui/react-components';
import {
  ShieldCheckmark24Regular,
  ArrowSync24Regular,
  Play24Regular,
  Clock24Regular,
  Checkmark24Regular,
  Warning24Regular,
} from '@fluentui/react-icons';
import { useAgentStatus, useWorkflows, useDashboardMetrics } from '../hooks';
import {
  VulnerabilityPieChart,
  TrendLineChart,
  PriorityBarChart,
  MetricCard,
} from '../components/Charts';

type TimeRange = '1h' | '6h' | '12h' | '24h' | '7d';

export function DashboardPage() {
  const { agents, allHealthy } = useAgentStatus(5000);
  const { startWorkflow } = useWorkflows(5000);
  const { metrics, loading, refresh } = useDashboardMetrics(5000);
  
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStartScan = async () => {
    setStarting(true);
    setError(null);
    try {
      await startWorkflow({
        repository: 'SYMBIONT-X/SYMBIONT-X',
        branch: 'main',
        scan_types: ['dependency', 'code', 'secret', 'container', 'iac'],
        auto_remediate: true,
      });
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start scan');
    } finally {
      setStarting(false);
    }
  };

  if (loading && !metrics) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spinner size="large" label="Loading dashboard..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <Title style={{ margin: 0 }}>Executive Dashboard</Title>
          <Text style={{ color: '#64748b' }}>
            SYMBIONT-X Security Overview • Last updated: {metrics ? new Date(metrics.lastUpdated).toLocaleTimeString() : '-'}
          </Text>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <Dropdown
            value={timeRange}
            onOptionSelect={(_, data) => setTimeRange(data.optionValue as TimeRange)}
            style={{ minWidth: '120px' }}
          >
            <Option value="1h">Last 1 hour</Option>
            <Option value="6h">Last 6 hours</Option>
            <Option value="12h">Last 12 hours</Option>
            <Option value="24h">Last 24 hours</Option>
            <Option value="7d">Last 7 days</Option>
          </Dropdown>
          <Button icon={<ArrowSync24Regular />} onClick={refresh}>
            Refresh
          </Button>
          <Button
            appearance="primary"
            icon={<Play24Regular />}
            onClick={handleStartScan}
            disabled={starting || !allHealthy}
          >
            {starting ? 'Starting...' : 'Start Scan'}
          </Button>
        </div>
      </div>

      {error && (
        <Card style={{ padding: '12px', marginBottom: '16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca' }}>
          <Text style={{ color: '#dc2626' }}>{error}</Text>
        </Card>
      )}

      {/* Agent Status Bar */}
      <Card style={{ padding: '12px 16px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheckmark24Regular />
            <Text weight="semibold">System Status:</Text>
            <Badge appearance="filled" color={allHealthy ? 'success' : 'danger'}>
              {allHealthy ? 'All Systems Operational' : 'Issues Detected'}
            </Badge>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '12px' }}>
            {agents.map((agent) => (
              <Badge
                key={agent.name}
                appearance="outline"
                color={agent.status === 'healthy' ? 'success' : 'danger'}
              >
                {agent.name}: {agent.status}
              </Badge>
            ))}
          </div>
        </div>
      </Card>

      {/* KPI Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <MetricCard
          title="Total Vulnerabilities"
          value={metrics?.vulnerabilities.total || 0}
          icon={<Warning24Regular />}
          color={metrics?.vulnerabilities.critical ? 'danger' : 'default'}
          trend={metrics?.vulnerabilities.total ? {
            value: 12,
            direction: 'down',
            isPositive: true,
          } : undefined}
        />
        <MetricCard
          title="Critical / High"
          value={`${metrics?.vulnerabilities.critical || 0} / ${metrics?.vulnerabilities.high || 0}`}
          icon={<ShieldCheckmark24Regular />}
          color={metrics?.vulnerabilities.critical ? 'danger' : metrics?.vulnerabilities.high ? 'warning' : 'success'}
        />
        <MetricCard
          title="Auto-Fix Success Rate"
          value={metrics?.remediation.successRate.toFixed(1) || '0'}
          unit="%"
          icon={<Checkmark24Regular />}
          color={
            (metrics?.remediation.successRate || 0) >= 80 ? 'success' :
            (metrics?.remediation.successRate || 0) >= 50 ? 'warning' : 'danger'
          }
        />
        <MetricCard
          title="Time Saved"
          value={metrics?.remediation.timeSavedHours.toFixed(1) || '0'}
          unit="hours"
          icon={<Clock24Regular />}
          color="success"
        />
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* Vulnerability by Severity */}
        <Card style={{ padding: '20px' }}>
          <Text weight="semibold" size={400} style={{ marginBottom: '16px', display: 'block' }}>
            Vulnerabilities by Severity
          </Text>
          <VulnerabilityPieChart
            data={{
              critical: metrics?.vulnerabilities.critical || 0,
              high: metrics?.vulnerabilities.high || 0,
              medium: metrics?.vulnerabilities.medium || 0,
              low: metrics?.vulnerabilities.low || 0,
            }}
          />
        </Card>

        {/* Vulnerability by Priority */}
        <Card style={{ padding: '20px' }}>
          <Text weight="semibold" size={400} style={{ marginBottom: '16px', display: 'block' }}>
            Vulnerabilities by Priority
          </Text>
          <PriorityBarChart data={metrics?.vulnerabilities.byPriority || { P0: 0, P1: 0, P2: 0, P3: 0, P4: 0 }} />
        </Card>
      </div>

      {/* Trend Chart */}
      <Card style={{ padding: '20px', marginBottom: '24px' }}>
        <TrendLineChart
          data={metrics?.trends || []}
          title="Detection & Remediation Trend (Last 12 Hours)"
        />
      </Card>

      {/* Workflow Summary */}
      <Card style={{ padding: '20px' }}>
        <Text weight="semibold" size={400} style={{ marginBottom: '16px', display: 'block' }}>
          Workflow Summary
        </Text>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px' }}>
          <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
            <Text size={600} weight="bold" style={{ display: 'block' }}>
              {metrics?.workflows.total || 0}
            </Text>
            <Text size={200} style={{ color: '#64748b' }}>Total</Text>
          </div>
          <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#eff6ff', borderRadius: '8px' }}>
            <Text size={600} weight="bold" style={{ display: 'block', color: '#2563eb' }}>
              {metrics?.workflows.active || 0}
            </Text>
            <Text size={200} style={{ color: '#64748b' }}>Active</Text>
          </div>
          <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#f0fdf4', borderRadius: '8px' }}>
            <Text size={600} weight="bold" style={{ display: 'block', color: '#16a34a' }}>
              {metrics?.workflows.completed || 0}
            </Text>
            <Text size={200} style={{ color: '#64748b' }}>Completed</Text>
          </div>
          <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#fffbeb', borderRadius: '8px' }}>
            <Text size={600} weight="bold" style={{ display: 'block', color: '#ca8a04' }}>
              {metrics?.workflows.awaitingApproval || 0}
            </Text>
            <Text size={200} style={{ color: '#64748b' }}>Awaiting</Text>
          </div>
          <div style={{ textAlign: 'center', padding: '16px', backgroundColor: '#fef2f2', borderRadius: '8px' }}>
            <Text size={600} weight="bold" style={{ display: 'block', color: '#dc2626' }}>
              {metrics?.workflows.failed || 0}
            </Text>
            <Text size={200} style={{ color: '#64748b' }}>Failed</Text>
          </div>
        </div>
      </Card>
    </div>
  );
}
