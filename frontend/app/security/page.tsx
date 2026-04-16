'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const SEV_COLORS: Record<string, string> = {
  critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#3b82f6', info: '#64748b',
};

function Card({ title, children, style }: { title: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{
      background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`,
      overflow: 'hidden', ...style,
    }}>
      <div style={{
        padding: '14px 20px', borderBottom: `1px solid ${colors.border}`,
        fontSize: 14, fontWeight: 600, color: colors.text,
      }}>{title}</div>
      <div style={{ padding: 20 }}>{children}</div>
    </div>
  );
}

export default function SecurityPage() {
  const [data, setData] = useState<any>(null);
  const [secrets, setSecrets] = useState<any>(null);
  const [tab, setTab] = useState<'events' | 'threats' | 'waf' | 'secrets'>('events');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/security/dashboard`, { headers: authHeaders() }).then(r => r.json()).catch(() => null),
      fetch(`${API}/secrets/audit`, { headers: authHeaders() }).then(r => r.json()).catch(() => null),
    ]).then(([d, s]) => {
      setData(d);
      setSecrets(s);
      setLoading(false);
    });
  }, []);

  if (loading) return (
    <DashboardShell>
      <div style={{ padding: 32, color: colors.textMuted }}>Loading security data...</div>
    </DashboardShell>
  );

  const summary = data?.summary || {};
  const tabs = [
    { key: 'events', label: 'Security Events' },
    { key: 'threats', label: 'Threat Intel' },
    { key: 'waf', label: 'WAF Rules' },
    { key: 'secrets', label: 'Secrets Vault' },
  ] as const;

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1400, margin: '0 auto' }}>
        <div style={{ marginBottom: 28 }} className="slide-up">
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: '0 0 6px', background: 'linear-gradient(135deg, #f0f0f0, #ef4444)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Security Center</h1>
          <p style={{ color: colors.textMuted, fontSize: 14 }}>
            Real-time threat monitoring, WAF management, and secrets vault
          </p>
        </div>

        {/* Summary Cards */}
        <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 14, marginBottom: 24 }}>
          {[
            { label: 'Events (1h)', value: summary.total_events_1h || 0, color: colors.accent },
            { label: 'Blocked', value: summary.blocked_requests || 0, color: colors.success },
            { label: 'Blocked IPs', value: summary.blocked_ips || 0, color: colors.warning },
            { label: 'Active Threats', value: summary.active_threats || 0, color: colors.danger },
            { label: 'Secrets', value: secrets?.total_secrets || 0, color: '#8b5cf6' },
          ].map(s => (
            <div key={s.label} style={{
              background: colors.bgCard, borderRadius: 10, border: `1px solid ${colors.border}`,
              padding: 16, textAlign: 'center', position: 'relative', overflow: 'hidden',
              borderTop: '2px solid #ef4444',
            }}>
              <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(239,68,68,0.18), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
              <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Severity Breakdown */}
        {data?.severity_breakdown && (
          <div className="slide-up-d2" style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
            {Object.entries(data.severity_breakdown).map(([sev, count]: [string, any]) => (
              <div key={sev} style={{
                padding: '6px 14px', borderRadius: 8,
                background: (SEV_COLORS[sev] || '#64748b') + '15',
                border: `1px solid ${SEV_COLORS[sev] || '#64748b'}30`,
                fontSize: 12, color: SEV_COLORS[sev] || '#64748b',
              }}>
                {sev}: <strong>{count}</strong>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="slide-up-d3" style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
          {tabs.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: '8px 18px', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer',
              border: 'none',
              background: tab === t.key ? colors.accent : colors.bgElevated,
              color: tab === t.key ? '#fff' : colors.textSecondary,
            }}>{t.label}</button>
          ))}
        </div>

        {/* Events Tab */}
        {tab === 'events' && (
          <Card title={`Recent Events (${(data?.recent_events || []).length})`}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {(data?.recent_events || []).map((e: any, i: number) => (
                <div key={i} style={{
                  padding: 12, borderRadius: 8, background: colors.bgElevated,
                  borderLeft: `3px solid ${SEV_COLORS[e.severity] || '#64748b'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{
                        padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 600,
                        background: (SEV_COLORS[e.severity] || '#64748b') + '20',
                        color: SEV_COLORS[e.severity] || '#64748b',
                      }}>{e.severity}</span>
                      <span style={{ fontSize: 13, color: colors.text, fontWeight: 500 }}>
                        {e.event_type.replace(/_/g, ' ')}
                      </span>
                      <span style={{ fontSize: 11, color: colors.textMuted }}>from {e.source_ip}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {e.blocked && (
                        <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 600, background: colors.dangerBg, color: colors.danger }}>
                          BLOCKED
                        </span>
                      )}
                      <span style={{ fontSize: 10, color: colors.textMuted }}>
                        {new Date(e.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                  {e.details && Object.keys(e.details).length > 0 && (
                    <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 6 }}>
                      {Object.entries(e.details).map(([k, v]) => `${k}: ${v}`).join(' · ')}
                    </div>
                  )}
                </div>
              ))}
              {(!data?.recent_events || data.recent_events.length === 0) && (
                <div style={{ color: colors.textMuted, fontSize: 13, textAlign: 'center', padding: 20 }}>No recent events</div>
              )}
            </div>
          </Card>
        )}

        {/* Threats Tab */}
        {tab === 'threats' && (
          <Card title={`Threat Indicators (${(data?.threats || []).length})`}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {(data?.threats || []).map((t: any, i: number) => (
                <div key={i} style={{
                  padding: 14, borderRadius: 8, background: colors.bgElevated,
                  borderLeft: `3px solid ${SEV_COLORS[t.threat_level] || '#64748b'}`,
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 14, color: colors.text, fontWeight: 600, fontFamily: 'monospace' }}>{t.indicator}</span>
                      <span style={{
                        padding: '2px 6px', borderRadius: 4, fontSize: 10,
                        background: colors.bgElevated, border: `1px solid ${colors.border}`, color: colors.textSecondary,
                      }}>{t.type}</span>
                    </div>
                    <div style={{ fontSize: 11, color: colors.textMuted, marginTop: 4 }}>
                      Hits: {t.hit_count} · First seen: {new Date(t.first_seen).toLocaleTimeString()}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                      background: (SEV_COLORS[t.threat_level] || '#64748b') + '20',
                      color: SEV_COLORS[t.threat_level] || '#64748b',
                    }}>{t.threat_level}</span>
                    {t.blocked && (
                      <span style={{ padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600, background: colors.dangerBg, color: colors.danger }}>
                        BLOCKED
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* WAF Tab */}
        {tab === 'waf' && (
          <Card title={`WAF Rules (${(data?.waf_rules || []).length})`}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {(data?.waf_rules || []).map((r: any, i: number) => (
                <div key={i} style={{
                  padding: 12, borderRadius: 8, background: colors.bgElevated,
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 11, color: '#60a5fa', fontWeight: 600, fontFamily: 'monospace' }}>{r.rule_id}</span>
                      <span style={{ fontSize: 13, color: colors.text }}>{r.name}</span>
                    </div>
                    <div style={{ fontSize: 11, color: colors.textMuted, marginTop: 2 }}>
                      Action: {r.action} · Hits: {r.hits}
                      {r.last_triggered && ` · Last: ${new Date(r.last_triggered).toLocaleTimeString()}`}
                    </div>
                  </div>
                  <span style={{
                    padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                    background: r.enabled ? colors.successBg : 'rgba(100,116,139,0.15)',
                    color: r.enabled ? colors.success : colors.textMuted,
                  }}>{r.enabled ? 'ACTIVE' : 'DISABLED'}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Secrets Tab */}
        {tab === 'secrets' && (
          <Card title={`Secrets Vault (${secrets?.total_secrets || 0})`}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {(secrets?.inventory || []).map((s: any, i: number) => (
                <div key={i} style={{
                  padding: 12, borderRadius: 8, background: colors.bgElevated,
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 13, color: colors.text, fontWeight: 600, fontFamily: 'monospace' }}>{s.name}</span>
                      <span style={{
                        padding: '2px 6px', borderRadius: 4, fontSize: 10,
                        background: colors.bgElevated, border: `1px solid ${colors.border}`, color: colors.textSecondary,
                      }}>v{s.version}</span>
                      {s.tags?.type && (
                        <span style={{
                          padding: '2px 6px', borderRadius: 4, fontSize: 10,
                          background: 'rgba(139,92,246,0.12)', color: '#8b5cf6',
                        }}>{s.tags.type}</span>
                      )}
                    </div>
                    <div style={{ fontSize: 11, color: colors.textMuted, marginTop: 2 }}>
                      Rotated {s.days_since_rotation}d ago · Policy: {s.rotation_policy_days}d · Accesses: {s.access_count}
                    </div>
                  </div>
                  <span style={{
                    padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                    background: s.status === 'healthy' ? colors.successBg : s.status === 'rotation_soon' ? colors.warningBg : colors.dangerBg,
                    color: s.status === 'healthy' ? colors.success : s.status === 'rotation_soon' ? colors.warning : colors.danger,
                  }}>{s.status.replace(/_/g, ' ')}</span>
                </div>
              ))}
            </div>
            {secrets?.issues?.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: colors.warning, marginBottom: 8 }}>Issues ({secrets.issues.length})</div>
                {secrets.issues.map((issue: any, i: number) => (
                  <div key={i} style={{
                    padding: 8, borderRadius: 6, background: colors.warningBg, marginBottom: 4,
                    fontSize: 12, color: colors.warning,
                  }}>
                    {issue.secret}: {issue.issue.replace(/_/g, ' ')}
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
