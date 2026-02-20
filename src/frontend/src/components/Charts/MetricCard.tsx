import { Card, Text } from '@fluentui/react-components';
import { ArrowUp24Regular, ArrowDown24Regular } from '@fluentui/react-icons';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down';
    isPositive: boolean;
  };
  icon?: React.ReactNode;
  color?: 'default' | 'success' | 'warning' | 'danger';
}

const colorStyles = {
  default: { bg: '#f8fafc', border: '#e2e8f0', text: '#1e293b' },
  success: { bg: '#f0fdf4', border: '#bbf7d0', text: '#16a34a' },
  warning: { bg: '#fffbeb', border: '#fde68a', text: '#ca8a04' },
  danger: { bg: '#fef2f2', border: '#fecaca', text: '#dc2626' },
};

export function MetricCard({ title, value, unit, trend, icon, color = 'default' }: MetricCardProps) {
  const styles = colorStyles[color];

  return (
    <Card
      style={{
        padding: '20px',
        backgroundColor: styles.bg,
        border: `1px solid ${styles.border}`,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Text size={200} weight="medium" style={{ color: '#64748b' }}>
          {title}
        </Text>
        {icon && <div style={{ color: styles.text }}>{icon}</div>}
      </div>
      
      <div style={{ marginTop: '12px' }}>
        <span style={{ fontSize: '32px', fontWeight: 700, color: styles.text }}>
          {value}
        </span>
        {unit && (
          <span style={{ fontSize: '16px', color: '#64748b', marginLeft: '4px' }}>
            {unit}
          </span>
        )}
      </div>

      {trend && (
        <div
          style={{
            marginTop: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            color: trend.isPositive ? '#16a34a' : '#dc2626',
          }}
        >
          {trend.direction === 'up' ? (
            <ArrowUp24Regular style={{ width: 16, height: 16 }} />
          ) : (
            <ArrowDown24Regular style={{ width: 16, height: 16 }} />
          )}
          <Text size={200} weight="medium">
            {trend.value}% vs last week
          </Text>
        </div>
      )}
    </Card>
  );
}
