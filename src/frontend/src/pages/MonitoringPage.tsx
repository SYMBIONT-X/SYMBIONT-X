import { useState, useEffect } from 'react';
import {
  Card,
  Title1 as Title,
  Text,
  Spinner,
  Badge,
  Button,
} from '@fluentui/react-components';
import { ArrowSync24Regular } from '@fluentui/react-icons';
import { monitoringService } from '../services';
import type { DashboardOverview, Alert } from '../services/monitoring.service';

export function MonitoringPage() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [overviewData, alertsData] = await Promise.all([
        monitoringService.getDashboardOverview(),
        monitoringService.getAlerts({ resolved: false }),
      ]);
      setOverview(overviewData);
      setAlerts(alertsData.alerts);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const statusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'danger';
      default: return 'informative';
    }
  };

  if (loading && !overview) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spinner size="large" label="Loading monitoring data..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <Title>Monitoring</Title>
          <Text>System health and observability</Text>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {overview && (
            <Badge appearance="filled" color={statusColor(overview.system_status)}>
              System: {overview.system_status}
            </Badge>
          )}
          <Button icon={<ArrowSync24Regular />} onClick={fetchData}>
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Card style={{ padding: '16px', marginBottom: '16px', backgroundColor: '#fef2f2' }}>
          <Text style={{ color: '#dc2626' }}>{error}</Text>
        </Card>
      )}

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <Card style={{ padding: '20px', textAlign: 'center' }}>
          <Text size={200} weight="medium" style={{ color: '#666' }}>Vulnerabilities (24h)</Text>
          <Text size={700} weight="bold" style={{ display: 'block', marginTop: '8px' }}>
            {overview?.metrics.vulnerabilities.total_last_24h || 0}
          </Text>
        </Card>
        
        <Card style={{ padding: '20px', textAlign: 'center' }}>
          <Text size={200} weight="medium" style={{ color: '#666' }}>Remediation Success</Text>
          <Text size={700} weight="bold" style={{ display: 'block', marginTop: '8px' }}>
            {overview?.metrics.remediation.success_rate.toFixed(1) || 0}%
          </Text>
        </Card>
        
        <Card style={{ padding: '20px', textAlign: 'center' }}>
          <Text size={200} weight="medium" style={{ color: '#666' }}>Avg Fix Time</Text>
          <Text size={700} weight="bold" style={{ display: 'block', marginTop: '8px' }}>
            {overview?.metrics.remediation.average_fix_time_seconds 
              ? `${(overview.metrics.remediation.average_fix_time_seconds / 60).toFixed(1)}m`
              : '0m'
            }
          </Text>
        </Card>
        
        <Card style={{ padding: '20px', textAlign: 'center' }}>
          <Text size={200} weight="medium" style={{ color: '#666' }}>Total Fixed</Text>
          <Text size={700} weight="bold" style={{ display: 'block', marginTop: '8px' }}>
            {overview?.metrics.remediation.total_successes || 0}
          </Text>
        </Card>
      </div>

      {/* Alerts */}
      <Card style={{ padding: '16px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <Text weight="semibold" size={500}>Active Alerts</Text>
          <Badge appearance="filled" color={alerts.length > 0 ? 'danger' : 'success'}>
            {alerts.length} active
          </Badge>
        </div>

        {alerts.length === 0 ? (
          <Text style={{ color: '#666' }}>No active alerts. System is healthy.</Text>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {alerts.map((alert) => (
              <Card key={alert.id} style={{ padding: '12px', backgroundColor: alert.severity === 'critical' ? '#fef2f2' : '#fffbeb' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <Badge appearance="filled" color={alert.severity === 'critical' ? 'danger' : 'warning'}>
                      {alert.severity}
                    </Badge>
                    <Text weight="medium" style={{ marginLeft: '8px' }}>{alert.title}</Text>
                    <Text size={200} style={{ display: 'block', color: '#666', marginTop: '4px' }}>
                      {alert.message}
                    </Text>
                  </div>
                  <Text size={200} style={{ color: '#888' }}>
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </Text>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Card>

      {/* Agent Latencies */}
      <Card style={{ padding: '16px' }}>
        <Text weight="semibold" size={500} style={{ marginBottom: '16px', display: 'block' }}>
          Agent Communication Latencies
        </Text>
        
        {overview?.metrics.latencies && Object.keys(overview.metrics.latencies).length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            {Object.entries(overview.metrics.latencies).map(([route, latency]) => (
              <Card key={route} style={{ padding: '12px' }}>
                <Text size={200} style={{ color: '#666' }}>{route}</Text>
                <Text weight="medium" style={{ display: 'block' }}>
                  {(latency * 1000).toFixed(2)} ms
                </Text>
              </Card>
            ))}
          </div>
        ) : (
          <Text style={{ color: '#666' }}>No latency data yet. Run some workflows to collect metrics.</Text>
        )}
      </Card>
    </div>
  );
}
