'use client';

import { useEffect, useState, useCallback } from 'react';
import { metricsAPI, alertsAPI } from '@/lib/api';
import { colors, severityColor } from '@/lib/theme';
import MetricsChart from './MetricsChart';

interface Metric {
  id: string;
  service_name: string;
  metric_name: string;
  value: number;
  unit: string | null;
  timestamp: string;
}

interface Alert {
  id: string;
  title: string;
  message: string;
  severity: string;
  acknowledged: boolean;
  resolved: boolean;
  triggered_at: string;
}

export default function LiveMetrics() {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredAlert, setHoveredAlert] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [metricsRes, alertsRes] = await Promise.all([
        metricsAPI.getAll({ hours: 1, limit: 1000 }),
        alertsAPI.getAll({ limit: 20 }),
      ]);
      setMetrics(metricsRes.data);
      setAlerts(alertsRes.data);
    } catch (err) {
      console.error('Failed to load metrics/alerts:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleAcknowledge = async (alertId: string) => {
    try {
      await alertsAPI.update(alertId, { acknowledged: true });
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, acknowledged: true } : a));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  const getChartData = (serviceName: string, metricName: string) => {
    return metrics
      .filter(m => m.service_name === serviceName && m.metric_name === metricName)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .slice(-30);
  };

  const services = [...new Set(metrics.map(m => m.service_name))];
  const activeAlerts = alerts.filter(a => !a.resolved);

  if (loading) {
    return (
      <div style={{
        background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.04)',
        borderRadius: 18, padding: 48, textAlign: 'center', color: colors.textMuted, fontSize: 13,
      }}>Loading metrics...</div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <div style={{
          background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.04)',
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
            }}>Active Alerts</h2>
            <span style={{
              fontSize: 11, color: '#ef4444', fontWeight: 600,
              padding: '4px 12px', borderRadius: 8,
              background: 'rgba(239,68,68,0.06)',
            }}>
              {activeAlerts.length} active
            </span>
          </div>
          {activeAlerts.slice(0, 8).map((alert, idx) => {
            const sev = severityColor(alert.severity);
            const hovered = hoveredAlert === alert.id;
            return (
              <div
                key={alert.id}
                onMouseEnter={() => setHoveredAlert(alert.id)}
                onMouseLeave={() => setHoveredAlert(null)}
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
                    background: sev.color, boxShadow: `0 0 6px ${sev.color}`, borderRadius: 2,
                  }} />
                )}
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: 14, fontWeight: 600,
                    color: hovered ? '#f0f0f0' : '#a1a1aa',
                    transition: 'color 0.2s', marginBottom: 3,
                  }}>{alert.title}</div>
                  <div style={{ fontSize: 12, color: '#3f3f46' }}>{alert.message}</div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
                  <span style={{
                    padding: '4px 12px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                    background: sev.bg, color: sev.color, border: `1px solid ${sev.border}`,
                    textTransform: 'uppercase',
                  }}>{alert.severity}</span>
                  <span style={{ fontSize: 11, color: '#52525b' }}>{timeAgo(alert.triggered_at)}</span>
                  {alert.acknowledged ? (
                    <span style={{
                      fontSize: 11, fontWeight: 600, color: '#10b981',
                      padding: '4px 10px', borderRadius: 8,
                      background: 'rgba(16,185,129,0.08)',
                    }}>Acked</span>
                  ) : (
                    <button onClick={() => handleAcknowledge(alert.id)} style={{
                      padding: '5px 12px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)',
                      background: 'rgba(255,255,255,0.03)', color: '#a1a1aa',
                      cursor: 'pointer', fontSize: 11, fontWeight: 500,
                      transition: 'all 0.2s',
                    }}>Ack</button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Metrics Charts */}
      {services.length === 0 ? (
        <div style={{
          background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.04)',
          borderRadius: 18, padding: 48, textAlign: 'center', color: colors.textMuted,
        }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>📈</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#71717a', marginBottom: 4 }}>No metrics data yet</div>
          <div style={{ fontSize: 13 }}>Start the Monitor Agent to begin collecting data.</div>
        </div>
      ) : (
        services.slice(0, 4).map((service, sIdx) => (
          <div key={service} style={{
            background: 'rgba(255,255,255,0.015)', border: '1px solid rgba(255,255,255,0.04)',
            borderRadius: 18, overflow: 'hidden',
            animation: `slide-up 0.4s ease-out ${sIdx * 0.1}s both`,
          }}>
            <div style={{
              padding: '16px 22px', borderBottom: '1px solid rgba(255,255,255,0.04)',
            }}>
              <h3 style={{
                fontSize: 15, fontWeight: 700, color: '#e2e8f0',
                display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: '#10b981', boxShadow: '0 0 6px rgba(16,185,129,0.4)',
                }} />
                {service}
              </h3>
            </div>
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, padding: 20,
            }}>
              <MetricsChart data={getChartData(service, 'cpu_percent')} title="CPU Usage" color="#ef4444" unit="%" />
              <MetricsChart data={getChartData(service, 'memory_percent')} title="Memory Usage" color="#8b5cf6" unit="%" />
              <MetricsChart data={getChartData(service, 'response_time_ms')} title="Response Time" color="#f59e0b" unit="ms" />
              <MetricsChart data={getChartData(service, 'error_rate')} title="Error Rate" color="#10b981" unit="%" />
            </div>
          </div>
        ))
      )}
    </div>
  );
}
