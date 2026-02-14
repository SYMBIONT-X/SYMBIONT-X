import {
  makeStyles,
  shorthands,
  Text,
  tokens,
} from '@fluentui/react-components';
import { AgentCard } from '@components/Agents/AgentCard';

const useStyles = makeStyles({
  page: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('24px'),
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  agentsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
    ...shorthands.gap('20px'),
  },
});

// Mock agent data
const agents = [
  {
    id: 'security-scanner',
    name: 'Security Scanner Agent',
    description: 'Continuous vulnerability detection across code, dependencies, containers, and IaC',
    status: 'running' as const,
    lastActivity: '2 minutes ago',
    metrics: {
      scansToday: 147,
      vulnerabilitiesFound: 23,
      avgScanTime: '12s',
    },
    icon: '🔍',
  },
  {
    id: 'risk-assessment',
    name: 'Risk Assessment Agent',
    description: 'AI-powered business context analysis using Microsoft Foundry GPT-4',
    status: 'running' as const,
    lastActivity: '1 minute ago',
    metrics: {
      assessmentsToday: 89,
      avgAssessmentTime: '3.2s',
      accuracy: '97.3%',
    },
    icon: '🧠',
  },
  {
    id: 'auto-remediation',
    name: 'Auto-Remediation Agent',
    description: 'Automated fix generation using GitHub Copilot Agent Mode',
    status: 'running' as const,
    lastActivity: '5 minutes ago',
    metrics: {
      fixesGenerated: 67,
      prsCreated: 45,
      successRate: '94.1%',
    },
    icon: '🔧',
  },
  {
    id: 'orchestrator',
    name: 'Orchestrator Agent',
    description: 'Central coordination hub managing workflow state and agent communication',
    status: 'running' as const,
    lastActivity: 'Just now',
    metrics: {
      workflowsActive: 12,
      messagesProcessed: 1847,
      uptime: '99.9%',
    },
    icon: '🎯',
  },
];

export const AgentsPage: React.FC = () => {
  const styles = useStyles();

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <Text size={700} weight="semibold" block>
            AI Agents
          </Text>
          <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
            Monitor and manage the multi-agent system
          </Text>
        </div>
      </div>

      {/* Agents Grid */}
      <div className={styles.agentsGrid}>
        {agents.map((agent) => (
          <AgentCard key={agent.id} {...agent} />
        ))}
      </div>
    </div>
  );
};
