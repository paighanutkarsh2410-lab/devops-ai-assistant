'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import { colors, card as cardStyle, btn, btnActive } from '@/lib/theme';
import TrendChart from '@/components/TrendChart';

export default function AnalyticsPage() {
  const router = useRouter();
  const [days, setDays] = useState(30);
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);
  const [dashboard, setDashboard] = useState<Record<string, unknown> | null>(null);
  const [trends, setTrends] = useState<Record<string, unknown> | null>(null);
  const [severityTrends, setSeverityTrends] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [days]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dashRes, trendRes, sevRes] = await Promise.all([
        api.get(`/analytics/dashboard?days=${days}`),
        api.get(`/trends/summary?days=${days}`),
        api.get(`/trends/severity?days=${days}`),
      ]);
      setDashboard(dashRes.data);
      setTrends(trendRes.data);
      setSeverityTrends(sevRes.data);
    } catch { /* empty */ }
    setLoading(false);
  };

  const mttr = (dashboard as Record<string, Record<string, unknown>>)?.mttr;
  const mttd = (dashboard as Record<string, Record<string, unknown>>)?.mttd;
  const freq = (dashboard as Record<string, Record<string, unknown>>)?.frequency;
  const effectiveness = (dashboard as Record<string, Record<string, unknown>>)?.effectiveness;
  const costImpact = (dashboard as Record<string, Record<string, unknown>>)?.cost_impact;

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
        {/* Header */}
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Analytics</h1>
            <p style={{ fontSize: 13, color: colors.textMuted }}>MTTR, MTTD, reliability scores, and trend analysis</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {[7, 14, 30, 90].map(d => (
              <button key={d} onClick={() => setDays(d)} style={days === d ? btnActive : btn}>
                {d}d
              </button>
            ))}
            <button onClick={() => router.push('/reports')} style={btn}>
              Reports
            </button>
            <button onClick={() => router.push('/dashboard')} style={btn}>
              Dashboard
            </button>
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 60, color: colors.textMuted }}>Loading analytics...</div>
        ) : (
          <>
            {/* Key Metrics Row */}
            <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 24 }}>
              {[
                { label: 'MTTR', value: `${(mttr?.mttr_minutes as number)?.toFixed?.(1) || '0'}m`, sub: `${(mttr?.count as number) || 0} resolved`, color: '#3b82f6' },
                { label: 'MTTD', value: `${(mttd?.mttd_minutes as number)?.toFixed?.(1) || '0'}m`, sub: `${(mttd?.count as number) || 0} detected`, color: '#8b5cf6' },
                { label: 'Incidents/Day', value: `${(freq?.avg_per_day as number) || 0}`, sub: `${(freq?.trend as string) || 'stable'} (${(freq?.trend_pct as number) || 0}%)`, color: freq?.trend === 'increasing' ? colors.danger : colors.success },
                { label: 'Auto-Remediation', value: `${(effectiveness?.auto_remediation_rate as number)?.toFixed?.(1) || '0'}%`, sub: `${(effectiveness?.auto_resolved as number) || 0} auto-resolved`, color: colors.success },
                { label: 'Cost Saved', value: `$${(costImpact?.total_savings_usd as number)?.toFixed?.(0) || '0'}`, sub: `${(costImpact?.engineer_hours_saved as number) || 0}h saved`, color: colors.accent },
              ].map((m, i) => (
                <div key={i}
                  onMouseEnter={() => setHoveredCard(i)} onMouseLeave={() => setHoveredCard(null)}
                  style={{
                    ...cardStyle, position: 'relative', overflow: 'hidden',
                    borderTop: `2px solid ${m.color}`,
                    transform: hoveredCard === i ? 'translateY(-3px)' : 'none',
                    boxShadow: hoveredCard === i ? `0 8px 32px ${m.color}15` : 'none',
                    transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
                  }}>
                  <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: `radial-gradient(circle, ${m.color}18, transparent)`, filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite', animationDelay: `${i * 0.5}s` }} />
                  <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 4, position: 'relative', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600 }}>{m.label}</div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: m.color, position: 'relative', textShadow: `0 0 20px ${m.color}25` }}>{m.value}</div>
                  <div style={{ fontSize: 11, color: colors.textMuted, position: 'relative' }}>{m.sub}</div>
                </div>
              ))}
            </div>

            {/* Trend Charts */}
            <div className="slide-up-d2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 24 }}>
              <TrendChart
                data={(trends as Record<string, number[]>)?.daily_counts || []}
                title="Incident Frequency"
                color="#3b82f6"
                trend={(trends as Record<string, string>)?.trend}
              />
              <TrendChart
                data={Object.values(
                  ((severityTrends as Record<string, Record<string, Record<string, number>>>)?.severity_trends) || {}
                ).map((s) => s.total || 0)}
                labels={['Critical', 'High', 'Medium', 'Low']}
                title="By Severity"
                color="#f59e0b"
                showArea={false}
              />
            </div>

            {/* Root Cause & Reliability */}
            <div className="slide-up-d3" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 24 }}>
              {/* Root causes */}
              <div style={cardStyle}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: colors.text }}>Root Cause Distribution</h3>
                {((dashboard as Record<string, Record<string, unknown[]>>)?.root_causes?.distribution || []).map((item: unknown, i: number) => {
                  const rc = item as { cause: string; count: number; percentage: number };
                  return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                          <span style={{ color: colors.textSecondary }}>{rc.cause}</span>
                          <span style={{ color: colors.textMuted }}>{rc.count} ({rc.percentage}%)</span>
                        </div>
                        <div style={{ height: 6, background: colors.bgElevated, borderRadius: 3 }}>
                          <div style={{
                            height: '100%', borderRadius: 3, background: colors.accent,
                            width: `${rc.percentage}%`, transition: 'width 0.5s',
                          }} />
                        </div>
                      </div>
                    </div>
                  );
                })}
                {((dashboard as Record<string, Record<string, unknown[]>>)?.root_causes?.distribution || []).length === 0 && (
                  <p style={{ color: colors.textMuted, fontSize: 13 }}>No root cause data yet</p>
                )}
              </div>

              {/* Service Reliability */}
              <div style={cardStyle}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: colors.text }}>Service Reliability</h3>
                {Object.entries((dashboard as Record<string, Record<string, Record<string, unknown>>>)?.reliability || {}).map(([svc, data]) => {
                  const score = data.score as number;
                  const grade = data.grade as string;
                  const gradeColor = grade === 'A' ? colors.success : grade === 'B' ? colors.accent : grade === 'C' ? colors.warning : colors.danger;
                  return (
                    <div key={svc} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                      <span style={{
                        width: 28, height: 28, borderRadius: 6, display: 'flex',
                        alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 14,
                        background: gradeColor + '15', color: gradeColor,
                      }}>
                        {grade}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                          <span style={{ fontWeight: 500, color: colors.textSecondary }}>{svc}</span>
                          <span style={{ color: colors.textMuted }}>{score}/100</span>
                        </div>
                        <div style={{ height: 6, background: colors.bgElevated, borderRadius: 3 }}>
                          <div style={{
                            height: '100%', borderRadius: 3, background: gradeColor,
                            width: `${score}%`, transition: 'width 0.5s',
                          }} />
                        </div>
                      </div>
                    </div>
                  );
                })}
                {Object.keys((dashboard as Record<string, Record<string, unknown>>)?.reliability || {}).length === 0 && (
                  <p style={{ color: colors.textMuted, fontSize: 13 }}>No service data yet</p>
                )}
              </div>
            </div>

            {/* Effectiveness */}
            <div className="slide-up-d4" style={{...cardStyle, position: 'relative', overflow: 'hidden'}}>
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: colors.text }}>Automation Effectiveness</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                {[
                  { label: 'Resolution Rate', value: `${(effectiveness?.resolution_rate as number)?.toFixed(1) || 0}%`, color: colors.success },
                  { label: 'Auto-Remediation', value: `${(effectiveness?.auto_remediation_rate as number)?.toFixed(1) || 0}%`, color: colors.accent },
                  { label: 'Prediction Prevention', value: `${(effectiveness?.prediction_prevention_rate as number)?.toFixed(1) || 0}%`, color: '#8b5cf6' },
                  { label: 'Action Success', value: `${(effectiveness?.action_success_rate as number)?.toFixed(1) || 0}%`, color: colors.warning },
                ].map((m, i) => (
                  <div key={i} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 28, fontWeight: 700, color: m.color }}>{m.value}</div>
                    <div style={{ fontSize: 11, color: colors.textMuted }}>{m.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
