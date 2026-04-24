'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import { colors, btn, btnPrimary, input as inputStyle } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

interface AvailableIntegration {
  name: string;
  display_name: string;
  type: string;
  description: string;
  icon: string;
  config_fields: { key: string; label: string; placeholder: string; secret?: boolean }[];
}

interface ConnectedIntegration {
  id: string;
  name: string;
  integration_type: string;
  config: Record<string, string>;
  enabled: boolean;
  sync_count: number;
  error_count: number;
  last_error: string | null;
  created_at: string;
}

export default function IntegrationsPage() {
  const router = useRouter();
  const { isMobile } = useBreakpoint();
  const [available, setAvailable] = useState<AvailableIntegration[]>([]);
  const [connected, setConnected] = useState<ConnectedIntegration[]>([]);
  const [configuring, setConfiguring] = useState<string | null>(null);
  const [configValues, setConfigValues] = useState<Record<string, string>>({});
  const [testing, setTesting] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [avRes, conRes] = await Promise.all([
        api.get('/integrations/available'),
        api.get('/integrations/connected'),
      ]);
      setAvailable(avRes.data);
      setConnected(conRes.data);
    } catch { /* empty */ }
  };

  const startConfig = (name: string) => {
    setConfiguring(name);
    setConfigValues({});
    setTestResult(null);
  };

  const connect = async () => {
    if (!configuring) return;
    try {
      await api.post('/integrations/connect', { name: configuring, config: configValues });
      setConfiguring(null);
      setConfigValues({});
      loadData();
    } catch { /* empty */ }
  };

  const disconnect = async (id: string) => {
    try { await api.delete(`/integrations/${id}`); loadData(); } catch { /* empty */ }
  };

  const testConnection = async (id: string) => {
    setTesting(id);
    try {
      const res = await api.post(`/integrations/${id}/test`);
      setTestResult(res.data);
    } catch { /* empty */ }
    setTesting(null);
  };

  const toggleEnabled = async (id: string) => {
    try { await api.post(`/integrations/${id}/toggle`); loadData(); } catch { /* empty */ }
  };

  // GitHub live data
  const [githubData, setGithubData] = useState<{ commits: any[]; deployments: any[]; repo: any } | null>(null);
  const [loadingGithub, setLoadingGithub] = useState(false);
  const [slackTestMsg, setSlackTestMsg] = useState('');
  const [slackSending, setSlackSending] = useState(false);
  const [slackResult, setSlackResult] = useState<string | null>(null);

  const connectedNames = new Set(connected.map(c => c.name));

  const loadGithubData = async () => {
    if (!connectedNames.has('github')) return;
    setLoadingGithub(true);
    try {
      const [commitsRes, deploymentsRes, repoRes] = await Promise.allSettled([
        api.get('/integrations/github/commits?limit=8'),
        api.get('/integrations/github/deployments?limit=5'),
        api.get('/integrations/github/repo'),
      ]);
      setGithubData({
        commits: commitsRes.status === 'fulfilled' ? commitsRes.value.data.commits || [] : [],
        deployments: deploymentsRes.status === 'fulfilled' ? deploymentsRes.value.data.deployments || [] : [],
        repo: repoRes.status === 'fulfilled' ? repoRes.value.data : null,
      });
    } catch { /* empty */ }
    setLoadingGithub(false);
  };

  const sendSlackTest = async () => {
    setSlackSending(true);
    setSlackResult(null);
    try {
      const res = await api.post('/integrations/slack/test-send', { message: slackTestMsg || 'Test notification from SentryAI' });
      setSlackResult(res.data.success ? 'Sent successfully!' : `Failed: ${res.data.error}`);
    } catch {
      setSlackResult('Failed to send');
    }
    setSlackSending(false);
  };

  useEffect(() => {
    if (connectedNames.has('github') && !githubData && !loadingGithub) {
      loadGithubData();
    }
  }, [connected]);

  const glassCard: React.CSSProperties = {
    background: colors.bgCard,
    backdropFilter: 'blur(12px)',
    borderRadius: 14,
    border: `1px solid ${colors.border}`,
    padding: 16,
    transition: 'all 0.2s ease',
  };

  const typeColor: Record<string, string> = {
    ticketing: '#8b5cf6', notification: '#3b82f6', alerting: '#ef4444',
    monitoring: '#10b981', scm: '#f59e0b',
  };

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 12 : 0, marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Integrations</h1>
            <p style={{ color: colors.textMuted, fontSize: 13, margin: '4px 0 0' }}>Connect third-party tools to your DevOps workflow</p>
          </div>
          <button onClick={() => router.push('/dashboard')} style={btn}>
            Dashboard
          </button>
        </div>

        {/* Connected */}
        {connected.length > 0 && (
          <>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>Connected ({connected.length})</h2>
            <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 12, marginBottom: 32 }}>
              {connected.map(c => {
                const avail = available.find(a => a.name === c.name);
                return (
                  <div key={c.id} style={{ ...glassCard, borderTop: `3px solid ${c.enabled ? colors.success : colors.textDim}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 24 }}>{avail?.icon || '🔌'}</span>
                        <div>
                          <h3 style={{ fontWeight: 600, fontSize: 14, color: colors.text, margin: 0 }}>{avail?.display_name || c.name}</h3>
                          <span style={{ fontSize: 11, color: colors.textMuted }}>{c.integration_type}</span>
                        </div>
                      </div>
                      <span style={{
                        padding: '2px 8px', borderRadius: 10, fontSize: 10, fontWeight: 600,
                        background: c.enabled ? colors.successBg : colors.bgElevated,
                        color: c.enabled ? colors.success : colors.textMuted,
                      }}>
                        {c.enabled ? 'Active' : 'Disabled'}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: colors.textDim, marginBottom: 8 }}>
                      {c.sync_count} syncs · {c.error_count} errors
                    </div>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button onClick={() => testConnection(c.id)} disabled={testing === c.id} style={{
                        padding: '4px 10px', borderRadius: 6, border: `1px solid ${colors.border}`,
                        background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 11,
                      }}>
                        {testing === c.id ? 'Testing...' : 'Test'}
                      </button>
                      <button onClick={() => toggleEnabled(c.id)} style={{
                        padding: '4px 10px', borderRadius: 6, border: `1px solid ${colors.border}`,
                        background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 11,
                      }}>
                        {c.enabled ? 'Disable' : 'Enable'}
                      </button>
                      <button onClick={() => disconnect(c.id)} style={{
                        padding: '4px 10px', borderRadius: 6, border: `1px solid ${colors.dangerBorder}`,
                        background: colors.dangerBg, color: colors.danger, cursor: 'pointer', fontSize: 11,
                      }}>
                        Remove
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}

        {/* GitHub Live Data */}
        {connectedNames.has('github') && (
          <div className="slide-up-d2" style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: colors.text, margin: 0 }}>
                <span style={{ marginRight: 8 }}>🐙</span>GitHub Live Data
              </h2>
              <button onClick={loadGithubData} disabled={loadingGithub} style={{
                padding: '4px 12px', borderRadius: 6, border: `1px solid ${colors.border}`,
                background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 11,
              }}>
                {loadingGithub ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            {githubData && (
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
                {/* Repo Info */}
                {githubData.repo && (
                  <div style={{ ...glassCard, gridColumn: isMobile ? '1' : '1 / -1', borderTop: `3px solid #f59e0b` }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 11, color: colors.textDim }}>Repository:</span>
                        <span style={{ fontSize: 13, fontWeight: 700, color: colors.text }}>{githubData.repo.name}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 11, color: colors.textDim }}>Branch:</span>
                        <span style={{ padding: '2px 8px', borderRadius: 5, fontSize: 11, fontWeight: 600, background: 'rgba(59,130,246,0.1)', color: colors.accent }}>{githubData.repo.default_branch}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 11, color: colors.textDim }}>Language:</span>
                        <span style={{ fontSize: 12, color: colors.textSecondary }}>{githubData.repo.language}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 11, color: colors.textDim }}>Open Issues:</span>
                        <span style={{ fontSize: 12, fontWeight: 600, color: githubData.repo.open_issues > 0 ? colors.warning : colors.success }}>{githubData.repo.open_issues}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Recent Commits */}
                <div style={{ ...glassCard, borderTop: '3px solid #8b5cf6' }}>
                  <h3 style={{ fontSize: 13, fontWeight: 600, color: colors.text, margin: '0 0 10px' }}>Recent Commits</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 300, overflowY: 'auto' }}>
                    {githubData.commits.length === 0 && <span style={{ fontSize: 12, color: colors.textDim }}>No commits found</span>}
                    {githubData.commits.map((c: any, i: number) => (
                      <div key={i} style={{
                        padding: '8px 10px', borderRadius: 8, background: colors.bgElevated,
                        border: `1px solid ${colors.borderLight}`,
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                          <span style={{ fontSize: 12, color: colors.textSecondary, lineHeight: 1.4, flex: 1 }}>{c.message}</span>
                          <span style={{ fontSize: 10, fontFamily: 'monospace', color: '#8b5cf6', flexShrink: 0, padding: '2px 6px', borderRadius: 4, background: 'rgba(139,92,246,0.1)' }}>{c.sha}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                          <span style={{ fontSize: 10, color: colors.textDim }}>{c.author}</span>
                          <span style={{ fontSize: 10, color: colors.textDim }}>{new Date(c.date).toLocaleDateString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Deployments / Workflow Runs */}
                <div style={{ ...glassCard, borderTop: '3px solid #10b981' }}>
                  <h3 style={{ fontSize: 13, fontWeight: 600, color: colors.text, margin: '0 0 10px' }}>Deployments / CI Runs</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 300, overflowY: 'auto' }}>
                    {githubData.deployments.length === 0 && <span style={{ fontSize: 12, color: colors.textDim }}>No deployments found</span>}
                    {githubData.deployments.map((d: any, i: number) => {
                      const statusColor = d.status === 'success' ? colors.success : d.status === 'failure' ? colors.danger : colors.warning;
                      return (
                        <div key={i} style={{
                          padding: '8px 10px', borderRadius: 8, background: colors.bgElevated,
                          border: `1px solid ${colors.borderLight}`,
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: 12, color: colors.textSecondary, fontWeight: 500 }}>{d.name || d.environment}</span>
                            <span style={{
                              fontSize: 10, padding: '2px 8px', borderRadius: 5, fontWeight: 600,
                              background: `${statusColor}15`, color: statusColor,
                            }}>{d.status}</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                            <span style={{ fontSize: 10, color: colors.textDim }}>{d.branch || ''} • {d.commit_sha}</span>
                            <span style={{ fontSize: 10, color: colors.textDim }}>{new Date(d.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {loadingGithub && !githubData && (
              <div style={{ ...glassCard, textAlign: 'center', padding: 24 }}>
                <span style={{ fontSize: 13, color: colors.textMuted }}>Loading GitHub data...</span>
              </div>
            )}
          </div>
        )}

        {/* Slack Test Panel */}
        {connectedNames.has('slack') && (
          <div className="slide-up-d2" style={{ marginBottom: 24 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>
              <span style={{ marginRight: 8 }}>💬</span>Slack Test
            </h2>
            <div style={{ ...glassCard, borderTop: '3px solid #3b82f6' }}>
              <div style={{ display: 'flex', gap: 8, alignItems: isMobile ? 'stretch' : 'flex-end', flexDirection: isMobile ? 'column' : 'row' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 11, color: colors.textMuted, display: 'block', marginBottom: 4 }}>Test Message</label>
                  <input
                    value={slackTestMsg}
                    onChange={e => setSlackTestMsg(e.target.value)}
                    placeholder="Test notification from SentryAI"
                    style={{ ...inputStyle, fontSize: 13, padding: '8px 12px', width: '100%' }}
                  />
                </div>
                <button onClick={sendSlackTest} disabled={slackSending} style={{
                  ...btnPrimary, padding: '8px 20px', fontSize: 12, whiteSpace: 'nowrap',
                  opacity: slackSending ? 0.6 : 1,
                }}>
                  {slackSending ? 'Sending...' : 'Send Test'}
                </button>
              </div>
              {slackResult && (
                <div style={{
                  marginTop: 10, padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 500,
                  background: slackResult.includes('success') ? colors.successBg : colors.dangerBg,
                  color: slackResult.includes('success') ? colors.success : colors.danger,
                }}>{slackResult}</div>
              )}
            </div>
          </div>
        )}

        {/* Test result */}
        {testResult && (
          <div style={{
            ...glassCard, marginBottom: 16,
            borderLeft: `4px solid ${(testResult.connected as boolean) ? colors.success : colors.danger}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: (testResult.connected as boolean) ? colors.success : colors.danger }}>
                {(testResult.connected as boolean) ? 'Connection successful' : `Connection failed: ${testResult.error}`}
              </span>
              <button onClick={() => setTestResult(null)} style={{
                padding: '2px 8px', border: `1px solid ${colors.border}`, borderRadius: 6, background: colors.bgElevated,
                cursor: 'pointer', fontSize: 11, color: colors.textSecondary,
              }}>Close</button>
            </div>
          </div>
        )}

        {/* Configuration modal */}
        {configuring && (
          <div style={{ ...glassCard, marginBottom: 24, border: `2px solid ${colors.accent}` }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: colors.text, marginTop: 0 }}>
              Configure {available.find(a => a.name === configuring)?.display_name || configuring}
            </h3>
            <div style={{ display: 'grid', gap: 8, marginBottom: 12 }}>
              {available.find(a => a.name === configuring)?.config_fields.map(field => (
                <div key={field.key}>
                  <label style={{ fontSize: 11, color: colors.textMuted, display: 'block', marginBottom: 4 }}>{field.label}</label>
                  <input
                    type={field.secret ? 'password' : 'text'}
                    value={configValues[field.key] || ''}
                    onChange={e => setConfigValues({ ...configValues, [field.key]: e.target.value })}
                    placeholder={field.placeholder}
                    style={{ ...inputStyle, fontSize: 13, padding: '6px 10px' }}
                  />
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={connect} style={{
                ...btnPrimary, padding: '6px 16px', fontSize: 12,
              }}>Connect</button>
              <button onClick={() => setConfiguring(null)} style={{
                ...btn, padding: '6px 16px', fontSize: 12,
              }}>Cancel</button>
            </div>
          </div>
        )}

        {/* Available */}
        <h2 className="slide-up-d2" style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>Available Integrations</h2>
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 12 }}>
          {available.map(a => {
            const isConnected = connectedNames.has(a.name);
            const color = typeColor[a.type] || colors.textMuted;
            return (
              <div key={a.name} style={{ ...glassCard, opacity: isConnected ? 0.7 : 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <span style={{ fontSize: 28 }}>{a.icon}</span>
                  <div>
                    <h3 style={{ fontWeight: 600, fontSize: 14, color: colors.text, margin: 0 }}>{a.display_name}</h3>
                    <span style={{
                      fontSize: 10, padding: '1px 6px', borderRadius: 8,
                      background: `${color}15`, color, fontWeight: 500,
                    }}>{a.type}</span>
                  </div>
                </div>
                <p style={{ fontSize: 12, color: colors.textMuted, marginBottom: 10 }}>{a.description}</p>
                {isConnected ? (
                  <span style={{ fontSize: 12, color: colors.success, fontWeight: 600 }}>Connected</span>
                ) : (
                  <button onClick={() => startConfig(a.name)} style={{
                    padding: '5px 12px', borderRadius: 6, border: `1px solid ${color}`,
                    background: `${color}10`, color, cursor: 'pointer', fontSize: 12, fontWeight: 500,
                  }}>
                    Connect
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </DashboardShell>
  );
}
