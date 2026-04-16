'use client';

import { useState } from 'react';

interface WorkflowStep {
  type: string;
  name: string;
  params: Record<string, unknown>;
  on_error?: string;
}

interface Props {
  steps: WorkflowStep[];
  onStepsChange: (steps: WorkflowStep[]) => void;
  readOnly?: boolean;
}

const STEP_TYPES = [
  { type: 'run_diagnostic', label: 'Run Diagnostic', icon: '🔍', color: '#3b82f6' },
  { type: 'execute_action', label: 'Execute Action', icon: '⚡', color: '#16a34a' },
  { type: 'send_notification', label: 'Send Notification', icon: '📢', color: '#8b5cf6' },
  { type: 'create_ticket', label: 'Create Ticket', icon: '🎫', color: '#d97706' },
  { type: 'wait_for_approval', label: 'Wait for Approval', icon: '✋', color: '#dc2626' },
  { type: 'conditional', label: 'Conditional Branch', icon: '🔀', color: '#0891b2' },
  { type: 'loop', label: 'Loop', icon: '🔄', color: '#7c3aed' },
  { type: 'api_call', label: 'API Call', icon: '🌐', color: '#059669' },
  { type: 'delay', label: 'Delay', icon: '⏰', color: '#6b7280' },
  { type: 'log', label: 'Log Message', icon: '📝', color: '#475569' },
];

export default function WorkflowCanvas({ steps, onStepsChange, readOnly = false }: Props) {
  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [editParams, setEditParams] = useState<Record<string, string>>({});

  const addStep = (type: string) => {
    const st = STEP_TYPES.find(s => s.type === type);
    if (!st) return;
    const newStep: WorkflowStep = {
      type,
      name: st.label,
      params: getDefaultParams(type),
      on_error: 'stop',
    };
    onStepsChange([...steps, newStep]);
  };

  const removeStep = (idx: number) => {
    onStepsChange(steps.filter((_, i) => i !== idx));
    if (editingIdx === idx) setEditingIdx(null);
  };

  const moveStep = (idx: number, dir: -1 | 1) => {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= steps.length) return;
    const updated = [...steps];
    [updated[idx], updated[newIdx]] = [updated[newIdx], updated[idx]];
    onStepsChange(updated);
  };

  const startEdit = (idx: number) => {
    setEditingIdx(idx);
    const p = steps[idx].params || {};
    const flat: Record<string, string> = {};
    for (const [k, v] of Object.entries(p)) {
      flat[k] = Array.isArray(v) ? v.join(', ') : String(v ?? '');
    }
    flat['_name'] = steps[idx].name;
    flat['_on_error'] = steps[idx].on_error || 'stop';
    setEditParams(flat);
  };

  const saveEdit = () => {
    if (editingIdx === null) return;
    const updated = [...steps];
    const params: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(editParams)) {
      if (k.startsWith('_')) continue;
      if (v.includes(',')) params[k] = v.split(',').map(s => s.trim());
      else params[k] = v;
    }
    updated[editingIdx] = {
      ...updated[editingIdx],
      name: editParams['_name'] || updated[editingIdx].name,
      params,
      on_error: editParams['_on_error'] || 'stop',
    };
    onStepsChange(updated);
    setEditingIdx(null);
  };

  const getStepMeta = (type: string) => STEP_TYPES.find(s => s.type === type) || { icon: '?', color: '#6b7280', label: type };

  return (
    <div>
      {/* Step palette */}
      {!readOnly && (
        <div style={{ marginBottom: '16px' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#a1a1aa', display: 'block', marginBottom: '6px' }}>
            Add Step
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {STEP_TYPES.map(st => (
              <button key={st.type} onClick={() => addStep(st.type)} style={{
                padding: '5px 10px', borderRadius: '14px', border: `1px solid ${st.color}30`,
                background: `${st.color}10`, cursor: 'pointer', fontSize: '11px', color: st.color,
                fontWeight: 500,
              }}>
                {st.icon} {st.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Flow visualization */}
      <div style={{ position: 'relative' }}>
        {steps.length === 0 && (
          <div style={{
            textAlign: 'center', padding: '40px', color: '#9ca3af',
            border: '2px dashed rgba(255,255,255,0.06)', borderRadius: '10px',
          }}>
            Add steps above to build your workflow
          </div>
        )}

        {steps.map((step, idx) => {
          const meta = getStepMeta(step.type);
          const isEditing = editingIdx === idx;

          return (
            <div key={idx}>
              {/* Connector arrow */}
              {idx > 0 && (
                <div style={{ textAlign: 'center', padding: '4px 0', color: '#52525b', fontSize: '18px' }}>
                  ↓
                </div>
              )}

              {/* Step card */}
              <div style={{
                border: `2px solid ${isEditing ? meta.color : 'rgba(255,255,255,0.06)'}`,
                borderRadius: '10px', padding: '12px', background: 'rgba(255,255,255,0.03)',
                display: 'flex', alignItems: 'start', gap: '10px',
              }}>
                {/* Step number + icon */}
                <div style={{
                  width: '36px', height: '36px', borderRadius: '8px',
                  background: `${meta.color}15`, display: 'flex', alignItems: 'center',
                  justifyContent: 'center', fontSize: '18px', flexShrink: 0,
                }}>
                  {meta.icon}
                </div>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  {isEditing ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <input value={editParams['_name'] || ''} onChange={e => setEditParams({ ...editParams, _name: e.target.value })}
                        placeholder="Step name" style={{
                          padding: '4px 8px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.05)', color: '#f0f0f0', fontSize: '13px',
                        }} />
                      {Object.entries(editParams).filter(([k]) => !k.startsWith('_')).map(([k, v]) => (
                        <div key={k} style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                          <label style={{ fontSize: '11px', color: '#a1a1aa', width: '80px' }}>{k}</label>
                          <input value={v} onChange={e => setEditParams({ ...editParams, [k]: e.target.value })}
                            style={{ flex: 1, padding: '3px 6px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.05)', color: '#f0f0f0', fontSize: '12px' }} />
                        </div>
                      ))}
                      <select value={editParams['_on_error'] || 'stop'}
                        onChange={e => setEditParams({ ...editParams, _on_error: e.target.value })}
                        style={{ padding: '3px 6px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.05)', color: '#f0f0f0', fontSize: '11px', width: 'fit-content' }}>
                        <option value="stop">On Error: Stop</option>
                        <option value="continue">On Error: Continue</option>
                      </select>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button onClick={saveEdit} style={{
                          padding: '3px 10px', borderRadius: '4px', background: meta.color, color: 'white',
                          border: 'none', cursor: 'pointer', fontSize: '11px',
                        }}>Save</button>
                        <button onClick={() => setEditingIdx(null)} style={{
                          padding: '3px 10px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)',
                          background: 'rgba(255,255,255,0.05)', color: '#a1a1aa', cursor: 'pointer', fontSize: '11px',
                        }}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 600, fontSize: '13px', color: '#f0f0f0' }}>
                          <span style={{ color: '#9ca3af', marginRight: '6px' }}>#{idx + 1}</span>
                          {step.name}
                        </span>
                        <span style={{
                          fontSize: '10px', padding: '1px 6px', borderRadius: '8px',
                          background: `${meta.color}15`, color: meta.color, fontWeight: 500,
                        }}>
                          {meta.label}
                        </span>
                      </div>
                      {Object.keys(step.params || {}).length > 0 && (
                        <div style={{ fontSize: '11px', color: '#a1a1aa', marginTop: '4px' }}>
                          {Object.entries(step.params).map(([k, v]) => (
                            <span key={k} style={{ marginRight: '10px' }}>
                              {k}: <strong>{Array.isArray(v) ? v.join(', ') : String(v)}</strong>
                            </span>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>

                {/* Actions */}
                {!readOnly && !isEditing && (
                  <div style={{ display: 'flex', gap: '3px', flexShrink: 0 }}>
                    <button onClick={() => moveStep(idx, -1)} disabled={idx === 0}
                      style={{ padding: '2px 5px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.05)', color: '#a1a1aa', cursor: 'pointer', fontSize: '10px', opacity: idx === 0 ? 0.3 : 1 }}>
                      ↑
                    </button>
                    <button onClick={() => moveStep(idx, 1)} disabled={idx === steps.length - 1}
                      style={{ padding: '2px 5px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.05)', color: '#a1a1aa', cursor: 'pointer', fontSize: '10px', opacity: idx === steps.length - 1 ? 0.3 : 1 }}>
                      ↓
                    </button>
                    <button onClick={() => startEdit(idx)}
                      style={{ padding: '2px 5px', borderRadius: '4px', border: '1px solid rgba(59,130,246,0.3)', background: 'rgba(37,99,235,0.15)', color: '#60a5fa', cursor: 'pointer', fontSize: '10px' }}>
                      Edit
                    </button>
                    <button onClick={() => removeStep(idx)}
                      style={{ padding: '2px 5px', borderRadius: '4px', border: '1px solid rgba(220,38,38,0.3)', background: 'rgba(220,38,38,0.1)', color: '#f87171', cursor: 'pointer', fontSize: '10px' }}>
                      ✕
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function getDefaultParams(type: string): Record<string, unknown> {
  switch (type) {
    case 'send_notification': return { channels: ['slack'], message: '' };
    case 'execute_action': return { action: 'restart_service', target: '' };
    case 'create_ticket': return { system: 'jira', title: '' };
    case 'wait_for_approval': return { approver: 'admin', auto_approve: true };
    case 'conditional': return { condition: 'severity_is_critical', true_step: 0, false_step: 0 };
    case 'loop': return { iterations: 3 };
    case 'api_call': return { url: '', method: 'GET' };
    case 'delay': return { seconds: 60 };
    case 'log': return { message: '', level: 'info' };
    default: return {};
  }
}
