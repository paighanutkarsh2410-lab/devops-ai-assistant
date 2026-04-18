'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

interface MaintenanceWindow {
  id: string;
  title: string;
  description: string | null;
  start_time: string;
  end_time: string;
  affected_services: string[];
  planned_actions: string[];
  status: string;
  actual_start: string | null;
  actual_end: string | null;
  completion_report: Record<string, unknown> | null;
}

export default function MaintenancePage() {
  const router = useRouter();
  const { isMobile } = useBreakpoint();
  const [windows, setWindows] = useState<MaintenanceWindow[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    title: '', description: '', start_time: '', end_time: '',
    affected_services: '', planned_actions: '',
  });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const res = await api.get('/maintenance/');
      setWindows(res.data);
    } catch { /* empty */ }
  };

  const create = async () => {
    if (!form.title || !form.start_time || !form.end_time) return;
    try {
      await api.post('/maintenance/', {
        title: form.title,
        description: form.description || null,
        start_time: new Date(form.start_time).toISOString(),
        end_time: new Date(form.end_time).toISOString(),
        affected_services: form.affected_services ? form.affected_services.split(',').map(s => s.trim()) : [],
        planned_actions: form.planned_actions ? form.planned_actions.split(',').map(s => s.trim()) : [],
      });
      setShowCreate(false);
      setForm({ title: '', description: '', start_time: '', end_time: '', affected_services: '', planned_actions: '' });
      loadData();
    } catch { /* empty */ }
  };

  const startWindow = async (id: string) => {
    try { await api.post(`/maintenance/${id}/start`); loadData(); } catch { /* empty */ }
  };

  const endWindow = async (id: string) => {
    try { await api.post(`/maintenance/${id}/end`, { notes: 'Completed via dashboard' }); loadData(); } catch { /* empty */ }
  };

  const cancelWindow = async (id: string) => {
    try { await api.post(`/maintenance/${id}/cancel`); loadData(); } catch { /* empty */ }
  };

  const statusColor: Record<string, string> = {
    scheduled: colors.accent, in_progress: colors.warning, completed: colors.success, cancelled: colors.textMuted,
  };

  const glassCard: React.CSSProperties = {
    background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`, padding: 16,
  };

  const inputStyle: React.CSSProperties = {
    padding: '8px 12px', borderRadius: 8, border: `1px solid ${colors.border}`,
    background: colors.bgInput, color: colors.text, fontSize: 13, outline: 'none',
  };

  const upcoming = windows.filter(w => w.status === 'scheduled' || w.status === 'in_progress');
  const past = windows.filter(w => w.status === 'completed' || w.status === 'cancelled');

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 12 : 0, marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Maintenance Windows</h1>
            <p style={{ color: colors.textMuted, fontSize: 14 }}>Schedule and manage planned downtime</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => setShowCreate(!showCreate)} style={{
              padding: '8px 16px', borderRadius: 8, background: colors.accentGradient, color: '#fff',
              border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13,
            }}>
              + Schedule
            </button>
            <button onClick={() => router.push('/dashboard')} style={{
              padding: '8px 16px', borderRadius: 8, border: `1px solid ${colors.border}`,
              background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 13,
            }}>
              Dashboard
            </button>
          </div>
        </div>

        {/* Create form */}
        {showCreate && (
          <div style={{ ...glassCard, marginBottom: 16 }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: colors.text }}>Schedule Maintenance</h2>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 10, marginBottom: 12 }}>
              <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Title *"
                style={inputStyle} />
              <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Description"
                style={inputStyle} />
              <div>
                <label style={{ fontSize: 11, color: colors.textMuted, display: 'block', marginBottom: 4 }}>Start Time</label>
                <input type="datetime-local" value={form.start_time} onChange={e => setForm({ ...form, start_time: e.target.value })}
                  style={{ ...inputStyle, width: '100%' }} />
              </div>
              <div>
                <label style={{ fontSize: 11, color: colors.textMuted, display: 'block', marginBottom: 4 }}>End Time</label>
                <input type="datetime-local" value={form.end_time} onChange={e => setForm({ ...form, end_time: e.target.value })}
                  style={{ ...inputStyle, width: '100%' }} />
              </div>
              <input value={form.affected_services} onChange={e => setForm({ ...form, affected_services: e.target.value })}
                placeholder="Affected services (comma-separated)" style={inputStyle} />
              <input value={form.planned_actions} onChange={e => setForm({ ...form, planned_actions: e.target.value })}
                placeholder="Planned actions (comma-separated)" style={inputStyle} />
            </div>
            <button onClick={create} style={{
              padding: '8px 20px', borderRadius: 8, background: colors.accentGradient, color: '#fff',
              border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13,
            }}>Schedule</button>
          </div>
        )}

        {/* Summary */}
        <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
          <div style={{...glassCard, position: 'relative', overflow: 'hidden'}}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div style={{ fontSize: 11, color: colors.textMuted }}>Upcoming</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: colors.accent }}>{upcoming.filter(w => w.status === 'scheduled').length}</div>
          </div>
          <div style={{...glassCard, position: 'relative', overflow: 'hidden'}}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div style={{ fontSize: 11, color: colors.textMuted }}>In Progress</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: colors.warning }}>{upcoming.filter(w => w.status === 'in_progress').length}</div>
          </div>
          <div style={{...glassCard, position: 'relative', overflow: 'hidden'}}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div style={{ fontSize: 11, color: colors.textMuted }}>Completed</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: colors.success }}>{past.filter(w => w.status === 'completed').length}</div>
          </div>
        </div>

        {/* Upcoming */}
        <h2 className="slide-up-d2" style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>Active & Upcoming</h2>
        {upcoming.length === 0 ? (
          <div style={{ ...glassCard, textAlign: 'center', padding: 30, color: colors.textMuted, marginBottom: 24 }}>
            No upcoming maintenance windows
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
            {upcoming.map(w => (
              <div key={w.id} style={{ ...glassCard, borderLeft: `4px solid ${statusColor[w.status] || colors.textMuted}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <h3 style={{ fontWeight: 600, fontSize: 15, color: colors.text }}>{w.title}</h3>
                      <span style={{
                        padding: '2px 8px', borderRadius: 10, fontSize: 10, fontWeight: 600,
                        background: `${statusColor[w.status]}15`, color: statusColor[w.status],
                      }}>{w.status.replace('_', ' ')}</span>
                    </div>
                    {w.description && <p style={{ color: colors.textMuted, fontSize: 12, marginBottom: 4 }}>{w.description}</p>}
                    <div style={{ display: 'flex', gap: 16, fontSize: 12, color: colors.textMuted }}>
                      <span>Start: {new Date(w.start_time).toLocaleString()}</span>
                      <span>End: {new Date(w.end_time).toLocaleString()}</span>
                    </div>
                    {w.affected_services.length > 0 && (
                      <div style={{ display: 'flex', gap: 4, marginTop: 6, flexWrap: 'wrap' }}>
                        {w.affected_services.map((s, i) => (
                          <span key={i} style={{ padding: '1px 8px', borderRadius: 8, fontSize: 10, background: colors.warningBg, color: colors.warning }}>{s}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {w.status === 'scheduled' && (
                      <>
                        <button onClick={() => startWindow(w.id)} style={{
                          padding: '5px 12px', borderRadius: 6, background: colors.warning, color: '#fff',
                          border: 'none', cursor: 'pointer', fontSize: 12,
                        }}>Start</button>
                        <button onClick={() => cancelWindow(w.id)} style={{
                          padding: '5px 12px', borderRadius: 6, border: `1px solid ${colors.border}`,
                          background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer', fontSize: 12,
                        }}>Cancel</button>
                      </>
                    )}
                    {w.status === 'in_progress' && (
                      <button onClick={() => endWindow(w.id)} style={{
                        padding: '5px 12px', borderRadius: 6, background: colors.success, color: '#fff',
                        border: 'none', cursor: 'pointer', fontSize: 12,
                      }}>Complete</button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Past */}
        {past.length > 0 && (
          <>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: colors.text }}>History</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {past.map(w => (
                <div key={w.id} style={{ ...glassCard, opacity: w.status === 'cancelled' ? 0.6 : 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontWeight: 500, fontSize: 13, color: colors.text }}>{w.title}</span>
                      <span style={{ fontSize: 12, color: colors.textMuted, marginLeft: 8 }}>
                        {new Date(w.start_time).toLocaleDateString()} — {w.status}
                      </span>
                    </div>
                    {w.completion_report && (
                      <span style={{ fontSize: 11, color: colors.success }}>
                        {(w.completion_report.actual_duration_minutes as number)?.toFixed(0)}min
                        {(w.completion_report.on_time as boolean) ? ' (on time)' : ' (over time)'}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
