import { useState, useEffect } from 'react';
import {
  Card,
  Title1 as Title,
  Text,
  Button,
  Spinner,
  Badge,
  MessageBar,
} from '@fluentui/react-components';
import {
  ShieldCheckmark24Regular,
  ArrowSync24Regular,
  Play24Regular,
} from '@fluentui/react-icons';
import { useAgentStatus, useWorkflows } from '../hooks';
import { orchestratorService } from '../services';

export function DashboardPage() {
  const { agents, allHealthy, loading: agentsLoading } = useAgentStatus(5000);
  const { workflows, loading: workflowsLoading, startWorkflow } = useWorkflows(3000);
  const [stats, setStats] = useState<{ workflows: { total: number; by_status: Record<string, number> } } | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    orchestratorService.getStats().then(setStats).catch(console.error);
  }, []);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start scan');
    } finally {
      setStarting(false);
    }
  };

  const activeWorkflows = workflows.filter(
    (w) => !['completed', 'failed', 'cancelled'].includes(w.status)
  );

  const recentWorkflows = workflows.slice(0, 5);

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <Title style={{ margin: 0 }}>Dashboard</Title>
          <Text>SYMBIONT-X Security Overview</Text>
        </div>
        <Button
          appearance="primary"
          icon={<Play24Regular />}
          onClick={handleStartScan}
          disabled={starting || !allHealthy}
        >
          {starting ? 'Starting...' : 'Start Security Scan'}
        </Button>
      </div>

      {error && (
        <MessageBar intent="error" style={{ marginBottom: '16px' }}>
          {error}
        </MessageBar>
      )}

      {/* Agent Status */}
      <Card style={{ marginBottom: '24px', padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <ShieldCheckmark24Regular />
          <Text weight="semibold" size={500}>Agent Status</Text>
          {allHealthy ? (
            <Badge appearance="filled" color="success">All Healthy</Badge>
          ) : (
            <Badge appearance="filled" color="danger">Issues Detected</Badge>
          )}
        </div>

        {agentsLoading ? (
          <Spinner size="small" label="Loading agents..." />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            {agents.map((agent) => (
              <Card key={agent.name} style={{ padding: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text weight="medium">{agent.name}</Text>
                  <Badge
                    appearance="filled"
                    color={agent.status === 'healthy' ? 'success' : 'danger'}
                  >
                    {agent.status}
                  </Badge>
                </div>
                <Text size={200} style={{ color: '#666' }}>
                  {agent.version || 'Unknown version'}
                </Text>
              </Card>
            ))}
          </div>
        )}
      </Card>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <Card style={{ padding: '16px', textAlign: 'center' }}>
          <Text size={600} weight="semibold">{stats?.workflows.total || 0}</Text>
          <Text size={200}>Total Workflows</Text>
        </Card>
        <Card style={{ padding: '16px', textAlign: 'center' }}>
          <Text size={600} weight="semibold">{activeWorkflows.length}</Text>
          <Text size={200}>Active</Text>
        </Card>
        <Card style={{ padding: '16px', textAlign: 'center' }}>
          <Text size={600} weight="semibold">{stats?.workflows.by_status?.completed || 0}</Text>
          <Text size={200}>Completed</Text>
        </Card>
        <Card style={{ padding: '16px', textAlign: 'center' }}>
          <Text size={600} weight="semibold">{stats?.workflows.by_status?.failed || 0}</Text>
          <Text size={200}>Failed</Text>
        </Card>
      </div>

      {/* Recent Workflows */}
      <Card style={{ padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <ArrowSync24Regular />
          <Text weight="semibold" size={500}>Recent Workflows</Text>
        </div>

        {workflowsLoading ? (
          <Spinner size="small" label="Loading workflows..." />
        ) : recentWorkflows.length === 0 ? (
          <Text style={{ color: '#666' }}>No workflows yet. Start a scan to begin.</Text>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {recentWorkflows.map((workflow) => (
              <Card key={workflow.workflow_id} style={{ padding: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <Text weight="medium">{workflow.repository}</Text>
                    <Text size={200} style={{ color: '#666', display: 'block' }}>
                      {workflow.workflow_id.slice(0, 8)}... • {workflow.branch}
                    </Text>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <Badge
                      appearance="filled"
                      color={
                        workflow.status === 'completed' ? 'success' :
                        workflow.status === 'failed' ? 'danger' :
                        workflow.status === 'awaiting_approval' ? 'warning' :
                        'informative'
                      }
                    >
                      {workflow.status}
                    </Badge>
                    <Text size={200} style={{ color: '#666', display: 'block' }}>
                      {workflow.total_vulnerabilities} vulns
                    </Text>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
