'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const STATUS_COLORS: Record<string, string> = {
  healthy: colors.success, degraded: colors.warning, unhealthy: colors.danger, stopped: colors.textMuted,
};
const SEVERITY_COLORS: Record<string, string> = {
  critical: colors.danger, warning: colors.warning, info: colors.accent,
};

function Card({ title, children, style }: { title: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`, overflow: 'hidden', ...style }}>
      <div style={{ padding: '14px 20px', borderBottom: `1px solid ${colors.border}`, fontSize: 14, fontWeight: 600, color: colors.text }}>{title}</div>
      <div style={{ padding: 20 }}>{children}</div>
    </div>
  );
}

export default function AgentStatusPage() {
  const [data, setData] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/agents/health/status`, { headers: authHeaders() }).then(r => r.json()),
      fetch(`${API}/agents/health/logs?limit=20`, { headers: authHeaders() }).then(r => r.json()),
    ]).then(([health, logData]) => {
      setData(health);
      setLogs(logData.logs || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <DashboardShell><div style={{ padding: 32, color: colors.textMuted }}>Loading agent status...</div></DashboardShell>;
  if (!data) return <DashboardShell><div style={{ padding: 32, color: colors.textDim }}>No data available</div></DashboardShell>;

  const agents = data.agents || {};
  const alerts = data.alerts || [];
  const sla = data.sla_compliance || {};

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1400, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: '0 0 6px', background: 'linear-gradient(135deg, #f0f0f0, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Agent Status Dashboard</h1>
          <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 0 }}>Real-time health, performance, and SLA compliance</p>
        </div>

        {/* Agent Grid */}
        <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16, marginBottom: 24 }}>
          {Object.entries(agents).map(([name, info]: [string, any]) => (
            <div key={name} style={{
              background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`, padding: 18,
              borderLeft: `4px solid ${STATUS_COLORS[info.status] || colors.textMuted}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: colors.text }}>{name}</span>
                <span style={{
                  padding: '3px 10px', borderRadius: 12, fontSize: 10, fontWeight: 600,
                  background: (STATUS_COLORS[info.status] || colors.textMuted) + '20',
                  color: STATUS_COLORS[info.status] || colors.textMuted,
                  textTransform: 'uppercase',
                }}>{info.status}</span>
              </div>
              {info.current_task && (
                <div style={{ fontSize: 11, color: colors.accent, marginBottom: 8, padding: '4px 8px', borderRadius: 4, background: 'rgba(59,130,246,0.1)' }}>
                  {info.current_task}
                </div>
              )}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 11 }}>
                <div><span style={{ color: colors.textDim }}>Tasks: </span><span style={{ color: colors.text }}>{info.total_tasks}</span></div>
                <div><span style={{ color: colors.textDim }}>Success: </span><span style={{ color: info.success_rate > 85 ? colors.success : colors.warning }}>{info.success_rate}%</span></div>
                <div><span style={{ color: colors.textDim }}>CPU: </span><span style={{ color: colors.text }}>{info.cpu_percent}%</span></div>
                <div><span style={{ color: colors.textDim }}>Memory: </span><span style={{ color: colors.text }}>{info.memory_mb}MB</span></div>
                <div><span style={{ color: colors.textDim }}>Queue: </span><span style={{ color: info.queue_depth > 10 ? colors.warning : colors.text }}>{info.queue_depth}</span></div>
                <div><span style={{ color: colors.textDim }}>Uptime: </span><span style={{ color: colors.text }}>{info.uptime_hours}h</span></div>
              </div>
            </div>
          ))}
        </div>

        {/* Alerts + SLA */}
        <div className="slide-up-d2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Card title={`Active Alerts (${alerts.length})`}>
            {alerts.length === 0 ? (
              <div style={{ fontSize: 12, color: colors.textDim, textAlign: 'center', padding: 16 }}>No active alerts</div>
            ) : alerts.map((a: any) => (
              <div key={a.id} style={{
                padding: 10, borderRadius: 8, background: colors.bgElevated, marginBottom: 8,
                borderLeft: `3px solid ${SEVERITY_COLORS[a.severity] || colors.textMuted}`,
              }}>
                <div style={{ fontSize: 12, color: colors.text, fontWeight: 500 }}>{a.message}</div>
                <div style={{ fontSize: 10, color: colors.textDim, marginTop: 4 }}>{a.agent} &middot; {a.type}</div>
              </div>
            ))}
          </Card>

          <Card title="SLA Compliance">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {Object.entries(sla).map(([name, info]: [string, any]) => (
                <div key={name} style={{
                  padding: 10, borderRadius: 8, background: colors.bgElevated,
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <span style={{ fontSize: 12, color: colors.text }}>{name}</span>
                  <span style={{
                    padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                    background: info.overall_compliant ? colors.successBg : colors.dangerBg,
                    color: info.overall_compliant ? colors.success : colors.danger,
                  }}>
                    {info.overall_compliant ? 'Compliant' : 'Non-Compliant'}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Logs */}
        <Card title="Recent Agent Logs" style={{ marginTop: 16 }}>
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {logs.map((log: any, i: number) => {
              const levelColor = log.level === 'ERROR' ? colors.danger : log.level === 'WARNING' ? colors.warning : colors.textDim;
              return (
                <div key={i} style={{
                  padding: '6px 10px', borderBottom: `1px solid ${colors.border}`, fontSize: 12,
                  display: 'flex', gap: 10, fontFamily: 'monospace',
                }}>
                  <span style={{ color: colors.textDim, minWidth: 130 }}>{log.timestamp?.slice(11, 19)}</span>
                  <span style={{ color: levelColor, minWidth: 55, fontWeight: 600 }}>{log.level}</span>
                  <span style={{ color: colors.accent, minWidth: 140 }}>{log.agent}</span>
                  <span style={{ color: colors.textSecondary }}>{log.message}</span>
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </DashboardShell>
  );
}
