'use client';

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  icon?: string;
}

export default function MetricCard({ title, value, subtitle, color = '#f0f0f0', trend, trendValue, icon }: Props) {
  const trendColor = trend === 'up' ? '#16a34a' : trend === 'down' ? '#dc2626' : '#6b7280';
  const trendArrow = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.06)',
      padding: '16px', display: 'flex', flexDirection: 'column', gap: '4px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '11px', color: '#71717a', fontWeight: 500 }}>{title}</span>
        {icon && <span style={{ fontSize: '16px' }}>{icon}</span>}
      </div>
      <div style={{ fontSize: '28px', fontWeight: 700, color, lineHeight: 1.1 }}>{value}</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {subtitle && <span style={{ fontSize: '11px', color: '#52525b' }}>{subtitle}</span>}
        {trend && trendValue && (
          <span style={{ fontSize: '11px', color: trendColor, fontWeight: 600 }}>
            {trendArrow} {trendValue}
          </span>
        )}
      </div>
    </div>
  );
}
