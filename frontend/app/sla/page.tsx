'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { colors } from '@/lib/theme';
import DashboardShell from '@/components/DashboardShell';
import { useBreakpoint } from '@/lib/useMediaQuery';

interface SLAStatus {
  service_name: string;
  uptime_percent: number;
  total_downtime_minutes: number;
  incidents_count: number;
  avg_mttr_minutes: number;
  error_budget_remaining_minutes: number;
  error_budget_percent: number;
  sla_met: boolean;
  breaches: { type: string; target: number; actual: number }[];
  target_uptime: number;
}

interface SLAConfig {
  id: string;
  service_name: string;
  target_uptime: number;
  max_mttr_minutes: number;
  max_incidents_per_month: number | null;
  error_budget_minutes: number;
}

export default function SLAPage() {
  const { isMobile } = useBreakpoint();
  const [statuses, setStatuses] = useState<SLAStatus[]>([]);
  const [configs, setConfigs] = useState<SLAConfig[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newService, setNewService] = useState('');
  const [newUptime, setNewUptime] = useState('99.9');
  const [newMttr, setNewMttr] = useState('30');
  const [days, setDays] = useState(30);

  useEffect(() => { loadData(); }, [days]);

  const loadData = async () => {
    try {
      const [statusRes, configRes] = await Promise.all([
        api.get(`/sla/status?days=${days}`),
        api.get('/sla/configs'),
      ]);
      setStatuses(statusRes.data);
      setConfigs(configRes.data);
    } catch { /* empty */ }
  };

  const addConfig = async () => {
    if (!newService.trim()) return;
    try {
      await api.post('/sla/configs', {
        service_name: newService,
        target_uptime: parseFloat(newUptime),
        max_mttr_minutes: parseInt(newMttr),
      });
      setShowAdd(false);
      setNewService('');
      loadData();
    } catch { /* empty */ }
  };

  const overallMet = statuses.filter(s => s.sla_met).length;
  const overallTotal = statuses.length;

  const inputStyle: React.CSSProperties = {
    padding: '8px 12px', borderRadius: 8, border: `1px solid ${colors.border}`,
    background: colors.bgInput, color: colors.text, fontSize: 13, outline: 'none',
  };

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 12 : 0, marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>SLA Tracking</h1>
            <p style={{ fontSize: 13, color: colors.textMuted }}>Uptime targets, error budgets, and breach alerts</p>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {[7, 30, 90].map(d => (
              <button key={d} onClick={() => setDays(d)} style={{
                padding: '6px 14px', borderRadius: 8, fontSize: 12, cursor: 'pointer', border: 'none',
                background: days === d ? colors.accentGradient : colors.bgElevated,
                color: days === d ? '#fff' : colors.textMuted, fontWeight: days === d ? 600 : 400,
              }}>{d}d</button>
            ))}
            <button onClick={() => setShowAdd(!showAdd)} style={{
              padding: '6px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: colors.accentGradient, color: '#fff', fontWeight: 600, fontSize: 13,
            }}>+ Add SLA</button>
          </div>
        </div>

        {/* Add SLA form */}
        {showAdd && (

          <div style={{
            background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14,
            padding: 18, marginBottom: 16, display: 'flex', gap: 12, alignItems: 'end', flexWrap: 'wrap' as const,
          }}>
            <div>
              <label style={{ fontSize: 11, color: colors.textMuted, display: 'block', marginBottom: 4 }}>Service</label>
              <input value={newService} onChange={e => setNewService(e.target.value)} placeholder="e.g. api-server" style={{ ...inputStyle, width: 160 }} />
            </div>
            <div>
              <label style={{ fontSize: 11, color: colors.textMuted, display: 'block', marginBottom: 4 }}>Target Uptime %</label>
              <input value={newUptime} onChange={e => setNewUptime(e.target.value)} type="number" step="0.01" style={{ ...inputStyle, width: 100 }} />
            </div>
            <div>
              <label style={{ fontSize: 11, color: colors.textMuted, display: 'block', marginBottom: 4 }}>Max MTTR (min)</label>
              <input value={newMttr} onChange={e => setNewMttr(e.target.value)} type="number" style={{ ...inputStyle, width: 80 }} />
            </div>
            <button onClick={addConfig} style={{
              padding: '8px 18px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: colors.success, color: '#fff', fontSize: 13, fontWeight: 600,
            }}>Save</button>
          </div>
        )}

        {/* Stats */}
        <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 14, marginBottom: 24 }}>
          {[
            { label: 'SLA Compliance', value: overallTotal > 0 ? `${overallMet}/${overallTotal}` : 'N/A', color: overallMet === overallTotal && overallTotal > 0 ? colors.success : colors.danger, sub: 'services meeting SLA' },
            { label: 'Active Breaches', value: statuses.reduce((sum, s) => sum + s.breaches.length, 0), color: colors.danger, sub: 'across all services' },
            { label: 'Configured Services', value: configs.length, color: colors.accent, sub: 'SLA targets defined' },
          ].map(s => (
            <div key={s.label} style={{
              background: colors.bgCard, border: `1px solid ${colors.border}`,
              borderRadius: 14, padding: 20, borderTop: `2px solid ${s.color}`,
              position: 'relative', overflow: 'hidden',
            }}>
              <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: `radial-gradient(circle, ${s.color}18, transparent)`, filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
              <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 6 }}>{s.label}</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 11, color: colors.textDim, marginTop: 4 }}>{s.sub}</div>
            </div>
          ))}
        </div>

        {/* Service SLA Cards */}
        <div className="slide-up-d2">
        {statuses.length === 0 ? (
          <div style={{
            background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14,
            textAlign: 'center', padding: 48, color: colors.textMuted,
          }}>No SLA data yet. Add SLA targets above, or create incidents with service names.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {statuses.map(s => (
              <div key={s.service_name} style={{
                background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14,
                padding: 20, borderLeft: `4px solid ${s.sla_met ? colors.success : colors.danger}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <h3 style={{ fontWeight: 600, fontSize: 15, color: colors.text }}>{s.service_name}</h3>
                    <span style={{
                      padding: '3px 10px', borderRadius: 10, fontSize: 11, fontWeight: 600,
                      background: s.sla_met ? colors.successBg : colors.dangerBg,
                      color: s.sla_met ? colors.success : colors.danger,
                    }}>{s.sla_met ? 'SLA Met' : 'SLA Breached'}</span>
                  </div>
                  <span style={{ fontSize: 12, color: colors.textDim }}>Target: {s.target_uptime}% uptime</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(3, 1fr)' : 'repeat(5, 1fr)', gap: isMobile ? 8 : 16, marginBottom: 14 }}>
                  {[
                    { label: 'Uptime', value: `${s.uptime_percent.toFixed(3)}%`, color: s.uptime_percent >= s.target_uptime ? colors.success : colors.danger },
                    { label: 'Downtime', value: `${s.total_downtime_minutes.toFixed(1)}m`, color: colors.text },
                    { label: 'MTTR', value: `${s.avg_mttr_minutes.toFixed(1)}m`, color: colors.text },
                    { label: 'Incidents', value: s.incidents_count, color: colors.text },
                    { label: 'Error Budget', value: `${s.error_budget_percent.toFixed(1)}%`, color: s.error_budget_percent > 20 ? colors.success : colors.danger },
                  ].map(m => (
                    <div key={m.label}>
                      <div style={{ fontSize: 10, color: colors.textDim }}>{m.label}</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: m.color }}>{m.value}</div>
                    </div>
                  ))}
                </div>

                {/* Error budget bar */}
                <div style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: colors.textDim, marginBottom: 3 }}>
                    <span>Error Budget Remaining</span>
                    <span>{s.error_budget_remaining_minutes.toFixed(1)} min left</span>
                  </div>
                  <div style={{ height: 6, background: colors.bgElevated, borderRadius: 4 }}>
                    <div style={{
                      height: '100%', borderRadius: 4, transition: 'width 0.5s',
                      width: `${Math.min(s.error_budget_percent, 100)}%`,
                      background: s.error_budget_percent > 50 ? colors.success : s.error_budget_percent > 20 ? colors.warning : colors.danger,
                    }} />
                  </div>
                </div>

                {s.breaches.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {s.breaches.map((b, i) => (
                      <span key={i} style={{
                        padding: '3px 10px', borderRadius: 12, fontSize: 11,
                        background: colors.dangerBg, color: colors.danger, fontWeight: 500,
                      }}>
                        {b.type}: target {b.target}, actual {typeof b.actual === 'number' ? b.actual.toFixed(1) : b.actual}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        </div>
      </div>
    </DashboardShell>
  );
}
