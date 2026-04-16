'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import WorkflowCanvas from '@/components/WorkflowCanvas';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';

const TRIGGER_TYPES = [
  { type: 'incident_created', label: 'Incident Created', icon: '\ud83d\udea8' },
  { type: 'metric_threshold', label: 'Metric Threshold', icon: '\ud83d\udcca' },
  { type: 'prediction_alert', label: 'Prediction Alert', icon: '\ud83d\udd2e' },
  { type: 'schedule', label: 'Schedule (Cron)', icon: '\ud83d\udcc5' },
  { type: 'manual', label: 'Manual Trigger', icon: '\ud83d\udc46' },
  { type: 'webhook', label: 'Webhook', icon: '\ud83d\udd17' },
];

export default function WorkflowBuilderPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [triggerType, setTriggerType] = useState('manual');
  const [triggerFilters, setTriggerFilters] = useState<Record<string, string>>({});
  const [steps, setSteps] = useState<{ type: string; name: string; params: Record<string, unknown>; on_error?: string }[]>([]);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!name.trim() || steps.length === 0) return;
    setSaving(true);
    try {
      await api.post('/workflows/', {
        name,
        description,
        trigger_conditions: { type: triggerType, filters: triggerFilters },
        steps,
        enabled: true,
      });
      router.push('/workflows');
    } catch { /* empty */ }
    setSaving(false);
  };

  const cardStyle: React.CSSProperties = {
    background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`, padding: 16,
  };

  const inputStyle: React.CSSProperties = {
    padding: '8px 12px', borderRadius: 6, border: `1px solid ${colors.border}`,
    background: colors.bgInput, color: colors.text, fontSize: 14, outline: 'none', boxSizing: 'border-box' as const,
  };

  const smallInputStyle: React.CSSProperties = {
    padding: '6px 10px', borderRadius: 6, border: `1px solid ${colors.border}`,
    background: colors.bgInput, color: colors.text, fontSize: 12, outline: 'none',
  };

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 900, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Build Workflow</h1>
            <p style={{ color: colors.textMuted, fontSize: 13, marginTop: 6 }}>Create a custom automation workflow</p>
          </div>
          <button onClick={() => router.push('/workflows')} style={{
            padding: '8px 16px', borderRadius: 8, border: `1px solid ${colors.border}`, background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer',
          }}>
            Back
          </button>
        </div>

        {/* Basic Info */}
        <div className="slide-up-d1" style={{ ...cardStyle, marginBottom: 16 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: colors.text }}>Workflow Details</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Workflow name *"
              style={inputStyle} />
            <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Description"
              style={inputStyle} />
          </div>
        </div>

        {/* Trigger */}
        <div className="slide-up-d2" style={{ ...cardStyle, marginBottom: 16 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: colors.text }}>Trigger</h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
            {TRIGGER_TYPES.map(t => (
              <button key={t.type} onClick={() => { setTriggerType(t.type); setTriggerFilters({}); }}
                style={{
                  padding: '6px 14px', borderRadius: 16, fontSize: 12, cursor: 'pointer',
                  border: `2px solid ${triggerType === t.type ? colors.accent : colors.border}`,
                  background: triggerType === t.type ? 'rgba(59,130,246,0.1)' : colors.bgElevated,
                  color: triggerType === t.type ? colors.accent : colors.textMuted, fontWeight: 500,
                }}>
                {t.icon} {t.label}
              </button>
            ))}
          </div>

          {/* Trigger filters */}
          {triggerType === 'incident_created' && (
            <div style={{ display: 'flex', gap: 8 }}>
              <select value={triggerFilters.severity || ''} onChange={e => setTriggerFilters({ ...triggerFilters, severity: e.target.value })}
                style={smallInputStyle}>
                <option value="">Any severity</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <input value={triggerFilters.service_name || ''} onChange={e => setTriggerFilters({ ...triggerFilters, service_name: e.target.value })}
                placeholder="Service name (optional)" style={smallInputStyle} />
            </div>
          )}
          {triggerType === 'metric_threshold' && (
            <div style={{ display: 'flex', gap: 8 }}>
              <input value={triggerFilters.metric_name || ''} onChange={e => setTriggerFilters({ ...triggerFilters, metric_name: e.target.value })}
                placeholder="Metric name" style={smallInputStyle} />
              <input value={triggerFilters.threshold || ''} onChange={e => setTriggerFilters({ ...triggerFilters, threshold: e.target.value })}
                placeholder="Threshold value" type="number" style={{ ...smallInputStyle, width: 120 }} />
            </div>
          )}
          {triggerType === 'schedule' && (
            <input value={triggerFilters.cron || ''} onChange={e => setTriggerFilters({ ...triggerFilters, cron: e.target.value })}
              placeholder="Cron expression (e.g. 0 2 * * 0)" style={smallInputStyle} />
          )}
        </div>

        {/* Steps */}
        <div style={{ ...cardStyle, marginBottom: 16 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, color: colors.text }}>Steps ({steps.length})</h2>
          <WorkflowCanvas steps={steps} onStepsChange={setSteps} />
        </div>

        {/* Save */}
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={save} disabled={saving || !name.trim() || steps.length === 0}
            style={{
              padding: '10px 24px', borderRadius: 8, fontWeight: 600, fontSize: 14, cursor: 'pointer',
              background: name.trim() && steps.length > 0 ? colors.accentGradient : colors.textDim,
              color: '#fff', border: 'none',
            }}>
            {saving ? 'Saving...' : 'Save Workflow'}
          </button>
          <button onClick={() => router.push('/workflows')} style={{
            padding: '10px 24px', borderRadius: 8, border: `1px solid ${colors.border}`, background: colors.bgElevated, color: colors.textSecondary, cursor: 'pointer',
          }}>
            Cancel
          </button>
        </div>
      </div>
    </DashboardShell>
  );
}
