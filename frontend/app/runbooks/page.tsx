'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import RunbookExecutionComp from '@/components/RunbookExecution';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';

interface RunbookType {
  id: string;
  name: string;
  description: string | null;
  service_name: string | null;
  steps: unknown[];
  version: number;
  tags: string[];
  estimated_duration_minutes: number | null;
  updated_at: string;
}

interface Execution {
  id: string;
  status: string;
  step_results: { order: number; name: string; type: string; status?: string; success?: boolean; message?: string; instruction?: string }[];
  duration_seconds: number | null;
  started_at: string;
}

export default function RunbooksPage() {
  const router = useRouter();
  const [runbooks, setRunbooks] = useState<RunbookType[]>([]);
  const [library, setLibrary] = useState<Record<string, unknown>[]>([]);
  const [execResult, setExecResult] = useState<Execution | null>(null);
  const [executing, setExecuting] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<Record<string, unknown> | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [rbRes, libRes, anRes] = await Promise.all([
        api.get('/runbooks/'),
        api.get('/runbooks/library'),
        api.get('/runbooks/analytics/stats').catch(() => ({ data: null })),
      ]);
      setRunbooks(rbRes.data);
      setLibrary(libRes.data);
      setAnalytics(anRes.data);
    } catch { /* empty */ }
  };

  const createFromLibrary = async (tpl: Record<string, unknown>) => {
    try {
      await api.post('/runbooks/', tpl);
      loadData();
    } catch { /* empty */ }
  };

  const executeRunbook = async (id: string) => {
    setExecuting(id);
    try {
      const res = await api.post(`/runbooks/${id}/execute`);
      setExecResult(res.data);
    } catch { /* empty */ }
    setExecuting(null);
  };

  const deleteRunbook = async (id: string) => {
    try { await api.delete(`/runbooks/${id}`); loadData(); } catch { /* empty */ }
  };

  const cardStyle: React.CSSProperties = {
    background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`, padding: 16,
  };

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Runbooks</h1>
            <p style={{ color: colors.textMuted, fontSize: 13, marginTop: 6 }}>Standard operating procedures for incident response</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => router.push('/runbooks/builder')} style={{
              padding: '8px 16px', borderRadius: 8, background: colors.accentGradient, color: '#fff',
              border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13,
            }}>
              + Create Runbook
            </button>
            <button onClick={() => router.push('/dashboard')} style={{
              padding: '8px 16px', borderRadius: 8, border: `1px solid ${colors.border}`, background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer',
            }}>
              Dashboard
            </button>
          </div>
        </div>

        {/* Analytics */}
        {analytics && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
            <div style={cardStyle}>
              <div style={{ fontSize: 11, color: colors.textMuted }}>Total Executions</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: colors.text }}>{(analytics.total_executions as number) || 0}</div>
            </div>
            <div style={cardStyle}>
              <div style={{ fontSize: 11, color: colors.textMuted }}>Success Rate</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: colors.success }}>{(analytics.success_rate as number) || 0}%</div>
            </div>
            <div style={cardStyle}>
              <div style={{ fontSize: 11, color: colors.textMuted }}>Avg Duration</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: colors.text }}>{(analytics.avg_duration_seconds as number) || 0}s</div>
            </div>
            <div style={cardStyle}>
              <div style={{ fontSize: 11, color: colors.textMuted }}>Runbooks</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: colors.text }}>{runbooks.length}</div>
            </div>
          </div>
        )}

        {/* Library */}
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>Runbook Library</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 32 }}>
          {library.map((tpl, i) => (
            <div key={i} style={cardStyle}>
              <h3 style={{ fontWeight: 600, fontSize: 14, marginBottom: 4, color: colors.text }}>{tpl.name as string}</h3>
              <p style={{ color: colors.textMuted, fontSize: 12, marginBottom: 6 }}>{tpl.description as string}</p>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
                {((tpl.tags as string[]) || []).map((t, ti) => (
                  <span key={ti} style={{ padding: '1px 6px', borderRadius: 8, fontSize: 10, background: colors.bgElevated, color: colors.textMuted }}>{t}</span>
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 11, color: colors.textDim }}>
                  {((tpl.steps as unknown[]) || []).length} steps · ~{tpl.estimated_duration_minutes as number}min
                </span>
                <button onClick={() => createFromLibrary(tpl)} style={{
                  padding: '4px 10px', borderRadius: 6, border: `1px solid ${colors.accent}`,
                  background: 'rgba(59,130,246,0.1)', color: colors.accent, cursor: 'pointer', fontSize: 11,
                }}>
                  Add
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* My Runbooks */}
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>My Runbooks</h2>
        {runbooks.length === 0 ? (
          <div style={{ ...cardStyle, textAlign: 'center', padding: 40, color: colors.textDim }}>
            No runbooks yet. Add from library or create your own.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 32 }}>
            {runbooks.map(rb => (
              <div key={rb.id} style={cardStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div>
                    <h3 style={{ fontWeight: 600, fontSize: 15, color: colors.text, margin: 0 }}>{rb.name}</h3>
                    {rb.description && <p style={{ color: colors.textMuted, fontSize: 12, margin: '4px 0 0' }}>{rb.description}</p>}
                    <div style={{ display: 'flex', gap: 8, marginTop: 4, fontSize: 11, color: colors.textDim }}>
                      <span>{rb.steps.length} steps</span>
                      <span>v{rb.version}</span>
                      {rb.service_name && <span>{rb.service_name}</span>}
                      {rb.estimated_duration_minutes && <span>~{rb.estimated_duration_minutes}min</span>}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button onClick={() => executeRunbook(rb.id)} disabled={executing === rb.id} style={{
                      padding: '5px 12px', borderRadius: 6, background: colors.success, color: '#fff',
                      border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 500,
                    }}>
                      {executing === rb.id ? 'Running...' : 'Execute'}
                    </button>
                    <button onClick={() => deleteRunbook(rb.id)} style={{
                      padding: '5px 12px', borderRadius: 6, border: `1px solid ${colors.dangerBorder}`,
                      background: colors.dangerBg, color: colors.danger, cursor: 'pointer', fontSize: 12,
                    }}>
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Execution Result */}
        {execResult && (
          <div style={{ ...cardStyle, marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: colors.text, margin: 0 }}>Execution Result</h2>
              <button onClick={() => setExecResult(null)} style={{
                padding: '4px 12px', borderRadius: 6, border: `1px solid ${colors.border}`, background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 12,
              }}>Close</button>
            </div>
            <RunbookExecutionComp stepResults={execResult.step_results} status={execResult.status} />
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
