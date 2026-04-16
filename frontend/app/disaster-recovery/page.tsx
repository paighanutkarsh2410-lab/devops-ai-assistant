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
  healthy: '#10b981', ready: '#10b981', mostly_ready: '#f59e0b',
  needs_improvement: '#f97316', not_ready: '#ef4444', pass: '#10b981',
  fail: '#ef4444', partial: '#f59e0b', critical: '#ef4444',
  high: '#f97316', medium: '#f59e0b', low: '#3b82f6',
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

export default function DisasterRecoveryPage() {
  const [status, setStatus] = useState<any>(null);
  const [testResults, setTestResults] = useState<any>(null);
  const [scenarios, setScenarios] = useState<any>(null);
  const [tab, setTab] = useState<'overview' | 'tests' | 'scenarios'>('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/dr/status`, { headers: authHeaders() }).then(r => r.json()).catch(() => null),
      fetch(`${API}/dr/test-results`, { headers: authHeaders() }).then(r => r.json()).catch(() => null),
      fetch(`${API}/dr/scenarios`, { headers: authHeaders() }).then(r => r.json()).catch(() => null),
    ]).then(([s, t, sc]) => {
      setStatus(s);
      setTestResults(t);
      setScenarios(sc);
      setLoading(false);
    });
  }, []);

  if (loading) return (
    <DashboardShell>
      <div style={{ padding: 32, color: colors.textMuted }}>Loading DR data...</div>
    </DashboardShell>
  );

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'tests', label: 'DR Tests' },
    { key: 'scenarios', label: 'Scenarios' },
  ] as const;

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1400, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: '0 0 6px', background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Disaster Recovery</h1>
          <p style={{ color: colors.textMuted, fontSize: 14 }}>
            Business continuity, backup status, and recovery testing
          </p>
        </div>

        {/* Readiness Badge */}
        {status && (
          <div className="slide-up-d1" style={{
            background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`,
            padding: 24, marginBottom: 24, textAlign: 'center', position: 'relative', overflow: 'hidden',
          }}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div style={{
              fontSize: 20, fontWeight: 700,
              color: STATUS_COLORS[status.readiness] || colors.textMuted,
            }}>
              {(status.readiness || 'unknown').toUpperCase().replace(/_/g, ' ')}
            </div>
            <div style={{ fontSize: 13, color: colors.textSecondary, marginTop: 4 }}>DR Readiness Status</div>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 24, marginTop: 12 }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: colors.accent }}>{status.rto_target_seconds / 60}m</div>
                <div style={{ fontSize: 11, color: colors.textMuted }}>RTO Target</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: '#8b5cf6' }}>{status.rpo_target_seconds / 60}m</div>
                <div style={{ fontSize: 11, color: colors.textMuted }}>RPO Target</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: colors.success }}>{status.availability_target}%</div>
                <div style={{ fontSize: 11, color: colors.textMuted }}>Availability</div>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="slide-up-d2" style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
          {tabs.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: '8px 18px', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer',
              border: 'none',
              background: tab === t.key ? colors.accent : colors.bgElevated,
              color: tab === t.key ? '#fff' : colors.textSecondary,
            }}>{t.label}</button>
          ))}
        </div>

        {/* Overview Tab */}
        {tab === 'overview' && status && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <Card title="Infrastructure Components">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {(status.components || []).map((c: any, i: number) => (
                  <div key={i} style={{
                    padding: 12, borderRadius: 8, background: colors.bgElevated,
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}>
                    <div>
                      <span style={{ fontSize: 13, color: colors.text, fontWeight: 500 }}>{c.name}</span>
                      <span style={{ fontSize: 11, color: colors.textMuted, marginLeft: 10 }}>Failover: {c.failover}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {c.last_backup && (
                        <span style={{ fontSize: 10, color: colors.textMuted }}>
                          Backup: {new Date(c.last_backup).toLocaleString()}
                        </span>
                      )}
                      <span style={{
                        padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                        background: (STATUS_COLORS[c.status] || '#64748b') + '20',
                        color: STATUS_COLORS[c.status] || '#64748b',
                      }}>{c.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="Backup Summary">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
                {Object.entries(status.backup_summary || {}).map(([key, b]: [string, any]) => (
                  <div key={key} style={{ padding: 14, borderRadius: 8, background: colors.bgElevated }}>
                    <div style={{ fontSize: 13, color: colors.text, fontWeight: 600, marginBottom: 6, textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</div>
                    <div style={{ fontSize: 11, color: colors.textSecondary, display: 'flex', flexDirection: 'column', gap: 3 }}>
                      <span>Frequency: {b.frequency}</span>
                      <span>Retention: {b.retention}</span>
                      <span>Cross-region: {b.cross_region ? 'Yes' : 'No'}</span>
                      <span>Verified: {new Date(b.last_verified).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* Tests Tab */}
        {tab === 'tests' && testResults && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
              {[
                { label: 'Total Tests', value: testResults.total_tests, color: colors.accent },
                { label: 'Passed', value: testResults.passed, color: colors.success },
                { label: 'Failed', value: testResults.failed, color: colors.danger },
                { label: 'Readiness', value: (testResults.overall_readiness || '').replace(/_/g, ' '), color: STATUS_COLORS[testResults.overall_readiness] || colors.textMuted },
              ].map(s => (
                <div key={s.label} style={{
                  background: colors.bgCard, borderRadius: 10, border: `1px solid ${colors.border}`, padding: 14, textAlign: 'center',
                }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
                  <div style={{ fontSize: 11, color: colors.textSecondary }}>{s.label}</div>
                </div>
              ))}
            </div>

            <Card title="Test Results">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {(testResults.results || []).map((r: any, i: number) => (
                  <div key={i} style={{
                    padding: 12, borderRadius: 8, background: colors.bgElevated,
                    borderLeft: `3px solid ${STATUS_COLORS[r.status] || '#64748b'}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <span style={{ fontSize: 13, color: colors.text, fontWeight: 500 }}>{r.test_name}</span>
                        <span style={{
                          marginLeft: 8, padding: '2px 6px', borderRadius: 4, fontSize: 10,
                          background: colors.bgElevated, border: `1px solid ${colors.border}`, color: colors.textSecondary,
                        }}>{r.category}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 11, color: colors.textMuted }}>{r.duration_seconds.toFixed(1)}s</span>
                        <span style={{
                          padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                          background: (STATUS_COLORS[r.status] || '#64748b') + '20',
                          color: STATUS_COLORS[r.status] || '#64748b',
                        }}>{r.status}</span>
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 4 }}>{r.details}</div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                      {r.rto_met !== undefined && (
                        <span style={{ fontSize: 10, color: r.rto_met ? colors.success : colors.danger }}>
                          RTO: {r.rto_met ? 'MET' : 'MISSED'}
                        </span>
                      )}
                      {r.rpo_met !== undefined && (
                        <span style={{ fontSize: 10, color: r.rpo_met ? colors.success : colors.danger }}>
                          RPO: {r.rpo_met ? 'MET' : 'MISSED'}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* Scenarios Tab */}
        {tab === 'scenarios' && scenarios && (
          <Card title={`Disaster Scenarios (${(scenarios.scenarios || []).length})`}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {(scenarios.scenarios || []).map((s: any, i: number) => (
                <div key={i} style={{
                  padding: 16, borderRadius: 8, background: colors.bgElevated,
                  borderLeft: `3px solid ${STATUS_COLORS[s.severity] || '#64748b'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14, color: colors.text, fontWeight: 600 }}>{s.name}</span>
                    <span style={{
                      padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                      background: (STATUS_COLORS[s.severity] || '#64748b') + '20',
                      color: STATUS_COLORS[s.severity] || '#64748b',
                    }}>{s.severity}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: 12, color: colors.textSecondary }}>
                    <span>Detection: {s.detection}</span>
                    <span>Recovery: {s.recovery_time}</span>
                    <span>Steps: {s.procedure_steps}</span>
                    <span style={{ color: s.automated ? colors.success : colors.warning }}>
                      {s.automated ? 'Automated' : 'Manual'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
