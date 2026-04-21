'use client';

import { useState, useEffect } from 'react';
import { capacityAPI, predictionsAPI } from '@/lib/api';
import {
  colors, pageContainer, pageContent, pageHeader, pageTitle, pageSubtitle,
  card, glassCard, statCard, badge, flexBetween, flexGap, btnPrimary,
} from '@/lib/theme';

interface PredictiveAlert {
  id: string;
  title: string;
  prediction_type: string;
  service_name: string;
  confidence: number;
  hours_until_issue: number;
  current_value: number;
  predicted_value: number;
  severity: string;
  prevented: boolean;
  preventive_actions: { action: string; description: string }[];
  created_at: string;
}

interface CapacityPlan {
  id?: string;
  service_name: string;
  metric_name: string;
  current_usage: number;
  predicted_usage: number;
  threshold: number;
  days_until_threshold: number;
  recommendation: string;
  priority: string;
  status: string;
}

interface Forecast {
  service_name: string;
  metric_name: string;
  current_value: number;
  predicted_value: number;
  trend: string;
  confidence: number;
}

export default function CapacityPlanningPage() {
  const [alerts, setAlerts] = useState<PredictiveAlert[]>([]);
  const [plans, setPlans] = useState<CapacityPlan[]>([]);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [alertsRes, plansRes, forecastsRes, trendsRes] = await Promise.all([
        predictionsAPI.getAlerts({ limit: 20 }).catch(() => ({ data: [] })),
        predictionsAPI.getCapacityPlans({ limit: 20 }).catch(() => ({ data: [] })),
        predictionsAPI.getForecasts({}).catch(() => ({ data: [] })),
        predictionsAPI.getTrends({}).catch(() => ({ data: [] })),
      ]);
      setAlerts(Array.isArray(alertsRes.data) ? alertsRes.data : alertsRes.data?.alerts || []);
      setPlans(Array.isArray(plansRes.data) ? plansRes.data : plansRes.data?.plans || []);
      setForecasts(Array.isArray(forecastsRes.data) ? forecastsRes.data : forecastsRes.data?.forecasts || []);
      setTrends(Array.isArray(trendsRes.data) ? trendsRes.data : trendsRes.data?.trends || []);
    } catch {
      // ignore
    }
    setLoading(false);
  };

  const urgencyColor = (h: number) => h <= 24 ? '#ef4444' : h <= 72 ? '#f97316' : '#f59e0b';
  const trendIcon = (t: string) => t === 'increasing' ? '↑' : t === 'decreasing' ? '↓' : '→';
  const trendColor = (t: string) => t === 'increasing' ? '#f97316' : t === 'decreasing' ? '#10b981' : '#71717a';
  const priorityColor = (p: string) => p === 'P1' || p === 'critical' ? '#ef4444' : p === 'P2' || p === 'high' ? '#f97316' : '#f59e0b';

  const sevColor = (s: string) => {
    switch (s) {
      case 'critical': return { c: '#ef4444', bg: 'rgba(239,68,68,0.1)' };
      case 'high': return { c: '#f97316', bg: 'rgba(249,115,22,0.1)' };
      case 'medium': return { c: '#f59e0b', bg: 'rgba(245,158,11,0.1)' };
      default: return { c: '#71717a', bg: 'rgba(113,113,122,0.1)' };
    }
  };

  // Compute summary stats
  const criticalAlerts = alerts.filter(a => a.severity === 'critical' || (a.hours_until_issue && a.hours_until_issue <= 24)).length;
  const preventedCount = alerts.filter(a => a.prevented).length;
  const avgConfidence = alerts.length > 0 ? Math.round(alerts.reduce((s, a) => s + (a.confidence || 0), 0) / alerts.length) : 0;

  return (
    <div style={pageContainer}>
      <div style={pageContent}>
        <div style={pageHeader}>
          <div style={flexBetween}>
            <div>
              <h1 style={pageTitle}>Capacity Planning</h1>
              <p style={pageSubtitle}>Resource usage trends, exhaustion predictions, and scaling recommendations</p>
            </div>
            <button onClick={loadData} style={{ ...btnPrimary, opacity: loading ? 0.5 : 1 }}>
              {loading ? 'Refreshing...' : 'Refresh Data'}
            </button>
          </div>
        </div>

        {/* Summary Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
          <div style={statCard('#ef4444')}>
            <div style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 4 }}>Critical Alerts</div>
            <div style={{ fontSize: 32, fontWeight: 700, color: criticalAlerts > 0 ? '#ef4444' : colors.success }}>{criticalAlerts}</div>
            <div style={{ fontSize: 12, color: colors.textDim }}>Exhaustion within 24h</div>
          </div>
          <div style={statCard('#3b82f6')}>
            <div style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 4 }}>Active Predictions</div>
            <div style={{ fontSize: 32, fontWeight: 700, color: colors.text }}>{alerts.length}</div>
            <div style={{ fontSize: 12, color: colors.textDim }}>Across all services</div>
          </div>
          <div style={statCard('#10b981')}>
            <div style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 4 }}>Issues Prevented</div>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#10b981' }}>{preventedCount}</div>
            <div style={{ fontSize: 12, color: colors.textDim }}>Proactive actions taken</div>
          </div>
          <div style={statCard('#8b5cf6')}>
            <div style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, marginBottom: 4 }}>Avg Confidence</div>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#8b5cf6' }}>{avgConfidence}%</div>
            <div style={{ fontSize: 12, color: colors.textDim }}>Prediction accuracy</div>
          </div>
        </div>

        {/* Predictive Alerts */}
        <div style={{ ...card, marginBottom: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f97316', marginBottom: 16 }}>Capacity Predictions</h3>
          {alerts.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column' as const, gap: 10 }}>
              {alerts.map((alert, i) => {
                const sc = sevColor(alert.severity);
                return (
                  <div key={alert.id || i} style={{
                    padding: 16, borderRadius: 12, background: colors.bgElevated,
                    border: `1px solid ${colors.border}`,
                    borderLeft: `3px solid ${sc.c}`,
                  }}>
                    <div style={{ ...flexBetween, marginBottom: 8 }}>
                      <div style={{ ...flexGap(10) }}>
                        <span style={badge(sc.c, sc.bg)}>{alert.severity?.toUpperCase()}</span>
                        <span style={{ fontSize: 14, fontWeight: 600, color: colors.text }}>{alert.title}</span>
                      </div>
                      <div style={{ ...flexGap(12) }}>
                        {alert.confidence > 0 && (
                          <span style={{ fontSize: 12, color: '#8b5cf6' }}>{alert.confidence}% confidence</span>
                        )}
                        {alert.prevented && (
                          <span style={badge('#10b981', 'rgba(16,185,129,0.1)')}>Prevented</span>
                        )}
                      </div>
                    </div>
                    <div style={{ ...flexGap(16), flexWrap: 'wrap' as const }}>
                      <span style={{ fontSize: 13, color: colors.textSecondary }}>
                        Service: <strong>{alert.service_name}</strong>
                      </span>
                      {alert.hours_until_issue > 0 && (
                        <span style={{ fontSize: 13, color: urgencyColor(alert.hours_until_issue) }}>
                          {alert.hours_until_issue < 24
                            ? `${Math.round(alert.hours_until_issue)}h until critical`
                            : `${Math.round(alert.hours_until_issue / 24)}d until critical`}
                        </span>
                      )}
                      {alert.current_value > 0 && (
                        <span style={{ fontSize: 13, color: colors.textMuted }}>
                          Current: {alert.current_value}% → Threshold: {alert.predicted_value}%
                        </span>
                      )}
                    </div>
                    {alert.preventive_actions?.length > 0 && (
                      <div style={{ marginTop: 10, padding: '10px 12px', borderRadius: 8, background: 'rgba(59,130,246,0.05)', border: '1px solid rgba(59,130,246,0.1)' }}>
                        <span style={{ fontSize: 11, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1 }}>Recommended Action</span>
                        <p style={{ fontSize: 13, color: colors.textSecondary, marginTop: 4 }}>
                          {alert.preventive_actions[0]?.description}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: 'center' as const, padding: 40 }}>
              <div style={{ fontSize: 36, marginBottom: 8 }}>&#9989;</div>
              <p style={{ color: colors.textMuted, fontSize: 14 }}>No capacity alerts — all resources within safe thresholds</p>
            </div>
          )}
        </div>

        {/* Capacity Plans + Forecasts */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 20, marginBottom: 24 }}>
          {/* Capacity Plans */}
          <div style={card}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: '#8b5cf6', marginBottom: 16 }}>Capacity Plans</h3>
            {plans.length > 0 ? (
              plans.map((plan, i) => (
                <div key={i} style={{ padding: 14, marginBottom: 8, borderRadius: 10, background: colors.bgElevated, border: `1px solid ${colors.borderLight}` }}>
                  <div style={flexBetween}>
                    <span style={{ fontSize: 14, fontWeight: 600, color: colors.text }}>{plan.service_name}</span>
                    <span style={badge(priorityColor(plan.priority), `${priorityColor(plan.priority)}15`)}>
                      {plan.priority}
                    </span>
                  </div>
                  <div style={{ fontSize: 13, color: colors.textMuted, marginTop: 4 }}>{plan.metric_name?.replace('_', ' ')}</div>
                  <div style={{ marginTop: 8 }}>
                    <div style={{ ...flexBetween, marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: colors.textDim }}>Usage</span>
                      <span style={{ fontSize: 12, color: colors.textMuted }}>{plan.current_usage}% / {plan.threshold}%</span>
                    </div>
                    <div style={{ height: 6, borderRadius: 3, background: colors.bgCard, overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: 3, transition: 'width 0.5s ease',
                        width: `${Math.min((plan.current_usage / plan.threshold) * 100, 100)}%`,
                        background: plan.current_usage > plan.threshold * 0.85 ? '#ef4444' : plan.current_usage > plan.threshold * 0.7 ? '#f59e0b' : '#10b981',
                      }} />
                    </div>
                  </div>
                  {plan.days_until_threshold > 0 && (
                    <div style={{ fontSize: 12, color: urgencyColor(plan.days_until_threshold * 24), marginTop: 6 }}>
                      {plan.days_until_threshold} days until threshold
                    </div>
                  )}
                  {plan.recommendation && (
                    <p style={{ fontSize: 12, color: colors.textSecondary, marginTop: 6, lineHeight: 1.5 }}>{plan.recommendation}</p>
                  )}
                </div>
              ))
            ) : (
              <div style={{ textAlign: 'center' as const, padding: 30 }}>
                <p style={{ color: colors.textMuted, fontSize: 13 }}>No active capacity plans</p>
              </div>
            )}
          </div>

          {/* Metric Forecasts */}
          <div style={card}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: '#06b6d4', marginBottom: 16 }}>Metric Forecasts</h3>
            {forecasts.length > 0 ? (
              forecasts.map((f, i) => (
                <div key={i} style={{ padding: 14, marginBottom: 8, borderRadius: 10, background: colors.bgElevated, border: `1px solid ${colors.borderLight}` }}>
                  <div style={flexBetween}>
                    <div>
                      <span style={{ fontSize: 14, fontWeight: 600, color: colors.text }}>{f.service_name}</span>
                      <span style={{ fontSize: 12, color: colors.textDim, marginLeft: 8 }}>{f.metric_name?.replace('_', ' ')}</span>
                    </div>
                    <span style={{ fontSize: 16, color: trendColor(f.trend), fontWeight: 700 }}>
                      {trendIcon(f.trend)}
                    </span>
                  </div>
                  <div style={{ ...flexGap(16), marginTop: 8 }}>
                    <div>
                      <span style={{ fontSize: 11, color: colors.textDim }}>Current</span>
                      <div style={{ fontSize: 16, fontWeight: 700, color: colors.text }}>{f.current_value}%</div>
                    </div>
                    <div style={{ fontSize: 18, color: colors.textDim }}>→</div>
                    <div>
                      <span style={{ fontSize: 11, color: colors.textDim }}>Predicted</span>
                      <div style={{ fontSize: 16, fontWeight: 700, color: trendColor(f.trend) }}>{f.predicted_value}%</div>
                    </div>
                    {f.confidence > 0 && (
                      <div style={{ marginLeft: 'auto' }}>
                        <span style={{ fontSize: 11, color: colors.textDim }}>Confidence</span>
                        <div style={{ fontSize: 14, fontWeight: 600, color: '#8b5cf6' }}>{f.confidence}%</div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ textAlign: 'center' as const, padding: 30 }}>
                <p style={{ color: colors.textMuted, fontSize: 13 }}>No forecasts available yet</p>
              </div>
            )}
          </div>
        </div>

        {/* Trends */}
        {trends.length > 0 && (
          <div style={card}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.text, marginBottom: 16 }}>Resource Trends</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' as const }}>
              <thead>
                <tr>
                  {['Service', 'Metric', 'Current', 'Trend', 'Growth/Day', 'Confidence'].map(h => (
                    <th key={h} style={{ textAlign: 'left' as const, padding: '10px 14px', fontSize: 11, fontWeight: 600, color: colors.textMuted, textTransform: 'uppercase' as const, letterSpacing: 1, borderBottom: `1px solid ${colors.border}` }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {trends.map((t: any, i: number) => (
                  <tr key={i}>
                    <td style={{ padding: '12px 14px', fontSize: 13, color: colors.text, borderBottom: `1px solid ${colors.borderLight}` }}>{t.service_name}</td>
                    <td style={{ padding: '12px 14px', fontSize: 13, color: colors.textSecondary, borderBottom: `1px solid ${colors.borderLight}` }}>{t.metric_name?.replace('_', ' ')}</td>
                    <td style={{ padding: '12px 14px', fontSize: 13, fontWeight: 600, color: colors.text, borderBottom: `1px solid ${colors.borderLight}` }}>{t.current_value}%</td>
                    <td style={{ padding: '12px 14px', borderBottom: `1px solid ${colors.borderLight}` }}>
                      <span style={{ color: trendColor(t.trend), fontWeight: 600 }}>{trendIcon(t.trend)} {t.trend}</span>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 13, color: colors.textMuted, borderBottom: `1px solid ${colors.borderLight}` }}>{t.growth_per_day || '—'}</td>
                    <td style={{ padding: '12px 14px', borderBottom: `1px solid ${colors.borderLight}` }}>
                      {t.confidence > 0 && <span style={{ fontSize: 12, color: '#8b5cf6' }}>{t.confidence}%</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center' as const, padding: 60 }}>
            <div style={{ fontSize: 36, marginBottom: 12, animation: 'pulse 2s infinite' }}>📈</div>
            <p style={{ color: colors.textMuted }}>Loading capacity data...</p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      `}</style>
    </div>
  );
}
