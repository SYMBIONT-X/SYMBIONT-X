import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface PriorityBarChartProps {
  data: {
    P0: number;
    P1: number;
    P2: number;
    P3: number;
    P4: number;
  };
}

const PRIORITY_COLORS = {
  P0: '#dc2626',
  P1: '#ea580c',
  P2: '#ca8a04',
  P3: '#2563eb',
  P4: '#16a34a',
};

const PRIORITY_LABELS = {
  P0: 'P0 - Critical',
  P1: 'P1 - High',
  P2: 'P2 - Medium',
  P3: 'P3 - Low',
  P4: 'P4 - Info',
};

export function PriorityBarChart({ data }: PriorityBarChartProps) {
  const chartData = Object.entries(data).map(([priority, count]) => ({
    priority,
    label: PRIORITY_LABELS[priority as keyof typeof PRIORITY_LABELS],
    count,
    color: PRIORITY_COLORS[priority as keyof typeof PRIORITY_COLORS],
  }));

  const total = Object.values(data).reduce((a, b) => a + b, 0);

  if (total === 0) {
    return (
      <div style={{ height: 250, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
        No vulnerabilities by priority
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis type="number" tick={{ fontSize: 12 }} />
        <YAxis 
          type="category" 
          dataKey="label" 
          tick={{ fontSize: 12 }}
          width={80}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
          }}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
