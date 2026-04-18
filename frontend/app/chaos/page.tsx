'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const SEV_COLORS: Record<string, string> = {
  critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#3b82f6',
};
const STATE_COLORS: Record<string, string> = {
  pending: '#64748b', running: '#f59e0b', completed: '#10b981',
  rolled_back: '#3b82f6', aborted: '#ef4444', failed: '#ef4444',
};
const DIFF_COLORS: Record<string, string> = {
  easy: '#10b981', medium: '#f59e0b', hard: '#f97316', extreme: '#ef4444',
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

export default function ChaosPage() {
  const { isMobile } = useBreakpoint();
  const [experiments, setExperiments] = useState<any[]>([]);
  const [resilience, setResilience] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [gamedayHistory, setGamedayHistory] = useState<any[]>([]);
  const [tab, setTab] = useState<'experiments' | 'resilience' | 'gameday'>('experiments');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/chaos-eng/experiments`, { headers: authHeaders() }).then(r => r.json()).catch(() => ({ experiments: [] })),
      fetch(`${API}/chaos-eng/resilience-score`, { headers: authHeaders() }).then(r => r.json()).catch(() => null),
      fetch(`${API}/chaos-eng/history`, { headers: authHeaders() }).then(r => r.json()).catch(() => ({ history: [] })),
      fetch(`${API}/chaos-eng/gameday/scenarios`, { headers: authHeaders() }).then(r => r.json()).catch(() => ({ scenarios: [] })),
      fetch(`${API}/chaos-eng/gameday/history`, { headers: authHeaders() }).then(r => r.json()).catch(() => ({ history: [] })),
    ]).then(([exp, res, hist, sc, gdh]) => {
      setExperiments(exp.experiments || []);
      setResilience(res);
      setHistory(hist.history || []);
      setScenarios(sc.scenarios || []);
      setGamedayHistory(gdh.history || []);
      setLoading(false);
    });
  }, []);

  if (loading) return (
    <DashboardShell>
      <div style={{ padding: 32, color: colors.textMuted }}>Loading chaos data...</div>
    </DashboardShell>
  );

  const tabs = [
    { key: 'experiments', label: 'Experiments' },
    { key: 'resilience', label: 'Resilience Score' },
    { key: 'gameday', label: 'Game Day' },
  ] as const;

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1400, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: '0 0 6px', background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Chaos Engineering</h1>
          <p style={{ color: colors.textMuted, fontSize: 14 }}>
            Controlled failure injection to test and improve system resilience
          </p>
        </div>

        {/* Resilience Score Banner */}
        {resilience && resilience.experiments_run > 0 && (
          <div className="slide-up-d1" style={{
            background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`,
            padding: isMobile ? 16 : 24, marginBottom: 24, display: 'flex', justifyContent: 'space-around', textAlign: 'center', position: 'relative', overflow: 'hidden', flexWrap: 'wrap' as const, gap: isMobile ? 12 : 0,
          }}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div>
              <div style={{
                fontSize: 40, fontWeight: 700,
                color: resilience.score >= 80 ? colors.success : resilience.score >= 60 ? colors.warning : colors.danger,
              }}>{resilience.score}%</div>
              <div style={{ fontSize: 12, color: colors.textSecondary }}>Resilience Score ({resilience.grade})</div>
            </div>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, color: colors.accent }}>{resilience.detection_rate}%</div>
              <div style={{ fontSize: 12, color: colors.textSecondary }}>Detection Rate</div>
            </div>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#8b5cf6' }}>{resilience.diagnosis_rate}%</div>
              <div style={{ fontSize: 12, color: colors.textSecondary }}>Diagnosis Rate</div>
            </div>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, color: colors.success }}>{resilience.remediation_rate}%</div>
              <div style={{ fontSize: 12, color: colors.textSecondary }}>Remediation Rate</div>
            </div>
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, color: colors.warning }}>{resilience.experiments_run}</div>
              <div style={{ fontSize: 12, color: colors.textSecondary }}>Experiments Run</div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="slide-up-d2" style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
          {tabs.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: '8px 18px', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer',
              border: 'none',
              background: tab === t.key ? colors.danger : colors.bgElevated,
              color: tab === t.key ? '#fff' : colors.textSecondary,
            }}>{t.label}</button>
          ))}
        </div>

        {/* Experiments Tab */}
        {tab === 'experiments' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <Card title={`Available Experiments (${experiments.length})`}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 10 }}>
                {experiments.map((exp, i) => (
                  <div key={i} style={{
                    padding: 14, borderRadius: 8, background: colors.bgElevated,
                    borderLeft: `3px solid ${SEV_COLORS[exp.severity] || '#64748b'}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 13, color: colors.text, fontWeight: 600 }}>{exp.name.replace(/_/g, ' ')}</span>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <span style={{
                          padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 600,
                          background: (SEV_COLORS[exp.severity] || '#64748b') + '20',
                          color: SEV_COLORS[exp.severity] || '#64748b',
                        }}>{exp.severity}</span>
                        <span style={{
                          padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 600,
                          background: (STATE_COLORS[exp.state] || '#64748b') + '20',
                          color: STATE_COLORS[exp.state] || '#64748b',
                        }}>{exp.state}</span>
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: colors.textSecondary, marginBottom: 4 }}>{exp.description}</div>
                    <div style={{ fontSize: 10, color: colors.textMuted }}>
                      Category: {exp.category} | Duration: {exp.duration_seconds}s
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {history.length > 0 && (
              <Card title={`Experiment History (${history.length})`}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {history.map((h, i) => (
                    <div key={i} style={{
                      padding: 12, borderRadius: 8, background: colors.bgElevated,
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    }}>
                      <div>
                        <span style={{ fontSize: 13, color: colors.text, fontWeight: 500 }}>{h.experiment}</span>
                        <span style={{ fontSize: 11, color: colors.textMuted, marginLeft: 8 }}>{h.category}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
                        {h.agent_response && (
                          <>
                            <span style={{ color: h.agent_response.detected ? colors.success : colors.danger }}>
                              {h.agent_response.detected ? 'Detected' : 'Missed'}
                            </span>
                            <span style={{ color: h.agent_response.remediated ? colors.success : colors.warning }}>
                              {h.agent_response.remediated ? 'Remediated' : 'Manual'}
                            </span>
                          </>
                        )}
                        <span style={{ color: h.rollback === 'completed' ? colors.success : colors.danger }}>
                          {h.rollback === 'completed' ? 'Recovered' : 'Failed'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}

        {/* Resilience Tab */}
        {tab === 'resilience' && resilience && (
          <Card title="Resilience Analysis">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14 }}>
              {[
                { label: 'Overall Score', value: `${resilience.score}%`, color: resilience.score >= 80 ? colors.success : colors.warning },
                { label: 'Grade', value: resilience.grade, color: colors.text },
                { label: 'Detection Rate', value: `${resilience.detection_rate}%`, color: colors.accent },
                { label: 'Diagnosis Rate', value: `${resilience.diagnosis_rate}%`, color: '#8b5cf6' },
                { label: 'Remediation Rate', value: `${resilience.remediation_rate}%`, color: colors.success },
                { label: 'Recovery Rate', value: `${resilience.recovery_rate}%`, color: colors.warning },
                { label: 'Avg Detection', value: `${resilience.avg_detection_time_ms}ms`, color: colors.textSecondary },
                { label: 'Experiments', value: resilience.experiments_run, color: colors.text },
              ].map(m => (
                <div key={m.label} style={{
                  padding: 16, borderRadius: 8, background: colors.bgElevated, textAlign: 'center',
                }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: m.color }}>{m.value}</div>
                  <div style={{ fontSize: 11, color: colors.textMuted, marginTop: 4 }}>{m.label}</div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Game Day Tab */}
        {tab === 'gameday' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <Card title={`Game Day Scenarios (${scenarios.length})`}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {scenarios.map((s, i) => (
                  <div key={i} style={{
                    padding: 16, borderRadius: 8, background: colors.bgElevated,
                    borderLeft: `3px solid ${DIFF_COLORS[s.difficulty] || '#64748b'}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 14, color: colors.text, fontWeight: 600 }}>{s.name}</span>
                      <span style={{
                        padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                        background: (DIFF_COLORS[s.difficulty] || '#64748b') + '20',
                        color: DIFF_COLORS[s.difficulty] || '#64748b',
                      }}>{s.difficulty}</span>
                    </div>
                    <div style={{ fontSize: 12, color: colors.textSecondary, marginBottom: 6 }}>{s.description}</div>
                    <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 6 }}>
                      Impact: {s.expected_impact} | Time limit: {s.time_limit_minutes}min | Experiments: {s.experiments.join(', ')}
                    </div>
                    <div style={{ fontSize: 11, color: '#60a5fa' }}>
                      Success criteria: {s.success_criteria.length} items
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {gamedayHistory.length > 0 && (
              <Card title={`Game Day History (${gamedayHistory.length})`}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {gamedayHistory.map((g, i) => (
                    <div key={i} style={{
                      padding: 14, borderRadius: 8, background: colors.bgElevated,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <span style={{ fontSize: 13, color: colors.text, fontWeight: 600 }}>{g.scenario_name}</span>
                        <span style={{
                          fontSize: 20, fontWeight: 700,
                          color: g.team_score >= 80 ? colors.success : g.team_score >= 60 ? colors.warning : colors.danger,
                        }}>{g.team_score}%</span>
                      </div>
                      <div style={{ display: 'flex', gap: 12, fontSize: 11, color: colors.textSecondary, marginBottom: 6 }}>
                        <span>Detected: {g.incidents_detected}/{g.criteria_total}</span>
                        <span>Resolved: {g.incidents_resolved}/{g.criteria_total}</span>
                        <span>Criteria: {g.criteria_met}/{g.criteria_total}</span>
                      </div>
                      {g.lessons_learned && g.lessons_learned.length > 0 && (
                        <div style={{ fontSize: 11, color: colors.warning }}>
                          {g.lessons_learned.slice(0, 2).map((l: string, j: number) => (
                            <div key={j}>{l}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
