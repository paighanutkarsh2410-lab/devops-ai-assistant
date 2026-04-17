'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { colors } from '@/lib/theme';

interface ActionEntry {
  id: string;
  incident_id: string | null;
  action_name: string;
  action_type: string;
  executed_by: string;
  executed_at: string;
  duration_seconds: number;
  status: string;
  impact_score: number;
  rollback_performed: boolean;
  error_message: string | null;
}

const STATUS_STYLES: Record<string, { color: string; bg: string; icon: string }> = {
  success: { color: '#10b981', bg: 'rgba(16,185,129,0.08)', icon: '✓' },
  failure: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', icon: '✗' },
  rollback: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', icon: '↺' },
  in_progress: { color: '#3b82f6', bg: 'rgba(59,130,246,0.08)', icon: '⟳' },
};

export default function ActionLog() {
  const [actions, setActions] = useState<ActionEntry[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  useEffect(() => {
    loadActions();
  }, [filter]);

  const loadActions = async () => {
    try {
      const params: Record<string, string> = {};
      if (filter !== 'all') params.status = filter;
      const resp = await api.get('/audit/actions', { params });
      setActions(resp.data);
    } catch (error) {
      console.error('Failed to load actions:', error);
    } finally {
      setLoading(false);
    }
  };

  const filters = ['all', 'success', 'failure', 'rollback'];

  return (
    <div style={{
      background: 'rgba(255,255,255,0.015)',
      border: `1px solid rgba(255,255,255,0.04)`,
      borderRadius: 18, overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '18px 22px',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <h2 style={{
          fontSize: 16, fontWeight: 700,
          background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>Action Log</h2>
        <div style={{ display: 'flex', gap: 4, padding: 3, borderRadius: 10, background: 'rgba(255,255,255,0.02)', border: `1px solid ${colors.border}` }}>
          {filters.map((f) => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: '6px 14px', borderRadius: 8, border: 'none',
              background: filter === f ? colors.accentGradient : 'transparent',
              color: filter === f ? '#fff' : colors.textMuted,
              cursor: 'pointer', fontSize: 12, fontWeight: filter === f ? 600 : 400,
              transition: 'all 0.2s',
              textTransform: 'capitalize',
            }}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ padding: 48, textAlign: 'center', color: colors.textMuted, fontSize: 13 }}>Loading actions...</div>
      ) : actions.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: colors.textMuted }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>🛠️</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#71717a', marginBottom: 4 }}>No actions recorded</div>
          <div style={{ fontSize: 13 }}>Remediation actions will appear here.</div>
        </div>
      ) : (
        actions.map((action, idx) => {
          const st = STATUS_STYLES[action.status] || STATUS_STYLES.success;
          const hovered = hoveredRow === action.id;
          return (
            <div
              key={action.id}
              onMouseEnter={() => setHoveredRow(action.id)}
              onMouseLeave={() => setHoveredRow(null)}
              style={{
                padding: '14px 22px',
                borderBottom: '1px solid rgba(255,255,255,0.03)',
                background: hovered ? 'rgba(59,130,246,0.03)' : 'transparent',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                transition: 'all 0.2s ease',
                animation: `slide-up 0.4s ease-out ${idx * 0.03}s both`,
                position: 'relative',
              }}
            >
              {hovered && (
                <div style={{
                  position: 'absolute', left: 0, top: '20%', bottom: '20%', width: 2,
                  background: st.color, boxShadow: `0 0 6px ${st.color}`, borderRadius: 2,
                }} />
              )}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{
                  width: 28, height: 28, borderRadius: 8,
                  background: st.bg, color: st.color,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14, fontWeight: 700, flexShrink: 0,
                }}>{st.icon}</span>
                <div>
                  <div style={{
                    fontSize: 14, fontWeight: 600,
                    color: hovered ? '#f0f0f0' : '#a1a1aa',
                    transition: 'color 0.2s',
                  }}>
                    {action.action_name.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontSize: 12, color: '#3f3f46' }}>
                    by {action.executed_by} &middot; {new Date(action.executed_at).toLocaleString()}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <span style={{
                  padding: '4px 10px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                  background: st.bg, color: st.color,
                  textTransform: 'capitalize',
                }}>{action.status}</span>
                <span style={{ fontSize: 12, color: '#71717a', fontFamily: 'monospace' }}>
                  {action.duration_seconds.toFixed(1)}s
                </span>
                <span style={{
                  fontSize: 12, fontWeight: 600, fontFamily: 'monospace',
                  color: action.impact_score >= 0.7 ? '#10b981' : action.impact_score >= 0.4 ? '#f59e0b' : '#ef4444',
                }}>
                  {(action.impact_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
