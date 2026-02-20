import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface TrendLineChartProps {
  data: Array<{
    time: string;
    detected: number;
    fixed: number;
  }>;
  title?: string;
}

export function TrendLineChart({ data, title }: TrendLineChartProps) {
  if (data.length === 0) {
    return (
      <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
        No trend data available
      </div>
    );
  }

  return (
    <div>
      {title && (
        <div style={{ marginBottom: '12px', fontWeight: 600, fontSize: '14px' }}>
          {title}
        </div>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="time" 
            tick={{ fontSize: 12 }}
            tickLine={false}
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="detected"
            stroke="#dc2626"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Detected"
          />
          <Line
            type="monotone"
            dataKey="fixed"
            stroke="#16a34a"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Fixed"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
