'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';

interface Workflow {
  id: string;
  name: string;
  description: string | null;
  trigger_conditions: Record<string, unknown>;
  steps: unknown[];
  enabled: boolean;
  updated_at: string;
}

interface Execution {
  id: string;
  status: string;
  trigger_type: string;
  started_at: string;
  duration_seconds: number | null;
  step_results: { step_name: string; success: boolean; message?: string }[];
}

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [templates, setTemplates] = useState<Workflow[]>([]);
  const [selectedExecs, setSelectedExecs] = useState<Record<string, Execution[]>>({});
  const [executing, setExecuting] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [wfRes, tplRes] = await Promise.all([
        api.get('/workflows/'),
        api.get('/workflows/templates'),
      ]);
      setWorkflows(wfRes.data);
      setTemplates(tplRes.data);
    } catch { /* empty */ }
  };

  const executeWorkflow = async (id: string) => {
    setExecuting(id);
    try {
      await api.post(`/workflows/${id}/execute`, { context: {}, trigger_type: 'manual' });
      await loadExecutions(id);
    } catch { /* empty */ }
    setExecuting(null);
  };

  const loadExecutions = async (id: string) => {
    try {
      const res = await api.get(`/workflows/${id}/executions?limit=5`);
      setSelectedExecs(prev => ({ ...prev, [id]: res.data }));
    } catch { /* empty */ }
  };

  const createFromTemplate = async (tpl: Workflow) => {
    try {
      await api.post('/workflows/', {
        name: tpl.name,
        description: tpl.description,
        trigger_conditions: tpl.trigger_conditions,
        steps: tpl.steps,
        enabled: true,
      });
      loadData();
    } catch { /* empty */ }
  };

  const toggleEnabled = async (wf: Workflow) => {
    try {
      await api.put(`/workflows/${wf.id}`, { enabled: !wf.enabled });
      loadData();
    } catch { /* empty */ }
  };

  const deleteWorkflow = async (id: string) => {
    try { await api.delete(`/workflows/${id}`); loadData(); } catch { /* empty */ }
  };

  const cardStyle: React.CSSProperties = {
    background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`, padding: 16,
  };

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Workflows</h1>
            <p style={{ color: colors.textMuted, fontSize: 13, marginTop: 6 }}>Automate incident response with custom workflows</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => router.push('/workflows/builder')} style={{
              padding: '8px 16px', borderRadius: 8, background: colors.accentGradient, color: '#fff',
              border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13,
            }}>
              + Build Workflow
            </button>
            <button onClick={() => router.push('/dashboard')} style={{
              padding: '8px 16px', borderRadius: 8, border: `1px solid ${colors.border}`, background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer',
            }}>
              Dashboard
            </button>
          </div>
        </div>

        {/* Templates */}
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>Templates</h2>
        <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 32 }}>
          {templates.map((tpl, i) => (
            <div key={i} style={{...cardStyle, position: 'relative', overflow: 'hidden'}}>
              <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
              <h3 style={{ fontWeight: 600, fontSize: 14, marginBottom: 4, color: colors.text }}>{tpl.name}</h3>
              <p style={{ color: colors.textMuted, fontSize: 12, marginBottom: 8 }}>{tpl.description}</p>
              <p style={{ fontSize: 11, color: colors.textDim, marginBottom: 8 }}>{(tpl.steps as unknown[]).length} steps</p>
              <button onClick={() => createFromTemplate(tpl)} style={{
                padding: '5px 12px', borderRadius: 6, border: `1px solid ${colors.accent}`,
                background: 'rgba(59,130,246,0.1)', color: colors.accent, cursor: 'pointer', fontSize: 12,
              }}>
                Use Template
              </button>
            </div>
          ))}
        </div>

        {/* My Workflows */}
        <h2 className="slide-up-d2" style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>My Workflows</h2>
        {workflows.length === 0 ? (
          <div style={{ ...cardStyle, textAlign: 'center', padding: 40, color: colors.textDim }}>
            No workflows yet. Build one or use a template above.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {workflows.map(wf => (
              <div key={wf.id} style={cardStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <h3 style={{ fontWeight: 600, fontSize: 15, color: colors.text, margin: 0 }}>{wf.name}</h3>
                      <span style={{
                        padding: '2px 8px', borderRadius: 10, fontSize: 10, fontWeight: 600,
                        background: wf.enabled ? colors.successBg : colors.bgElevated,
                        color: wf.enabled ? colors.success : colors.textDim,
                      }}>
                        {wf.enabled ? 'Active' : 'Disabled'}
                      </span>
                    </div>
                    {wf.description && <p style={{ color: colors.textMuted, fontSize: 12, margin: '4px 0 0' }}>{wf.description}</p>}
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button onClick={() => executeWorkflow(wf.id)} disabled={executing === wf.id} style={{
                      padding: '5px 12px', borderRadius: 6, background: colors.success, color: '#fff',
                      border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 500,
                    }}>
                      {executing === wf.id ? 'Running...' : 'Run'}
                    </button>
                    <button onClick={() => toggleEnabled(wf)} style={{
                      padding: '5px 12px', borderRadius: 6, border: `1px solid ${colors.border}`,
                      background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 12,
                    }}>
                      {wf.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button onClick={() => loadExecutions(wf.id)} style={{
                      padding: '5px 12px', borderRadius: 6, border: `1px solid ${colors.border}`,
                      background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 12,
                    }}>
                      History
                    </button>
                    <button onClick={() => deleteWorkflow(wf.id)} style={{
                      padding: '5px 12px', borderRadius: 6, border: `1px solid ${colors.dangerBorder}`,
                      background: colors.dangerBg, color: colors.danger, cursor: 'pointer', fontSize: 12,
                    }}>
                      Delete
                    </button>
                  </div>
                </div>

                {/* Steps preview */}
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
                  {(wf.steps || []).map((s: unknown, i: number) => {
                    const step = s as { name: string; type: string };
                    return (
                      <span key={i} style={{
                        padding: '2px 8px', borderRadius: 10, fontSize: 10,
                        background: colors.bgElevated, color: colors.textMuted,
                      }}>
                        {i + 1}. {step.name || step.type}
                      </span>
                    );
                  })}
                </div>

                {/* Execution history */}
                {selectedExecs[wf.id] && (
                  <div style={{ marginTop: 8, borderTop: `1px solid ${colors.border}`, paddingTop: 8 }}>
                    <h4 style={{ fontSize: 12, fontWeight: 600, color: colors.textMuted, marginBottom: 6 }}>Recent Executions</h4>
                    {selectedExecs[wf.id].length === 0 ? (
                      <p style={{ fontSize: 11, color: colors.textDim }}>No executions yet</p>
                    ) : (
                      selectedExecs[wf.id].map(exec => (
                        <div key={exec.id} style={{
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          padding: '6px 0', borderBottom: `1px solid ${colors.border}`, fontSize: 12,
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{
                              width: 8, height: 8, borderRadius: '50%',
                              background: exec.status === 'completed' ? colors.success : exec.status === 'failed' ? colors.danger : colors.warning,
                            }} />
                            <span style={{ fontWeight: 500, color: colors.text }}>{exec.status}</span>
                            <span style={{ color: colors.textDim }}>{exec.trigger_type}</span>
                          </div>
                          <div style={{ display: 'flex', gap: 12, color: colors.textMuted }}>
                            <span>{exec.step_results?.length || 0} steps</span>
                            {exec.duration_seconds != null && <span>{exec.duration_seconds}s</span>}
                            <span>{new Date(exec.started_at).toLocaleString()}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
