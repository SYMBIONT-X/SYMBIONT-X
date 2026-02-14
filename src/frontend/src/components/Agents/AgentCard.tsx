import {
  makeStyles,
  shorthands,
  Text,
  Card,
  Badge,
  Button,
  tokens,
  Divider,
} from '@fluentui/react-components';
import {
  PlayRegular,
  PauseRegular,
  ArrowSyncRegular,
  MoreHorizontalRegular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  card: {
    ...shorthands.padding('20px'),
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '12px',
  },
  titleRow: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('12px'),
  },
  icon: {
    fontSize: '28px',
  },
  titleGroup: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('4px'),
  },
  actions: {
    display: 'flex',
    ...shorthands.gap('4px'),
  },
  description: {
    color: tokens.colorNeutralForeground3,
    marginBottom: '16px',
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    ...shorthands.gap('16px'),
    marginTop: '16px',
  },
  metric: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    ...shorthands.padding('12px'),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius('8px'),
  },
  metricValue: {
    fontSize: '20px',
    fontWeight: tokens.fontWeightBold,
    color: tokens.colorBrandForeground1,
  },
  metricLabel: {
    fontSize: '11px',
    color: tokens.colorNeutralForeground3,
    marginTop: '4px',
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '16px',
  },
});

interface AgentCardProps {
  id: string;
  name: string;
  description: string;
  status: 'running' | 'stopped' | 'error';
  lastActivity: string;
  metrics: Record<string, string | number>;
  icon: string;
}

const statusConfig = {
  running: { color: 'success' as const, label: 'Running' },
  stopped: { color: 'warning' as const, label: 'Stopped' },
  error: { color: 'danger' as const, label: 'Error' },
};

export const AgentCard: React.FC<AgentCardProps> = ({
  name,
  description,
  status,
  lastActivity,
  metrics,
  icon,
}) => {
  const styles = useStyles();
  const statusInfo = statusConfig[status];

  const metricEntries = Object.entries(metrics);

  return (
    <Card className={styles.card}>
      <div className={styles.header}>
        <div className={styles.titleRow}>
          <span className={styles.icon}>{icon}</span>
          <div className={styles.titleGroup}>
            <Text weight="semibold" size={400}>
              {name}
            </Text>
            <Badge size="small" appearance="filled" color={statusInfo.color}>
              {statusInfo.label}
            </Badge>
          </div>
        </div>

        <div className={styles.actions}>
          {status === 'running' ? (
            <Button
              appearance="subtle"
              icon={<PauseRegular />}
              size="small"
              title="Pause Agent"
            />
          ) : (
            <Button
              appearance="subtle"
              icon={<PlayRegular />}
              size="small"
              title="Start Agent"
            />
          )}
          <Button
            appearance="subtle"
            icon={<ArrowSyncRegular />}
            size="small"
            title="Restart Agent"
          />
          <Button
            appearance="subtle"
            icon={<MoreHorizontalRegular />}
            size="small"
            title="More Options"
          />
        </div>
      </div>

      <Text size={200} className={styles.description}>
        {description}
      </Text>

      <Divider />

      <div className={styles.metricsGrid}>
        {metricEntries.map(([key, value]) => (
          <div key={key} className={styles.metric}>
            <span className={styles.metricValue}>{value}</span>
            <span className={styles.metricLabel}>
              {key.replace(/([A-Z])/g, ' $1').trim()}
            </span>
          </div>
        ))}
      </div>

      <div className={styles.footer}>
        <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
          Last activity: {lastActivity}
        </Text>
        <Button appearance="subtle" size="small">
          View Logs
        </Button>
      </div>
    </Card>
  );
};
