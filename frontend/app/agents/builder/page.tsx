'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

async function fetchJSON(path: string) {
  const res = await fetch(`${API}${path}`, { headers: authHeaders() });
  return res.json();
}

/* -- Types ------------------------------------------------------------ */

interface TriggerConfig {
  metric: string;
  threshold: number;
  duration: string;
}

interface ActionConfig {
  type: string;
  params: Record<string, any>;
}

interface AgentDraft {
  name: string;
  description: string;
  triggers: TriggerConfig;
  data_sources: string[];
  analysis_prompt: string;
  actions: ActionConfig[];
}

const EMPTY_DRAFT: AgentDraft = {
  name: '', description: '',
  triggers: { metric: 'cpu_percent', threshold: 80, duration: '5m' },
  data_sources: [], analysis_prompt: '', actions: [],
};

const DATA_SOURCE_OPTIONS = [
  { id: 'prometheus_metrics', label: 'Prometheus Metrics' },
  { id: 'application_logs', label: 'Application Logs' },
  { id: 'database_queries', label: 'Database Queries' },
  { id: 'recent_deployments', label: 'Recent Deployments' },
  { id: 'external_api', label: 'External API' },
  { id: 'cloud_billing', label: 'Cloud Billing' },
];

const METRIC_OPTIONS = [
  'cpu_percent', 'memory_percent', 'disk_percent', 'api_response_time',
  'error_rate', 'request_rate', 'connection_count', 'hourly_cost',
];

/* -- Card ------------------------------------------------------------- */

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

function Input({ label, value, onChange, placeholder, type = 'text' }: any) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: 'block', fontSize: 12, color: colors.textSecondary, marginBottom: 4, fontWeight: 500 }}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(type === 'number' ? +e.target.value : e.target.value)}
        placeholder={placeholder}
        style={{
          width: '100%', padding: '8px 12px', borderRadius: 6, border: `1px solid ${colors.border}`,
          background: colors.bgInput, color: colors.text, fontSize: 13, outline: 'none', boxSizing: 'border-box',
        }}
      />
    </div>
  );
}

/* -- Page ------------------------------------------------------------- */

export default function AgentBuilderPage() {
  const [draft, setDraft] = useState<AgentDraft>(EMPTY_DRAFT);
  const [templates, setTemplates] = useState<any[]>([]);
  const [actionLib, setActionLib] = useState<any[]>([]);
  const [testResult, setTestResult] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [step, setStep] = useState(0);
  const [myAgents, setMyAgents] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      fetchJSON('/agents/custom/templates'),
      fetchJSON('/agents/custom/actions/library'),
      fetchJSON('/agents/custom'),
    ]).then(([t, a, m]) => {
      setTemplates(t.templates || []);
      setActionLib(a.actions || []);
      setMyAgents(m.agents || []);
    }).catch(() => {});
  }, []);

  const update = (field: string, value: any) => setDraft(d => ({ ...d, [field]: value }));
  const updateTrigger = (field: string, value: any) =>
    setDraft(d => ({ ...d, triggers: { ...d.triggers, [field]: value } }));

  const toggleDataSource = (id: string) => {
    setDraft(d => ({
      ...d,
      data_sources: d.data_sources.includes(id)
        ? d.data_sources.filter(s => s !== id)
        : [...d.data_sources, id],
    }));
  };

  const addAction = (type: string) => {
    setDraft(d => ({ ...d, actions: [...d.actions, { type, params: {} }] }));
  };

  const removeAction = (idx: number) => {
    setDraft(d => ({ ...d, actions: d.actions.filter((_, i) => i !== idx) }));
  };

  const loadTemplate = (tpl: any) => {
    setDraft({
      name: tpl.name,
      description: tpl.description,
      triggers: tpl.triggers,
      data_sources: tpl.data_sources,
      analysis_prompt: tpl.analysis_prompt,
      actions: tpl.actions,
    });
    setStep(0);
  };

  const save = async () => {
    setSaving(true);
    await fetch(`${API}/agents/custom`, { method: 'POST', headers: authHeaders(), body: JSON.stringify(draft) });
    const m = await fetchJSON('/agents/custom');
    setMyAgents(m.agents || []);
    setSaving(false);
  };

  const steps = ['Basics', 'Triggers', 'Data Sources', 'Analysis', 'Actions', 'Review'];

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Custom Agent Builder</h1>
          <p style={{ color: colors.textMuted, fontSize: 13, marginTop: 6 }}>
            Create AI agents without code — define triggers, data sources, analysis prompts, and actions
          </p>
        </div>

        {/* Templates */}
        <div className="slide-up-d1">
        <Card title="Start from Template" style={{ marginBottom: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10 }}>
            {templates.map((tpl: any) => (
              <button key={tpl.id} onClick={() => loadTemplate(tpl)} style={{
                padding: 14, borderRadius: 8, background: colors.bgElevated, border: `1px solid ${colors.border}`,
                cursor: 'pointer', textAlign: 'left',
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: colors.text, marginBottom: 4 }}>{tpl.name}</div>
                <div style={{ fontSize: 11, color: colors.textDim }}>{tpl.description?.slice(0, 80)}...</div>
              </button>
            ))}
          </div>
        </Card>
        </div>

        {/* Step indicator */}
        <div className="slide-up-d2" style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
          {steps.map((s, i) => (
            <button key={s} onClick={() => setStep(i)} style={{
              flex: 1, padding: '8px 4px', fontSize: 11, fontWeight: 600, border: 'none', cursor: 'pointer',
              borderRadius: 6,
              background: step === i ? colors.accent : i < step ? colors.successBg : colors.bgElevated,
              color: step === i ? '#fff' : i < step ? colors.success : colors.textDim,
            }}>
              {s}
            </button>
          ))}
        </div>

        {/* Step content */}
        <Card title={steps[step]} style={{ marginBottom: 20 }}>
          {step === 0 && (
            <>
              <Input label="Agent Name" value={draft.name} onChange={(v: string) => update('name', v)} placeholder="My Custom Agent" />
              <Input label="Description" value={draft.description} onChange={(v: string) => update('description', v)} placeholder="What this agent does..." />
            </>
          )}

          {step === 1 && (
            <>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: 12, color: colors.textSecondary, marginBottom: 4, fontWeight: 500 }}>Metric</label>
                <select value={draft.triggers.metric} onChange={e => updateTrigger('metric', e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: `1px solid ${colors.border}`, background: colors.bgInput, color: colors.text, fontSize: 13 }}>
                  {METRIC_OPTIONS.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <Input label="Threshold" type="number" value={draft.triggers.threshold} onChange={(v: number) => updateTrigger('threshold', v)} />
              <Input label="Duration" value={draft.triggers.duration} onChange={(v: string) => updateTrigger('duration', v)} placeholder="5m" />
            </>
          )}

          {step === 2 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
              {DATA_SOURCE_OPTIONS.map(ds => {
                const active = draft.data_sources.includes(ds.id);
                return (
                  <button key={ds.id} onClick={() => toggleDataSource(ds.id)} style={{
                    padding: 14, borderRadius: 8, border: `1px solid ${active ? colors.accent : colors.border}`,
                    background: active ? 'rgba(59,130,246,0.1)' : colors.bgElevated, cursor: 'pointer', textAlign: 'left',
                  }}>
                    <div style={{ fontSize: 13, color: active ? colors.accent : colors.textSecondary, fontWeight: 600 }}>{ds.label}</div>
                  </button>
                );
              })}
            </div>
          )}

          {step === 3 && (
            <div>
              <label style={{ display: 'block', fontSize: 12, color: colors.textSecondary, marginBottom: 4, fontWeight: 500 }}>
                Analysis Prompt (use &#123;variable&#125; for template variables)
              </label>
              <textarea
                value={draft.analysis_prompt}
                onChange={e => update('analysis_prompt', e.target.value)}
                placeholder="Analyze why {metric} exceeded {threshold}. Check for..."
                rows={8}
                style={{
                  width: '100%', padding: 12, borderRadius: 6, border: `1px solid ${colors.border}`,
                  background: colors.bgInput, color: colors.text, fontSize: 13, fontFamily: 'monospace',
                  resize: 'vertical', outline: 'none', boxSizing: 'border-box',
                }}
              />
              <div style={{ fontSize: 11, color: colors.textDim, marginTop: 6 }}>
                Available variables: &#123;service&#125;, &#123;metric&#125;, &#123;threshold&#125;, &#123;value&#125;, &#123;change_pct&#125;, &#123;endpoint&#125;, &#123;host&#125;
              </div>
            </div>
          )}

          {step === 4 && (
            <>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
                {actionLib.map((a: any) => (
                  <button key={a.type} onClick={() => addAction(a.type)} style={{
                    padding: '6px 12px', borderRadius: 6, border: `1px solid ${colors.border}`,
                    background: colors.bgElevated, color: colors.textSecondary, fontSize: 11, cursor: 'pointer',
                  }}>
                    + {a.label}
                  </button>
                ))}
              </div>
              {draft.actions.map((action, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: 10, borderRadius: 6,
                  background: colors.bgElevated, marginBottom: 6,
                }}>
                  <span style={{ fontSize: 12, color: colors.text, flex: 1 }}>{action.type.replace(/_/g, ' ')}</span>
                  <button onClick={() => removeAction(i)} style={{
                    padding: '4px 10px', borderRadius: 4, border: 'none', background: colors.dangerBg,
                    color: colors.danger, fontSize: 11, cursor: 'pointer',
                  }}>Remove</button>
                </div>
              ))}
              {draft.actions.length === 0 && (
                <div style={{ fontSize: 12, color: colors.textDim, textAlign: 'center', padding: 20 }}>
                  Click actions above to add them to your agent
                </div>
              )}
            </>
          )}

          {step === 5 && (
            <div style={{ fontSize: 13 }}>
              <div style={{ marginBottom: 12 }}>
                <span style={{ color: colors.textSecondary }}>Name: </span>
                <span style={{ color: colors.text, fontWeight: 600 }}>{draft.name || '(unnamed)'}</span>
              </div>
              <div style={{ marginBottom: 12 }}>
                <span style={{ color: colors.textSecondary }}>Trigger: </span>
                <span style={{ color: colors.text }}>{draft.triggers.metric} &gt; {draft.triggers.threshold} for {draft.triggers.duration}</span>
              </div>
              <div style={{ marginBottom: 12 }}>
                <span style={{ color: colors.textSecondary }}>Data Sources: </span>
                <span style={{ color: colors.text }}>{draft.data_sources.join(', ') || 'none'}</span>
              </div>
              <div style={{ marginBottom: 12 }}>
                <span style={{ color: colors.textSecondary }}>Actions: </span>
                <span style={{ color: colors.text }}>{draft.actions.map(a => a.type).join(', ') || 'none'}</span>
              </div>
              <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
                <button onClick={save} disabled={saving || !draft.name} style={{
                  padding: '10px 24px', borderRadius: 8, border: 'none', cursor: 'pointer',
                  background: colors.accentGradient, color: '#fff', fontWeight: 600, fontSize: 13,
                  opacity: saving || !draft.name ? 0.5 : 1,
                }}>
                  {saving ? 'Saving...' : 'Create Agent'}
                </button>
              </div>
            </div>
          )}
        </Card>

        {/* Navigation */}
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <button onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}
            style={{ padding: '8px 20px', borderRadius: 6, border: `1px solid ${colors.border}`, background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', opacity: step === 0 ? 0.3 : 1 }}>
            Previous
          </button>
          <button onClick={() => setStep(Math.min(steps.length - 1, step + 1))} disabled={step === steps.length - 1}
            style={{ padding: '8px 20px', borderRadius: 6, border: 'none', background: colors.accentGradient, color: '#fff', cursor: 'pointer', opacity: step === steps.length - 1 ? 0.3 : 1 }}>
            Next
          </button>
        </div>

        {/* My Agents */}
        {myAgents.length > 0 && (
          <Card title={`My Custom Agents (${myAgents.length})`} style={{ marginTop: 24 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {myAgents.map((a: any) => (
                <div key={a.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: 12, borderRadius: 8, background: colors.bgElevated,
                }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: colors.text }}>{a.name}</div>
                    <div style={{ fontSize: 11, color: colors.textDim }}>{a.description?.slice(0, 60)}</div>
                  </div>
                  <span style={{
                    padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                    background: a.enabled ? colors.successBg : colors.dangerBg,
                    color: a.enabled ? colors.success : colors.danger,
                  }}>
                    {a.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
