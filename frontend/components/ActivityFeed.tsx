'use client';

import { WSMessage } from '@/lib/useWebSocket';

interface Props {
  messages: WSMessage[];
}

const eventLabels: Record<string, { label: string; color: string }> = {
  new_incident: { label: 'New Incident', color: '#dc2626' },
  incident_updated: { label: 'Incident Updated', color: '#d97706' },
  incident_resolved: { label: 'Incident Resolved', color: '#16a34a' },
  metric_alert: { label: 'Metric Alert', color: '#ea580c' },
  remediation_started: { label: 'Remediation Started', color: '#2563eb' },
  remediation_completed: { label: 'Remediation Done', color: '#16a34a' },
  prediction_alert: { label: 'Prediction', color: '#8b5cf6' },
  diagnostic_progress: { label: 'Diagnosis', color: '#0891b2' },
  comment_added: { label: 'Comment', color: '#6b7280' },
  agent_status_change: { label: 'Agent Status', color: '#6b7280' },
};

export default function ActivityFeed({ messages }: Props) {
  const events = messages
    .filter(m => m.type !== 'ping' && m.type !== 'pong' && m.type !== 'connected' && m.type !== 'metric_update')
    .reverse()
    .slice(0, 50);

  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)', overflow: 'hidden' }}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.06)', fontWeight: 600, fontSize: '14px', color: '#f0f0f0' }}>
        Activity Feed
      </div>
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {events.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: '#71717a', fontSize: '13px' }}>
            No activity yet. Events will appear here in real-time.
          </div>
        ) : (
          events.map((msg, i) => {
            const info = eventLabels[msg.type] || { label: msg.type, color: '#6b7280' };
            const data = msg.data || {};
            const title = (data.title || data.message || data.step || '') as string;
            return (
              <div
                key={i}
                style={{
                  padding: '10px 16px',
                  borderBottom: '1px solid rgba(255,255,255,0.04)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                }}
              >
                <span style={{
                  width: '8px', height: '8px', borderRadius: '50%',
                  background: info.color, flexShrink: 0,
                }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: info.color }}>{info.label}</span>
                  {title && (
                    <span style={{ fontSize: '12px', color: '#6b7280', marginLeft: '6px' }}>
                      {title.slice(0, 80)}
                    </span>
                  )}
                </div>
                <span style={{ fontSize: '10px', color: '#9ca3af', flexShrink: 0 }}>
                  {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
