'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { colors } from '@/lib/theme';
import DashboardShell from '@/components/DashboardShell';

interface Step {
  order: number;
  type: string;
  name: string;
  action?: string;
  instruction?: string;
  params?: Record<string, string>;
  requires_approval?: boolean;
  on_failure?: string;
}

const ACTIONS = [
  'collect_logs', 'restart_service', 'scale_up', 'clear_cache',
  'check_metrics', 'run_health_check', 'rollback_deployment',
  'rotate_credentials', 'check_disk_space', 'analyze_connections',
];

export default function RunbookBuilderPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [pattern, setPattern] = useState('');
  const [service, setService] = useState('');
  const [tags, setTags] = useState('');
  const [duration, setDuration] = useState('');
  const [steps, setSteps] = useState<Step[]>([]);
  const [saving, setSaving] = useState(false);

  const addStep = (type: string) => {
    setSteps(prev => [...prev, {
      order: prev.length + 1, type, name: '',
      action: type === 'automated' ? 'collect_logs' : undefined,
      instruction: type === 'manual' ? '' : undefined,
      params: {}, on_failure: 'stop',
    }]);
  };

  const updateStep = (idx: number, updates: Partial<Step>) => {
    setSteps(prev => prev.map((s, i) => i === idx ? { ...s, ...updates } : s));
  };

  const removeStep = (idx: number) => {
    setSteps(prev => prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, order: i + 1 })));
  };

  const save = async () => {
    if (!name.trim() || steps.length === 0) return;
    setSaving(true);
    try {
      await api.post('/runbooks/', {
        name, description, incident_pattern: pattern || null,
        service_name: service || null,
        steps: steps.map(s => ({ ...s, name: s.name || `Step ${s.order}` })),
        estimated_duration_minutes: duration ? parseInt(duration) : null,
        tags: tags ? tags.split(',').map(t => t.trim()) : [],
      });
      router.push('/runbooks');
    } catch { /* empty */ }
    setSaving(false);
  };

  const inputStyle: React.CSSProperties = {
    padding: '8px 12px', borderRadius: 8, border: `1px solid ${colors.border}`,
    background: colors.bgInput, color: colors.text, fontSize: 13, outline: 'none',
    width: '100%', boxSizing: 'border-box',
  };

  const stepTypeColors: Record<string, string> = {
    automated: colors.success, manual: colors.accent, approval: colors.warning,
  };

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 900, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Create Runbook</h1>
            <p style={{ fontSize: 13, color: colors.textMuted }}>Define automated and manual incident response steps</p>
          </div>
          <button onClick={() => router.push('/runbooks')} style={{
            padding: '8px 16px', borderRadius: 8, border: `1px solid ${colors.border}`,
            background: 'transparent', color: colors.textSecondary, cursor: 'pointer', fontSize: 13,
          }}>Back</button>
        </div>

        {/* Details */}
        <div style={{ background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14, padding: 20, marginBottom: 16 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, color: colors.text, marginBottom: 12 }}>Details</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Runbook name *" style={inputStyle} />
            <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" style={inputStyle} />
            <input value={pattern} onChange={e => setPattern(e.target.value)} placeholder="Incident pattern (e.g. memory leak)" style={inputStyle} />
            <input value={service} onChange={e => setService(e.target.value)} placeholder="Service name" style={inputStyle} />
            <input value={tags} onChange={e => setTags(e.target.value)} placeholder="Tags (comma-separated)" style={inputStyle} />
            <input value={duration} onChange={e => setDuration(e.target.value)} placeholder="Est. duration (minutes)" type="number" style={inputStyle} />
          </div>
        </div>

        {/* Steps */}
        <div style={{ background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14, padding: 20, marginBottom: 16 }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, color: colors.text, marginBottom: 12 }}>Steps ({steps.length})</h2>

          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            {(['automated', 'manual', 'approval'] as const).map(type => (
              <button key={type} onClick={() => addStep(type)} style={{
                padding: '6px 14px', borderRadius: 20, cursor: 'pointer', fontSize: 12, fontWeight: 500,
                border: `1px solid ${stepTypeColors[type]}`,
                background: stepTypeColors[type] + '15',
                color: stepTypeColors[type],
              }}>+ {type.charAt(0).toUpperCase() + type.slice(1)} Step</button>
            ))}
          </div>

          {steps.length === 0 && (
            <div style={{
              textAlign: 'center', padding: 32, color: colors.textDim,
              border: `2px dashed ${colors.border}`, borderRadius: 10,
            }}>Add steps to your runbook</div>
          )}

          {steps.map((step, idx) => {
            const clr = stepTypeColors[step.type] || colors.accent;
            return (
              <div key={idx} style={{
                border: `1px solid ${clr}30`, borderRadius: 10, padding: 14, marginBottom: 8,
                background: colors.bgElevated,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: clr }}>
                    #{step.order} {step.type.toUpperCase()}
                  </span>
                  <button onClick={() => removeStep(idx)} style={{
                    padding: '2px 10px', borderRadius: 6, border: 'none',
                    background: colors.dangerBg, color: colors.danger, cursor: 'pointer', fontSize: 10,
                  }}>Remove</button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  <input value={step.name} onChange={e => updateStep(idx, { name: e.target.value })}
                    placeholder="Step name" style={inputStyle} />
                  {step.type === 'automated' && (
                    <select value={step.action || ''} onChange={e => updateStep(idx, { action: e.target.value })}
                      style={{ ...inputStyle }}>
                      {ACTIONS.map(a => <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>)}
                    </select>
                  )}
                  {(step.type === 'manual' || step.type === 'approval') && (
                    <input value={step.instruction || ''} onChange={e => updateStep(idx, { instruction: e.target.value })}
                      placeholder={step.type === 'manual' ? 'Instructions for the operator' : 'Who should approve?'} style={inputStyle} />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={save} disabled={saving || !name.trim() || steps.length === 0} style={{
            padding: '10px 24px', borderRadius: 8, fontWeight: 600, border: 'none', cursor: 'pointer',
            background: name.trim() && steps.length > 0 ? colors.accentGradient : colors.bgElevated,
            color: name.trim() && steps.length > 0 ? '#fff' : colors.textDim,
          }}>
            {saving ? 'Saving...' : 'Save Runbook'}
          </button>
          <button onClick={() => router.push('/runbooks')} style={{
            padding: '10px 24px', borderRadius: 8, border: `1px solid ${colors.border}`,
            background: 'transparent', color: colors.textSecondary, cursor: 'pointer',
          }}>Cancel</button>
        </div>
      </div>
    </DashboardShell>
  );
}
