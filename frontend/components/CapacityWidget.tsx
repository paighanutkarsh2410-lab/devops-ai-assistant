'use client';

import { colors } from '@/lib/theme';

interface ServiceCapacity {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  peak_utilization: number;
  buffer_percent: number;
  status: string;
}

interface CapacityWidgetProps {
  services: Record<string, ServiceCapacity>;
  overall?: {
    avg_utilization: number;
    total_services: number;
    critical_count: number;
    healthy_count: number;
  };
}

const STATUS_COLORS: Record<string, { color: string; bg: string }> = {
  critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)' },
  warning: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },
  healthy: { color: '#10b981', bg: 'rgba(16,185,129,0.08)' },
};

function BarColor(pct: number): string {
  if (pct >= 90) return '#ef4444';
  if (pct >= 75) return '#f59e0b';
  return '#10b981';
}

export default function CapacityWidget({ services, overall }: CapacityWidgetProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Overall Summary */}
      {overall && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          {[
            { label: 'Avg Utilization', value: `${overall.avg_utilization}%`, color: '#3b82f6' },
            { label: 'Services', value: overall.total_services, color: '#8b5cf6' },
            { label: 'Healthy', value: overall.healthy_count, color: '#10b981' },
            { label: 'Critical', value: overall.critical_count, color: '#ef4444' },
          ].map((s, i) => (
            <div key={i} style={{
              background: colors.bgCard, border: `1px solid ${colors.border}`,
              borderRadius: 14, padding: 18, borderTop: `2px solid ${s.color}`,
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: s.color, marginBottom: 4 }}>{s.value}</div>
              <div style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600 }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Per-Service Capacity */}
      <div style={{
        background: 'rgba(255,255,255,0.015)',
        border: '1px solid rgba(255,255,255,0.04)',
        borderRadius: 18, overflow: 'hidden',
      }}>
        <div style={{
          padding: '18px 22px', borderBottom: '1px solid rgba(255,255,255,0.04)',
        }}>
          <h2 style={{
            fontSize: 16, fontWeight: 700,
            background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>Service Capacity</h2>
        </div>

        {Object.entries(services).length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center', color: colors.textMuted }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>📊</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#71717a', marginBottom: 4 }}>No capacity data</div>
            <div style={{ fontSize: 13 }}>Run the Prediction Agent to generate capacity analysis.</div>
          </div>
        ) : (
          Object.entries(services).map(([name, svc], idx) => {
            const st = STATUS_COLORS[svc.status] || STATUS_COLORS.healthy;
            return (
              <div key={name} style={{
                padding: '18px 22px',
                borderBottom: '1px solid rgba(255,255,255,0.03)',
                animation: `slide-up 0.4s ease-out ${idx * 0.05}s both`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{
                      width: 8, height: 8, borderRadius: '50%',
                      background: st.color,
                      boxShadow: `0 0 6px ${st.color}60`,
                    }} />
                    <span style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0' }}>{name}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 600, color: st.color,
                      padding: '2px 8px', borderRadius: 6,
                      background: st.bg, textTransform: 'uppercase',
                    }}>{svc.status}</span>
                  </div>
                  <span style={{ fontSize: 12, color: '#52525b' }}>
                    Buffer: <span style={{ color: '#71717a', fontWeight: 600 }}>{svc.buffer_percent.toFixed(0)}%</span>
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                  {[
                    { label: 'CPU', value: svc.cpu_percent },
                    { label: 'Memory', value: svc.memory_percent },
                    { label: 'Disk', value: svc.disk_percent },
                  ].map(({ label, value }) => {
                    const barCol = BarColor(value);
                    return (
                      <div key={label}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                          <span style={{ fontSize: 11, color: '#52525b' }}>{label}</span>
                          <span style={{ fontSize: 11, color: barCol, fontWeight: 600, fontFamily: 'monospace' }}>{value.toFixed(0)}%</span>
                        </div>
                        <div style={{
                          height: 6, borderRadius: 3,
                          background: 'rgba(255,255,255,0.04)',
                          overflow: 'hidden',
                        }}>
                          <div style={{
                            height: '100%', borderRadius: 3,
                            background: barCol,
                            width: `${Math.min(value, 100)}%`,
                            boxShadow: `0 0 8px ${barCol}40`,
                            transition: 'width 0.6s ease',
                          }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
