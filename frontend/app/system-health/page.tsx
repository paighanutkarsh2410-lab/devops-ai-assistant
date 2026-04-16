'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardShell from '@/components/DashboardShell';
import { colors, card as cardStyle, btn } from '@/lib/theme';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface HealthData {
  status: string;
  api: boolean;
  database: boolean;
  redis: boolean;
}

export default function SystemHealthPage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [hoveredSvc, setHoveredSvc] = useState<number | null>(null);

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data = await response.json();
      setHealth(data);
      setLastRefresh(new Date());
    } catch {
      setHealth({ status: 'unreachable', api: false, database: false, redis: false });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const StatusDot = ({ healthy }: { healthy: boolean }) => (
    <span
      role="img"
      aria-label={healthy ? 'Healthy' : 'Unhealthy'}
      style={{
        display: 'inline-block',
        width: 12,
        height: 12,
        borderRadius: '50%',
        background: healthy ? colors.success : colors.danger,
        marginRight: 8,
        boxShadow: healthy ? `0 0 6px rgba(16,185,129,0.5)` : `0 0 6px rgba(239,68,68,0.5)`,
      }}
    />
  );

  const services = health ? [
    { name: 'API Server', healthy: health.api, description: 'FastAPI backend' },
    { name: 'Database', healthy: health.database, description: 'PostgreSQL + TimescaleDB' },
    { name: 'Redis', healthy: health.redis, description: 'Cache & message broker' },
  ] : [];

  const agents = [
    { name: 'Monitor Agent', interval: '30s', description: 'Anomaly detection' },
    { name: 'Diagnostic Agent', interval: '60s', description: 'Root cause analysis' },
    { name: 'Remediation Agent', interval: '90s', description: 'Auto-remediation' },
    { name: 'Learning Agent', interval: '120s', description: 'Pattern recognition' },
    { name: 'Prediction Agent', interval: '3600s', description: 'Forecasting' },
    { name: 'Communication Agent', interval: '300s', description: 'Notifications' },
  ];

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 900, margin: '0 auto' }}>
        {/* Header */}
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #10b981)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>System Health</h1>
            <p style={{ fontSize: 13, color: colors.textMuted }}>
              Last updated: {lastRefresh.toLocaleTimeString()}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={fetchHealth} aria-label="Refresh health status" style={btn}>
              Refresh
            </button>
            <button onClick={() => router.push('/dashboard')} style={btn}>
              Dashboard
            </button>
          </div>
        </div>

        {/* Overall Status */}
        <div className="slide-up-d1" style={{
          background: health?.status === 'healthy' ? colors.successBg : colors.dangerBg,
          border: `2px solid ${health?.status === 'healthy' ? colors.success : colors.danger}`,
          borderRadius: 14,
          padding: 20,
          marginBottom: 24,
          textAlign: 'center',
          position: 'relative', overflow: 'hidden',
        }}>
          <div style={{ position: 'absolute', top: -30, left: '50%', transform: 'translateX(-50%)', width: 200, height: 60, background: `radial-gradient(circle, ${health?.status === 'healthy' ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}, transparent)`, filter: 'blur(20px)', animation: 'breathe 3s ease-in-out infinite' }} />
          <div style={{ fontSize: 20, fontWeight: 700, color: health?.status === 'healthy' ? colors.success : colors.danger, position: 'relative', textShadow: `0 0 20px ${health?.status === 'healthy' ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}` }}>
            {loading ? 'Checking...' : health?.status === 'healthy' ? 'All Systems Operational' : 'System Degraded'}
          </div>
        </div>

        {/* Infrastructure Services */}
        <h2 className="slide-up-d2" style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: colors.text }}>Infrastructure</h2>
        <div className="slide-up-d2" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 32 }}>
          {services.map((svc, i) => (
            <div key={svc.name}
              onMouseEnter={() => setHoveredSvc(i)} onMouseLeave={() => setHoveredSvc(null)}
              style={{
                ...cardStyle, position: 'relative', overflow: 'hidden',
                borderTop: `2px solid ${svc.healthy ? colors.success : colors.danger}`,
                transform: hoveredSvc === i ? 'translateY(-3px)' : 'none',
                boxShadow: hoveredSvc === i ? `0 8px 32px ${svc.healthy ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)'}` : 'none',
                transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
              }}>
              <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: `radial-gradient(circle, ${svc.healthy ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}, transparent)`, filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite', animationDelay: `${i * 0.5}s` }} />
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4, position: 'relative' }}>
                <StatusDot healthy={svc.healthy} />
                <span style={{ fontWeight: 600, fontSize: 14, color: colors.text }}>{svc.name}</span>
              </div>
              <div style={{ color: colors.textMuted, fontSize: 12, position: 'relative' }}>{svc.description}</div>
              <div style={{ marginTop: 8, fontSize: 12, color: svc.healthy ? colors.success : colors.danger, fontWeight: 600, position: 'relative' }}>
                {svc.healthy ? 'Operational' : 'Down'}
              </div>
            </div>
          ))}
        </div>

        {/* Agent Pipeline */}
        <h2 className="slide-up-d3" style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: colors.text }}>Agent Pipeline</h2>
        <div style={{
          background: colors.bgCard,
          borderRadius: 14,
          border: `1px solid ${colors.border}`,
          overflow: 'hidden',
        }}>
          {agents.map((agent, i) => (
            <div key={agent.name} style={{
              padding: '14px 20px',
              borderBottom: i < agents.length - 1 ? `1px solid ${colors.border}` : 'none',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <div>
                <span style={{ fontWeight: 500, fontSize: 14, color: colors.text }}>{agent.name}</span>
                <span style={{ color: colors.textMuted, fontSize: 12, marginLeft: 8 }}>{agent.description}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{
                  fontSize: 12, color: colors.textMuted, background: colors.bgElevated,
                  padding: '2px 8px', borderRadius: 4,
                }}>
                  every {agent.interval}
                </span>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 12,
                  background: colors.successBg, color: colors.success,
                }}>
                  Ready
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
