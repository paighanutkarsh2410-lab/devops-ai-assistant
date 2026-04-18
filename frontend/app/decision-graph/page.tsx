'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import NetworkGraph from '@/components/charts/NetworkGraph';
import { colors } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const AGENT_COLORS: Record<string, string> = {
  monitor: '#3b82f6',
  diagnostic: '#8b5cf6',
  remediation: '#10b981',
  learning: '#f59e0b',
  prediction: '#06b6d4',
  communication: '#ef4444',
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#f59e0b',
  low: '#10b981',
};

function Card({ title, children, style }: { title: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`, overflow: 'hidden', ...style }}>
      <div style={{ padding: '14px 20px', borderBottom: `1px solid ${colors.border}`, fontSize: 14, fontWeight: 600, color: colors.text }}>
        {title}
      </div>
      <div style={{ padding: 16 }}>{children}</div>
    </div>
  );
}

export default function DecisionGraphPage() {
  const { isMobile } = useBreakpoint();
  const [data, setData] = useState<any>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    fetch(`${API}/agents/decision-graph`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <DashboardShell>
      <div style={{ padding: 32, color: colors.textMuted }}>Loading decision graph...</div>
    </DashboardShell>
  );

  const nodes = (data?.nodes || []).map((n: any) => ({
    ...n,
    color: AGENT_COLORS[n.group] || '#64748b',
  }));
  const edges = data?.edges || [];
  const activity = data?.activity || [];
  const stats = data?.agent_stats || {};

  const selectedStats = selectedAgent ? stats[selectedAgent] : null;
  const selectedNode = selectedAgent ? nodes.find((n: any) => n.id === selectedAgent) : null;

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1400, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 24 }}>
          <h1 style={{
            fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: '0 0 6px',
            background: 'linear-gradient(135deg, #f0f0f0, #8b5cf6)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>Live Agent Decision Graph</h1>
          <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 0 }}>
            Real-time visualization of how AI agents communicate and make decisions
          </p>
        </div>

        {/* Agent stat pills */}
        <div className="slide-up-d1" style={{
          display: 'grid',
          gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(6, 1fr)',
          gap: 10, marginBottom: 20,
        }}>
          {nodes.map((n: any) => {
            const s = stats[n.id];
            return (
              <button key={n.id} onClick={() => setSelectedAgent(selectedAgent === n.id ? null : n.id)}
                style={{
                  padding: 12, borderRadius: 10, textAlign: 'left' as const, cursor: 'pointer',
                  border: selectedAgent === n.id ? `1px solid ${n.color}` : `1px solid ${colors.border}`,
                  background: selectedAgent === n.id ? `${n.color}15` : colors.bgCard,
                  transition: 'all 0.2s',
                }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: n.color, boxShadow: `0 0 6px ${n.color}60` }} />
                  <span style={{ fontSize: 12, fontWeight: 600, color: colors.text }}>{n.label.replace(' Agent', '')}</span>
                </div>
                <div style={{ fontSize: 11, color: colors.textDim }}>
                  {s?.events_processed || 0} events &middot; {s?.success_rate || 0}%
                </div>
                <div style={{
                  fontSize: 10, fontWeight: 600, marginTop: 4,
                  color: s?.status === 'active' ? colors.success : colors.textDim,
                }}>{s?.status || 'unknown'}</div>
              </button>
            );
          })}
        </div>

        <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 16 }}>
          {/* Graph */}
          <div className="slide-up-d2" style={{ flex: 1, minWidth: 0 }}>
            <Card title="Agent Communication Graph">
              <div style={{ display: 'flex', justifyContent: 'center' }}>
                <NetworkGraph
                  nodes={nodes}
                  edges={edges}
                  width={isMobile ? 340 : 620}
                  height={isMobile ? 300 : 420}
                  onNodeClick={(n) => setSelectedAgent(selectedAgent === n.id ? null : n.id)}
                />
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 12, justifyContent: 'center' }}>
                {Object.entries(AGENT_COLORS).map(([key, color]) => (
                  <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
                    <span style={{ fontSize: 11, color: colors.textDim, textTransform: 'capitalize' }}>{key}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Selected agent detail */}
            {selectedNode && selectedStats && (
              <Card title={selectedNode.label} style={{ marginTop: 16 }}>
                <p style={{ fontSize: 13, color: colors.textSecondary, lineHeight: 1.6, marginTop: 0, marginBottom: 14 }}>
                  {selectedNode.description}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4, 1fr)', gap: 10 }}>
                  {[
                    { label: 'Events Processed', value: selectedStats.events_processed },
                    { label: 'Avg Response', value: `${selectedStats.avg_response_ms}ms` },
                    { label: 'Success Rate', value: `${selectedStats.success_rate}%` },
                    { label: 'Status', value: selectedStats.status },
                  ].map(s => (
                    <div key={s.label} style={{
                      padding: 10, borderRadius: 8, background: colors.bgElevated,
                      border: `1px solid ${colors.borderLight}`,
                    }}>
                      <div style={{ fontSize: 10, color: colors.textDim, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>{s.label}</div>
                      <div style={{ fontSize: 16, fontWeight: 700, color: colors.text, marginTop: 4 }}>{s.value}</div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Live Activity Feed */}
          <div className="slide-up-d3" style={{ width: isMobile ? '100%' : 340, flexShrink: 0 }}>
            <Card title="Live Event Feed">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 600, overflowY: 'auto' }}>
                {activity.map((evt: any, i: number) => (
                  <div key={i} style={{
                    padding: 10, borderRadius: 8, background: colors.bgElevated,
                    border: `1px solid ${colors.borderLight}`,
                    animation: i < 3 ? `slide-up 0.3s ease-out ${i * 0.1}s both` : undefined,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                      <div style={{
                        width: 6, height: 6, borderRadius: '50%',
                        background: SEVERITY_COLORS[evt.severity] || colors.textDim,
                        boxShadow: `0 0 4px ${SEVERITY_COLORS[evt.severity] || colors.textDim}60`,
                      }} />
                      <span style={{
                        fontSize: 10, fontWeight: 700, color: AGENT_COLORS[evt.source_agent] || colors.accent,
                        textTransform: 'uppercase', letterSpacing: 0.5,
                      }}>{evt.source_agent}</span>
                      <span style={{ fontSize: 10, color: colors.textDim }}>→</span>
                      <span style={{
                        fontSize: 10, fontWeight: 700, color: AGENT_COLORS[evt.target_agent] || colors.accent,
                        textTransform: 'uppercase', letterSpacing: 0.5,
                      }}>{evt.target_agent}</span>
                    </div>
                    <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 2 }}>
                      {evt.message}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{
                        fontSize: 9, padding: '1px 6px', borderRadius: 4,
                        background: `${SEVERITY_COLORS[evt.severity] || colors.textDim}15`,
                        color: SEVERITY_COLORS[evt.severity] || colors.textDim,
                        fontWeight: 600,
                      }}>{evt.severity}</span>
                      <span style={{ fontSize: 10, color: colors.textDim }}>
                        {new Date(evt.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
