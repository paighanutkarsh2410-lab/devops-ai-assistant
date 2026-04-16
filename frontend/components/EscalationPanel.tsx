'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface Props {
  incidentId: string;
}

interface EscalationStatus {
  needs_escalation: boolean;
  current_level?: number;
  seconds_until_next?: number;
  record_id?: string;
  reason?: string;
}

export default function EscalationPanel({ incidentId }: Props) {
  const [status, setStatus] = useState<EscalationStatus | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { checkStatus(); }, [incidentId]);

  const checkStatus = async () => {
    try {
      const res = await api.get(`/escalation/incidents/${incidentId}/status`);
      setStatus(res.data);
    } catch { /* empty */ }
  };

  const startEscalation = async () => {
    setLoading(true);
    try {
      await api.post(`/escalation/incidents/${incidentId}/escalate`);
      await checkStatus();
    } catch { /* empty */ }
    setLoading(false);
  };

  const acknowledge = async () => {
    setLoading(true);
    try {
      await api.post(`/escalation/incidents/${incidentId}/acknowledge`);
      await checkStatus();
    } catch { /* empty */ }
    setLoading(false);
  };

  const escalateNext = async () => {
    setLoading(true);
    try {
      await api.post(`/escalation/incidents/${incidentId}/next-level`);
      await checkStatus();
    } catch { /* empty */ }
    setLoading(false);
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)', padding: '14px',
    }}>
      <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '10px', color: '#f0f0f0' }}>Escalation</h3>

      {!status || status.reason === 'No active escalation' ? (
        <div>
          <p style={{ fontSize: '12px', color: '#a1a1aa', marginBottom: '8px' }}>No active escalation</p>
          <button onClick={startEscalation} disabled={loading} style={{
            padding: '5px 12px', borderRadius: '6px', background: '#dc2626', color: 'white',
            border: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: 500,
          }}>
            {loading ? 'Starting...' : 'Start Escalation'}
          </button>
        </div>
      ) : (
        <div>
          {/* Current level */}
          <div style={{ display: 'flex', gap: '16px', marginBottom: '10px' }}>
            <div>
              <div style={{ fontSize: '10px', color: '#9ca3af' }}>Level</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#dc2626' }}>
                L{status.current_level}
              </div>
            </div>
            {status.seconds_until_next != null && status.seconds_until_next > 0 && (
              <div>
                <div style={{ fontSize: '10px', color: '#9ca3af' }}>Next escalation in</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: '#d97706' }}>
                  {formatTime(status.seconds_until_next)}
                </div>
              </div>
            )}
          </div>

          {/* Level indicator */}
          <div style={{ display: 'flex', gap: '4px', marginBottom: '10px' }}>
            {[1, 2, 3].map(l => (
              <div key={l} style={{
                flex: 1, height: '4px', borderRadius: '2px',
                background: l <= (status.current_level || 0) ? '#dc2626' : 'rgba(255,255,255,0.06)',
              }} />
            ))}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '6px' }}>
            <button onClick={acknowledge} disabled={loading} style={{
              padding: '5px 12px', borderRadius: '6px', background: '#16a34a', color: 'white',
              border: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: 500,
            }}>
              Acknowledge
            </button>
            <button onClick={escalateNext} disabled={loading} style={{
              padding: '5px 12px', borderRadius: '6px', background: '#d97706', color: 'white',
              border: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: 500,
            }}>
              Escalate Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
