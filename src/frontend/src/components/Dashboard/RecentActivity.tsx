import {
  makeStyles,
  shorthands,
  Text,
  Badge,
  tokens,
} from '@fluentui/react-components';
import {
  ShieldErrorRegular,
  CheckmarkCircleRegular,
  ClockRegular,
  BotRegular,
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    marginTop: '16px',
  },
  item: {
    display: 'flex',
    alignItems: 'flex-start',
    ...shorthands.gap('12px'),
    ...shorthands.padding('12px', '0'),
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    ':last-child': {
      borderBottom: 'none',
    },
  },
  iconContainer: {
    width: '36px',
    height: '36px',
    ...shorthands.borderRadius('8px'),
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  content: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('4px'),
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    ...shorthands.gap('8px'),
  },
  meta: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('8px'),
  },
});

interface Activity {
  id: string;
  type: 'detected' | 'assessed' | 'remediated' | 'resolved';
  title: string;
  description: string;
  time: string;
  severity?: 'critical' | 'high' | 'medium' | 'low';
}

const activities: Activity[] = [
  {
    id: '1',
    type: 'resolved',
    title: 'CVE-2026-12345 Resolved',
    description: 'Dependency update merged automatically',
    time: '2 min ago',
    severity: 'critical',
  },
  {
    id: '2',
    type: 'remediated',
    title: 'Pull Request Created',
    description: 'Auto-fix for lodash vulnerability',
    time: '5 min ago',
    severity: 'high',
  },
  {
    id: '3',
    type: 'assessed',
    title: 'Risk Assessment Complete',
    description: 'CVE-2026-67890 marked as P1 priority',
    time: '8 min ago',
    severity: 'high',
  },
  {
    id: '4',
    type: 'detected',
    title: 'New Vulnerability Detected',
    description: 'SQL injection in auth module',
    time: '12 min ago',
    severity: 'critical',
  },
  {
    id: '5',
    type: 'resolved',
    title: 'CVE-2026-11111 Resolved',
    description: 'Configuration fix applied',
    time: '15 min ago',
    severity: 'medium',
  },
];

const typeConfig = {
  detected: {
    icon: <ShieldErrorRegular />,
    color: '#D13438',
    bg: '#FDE7E9',
  },
  assessed: {
    icon: <ClockRegular />,
    color: '#0078D4',
    bg: '#DEECF9',
  },
  remediated: {
    icon: <BotRegular />,
    color: '#7E57C2',
    bg: '#EDE7F6',
  },
  resolved: {
    icon: <CheckmarkCircleRegular />,
    color: '#107C10',
    bg: '#DFF6DD',
  },
};

const severityColors = {
  critical: 'danger',
  high: 'warning',
  medium: 'warning',
  low: 'success',
} as const;

export const RecentActivity: React.FC = () => {
  const styles = useStyles();

  return (
    <div className={styles.container}>
      {activities.map((activity) => {
        const config = typeConfig[activity.type];
        
        return (
          <div key={activity.id} className={styles.item}>
            <div
              className={styles.iconContainer}
              style={{ backgroundColor: config.bg, color: config.color }}
            >
              {config.icon}
            </div>
            
            <div className={styles.content}>
              <div className={styles.header}>
                <Text weight="medium">{activity.title}</Text>
                <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                  {activity.time}
                </Text>
              </div>
              
              <div className={styles.meta}>
                <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
                  {activity.description}
                </Text>
                {activity.severity && (
                  <Badge
                    size="small"
                    appearance="tint"
                    color={severityColors[activity.severity]}
                  >
                    {activity.severity}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
