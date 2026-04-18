'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

const SCENARIO_ICONS: Record<string, string> = {
  cpu: '🔥', memory: '🧠', disk: '💾', network: '🌐',
  database: '🗄️', cascade: '💥', deploy: '🚀', shield: '🛡️',
};

const AGENT_COLORS: Record<string, string> = {
  'Monitor Agent': '#3b82f6',
  'Diagnostic Agent': '#8b5cf6',
  'Remediation Agent': '#10b981',
  'Communication Agent': '#ef4444',
  'Learning Agent': '#f59e0b',
  'Prediction Agent': '#06b6d4',
};

const SERVICES = ['api-server', 'auth-service', 'db-primary', 'cache-redis', 'worker-queue', 'web-frontend'];
const SEVERITIES = ['low', 'medium', 'high', 'critical'];

function Card({ title, children, style }: { title: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`, overflow: 'hidden', ...style }}>
      <div style={{ padding: '14px 20px', borderBottom: `1px solid ${colors.border}`, fontSize: 14, fontWeight: 600, color: colors.text }}>
        {title}
      </div>
      <div style={{ padding: 20 }}>{children}</div>
    </div>
  );
}

export default function ScenariosPage() {
  const { isMobile } = useBreakpoint();
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [service, setService] = useState(SERVICES[0]);
  const [severity, setSeverity] = useState('high');
  const [result, setResult] = useState<any>(null);
  const [simulating, setSimulating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/scenarios/templates`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => { setTemplates(d.templates || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const runSimulation = async () => {
    if (!selectedType) return;
    setSimulating(true);
    setResult(null);
    try {
      const res = await fetch(`${API}/scenarios/simulate`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ scenario_type: selectedType, service, severity }),
      });
      const data = await res.json();
      setResult(data);
    } catch {
      // ignore
    } finally {
      setSimulating(false);
    }
  };

  const selectedTemplate = templates.find(t => t.id === selectedType);

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1400, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 24 }}>
          <h1 style={{
            fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: '0 0 6px',
            background: 'linear-gradient(135deg, #f0f0f0, #f59e0b)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>What-If Scenario Simulator</h1>
          <p style={{ color: colors.textMuted, fontSize: 13 }}>
            Simulate infrastructure incidents and see how AI agents would detect, diagnose, and remediate them
          </p>
        </div>

        {/* Scenario Picker */}
        <div className="slide-up-d1">
          <Card title="Choose a Scenario" style={{ marginBottom: 20 }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)',
              gap: 10,
            }}>
              {templates.map(t => (
                <button key={t.id} onClick={() => { setSelectedType(t.id); setResult(null); }}
                  style={{
                    padding: 14, borderRadius: 10, textAlign: 'left' as const, cursor: 'pointer',
                    border: selectedType === t.id ? `1px solid ${colors.accent}` : `1px solid ${colors.border}`,
                    background: selectedType === t.id ? 'rgba(59,130,246,0.1)' : colors.bgElevated,
                    transition: 'all 0.2s',
                  }}>
                  <div style={{ fontSize: 20, marginBottom: 6 }}>{SCENARIO_ICONS[t.icon] || '⚡'}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: colors.text, marginBottom: 4 }}>{t.name}</div>
                  <div style={{ fontSize: 11, color: colors.textDim, lineHeight: 1.4 }}>{t.description}</div>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Configuration & Run */}
        {selectedType && (
          <div className="slide-up-d2">
            <Card title="Configure Simulation" style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 16, alignItems: isMobile ? 'stretch' : 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: 12, color: colors.textSecondary, marginBottom: 4, fontWeight: 500 }}>Target Service</label>
                  <select value={service} onChange={e => setService(e.target.value)}
                    style={{
                      width: '100%', padding: '8px 12px', borderRadius: 6,
                      border: `1px solid ${colors.border}`, background: colors.bgInput,
                      color: colors.text, fontSize: 13,
                    }}>
                    {SERVICES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: 12, color: colors.textSecondary, marginBottom: 4, fontWeight: 500 }}>Severity</label>
                  <select value={severity} onChange={e => setSeverity(e.target.value)}
                    style={{
                      width: '100%', padding: '8px 12px', borderRadius: 6,
                      border: `1px solid ${colors.border}`, background: colors.bgInput,
                      color: colors.text, fontSize: 13,
                    }}>
                    {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                {selectedTemplate && (
                  <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', fontSize: 12, color: colors.textSecondary, marginBottom: 4, fontWeight: 500 }}>Affected Metrics</label>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {selectedTemplate.affected_metrics.map((m: string) => (
                        <span key={m} style={{
                          padding: '4px 8px', borderRadius: 5, fontSize: 11,
                          background: 'rgba(59,130,246,0.1)', color: colors.accent,
                        }}>{m}</span>
                      ))}
                    </div>
                  </div>
                )}
                <button onClick={runSimulation} disabled={simulating}
                  style={{
                    padding: '10px 28px', borderRadius: 8, border: 'none', cursor: 'pointer',
                    background: simulating ? colors.bgElevated : colors.accentGradient,
                    color: '#fff', fontWeight: 600, fontSize: 13, whiteSpace: 'nowrap',
                    opacity: simulating ? 0.6 : 1,
                  }}>
                  {simulating ? 'Simulating...' : 'Run Simulation'}
                </button>
              </div>
            </Card>
          </div>
        )}

        {/* Simulation Results */}
        {result && (
          <div className="slide-up">
            {/* Summary stats */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)',
              gap: 10, marginBottom: 20,
            }}>
              {[
                { label: 'Detection Time', value: `${result.simulation.total_detection_time_seconds}s`, color: colors.accent },
                { label: 'Total Resolution', value: `${Math.round(result.simulation.total_resolution_time_seconds / 60)}min`, color: colors.success },
                { label: 'Agents Involved', value: result.simulation.agents_involved, color: '#8b5cf6' },
                { label: 'Auto Resolution', value: result.simulation.automatic_resolution ? 'Yes' : 'Needs Approval', color: result.simulation.automatic_resolution ? colors.success : colors.warning },
              ].map(s => (
                <div key={s.label} style={{
                  padding: 16, borderRadius: 12, background: colors.bgCard,
                  border: `1px solid ${colors.border}`, borderTop: `2px solid ${s.color}`,
                }}>
                  <div style={{ fontSize: 10, color: colors.textDim, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>{s.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: colors.text, marginTop: 4 }}>{s.value}</div>
                </div>
              ))}
            </div>

            {/* Agent Response Timeline */}
            <Card title="Agent Response Timeline" style={{ marginBottom: 20 }}>
              <div style={{ position: 'relative', paddingLeft: 28 }}>
                {/* Vertical line */}
                <div style={{
                  position: 'absolute', left: 8, top: 6, bottom: 6, width: 2,
                  background: 'linear-gradient(180deg, #3b82f6, #10b981, #f59e0b)',
                  borderRadius: 2,
                }} />

                {result.simulation.timeline.map((step: any, i: number) => {
                  const agentColor = AGENT_COLORS[step.agent] || colors.accent;
                  return (
                    <div key={i} style={{
                      marginBottom: i < result.simulation.timeline.length - 1 ? 20 : 0,
                      position: 'relative',
                      animation: `slide-up 0.4s ease-out ${i * 0.12}s both`,
                    }}>
                      {/* Dot */}
                      <div style={{
                        position: 'absolute', left: -28, top: 4,
                        width: 18, height: 18, borderRadius: '50%',
                        background: agentColor, boxShadow: `0 0 10px ${agentColor}50`,
                        border: '3px solid #04040c',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#fff' }} />
                      </div>

                      {/* Content */}
                      <div style={{
                        padding: 14, borderRadius: 10,
                        background: colors.bgElevated,
                        border: `1px solid ${colors.borderLight}`,
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: 13, fontWeight: 700, color: agentColor }}>{step.agent}</span>
                            <span style={{
                              padding: '2px 8px', borderRadius: 5, fontSize: 10, fontWeight: 600,
                              background: `${agentColor}15`, color: agentColor,
                            }}>{step.action}</span>
                          </div>
                          <span style={{ fontSize: 11, color: colors.textDim }}>+{step.delay_seconds}s</span>
                        </div>
                        <p style={{ fontSize: 13, color: colors.textSecondary, lineHeight: 1.6, margin: '0 0 8px' }}>
                          {step.details}
                        </p>

                        {/* Extra details */}
                        {step.confidence && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                            <span style={{ fontSize: 11, color: colors.textDim }}>Confidence:</span>
                            <div style={{ flex: 1, maxWidth: 120, height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)' }}>
                              <div style={{ width: `${step.confidence}%`, height: '100%', borderRadius: 3, background: step.confidence >= 85 ? colors.success : colors.warning }} />
                            </div>
                            <span style={{ fontSize: 12, fontWeight: 700, color: step.confidence >= 85 ? colors.success : colors.warning }}>{step.confidence}%</span>
                          </div>
                        )}

                        {step.reasoning && (
                          <div style={{ marginTop: 6 }}>
                            {step.reasoning.map((r: string, j: number) => (
                              <div key={j} style={{ display: 'flex', alignItems: 'flex-start', gap: 6, marginBottom: 3 }}>
                                <span style={{ width: 4, height: 4, borderRadius: '50%', background: agentColor, marginTop: 6, flexShrink: 0 }} />
                                <span style={{ fontSize: 12, color: colors.textDim, lineHeight: 1.5 }}>{r}</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {step.proposed_actions && (
                          <div style={{ marginTop: 8 }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: colors.textDim, marginBottom: 4 }}>Proposed Actions:</div>
                            {step.proposed_actions.map((a: string, j: number) => (
                              <div key={j} style={{
                                padding: '6px 10px', borderRadius: 6, marginBottom: 4,
                                background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.12)',
                                fontSize: 12, color: colors.success,
                              }}>{a}</div>
                            ))}
                            {step.requires_approval && (
                              <div style={{
                                marginTop: 4, padding: '4px 10px', borderRadius: 5, fontSize: 11, fontWeight: 600,
                                background: colors.warningBg, color: colors.warning, display: 'inline-block',
                              }}>Requires human approval</div>
                            )}
                          </div>
                        )}

                        {step.channels && (
                          <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                            {step.channels.map((ch: string) => (
                              <span key={ch} style={{
                                padding: '3px 8px', borderRadius: 5, fontSize: 10,
                                background: 'rgba(239,68,68,0.08)', color: '#f87171',
                              }}>{ch}</span>
                            ))}
                          </div>
                        )}

                        {step.prevention_recommendations && (
                          <div style={{ marginTop: 6 }}>
                            <div style={{ fontSize: 11, fontWeight: 600, color: colors.textDim, marginBottom: 4 }}>Prevention:</div>
                            {step.prevention_recommendations.map((r: string, j: number) => (
                              <div key={j} style={{ fontSize: 12, color: colors.info, marginBottom: 2 }}>• {r}</div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
