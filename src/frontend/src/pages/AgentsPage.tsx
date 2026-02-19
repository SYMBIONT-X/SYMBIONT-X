import { useState, useEffect } from 'react';
import {
  Card,
  Title1 as Title,
  Text,
  Button,
  Spinner,
  Badge,
} from '@fluentui/react-components';
import { ArrowSync24Regular } from '@fluentui/react-icons';
import { useAgentStatus } from '../hooks';
import { scannerService, remediationService, assessmentService } from '../services';

interface AgentDetails {
  scanners?: Record<string, boolean>;
  ai_enabled?: boolean;
  github_enabled?: boolean;
  templates_count?: number;
}

export function AgentsPage() {
  const { agents, allHealthy, loading, refresh } = useAgentStatus(10000);
  const [details, setDetails] = useState<Record<string, AgentDetails>>({});
  const [loadingDetails, setLoadingDetails] = useState(true);

  useEffect(() => {
    async function fetchDetails() {
      setLoadingDetails(true);
      try {
        const [scannerHealth, assessmentHealth, remediationHealth] = await Promise.all([
          scannerService.getHealth().catch(() => null),
          assessmentService.getHealth().catch(() => null),
          remediationService.getHealth().catch(() => null),
        ]);

        setDetails({
          'security-scanner': scannerHealth ? { scanners: scannerHealth.scanners } : {},
          'risk-assessment': assessmentHealth ? { ai_enabled: assessmentHealth.ai_enabled } : {},
          'auto-remediation': remediationHealth ? {
            ai_enabled: remediationHealth.ai_enabled,
            github_enabled: remediationHealth.github_enabled,
            templates_count: remediationHealth.templates_count,
          } : {},
        });
      } catch (err) {
        console.error('Failed to fetch agent details:', err);
      } finally {
        setLoadingDetails(false);
      }
    }

    fetchDetails();
  }, [agents]);

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <Title>Agents</Title>
          <Text>Monitor SYMBIONT-X agent status and capabilities</Text>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {allHealthy ? (
            <Badge appearance="filled" color="success">All Systems Operational</Badge>
          ) : (
            <Badge appearance="filled" color="danger">Issues Detected</Badge>
          )}
          <Button icon={<ArrowSync24Regular />} onClick={refresh}>
            Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <Spinner size="large" label="Loading agents..." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {agents.map((agent) => (
            <Card key={agent.name} style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <Text size={500} weight="semibold">{agent.name}</Text>
                    <Badge
                      appearance="filled"
                      color={agent.status === 'healthy' ? 'success' : 'danger'}
                    >
                      {agent.status}
                    </Badge>
                  </div>
                  <Text size={300} style={{ color: '#666' }}>{agent.url}</Text>
                  {agent.version && (
                    <Text size={200} style={{ color: '#888', display: 'block' }}>
                      Version: {agent.version}
                    </Text>
                  )}
                </div>
              </div>

              {/* Agent-specific details */}
              {!loadingDetails && details[agent.name] && (
                <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #eee' }}>
                  {agent.name === 'security-scanner' && details[agent.name].scanners && (
                    <div>
                      <Text weight="medium" size={300}>Scanners:</Text>
                      <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
                        {Object.entries(details[agent.name].scanners!).map(([name, available]) => (
                          <Badge
                            key={name}
                            appearance="outline"
                            color={available ? 'success' : 'danger'}
                          >
                            {name}: {available ? '✓' : '✗'}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {agent.name === 'risk-assessment' && (
                    <div style={{ display: 'flex', gap: '16px' }}>
                      <Badge appearance="outline" color={details[agent.name].ai_enabled ? 'success' : 'warning'}>
                        AI Analysis: {details[agent.name].ai_enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                  )}

                  {agent.name === 'auto-remediation' && (
                    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                      <Badge appearance="outline" color={details[agent.name].github_enabled ? 'success' : 'warning'}>
                        GitHub: {details[agent.name].github_enabled ? 'Connected' : 'Not configured'}
                      </Badge>
                      <Badge appearance="outline" color={details[agent.name].ai_enabled ? 'success' : 'warning'}>
                        AI: {details[agent.name].ai_enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                      <Badge appearance="outline" color="informative">
                        Templates: {details[agent.name].templates_count || 0}
                      </Badge>
                    </div>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
