'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { colors, severityColor } from '@/lib/theme';

interface PredictiveAlertItem {
  id: string;
  title: string;
  message: string | null;
  severity: string;
  prediction_type: string;
  service_name: string | null;
  confidence: number;
  hours_until_issue: number | null;
  prevented: boolean;
  prevention_action: string | null;
  preventive_actions: Array<{ action: string; description: string; effort: string }> | null;
  created_at: string;
}

interface PredictiveAlertsProps {
  alerts: PredictiveAlertItem[];
  onRefresh: () => void;
}

const TYPE_LABELS: Record<string, string> = {
  resource_exhaustion: 'Resource Exhaustion',
  capacity_breach: 'Capacity Breach',
  degrading_trend: 'Degrading Trend',
  cost_overrun: 'Cost Overrun',
  anomaly_forecast: 'Anomaly Forecast',
  threshold_breach: 'Threshold Breach',
  sla_violation: 'SLA Violation',
  capacity: 'Capacity',
  security: 'Security',
  anomaly: 'Anomaly',
};

export default function PredictiveAlerts({ alerts, onRefresh }: PredictiveAlertsProps) {
  const [preventing, setPreventing] = useState<string | null>(null);
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  const handlePrevent = async (alertId: string) => {
    setPreventing(alertId);
    try {
      await api.post(`/alerts/predictive/${alertId}/prevent`, { action_taken: 'manual_prevention' });
      onRefresh();
    } catch (error) {
      console.error('Failed to mark as prevented:', error);
    } finally {
      setPreventing(null);
    }
  };

  const sortedAlerts = [...alerts].sort((a, b) => {
    if (a.prevented !== b.prevented) return a.prevented ? 1 : -1;
    return (a.hours_until_issue ?? 9999) - (b.hours_until_issue ?? 9999);
  });

  return (
    <div style={{
      background: 'rgba(255,255,255,0.015)',
      border: '1px solid rgba(255,255,255,0.04)',
      borderRadius: 18, overflow: 'hidden',
    }}>
      <div style={{
        padding: '18px 22px', borderBottom: '1px solid rgba(255,255,255,0.04)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <h2 style={{
          fontSize: 16, fontWeight: 700,
          background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>Predictive Alerts</h2>
        <span style={{
          fontSize: 11, color: '#ec4899', fontWeight: 600,
          padding: '4px 12px', borderRadius: 8,
          background: 'rgba(236,72,153,0.06)',
        }}>
          {alerts.filter(a => !a.prevented).length} active
        </span>
      </div>

      {sortedAlerts.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: colors.textMuted }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>🎯</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#71717a', marginBottom: 4 }}>No predictive alerts</div>
          <div style={{ fontSize: 13 }}>System is looking healthy!</div>
        </div>
      ) : (
        sortedAlerts.map((alert, idx) => {
          const sev = severityColor(alert.severity);
          const hovered = hoveredRow === alert.id;
          const confColor = alert.confidence >= 85 ? '#10b981' : alert.confidence >= 70 ? '#f59e0b' : '#ef4444';
          return (
            <div
              key={alert.id}
              onMouseEnter={() => setHoveredRow(alert.id)}
              onMouseLeave={() => setHoveredRow(null)}
              style={{
                padding: '16px 22px',
                borderBottom: '1px solid rgba(255,255,255,0.03)',
                background: hovered ? 'rgba(59,130,246,0.03)' : 'transparent',
                opacity: alert.prevented ? 0.5 : 1,
                transition: 'all 0.2s ease',
                animation: `slide-up 0.4s ease-out ${idx * 0.03}s both`,
                position: 'relative',
              }}
            >
              {hovered && !alert.prevented && (
                <div style={{
                  position: 'absolute', left: 0, top: '20%', bottom: '20%', width: 2,
                  background: sev.color, boxShadow: `0 0 6px ${sev.color}`, borderRadius: 2,
                }} />
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{
                      fontSize: 14, fontWeight: 600,
                      color: hovered ? '#f0f0f0' : '#a1a1aa',
                      transition: 'color 0.2s',
                    }}>{alert.title}</span>
                    {alert.prevented && (
                      <span style={{
                        fontSize: 10, fontWeight: 700, color: '#10b981',
                        padding: '2px 8px', borderRadius: 6,
                        background: 'rgba(16,185,129,0.1)',
                        textTransform: 'uppercase',
                      }}>Prevented</span>
                    )}
                  </div>
                  {alert.message && (
                    <p style={{ fontSize: 12, color: '#52525b', marginBottom: 8, lineHeight: 1.5 }}>{alert.message}</p>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{
                      padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                      background: sev.bg, color: sev.color, border: `1px solid ${sev.border}`,
                      textTransform: 'uppercase',
                    }}>{alert.severity}</span>
                    <span style={{
                      padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 500,
                      background: 'rgba(255,255,255,0.03)', color: '#71717a',
                      border: '1px solid rgba(255,255,255,0.06)',
                    }}>{TYPE_LABELS[alert.prediction_type] || alert.prediction_type}</span>
                    {alert.service_name && (
                      <span style={{ fontSize: 11, color: '#52525b' }}>{alert.service_name}</span>
                    )}
                    <span style={{
                      fontSize: 11, fontWeight: 600, color: confColor,
                      padding: '2px 8px', borderRadius: 6,
                      background: `${confColor}12`,
                    }}>
                      {alert.confidence}% conf
                    </span>
                    {alert.hours_until_issue != null && (
                      <span style={{
                        fontSize: 11, fontWeight: 700,
                        color: alert.hours_until_issue < 6 ? '#ef4444' : alert.hours_until_issue < 24 ? '#f59e0b' : '#71717a',
                      }}>
                        {alert.hours_until_issue < 24
                          ? `${alert.hours_until_issue.toFixed(0)}h until issue`
                          : `${(alert.hours_until_issue / 24).toFixed(1)}d until issue`}
                      </span>
                    )}
                  </div>
                </div>
                {!alert.prevented && (
                  <button
                    onClick={() => handlePrevent(alert.id)}
                    disabled={preventing === alert.id}
                    style={{
                      padding: '8px 16px', borderRadius: 10, border: 'none',
                      background: 'linear-gradient(135deg, #10b981, #059669)',
                      color: '#fff', fontSize: 12, fontWeight: 600,
                      cursor: preventing === alert.id ? 'not-allowed' : 'pointer',
                      opacity: preventing === alert.id ? 0.5 : 1,
                      boxShadow: '0 4px 12px rgba(16,185,129,0.2)',
                      transition: 'all 0.2s',
                      whiteSpace: 'nowrap',
                      flexShrink: 0,
                    }}
                  >
                    {preventing === alert.id ? 'Saving...' : 'Mark Prevented'}
                  </button>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
