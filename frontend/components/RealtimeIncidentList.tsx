'use client';

import { useState, useEffect } from 'react';
import { WSMessage } from '@/lib/useWebSocket';

interface Incident {
  id: string;
  title: string;
  severity: string;
  status: string;
  service_name?: string;
  detected_at?: string;
}

interface Props {
  initialIncidents: Incident[];
  lastMessage: WSMessage | null;
  onSelect?: (incident: Incident) => void;
}

const severityColor: Record<string, { bg: string; text: string }> = {
  critical: { bg: 'rgba(220,38,38,0.15)', text: '#f87171' },
  high: { bg: 'rgba(234,88,12,0.15)', text: '#fb923c' },
  medium: { bg: 'rgba(217,119,6,0.15)', text: '#fbbf24' },
  low: { bg: 'rgba(22,163,74,0.15)', text: '#4ade80' },
};

export default function RealtimeIncidentList({ initialIncidents, lastMessage, onSelect }: Props) {
  const [incidents, setIncidents] = useState<Incident[]>(initialIncidents);
  const [newIds, setNewIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    setIncidents(initialIncidents);
  }, [initialIncidents]);

  // React to WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === 'new_incident' && lastMessage.data) {
      const inc = lastMessage.data as unknown as Incident;
      setIncidents(prev => [inc, ...prev]);
      setNewIds(prev => new Set(prev).add(inc.id));
      // Remove highlight after 5 seconds
      setTimeout(() => setNewIds(prev => {
        const next = new Set(prev);
        next.delete(inc.id);
        return next;
      }), 5000);
    }

    if (lastMessage.type === 'incident_updated' && lastMessage.data) {
      const { incident_id, changes } = lastMessage.data as { incident_id: string; changes: Record<string, unknown> };
      setIncidents(prev => prev.map(i =>
        i.id === incident_id ? { ...i, ...changes } : i
      ));
    }

    if (lastMessage.type === 'incident_resolved' && lastMessage.data) {
      const { incident_id } = lastMessage.data as { incident_id: string };
      setIncidents(prev => prev.map(i =>
        i.id === incident_id ? { ...i, status: 'resolved' } : i
      ));
    }
  }, [lastMessage]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {incidents.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>
          No incidents. System is healthy!
        </div>
      ) : (
        incidents.slice(0, 20).map(inc => {
          const isNew = newIds.has(inc.id);
          const colors = severityColor[inc.severity] || { bg: 'rgba(255,255,255,0.05)', text: '#71717a' };
          return (
            <div
              key={inc.id}
              onClick={() => onSelect?.(inc)}
              role="button"
              tabIndex={0}
              aria-label={`Incident: ${inc.title}`}
              onKeyDown={(e) => e.key === 'Enter' && onSelect?.(inc)}
              style={{
                padding: '12px 16px',
                background: isNew ? 'rgba(37,99,235,0.1)' : 'rgba(255,255,255,0.03)',
                border: isNew ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.06)',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                transition: 'all 0.3s ease',
                animation: isNew ? 'slideIn 0.3s ease' : 'none',
              }}
            >
              <div>
                <div style={{ fontWeight: 500, fontSize: '14px', color: '#f0f0f0' }}>{inc.title}</div>
                <div style={{ fontSize: '12px', color: '#71717a', marginTop: '2px' }}>
                  {inc.service_name || 'Unknown service'} &middot; {inc.detected_at ? new Date(inc.detected_at).toLocaleTimeString() : ''}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{
                  fontSize: '11px', fontWeight: 600, padding: '2px 10px',
                  borderRadius: '12px', background: colors.bg, color: colors.text,
                }}>
                  {inc.severity}
                </span>
                <span style={{
                  fontSize: '11px', padding: '2px 10px', borderRadius: '12px',
                  background: inc.status === 'resolved' ? 'rgba(22,163,74,0.15)' : 'rgba(217,119,6,0.15)',
                  color: inc.status === 'resolved' ? '#4ade80' : '#fbbf24',
                }}>
                  {inc.status}
                </span>
              </div>
            </div>
          );
        })
      )}
      <style>{`@keyframes slideIn { from { opacity:0; transform:translateY(-10px); } to { opacity:1; transform:translateY(0); } }`}</style>
    </div>
  );
}
