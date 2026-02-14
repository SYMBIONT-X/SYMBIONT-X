import {
  makeStyles,
  shorthands,
  Text,
  Badge,
  ProgressBar,
  tokens,
} from '@fluentui/react-components';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('16px'),
    marginTop: '16px',
  },
  agentRow: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('8px'),
    ...shorthands.padding('12px'),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius('8px'),
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  name: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('8px'),
  },
  metrics: {
    display: 'flex',
    ...shorthands.gap('16px'),
    marginTop: '4px',
  },
  metric: {
    display: 'flex',
    flexDirection: 'column',
  },
});

interface AgentStatus {
  name: string;
  icon: string;
  status: 'running' | 'idle' | 'error';
  load: number;
  tasksCompleted: number;
}

const agents: AgentStatus[] = [
  {
    name: 'Security Scanner',
    icon: '🔍',
    status: 'running',
    load: 65,
    tasksCompleted: 147,
  },
  {
    name: 'Risk Assessment',
    icon: '🧠',
    status: 'running',
    load: 42,
    tasksCompleted: 89,
  },
  {
    name: 'Auto-Remediation',
    icon: '🔧',
    status: 'running',
    load: 28,
    tasksCompleted: 67,
  },
  {
    name: 'Orchestrator',
    icon: '🎯',
    status: 'running',
    load: 15,
    tasksCompleted: 1847,
  },
];

const statusColors = {
  running: 'success',
  idle: 'warning',
  error: 'danger',
} as const;

export const AgentStatusOverview: React.FC = () => {
  const styles = useStyles();

  return (
    <div className={styles.container}>
      {agents.map((agent) => (
        <div key={agent.name} className={styles.agentRow}>
          <div className={styles.header}>
            <div className={styles.name}>
              <span>{agent.icon}</span>
              <Text weight="medium">{agent.name}</Text>
            </div>
            <Badge
              size="small"
              appearance="filled"
              color={statusColors[agent.status]}
            >
              {agent.status}
            </Badge>
          </div>

          <ProgressBar
            value={agent.load / 100}
            thickness="medium"
            color={agent.load > 80 ? 'error' : agent.load > 60 ? 'warning' : 'brand'}
          />

          <div className={styles.metrics}>
            <div className={styles.metric}>
              <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                Load
              </Text>
              <Text weight="semibold">{agent.load}%</Text>
            </div>
            <div className={styles.metric}>
              <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                Tasks Today
              </Text>
              <Text weight="semibold">{agent.tasksCompleted}</Text>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
