'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/* -- Helpers ---------------------------------------------------------- */

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchJSON(path: string) {
  const res = await fetch(`${API}${path}`, { headers: authHeaders() });
  return res.json();
}

const STATUS_COLORS: Record<string, string> = {
  idle: colors.success, busy: colors.warning, offline: colors.danger, active: colors.success,
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: colors.danger, high: '#f97316', medium: colors.warning, low: colors.accent, info: colors.textMuted,
};

const PATTERN_ICONS: Record<string, string> = {
  cascading_failure: '\u26a1', temporal_hour: '\u23f0', slow_degradation: '\ud83d\udcc9',
  oscillating: '\ud83c\udf0a', correlation: '\ud83d\udd17', rare_event: '\ud83d\udea8', sequence: '\u2699\ufe0f',
};

/* -- Card Component --------------------------------------------------- */

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

/* -- Main Page -------------------------------------------------------- */

export default function AgentIntelligencePage() {
  const [orchStatus, setOrchStatus] = useState<any>(null);
  const [specialists, setSpecialists] = useState<any>(null);
  const [learning, setLearning] = useState<any>(null);
  const [patterns, setPatterns] = useState<any>(null);
  const [performance, setPerformance] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'specialists' | 'learning' | 'patterns' | 'performance'>('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchJSON('/agents/orchestration/status'),
      fetchJSON('/agents/specialists'),
      fetchJSON('/agents/learning/progress'),
      fetchJSON('/agents/patterns'),
      fetchJSON('/agents/performance'),
    ]).then(([o, s, l, p, perf]) => {
      setOrchStatus(o);
      setSpecialists(s);
      setLearning(l);
      setPatterns(p);
      setPerformance(perf);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <DashboardShell>
        <div style={{ padding: 32, color: colors.textMuted, fontSize: 14 }}>
          Loading agent intelligence data...
        </div>
      </DashboardShell>
    );
  }

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'specialists', label: 'Specialists' },
    { key: 'learning', label: 'Learning' },
    { key: 'patterns', label: 'Patterns' },
    { key: 'performance', label: 'Performance' },
  ] as const;

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1400, margin: '0 auto' }}>
        {/* Header */}
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Agent Intelligence
          </h1>
          <p style={{ color: colors.textMuted, fontSize: 13, marginTop: 6 }}>
            Multi-agent orchestration, specialist analysis, learning progress &amp; pattern recognition
          </p>
        </div>

        {/* Tabs */}
        <div className="slide-up-d1" style={{
          display: 'flex', gap: 4, marginBottom: 24, borderBottom: `1px solid ${colors.border}`,
          overflowX: 'auto',
        }}>
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '10px 20px', border: 'none', cursor: 'pointer',
                fontSize: 13, fontWeight: 600, background: 'transparent',
                color: activeTab === tab.key ? colors.text : colors.textDim,
                borderBottom: activeTab === tab.key ? `2px solid ${colors.accent}` : '2px solid transparent',
                whiteSpace: 'nowrap',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="slide-up-d2">
        {activeTab === 'overview' && <OverviewTab orch={orchStatus} learning={learning} patterns={patterns} performance={performance} />}
        {activeTab === 'specialists' && <SpecialistsTab data={specialists} />}
        {activeTab === 'learning' && <LearningTab data={learning} />}
        {activeTab === 'patterns' && <PatternsTab data={patterns} />}
        {activeTab === 'performance' && <PerformanceTab data={performance} />}
        </div>
      </div>
    </DashboardShell>
  );
}

/* -- Overview Tab ----------------------------------------------------- */

function OverviewTab({ orch, learning, patterns, performance }: any) {
  const registry = orch?.registry;
  const agents = registry?.agents || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        {[
          { label: 'Total Agents', value: registry?.total_agents || 0, color: colors.accent },
          { label: 'Available', value: registry?.available || 0, color: colors.success },
          { label: 'Busy', value: registry?.busy || 0, color: colors.warning },
          { label: 'Patterns Detected', value: patterns?.total_patterns || 0, color: '#8b5cf6' },
          { label: 'Learning Records', value: learning?.total_records || 0, color: '#06b6d4' },
        ].map(stat => (
          <div key={stat.label} style={{
            background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`,
            padding: 20, textAlign: 'center', position: 'relative', overflow: 'hidden',
          }}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div style={{ fontSize: 28, fontWeight: 700, color: stat.color }}>{stat.value}</div>
            <div style={{ fontSize: 12, color: colors.textDim, marginTop: 4 }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Agent Registry */}
      <Card title="Agent Registry">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
          {agents.map((agent: any) => (
            <div key={agent.id} style={{
              padding: 14, borderRadius: 8, background: colors.bgElevated,
              display: 'flex', flexDirection: 'column', gap: 8,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: colors.text }}>{agent.id}</span>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: STATUS_COLORS[agent.status] || colors.textMuted,
                  boxShadow: agent.status === 'idle' ? `0 0 6px ${colors.success}` : 'none',
                }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: colors.textDim }}>
                <span>{agent.type}</span>
                <span>{agent.success_rate}% success</span>
              </div>
              <div style={{ height: 4, borderRadius: 2, background: colors.bgCard, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 2,
                  width: `${agent.success_rate}%`,
                  background: agent.success_rate > 85 ? colors.success : agent.success_rate > 70 ? colors.warning : colors.danger,
                }} />
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Orchestration Patterns */}
      <Card title="Orchestration Patterns">
        <div style={{ display: 'flex', gap: 20 }}>
          {Object.entries(orch?.orchestrator?.pattern_usage || {}).map(([pattern, count]) => (
            <div key={pattern} style={{
              flex: 1, padding: 16, borderRadius: 8, background: colors.bgElevated, textAlign: 'center',
            }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: colors.accent }}>{count as number}</div>
              <div style={{ fontSize: 12, color: colors.textSecondary, marginTop: 4, textTransform: 'capitalize' }}>{pattern}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* -- Specialists Tab -------------------------------------------------- */

function SpecialistsTab({ data }: any) {
  const specs = data?.specialists || [];

  return (
    <Card title={`Specialist Agents (${specs.length})`}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {specs.map((spec: any) => (
          <div key={spec.id} style={{
            padding: 18, borderRadius: 10, background: colors.bgElevated,
            border: `1px solid ${colors.border}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: colors.text }}>{spec.id}</span>
              <span style={{
                padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600,
                background: (STATUS_COLORS[spec.status] || colors.textMuted) + '20',
                color: STATUS_COLORS[spec.status] || colors.textMuted,
              }}>
                {spec.status}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
              {spec.domains.map((d: string) => (
                <span key={d} style={{
                  padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 500,
                  background: 'rgba(59,130,246,0.1)', color: colors.accent,
                }}>
                  {d}
                </span>
              ))}
            </div>
            <div style={{ fontSize: 12, color: colors.textSecondary }}>
              Findings today: <span style={{ color: colors.text, fontWeight: 600 }}>{spec.findings_today}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* -- Learning Tab ----------------------------------------------------- */

function LearningTab({ data }: any) {
  const agents = data?.agents || {};
  const strategies = data?.strategy_rankings?.remediation || [];
  const featureImportance = data?.feature_importance?.feature_importance || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Agent Accuracy */}
      <Card title="Agent Learning Progress">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
          {Object.entries(agents).map(([name, info]: [string, any]) => (
            <div key={name} style={{
              padding: 16, borderRadius: 8, background: colors.bgElevated,
            }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: colors.text, marginBottom: 10 }}>{name}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 12, color: colors.textSecondary }}>Accuracy</span>
                <span style={{
                  fontSize: 13, fontWeight: 700,
                  color: info.accuracy > 85 ? colors.success : info.accuracy > 75 ? colors.warning : colors.danger,
                }}>
                  {info.accuracy}%
                </span>
              </div>
              <div style={{ height: 6, borderRadius: 3, background: colors.bgCard, overflow: 'hidden', marginBottom: 10 }}>
                <div style={{
                  height: '100%', borderRadius: 3,
                  width: `${info.accuracy}%`,
                  background: info.accuracy > 85 ? colors.success : info.accuracy > 75 ? colors.warning : colors.danger,
                }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: colors.textDim }}>
                <span>{info.total_tasks} tasks</span>
                <span style={{
                  color: info.trend === 'improving' ? colors.success : colors.warning,
                }}>
                  {info.trend === 'improving' ? '\u2191' : '\u2192'} {info.improvement_30d > 0 ? '+' : ''}{info.improvement_30d}% (30d)
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Strategy Rankings */}
      <Card title="Remediation Strategy Rankings">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {strategies.map((s: any, i: number) => (
            <div key={s.strategy} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '10px 14px', borderRadius: 8, background: colors.bgElevated,
            }}>
              <span style={{
                width: 26, height: 26, borderRadius: '50%', display: 'flex',
                alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700,
                background: i === 0 ? colors.successBg : colors.bgCard,
                color: i === 0 ? colors.success : colors.textDim,
                border: `1px solid ${i === 0 ? colors.success : colors.border}`,
              }}>
                {i + 1}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, color: colors.text, fontWeight: 500 }}>{s.strategy.replace(/_/g, ' ')}</div>
                <div style={{ fontSize: 11, color: colors.textDim }}>Avg time: {s.avg_time_sec}s</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: 14, fontWeight: 700,
                  color: s.success_rate > 80 ? colors.success : s.success_rate > 70 ? colors.warning : colors.danger,
                }}>
                  {s.success_rate}%
                </div>
                <div style={{ fontSize: 10, color: colors.textDim }}>success</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Feature Importance */}
      <Card title="Feature Importance (Meta-Learning)">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {Object.entries(featureImportance).map(([feature, importance]) => (
            <div key={feature} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontSize: 12, color: colors.textSecondary, width: 120, textTransform: 'capitalize' }}>
                {feature.replace(/_/g, ' ')}
              </span>
              <div style={{ flex: 1, height: 8, borderRadius: 4, background: colors.bgElevated, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 4,
                  width: `${(importance as number) * 100}%`,
                  background: '#8b5cf6',
                }} />
              </div>
              <span style={{ fontSize: 12, fontWeight: 600, color: colors.textSecondary, width: 40, textAlign: 'right' }}>
                {((importance as number) * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* -- Patterns Tab ----------------------------------------------------- */

function PatternsTab({ data }: any) {
  const pats = data?.patterns || [];

  return (
    <Card title={`Detected Patterns (${data?.total_patterns || 0})`}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {pats.map((p: any, i: number) => (
          <div key={i} style={{
            padding: 16, borderRadius: 10, background: colors.bgElevated,
            border: `1px solid ${(SEVERITY_COLORS[p.severity] || colors.border) + '30'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 18 }}>{PATTERN_ICONS[p.type] || '\ud83d\udd0d'}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: colors.text }}>{p.description}</div>
                  <div style={{ fontSize: 11, color: colors.textDim, marginTop: 2 }}>
                    Type: {p.type.replace(/_/g, ' ')} &middot; {p.occurrences} occurrences
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{
                  padding: '3px 10px', borderRadius: 12, fontSize: 10, fontWeight: 600,
                  background: (SEVERITY_COLORS[p.severity] || colors.textMuted) + '20',
                  color: SEVERITY_COLORS[p.severity] || colors.textMuted,
                  textTransform: 'uppercase',
                }}>
                  {p.severity}
                </span>
                <span style={{
                  padding: '3px 10px', borderRadius: 12, fontSize: 10, fontWeight: 600,
                  background: 'rgba(59,130,246,0.1)', color: colors.accent,
                }}>
                  {p.confidence}% conf.
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {p.affected_services.map((svc: string) => (
                <span key={svc} style={{
                  padding: '2px 8px', borderRadius: 6, fontSize: 10,
                  background: colors.bgCard, color: colors.textSecondary,
                }}>
                  {svc}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* -- Performance Tab -------------------------------------------------- */

function PerformanceTab({ data }: any) {
  const agents = data?.agents || {};
  const cache = data?.cache_stats || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Agent Performance */}
      <Card title="Agent Performance Benchmarks">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {Object.entries(agents).map(([name, info]: [string, any]) => {
            const pct = Math.min(100, (info.avg_cycle_ms / info.target_ms) * 100);
            return (
              <div key={name} style={{
                padding: 14, borderRadius: 8, background: colors.bgElevated,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: colors.text }}>{name}</span>
                  <span style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                    background: info.target_met ? colors.successBg : colors.dangerBg,
                    color: info.target_met ? colors.success : colors.danger,
                  }}>
                    {info.target_met ? 'Target Met' : 'Over Target'}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                  <div style={{ flex: 1, height: 8, borderRadius: 4, background: colors.bgCard, overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', borderRadius: 4,
                      width: `${pct}%`,
                      background: pct < 70 ? colors.success : pct < 90 ? colors.warning : colors.danger,
                    }} />
                  </div>
                  <span style={{ fontSize: 11, color: colors.textSecondary, minWidth: 90, textAlign: 'right' }}>
                    {(info.avg_cycle_ms / 1000).toFixed(1)}s / {(info.target_ms / 1000).toFixed(0)}s
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: colors.textDim }}>
                  <span>{info.operations} operations</span>
                  <span>Optimization: {info.optimization}</span>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Cache Stats */}
      <Card title="Cache Performance">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
          {Object.entries(cache).map(([name, stats]: [string, any]) => (
            <div key={name} style={{
              padding: 16, borderRadius: 8, background: colors.bgElevated, textAlign: 'center',
            }}>
              <div style={{ fontSize: 12, color: colors.textDim, marginBottom: 8, textTransform: 'uppercase' }}>{name}</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: colors.accent }}>{stats.hit_rate}%</div>
              <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 2 }}>hit rate</div>
              <div style={{ fontSize: 11, color: colors.textDim, marginTop: 6 }}>{stats.size} entries</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Bottlenecks */}
      {data?.bottlenecks?.length > 0 && (
        <Card title="Bottlenecks">
          {data.bottlenecks.map((b: any, i: number) => (
            <div key={i} style={{
              padding: 12, borderRadius: 8, background: colors.bgElevated, marginBottom: 8,
              borderLeft: `3px solid ${colors.danger}`,
            }}>
              <div style={{ fontSize: 13, color: colors.text, fontWeight: 500 }}>{b.agent} &mdash; {b.operation}</div>
              <div style={{ fontSize: 11, color: colors.danger, marginTop: 4 }}>
                {b.duration_ms}ms (target: {b.target_ms}ms, overshoot: +{b.overshoot_pct}%)
              </div>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
