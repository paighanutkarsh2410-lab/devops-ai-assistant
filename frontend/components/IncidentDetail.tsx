'use client';

import { useEffect, useState } from 'react';
import { api, learningAPI } from '@/lib/api';
import { colors, severityColor, statusColor } from '@/lib/theme';

interface Recommendation {
  action_name: string;
  confidence: number;
  success_rate: number;
  similar_count: number;
  explanation?: string;
}

interface Incident {
  id: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  service_name: string | null;
  root_cause: string | null;
  solution: string | null;
  detected_at: string;
  resolved_at: string | null;
  auto_resolved: boolean;
}

interface TimelineEvent {
  timestamp: string;
  event_type: string;
  description: string;
  metadata?: Record<string, unknown>;
}

interface TimelineData {
  incident_id: string;
  events: TimelineEvent[];
  summary: string | null;
}

interface IncidentDetailProps {
  incident: Incident;
  onClose: () => void;
}

const EVENT_DOT_COLORS: Record<string, string> = {
  detection: '#ef4444',
  alert: '#f97316',
  metric_spike: '#f59e0b',
  deployment: '#a855f7',
  error_log: '#f87171',
  diagnosis: '#3b82f6',
  resolution: '#10b981',
};

const EVENT_LABELS: Record<string, string> = {
  detection: 'Detected',
  alert: 'Alert',
  metric_spike: 'Metric Spike',
  deployment: 'Deployment',
  error_log: 'Error Log',
  diagnosis: 'Diagnosis',
  resolution: 'Resolved',
};

export default function IncidentDetail({ incident, onClose }: IncidentDetailProps) {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [loadingTimeline, setLoadingTimeline] = useState(true);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    requestAnimationFrame(() => setVisible(true));
    // Lock body scroll while modal is open
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  useEffect(() => {
    const loadTimeline = async () => {
      try {
        const resp = await api.get(`/incidents/${incident.id}/timeline`);
        setTimeline(resp.data);
      } catch (err) {
        console.error('Failed to load timeline:', err);
      } finally {
        setLoadingTimeline(false);
      }
    };

    const loadRecommendations = async () => {
      setLoadingRecs(true);
      try {
        const resp = await learningAPI.recommend(incident.id);
        setRecommendations(resp.data.recommendations || []);
      } catch {
        // Recommendations are optional
      } finally {
        setLoadingRecs(false);
      }
    };

    loadTimeline();
    loadRecommendations();
  }, [incident.id]);

  const handleClose = () => {
    setVisible(false);
    setTimeout(onClose, 300);
  };

  const sev = severityColor(incident.severity);
  const stat = statusColor(incident.status);
  const actions = incident.solution?.split(';').map(s => s.trim()).filter(Boolean) || [];

  const formatTime = (ts: string) =>
    new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  return (
    <div
      onClick={handleClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 100, overflowY: 'auto',
        background: visible ? 'rgba(0,0,0,0.7)' : 'rgba(0,0,0,0)',
        backdropFilter: visible ? 'blur(8px)' : 'blur(0px)',
        WebkitBackdropFilter: visible ? 'blur(8px)' : 'blur(0px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 24,
        transition: 'all 0.3s ease',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 720, maxHeight: '90vh',
          overflowY: 'auto',
          background: 'rgba(10,10,20,0.95)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 24,
          boxShadow: '0 40px 120px rgba(0,0,0,0.8), 0 0 60px rgba(59,130,246,0.08)',
          transform: visible ? 'scale(1) translateY(0)' : 'scale(0.92) translateY(30px)',
          opacity: visible ? 1 : 0,
          transition: 'all 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
          position: 'relative',
        }}
      >
        {/* Top glow accent based on severity */}
        <div style={{
          position: 'absolute', top: -60, left: '50%', transform: 'translateX(-50%)',
          width: 300, height: 120,
          background: `radial-gradient(circle, ${sev.color}20, transparent)`,
          filter: 'blur(30px)', pointerEvents: 'none',
        }} />

        {/* Severity top bar */}
        <div style={{
          height: 3,
          background: `linear-gradient(90deg, transparent, ${sev.color}, transparent)`,
          opacity: 0.6,
        }} />

        {/* Header */}
        <div style={{
          padding: '24px 28px 20px',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          position: 'relative',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ flex: 1, paddingRight: 20 }}>
              <h2 style={{
                fontSize: 22, fontWeight: 800, color: '#f0f0f0',
                letterSpacing: '-0.3px', marginBottom: 12,
              }}>{incident.title}</h2>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                <span style={{
                  padding: '4px 14px', borderRadius: 8, fontSize: 11, fontWeight: 700,
                  background: sev.bg, color: sev.color, border: `1px solid ${sev.border}`,
                  textTransform: 'uppercase', letterSpacing: 0.5,
                }}>{incident.severity}</span>
                <span style={{
                  padding: '4px 14px', borderRadius: 8, fontSize: 11, fontWeight: 700,
                  background: stat.bg, color: stat.color,
                  textTransform: 'uppercase', letterSpacing: 0.5,
                }}>{incident.status}</span>
                {incident.service_name && (
                  <span style={{
                    padding: '4px 14px', borderRadius: 8, fontSize: 11, fontWeight: 500,
                    background: 'rgba(255,255,255,0.04)', color: '#71717a',
                    border: '1px solid rgba(255,255,255,0.06)',
                  }}>{incident.service_name}</span>
                )}
                {incident.auto_resolved && (
                  <span style={{
                    padding: '4px 14px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                    background: 'rgba(139,92,246,0.1)', color: '#a78bfa',
                    border: '1px solid rgba(139,92,246,0.2)',
                    display: 'flex', alignItems: 'center', gap: 4,
                  }}>🤖 Auto-resolved</span>
                )}
              </div>
            </div>
            <button onClick={handleClose} style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.06)',
              color: '#71717a', fontSize: 18, cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.2s',
            }}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(239,68,68,0.1)'; e.currentTarget.style.color = '#f87171'; e.currentTarget.style.borderColor = 'rgba(239,68,68,0.2)'; }}
              onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; e.currentTarget.style.color = '#71717a'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'; }}
            >&times;</button>
          </div>
        </div>

        <div style={{ padding: '24px 28px 28px' }}>
          {/* Description */}
          {incident.description && (
            <div style={{ marginBottom: 24 }}>
              <h3 style={{ fontSize: 12, fontWeight: 700, color: '#52525b', textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 10 }}>
                Description
              </h3>
              <p style={{ fontSize: 14, color: '#a1a1aa', lineHeight: 1.7 }}>{incident.description}</p>
            </div>
          )}

          {/* Root Cause Analysis */}
          {incident.root_cause && (
            <div style={{
              marginBottom: 24, padding: 20, borderRadius: 16,
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.05)',
              position: 'relative', overflow: 'hidden',
            }}>
              {/* Left accent */}
              <div style={{
                position: 'absolute', left: 0, top: 0, bottom: 0, width: 3,
                background: `linear-gradient(180deg, ${sev.color}, ${sev.color}40)`,
                borderRadius: '3px 0 0 3px',
              }} />
              <h3 style={{
                fontSize: 14, fontWeight: 700, marginBottom: 14,
                background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              }}>Root Cause Analysis</h3>
              <div style={{
                padding: '14px 16px', borderRadius: 10, marginBottom: 16,
                background: `${sev.color}08`,
                border: `1px solid ${sev.color}15`,
              }}>
                <p style={{ fontSize: 14, color: sev.color, fontWeight: 600, lineHeight: 1.6 }}>{incident.root_cause}</p>
              </div>

              {actions.length > 0 && (
                <div>
                  <h4 style={{ fontSize: 12, fontWeight: 600, color: '#71717a', marginBottom: 10 }}>
                    Recommended Actions
                  </h4>
                  {actions.map((action, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 6,
                    }}>
                      <span style={{
                        width: 6, height: 6, borderRadius: '50%', marginTop: 6, flexShrink: 0,
                        background: '#3b82f6', boxShadow: '0 0 6px rgba(59,130,246,0.4)',
                      }} />
                      <span style={{ fontSize: 13, color: '#a1a1aa', lineHeight: 1.6 }}>{action}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Recommendations */}
          {!loadingRecs && recommendations.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <h3 style={{ fontSize: 12, fontWeight: 700, color: '#52525b', textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 14 }}>
                AI Recommendations
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {recommendations.map((rec, i) => {
                  const confColor = rec.confidence >= 80 ? '#10b981' : rec.confidence >= 60 ? '#f59e0b' : '#ef4444';
                  return (
                    <div key={i} style={{
                      padding: '14px 16px', borderRadius: 12,
                      background: 'rgba(255,255,255,0.02)',
                      border: '1px solid rgba(255,255,255,0.05)',
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <span style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0' }}>{rec.action_name}</span>
                          <span style={{
                            fontSize: 11, fontWeight: 700, color: confColor,
                            padding: '2px 8px', borderRadius: 6,
                            background: `${confColor}15`,
                          }}>{rec.confidence}%</span>
                        </div>
                        {rec.explanation && (
                          <p style={{ fontSize: 12, color: '#71717a', marginTop: 4 }}>{rec.explanation}</p>
                        )}
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: 12, color: '#a1a1aa' }}>{rec.success_rate}% success</div>
                        <div style={{ fontSize: 11, color: '#52525b' }}>{rec.similar_count} similar</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Timeline */}
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 12, fontWeight: 700, color: '#52525b', textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 14 }}>
              Timeline
            </h3>
            {loadingTimeline ? (
              <div style={{
                padding: 20, borderRadius: 12, textAlign: 'center',
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.04)',
              }}>
                <div style={{ fontSize: 13, color: '#52525b' }}>Loading timeline...</div>
              </div>
            ) : timeline && timeline.events.length > 0 ? (
              <div>
                {/* AI Summary */}
                {timeline.summary && (
                  <div style={{
                    padding: '14px 16px', borderRadius: 12, marginBottom: 16,
                    background: 'rgba(59,130,246,0.06)',
                    border: '1px solid rgba(59,130,246,0.12)',
                  }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#60a5fa', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>
                      AI Summary
                    </div>
                    <p style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.6 }}>
                      {timeline.summary}
                    </p>
                  </div>
                )}

                {/* Events */}
                <div style={{ position: 'relative', paddingLeft: 24 }}>
                  {/* Vertical line */}
                  <div style={{
                    position: 'absolute', left: 5, top: 6, bottom: 6, width: 1,
                    background: 'linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02))',
                  }} />

                  {timeline.events.map((event, i) => {
                    const dotColor = EVENT_DOT_COLORS[event.event_type] || '#71717a';
                    return (
                      <div key={i} style={{
                        marginBottom: i < timeline.events.length - 1 ? 20 : 0,
                        position: 'relative',
                        animation: `slide-up 0.4s ease-out ${i * 0.08}s both`,
                      }}>
                        {/* Dot */}
                        <div style={{
                          position: 'absolute', left: -24, top: 2,
                          width: 12, height: 12, borderRadius: '50%',
                          background: dotColor,
                          boxShadow: `0 0 8px ${dotColor}60`,
                          border: '2px solid rgba(10,10,20,0.95)',
                        }} />
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                          <span style={{ fontSize: 12, color: '#71717a', fontFamily: 'monospace' }}>
                            {formatTime(event.timestamp)}
                          </span>
                          <span style={{
                            fontSize: 10, fontWeight: 700, color: dotColor,
                            padding: '2px 8px', borderRadius: 6,
                            background: `${dotColor}15`,
                            textTransform: 'uppercase', letterSpacing: 0.5,
                          }}>
                            {EVENT_LABELS[event.event_type] || event.event_type}
                          </span>
                        </div>
                        <p style={{ fontSize: 13, color: '#a1a1aa', lineHeight: 1.6 }}>
                          {event.description}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div style={{
                padding: 20, borderRadius: 12, textAlign: 'center',
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.04)',
              }}>
                <div style={{ fontSize: 13, color: '#52525b' }}>No timeline events yet.</div>
              </div>
            )}
          </div>

          {/* Metadata Grid */}
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12,
            padding: '18px 20px', borderRadius: 14,
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.05)',
          }}>
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#52525b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
                Detected
              </div>
              <div style={{ fontSize: 13, color: '#a1a1aa', fontFamily: 'monospace' }}>
                {new Date(incident.detected_at).toLocaleString()}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#52525b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
                Resolved
              </div>
              <div style={{ fontSize: 13, color: incident.resolved_at ? '#10b981' : '#71717a', fontFamily: 'monospace' }}>
                {incident.resolved_at ? new Date(incident.resolved_at).toLocaleString() : '—'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#52525b', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
                Auto-resolved
              </div>
              <div style={{
                fontSize: 13, fontWeight: 600,
                color: incident.auto_resolved ? '#a78bfa' : '#71717a',
              }}>
                {incident.auto_resolved ? '✓ Yes' : 'No'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
