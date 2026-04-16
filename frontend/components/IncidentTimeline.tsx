'use client';

import { useState, useEffect } from 'react';
import { WSMessage } from '@/lib/useWebSocket';

interface TimelineStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'complete' | 'error';
  message?: string;
  timestamp?: string;
}

interface Props {
  incidentId: string;
  lastMessage: WSMessage | null;
}

const PIPELINE_STEPS: TimelineStep[] = [
  { id: 'detected', label: 'Detected', status: 'complete' },
  { id: 'analyzing_metrics', label: 'Analyzing Metrics', status: 'pending' },
  { id: 'ai_analysis', label: 'AI Diagnosis', status: 'pending' },
  { id: 'checkpoint', label: 'Creating Checkpoint', status: 'pending' },
  { id: 'executing', label: 'Executing Fix', status: 'pending' },
  { id: 'verifying', label: 'Verifying', status: 'pending' },
  { id: 'resolved', label: 'Resolved', status: 'pending' },
];

const statusStyle: Record<string, { bg: string; border: string; icon: string }> = {
  pending: { bg: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.1)', icon: '\u25CB' },
  active: { bg: '#dbeafe', border: '#3b82f6', icon: '\u25CF' },
  complete: { bg: '#dcfce7', border: '#16a34a', icon: '\u2713' },
  error: { bg: '#fef2f2', border: '#dc2626', icon: '\u2717' },
};

export default function IncidentTimeline({ incidentId, lastMessage }: Props) {
  const [steps, setSteps] = useState<TimelineStep[]>(PIPELINE_STEPS.map(s => ({ ...s })));

  useEffect(() => {
    if (!lastMessage || !lastMessage.data) return;
    const data = lastMessage.data as Record<string, unknown>;
    if (data.incident_id !== incidentId) return;

    const step = data.step as string;
    if (!step) return;

    setSteps(prev => prev.map(s => {
      if (s.id === step) {
        return {
          ...s,
          status: step === 'resolved' ? 'complete' : 'active',
          message: data.message as string,
          timestamp: new Date().toLocaleTimeString(),
        };
      }
      // Mark previous steps as complete
      const stepIdx = PIPELINE_STEPS.findIndex(ps => ps.id === step);
      const thisIdx = PIPELINE_STEPS.findIndex(ps => ps.id === s.id);
      if (thisIdx < stepIdx && s.status !== 'complete') {
        return { ...s, status: 'complete' };
      }
      return s;
    }));
  }, [lastMessage, incidentId]);

  return (
    <div style={{ padding: '16px' }}>
      <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: '#f0f0f0' }}>Incident Timeline</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {steps.map((step, i) => {
          const style = statusStyle[step.status];
          return (
            <div key={step.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              {/* Connector line + dot */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '24px' }}>
                <div style={{
                  width: '24px', height: '24px', borderRadius: '50%',
                  border: `2px solid ${style.border}`, background: style.bg,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '12px', fontWeight: 700, color: style.border,
                  animation: step.status === 'active' ? 'pulse 1.5s infinite' : 'none',
                }}>
                  {style.icon}
                </div>
                {i < steps.length - 1 && (
                  <div style={{
                    width: '2px', height: '24px',
                    background: step.status === 'complete' ? '#16a34a' : 'rgba(255,255,255,0.1)',
                  }} />
                )}
              </div>
              {/* Label */}
              <div style={{ paddingTop: '2px', flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 500, color: step.status === 'pending' ? '#71717a' : '#f0f0f0' }}>
                  {step.label}
                </div>
                {step.message && (
                  <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>{step.message}</div>
                )}
                {step.timestamp && (
                  <div style={{ fontSize: '10px', color: '#9ca3af' }}>{step.timestamp}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <style>{`@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }`}</style>
    </div>
  );
}
