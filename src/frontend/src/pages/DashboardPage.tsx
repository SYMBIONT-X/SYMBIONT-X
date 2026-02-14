import {
  makeStyles,
  shorthands,
  Text,
  Card,
  CardHeader,
  tokens,
} from '@fluentui/react-components';
import {
  ShieldErrorRegular,
  CheckmarkCircleRegular,
  ClockRegular,
  BotRegular,
} from '@fluentui/react-icons';
import { MetricCard } from '@components/Dashboard/MetricCard';
import { VulnerabilityChart } from '@components/Dashboard/VulnerabilityChart';
import { RecentActivity } from '@components/Dashboard/RecentActivity';
import { AgentStatusOverview } from '@components/Dashboard/AgentStatusOverview';

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
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    ...shorthands.gap('16px'),
  },
  chartsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    ...shorthands.gap('16px'),
  },
  card: {
    ...shorthands.padding('20px'),
  },
});

// Mock data - will be replaced with real API data
const metrics = [
  {
    title: 'Critical Vulnerabilities',
    value: 12,
    change: -25,
    changeLabel: 'vs last week',
    icon: <ShieldErrorRegular />,
    color: '#D13438' as const,
  },
  {
    title: 'Resolved Today',
    value: 47,
    change: 156,
    changeLabel: 'vs yesterday',
    icon: <CheckmarkCircleRegular />,
    color: '#107C10' as const,
  },
  {
    title: 'Avg. Resolution Time',
    value: '4.2 min',
    change: -89,
    changeLabel: 'vs manual (30 days)',
    icon: <ClockRegular />,
    color: '#0078D4' as const,
  },
  {
    title: 'Active Agents',
    value: '3/3',
    change: 0,
    changeLabel: 'all operational',
    icon: <BotRegular />,
    color: '#7E57C2' as const,
  },
];

export const DashboardPage: React.FC = () => {
  const styles = useStyles();

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <Text size={700} weight="semibold" block>
            Security Overview
          </Text>
          <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
            Real-time vulnerability monitoring and remediation status
          </Text>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className={styles.metricsGrid}>
        {metrics.map((metric, index) => (
          <MetricCard key={index} {...metric} />
        ))}
      </div>

      {/* Charts Grid */}
      <div className={styles.chartsGrid}>
        <Card className={styles.card}>
          <CardHeader
            header={<Text weight="semibold" size={400}>Vulnerabilities Over Time</Text>}
          />
          <VulnerabilityChart />
        </Card>

        <Card className={styles.card}>
          <CardHeader
            header={<Text weight="semibold" size={400}>Agent Status</Text>}
          />
          <AgentStatusOverview />
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className={styles.card}>
        <CardHeader
          header={<Text weight="semibold" size={400}>Recent Activity</Text>}
        />
        <RecentActivity />
      </Card>
    </div>
  );
};
