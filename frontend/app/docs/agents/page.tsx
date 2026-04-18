'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors, input as inputStyle } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function Card({ title, children, style }: { title: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{
      background: colors.bgCard,
      backdropFilter: 'blur(12px)',
      borderRadius: 14,
      border: `1px solid ${colors.border}`,
      overflow: 'hidden',
      ...style,
    }}>
      <div style={{
        padding: '14px 20px',
        borderBottom: `1px solid ${colors.border}`,
        fontSize: 14,
        fontWeight: 600,
        color: colors.text,
      }}>{title}</div>
      <div style={{ padding: 20 }}>{children}</div>
    </div>
  );
}

export default function AgentDocsPage() {
  const { isMobile } = useBreakpoint();
  const [docs, setDocs] = useState<any>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/agents/docs`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => { setDocs(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <DashboardShell>
      <div style={{ padding: 32, color: colors.textMuted }}>Loading documentation...</div>
    </DashboardShell>
  );

  const agents = docs?.agents || [];
  const filtered = search
    ? agents.filter((a: any) =>
        a.name.toLowerCase().includes(search.toLowerCase()) ||
        a.description.toLowerCase().includes(search.toLowerCase()))
    : agents;

  const selected = selectedAgent ? agents.find((a: any) => a.name === selectedAgent) : null;

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1400, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: '0 0 6px', background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Agent Documentation</h1>
          <p style={{ color: colors.textMuted, fontSize: 13, marginBottom: 0 }}>Interactive reference for all AI agents</p>
        </div>

        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search agents, capabilities, endpoints..."
          style={{
            ...inputStyle,
            maxWidth: 500,
            marginBottom: 24,
            boxSizing: 'border-box' as const,
          }}
        />

        <div style={{ display: 'flex', gap: 20 }}>
          {/* Agent List */}
          <div style={{ width: 280, flexShrink: 0 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {filtered.map((agent: any) => (
                <button key={agent.name} onClick={() => setSelectedAgent(agent.name)}
                  style={{
                    padding: 14, borderRadius: 10, textAlign: 'left' as const, cursor: 'pointer',
                    border: selectedAgent === agent.name ? `1px solid ${colors.accent}` : `1px solid ${colors.border}`,
                    background: selectedAgent === agent.name ? 'rgba(59,130,246,0.1)' : colors.bgCard,
                    transition: 'all 0.2s ease',
                  }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: colors.text }}>{agent.name}</div>
                  <div style={{ fontSize: 11, color: colors.textDim, marginTop: 4 }}>
                    {agent.capabilities?.length || 0} capabilities
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Agent Detail */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {selected ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {/* Overview */}
                <Card title={selected.name}>
                  <p style={{ fontSize: 13, color: colors.textSecondary, lineHeight: 1.6, margin: 0 }}>
                    {selected.description}
                  </p>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 12 }}>
                    {(selected.capabilities || []).map((cap: string) => (
                      <span key={cap} style={{
                        padding: '4px 10px', borderRadius: 6, fontSize: 11,
                        background: 'rgba(59,130,246,0.1)', color: colors.accent,
                      }}>{cap}</span>
                    ))}
                  </div>
                </Card>

                {/* Configuration */}
                {selected.configuration && (
                  <Card title="Configuration">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {Object.entries(selected.configuration).map(([key, info]: [string, any]) => (
                        <div key={key} style={{
                          padding: 10, borderRadius: 8, background: colors.bgElevated,
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          border: `1px solid ${colors.borderLight}`,
                        }}>
                          <div>
                            <code style={{ fontSize: 12, color: colors.accent }}>{key}</code>
                            <div style={{ fontSize: 11, color: colors.textDim, marginTop: 2 }}>{info.description}</div>
                          </div>
                          <div style={{ textAlign: 'right' as const }}>
                            <div style={{ fontSize: 11, color: colors.textSecondary }}>Default: <code style={{ color: colors.success }}>{String(info.default)}</code></div>
                            <div style={{ fontSize: 10, color: colors.textDim }}>Type: {info.type}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {/* API Endpoints */}
                {selected.api_endpoints && (
                  <Card title="API Endpoints">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {selected.api_endpoints.map((ep: any, i: number) => (
                        <div key={i} style={{
                          padding: 10, borderRadius: 8, background: colors.bgElevated,
                          display: 'flex', alignItems: 'center', gap: 10,
                          border: `1px solid ${colors.borderLight}`,
                        }}>
                          <span style={{
                            padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 700,
                            background: ep.method === 'GET' ? colors.successBg : 'rgba(59,130,246,0.1)',
                            color: ep.method === 'GET' ? colors.success : colors.accent,
                          }}>{ep.method}</span>
                          <code style={{ fontSize: 12, color: colors.text }}>{ep.path}</code>
                          <span style={{ fontSize: 11, color: colors.textDim, marginLeft: 'auto' }}>{ep.description}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {/* Troubleshooting */}
                {selected.troubleshooting && (
                  <Card title="Troubleshooting">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {selected.troubleshooting.map((item: any, i: number) => (
                        <div key={i} style={{
                          padding: 10, borderRadius: 8, background: colors.bgElevated,
                          border: `1px solid ${colors.borderLight}`,
                        }}>
                          <div style={{ fontSize: 12, color: colors.warning, fontWeight: 600, marginBottom: 4 }}>
                            Issue: {item.issue}
                          </div>
                          <div style={{ fontSize: 12, color: colors.textSecondary }}>
                            Solution: {item.solution}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </div>
            ) : (
              <div style={{ padding: 40, textAlign: 'center' as const, color: colors.textDim, fontSize: 14 }}>
                Select an agent from the left to view its documentation
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
