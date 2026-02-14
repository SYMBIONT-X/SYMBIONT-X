import {
  makeStyles,
  shorthands,
  Text,
  Card,
  tokens,
} from '@fluentui/react-components';
import { ArrowTrendingRegular } from '@fluentui/react-icons';

const useStyles = makeStyles({
  card: {
    ...shorthands.padding('20px'),
    minHeight: '140px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '16px',
  },
  iconContainer: {
    width: '40px',
    height: '40px',
    ...shorthands.borderRadius('10px'),
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '20px',
  },
  value: {
    fontSize: '32px',
    fontWeight: tokens.fontWeightBold,
    lineHeight: '1',
    marginBottom: '8px',
  },
  change: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('4px'),
    fontSize: '13px',
  },
  positive: {
    color: tokens.colorPaletteGreenForeground1,
  },
  negative: {
    color: tokens.colorPaletteRedForeground1,
  },
  neutral: {
    color: tokens.colorNeutralForeground3,
  },
});

interface MetricCardProps {
  title: string;
  value: string | number;
  change: number;
  changeLabel: string;
  icon: React.ReactElement;
  color: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon,
  color,
}) => {
  const styles = useStyles();

  const getChangeStyle = () => {
    if (change > 0) return styles.positive;
    if (change < 0) return styles.negative;
    return styles.neutral;
  };

  const formatChange = () => {
    if (change === 0) return '—';
    const prefix = change > 0 ? '+' : '';
    return `${prefix}${change}%`;
  };

  return (
    <Card className={styles.card}>
      <div className={styles.header}>
        <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
          {title}
        </Text>
        <div
          className={styles.iconContainer}
          style={{ backgroundColor: `${color}15`, color }}
        >
          {icon}
        </div>
      </div>

      <div className={styles.value}>{value}</div>

      <div className={`${styles.change} ${getChangeStyle()}`}>
        <ArrowTrendingRegular />
        <span>{formatChange()}</span>
        <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
          {changeLabel}
        </Text>
      </div>
    </Card>
  );
};
