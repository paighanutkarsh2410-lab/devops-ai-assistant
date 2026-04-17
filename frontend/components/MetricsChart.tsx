'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DataPoint {
  timestamp: string;
  value: number;
}

interface MetricsChartProps {
  data: DataPoint[];
  title: string;
  color?: string;
  unit?: string;
}

export default function MetricsChart({ data, title, color = '#3b82f6', unit = '' }: MetricsChartProps) {
  const chartData = data.map(d => ({
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    value: d.value,
  }));

  return (
    <div style={{
      padding: 16, borderRadius: 14,
      background: 'rgba(255,255,255,0.02)',
      border: '1px solid rgba(255,255,255,0.04)',
    }}>
      <h3 style={{
        fontSize: 12, fontWeight: 600, color: '#71717a',
        marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.5,
      }}>{title}</h3>
      {chartData.length === 0 ? (
        <div style={{
          height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#3f3f46', fontSize: 12,
        }}>
          No data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={140}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#52525b' }} axisLine={{ stroke: 'rgba(255,255,255,0.06)' }} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#52525b' }} axisLine={{ stroke: 'rgba(255,255,255,0.06)' }} tickLine={false} width={35} />
            <Tooltip
              formatter={(value) => [`${Number(value).toFixed(1)}${unit}`, title]}
              contentStyle={{
                background: 'rgba(10,10,20,0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 10,
                fontSize: 12,
                color: '#e2e8f0',
                boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
              }}
              labelStyle={{ fontSize: 11, color: '#71717a' }}
              itemStyle={{ color: color }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
              style={{ filter: `drop-shadow(0 0 4px ${color}40)` }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
