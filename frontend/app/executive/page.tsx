'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { colors } from '@/lib/theme';
import DashboardShell from '@/components/DashboardShell';
import MetricCard from '@/components/MetricCard';
import HealthScore from '@/components/HealthScore';
import TrendChart from '@/components/TrendChart';
import { useBreakpoint } from '@/lib/useMediaQuery';

export default function ExecutivePage() {
  const { isMobile } = useBreakpoint();
  const [analytics, setAnalytics] = useState<Record<string, unknown> | null>(null);
  const [roi, setRoi] = useState<Record<string, unknown> | null>(null);
  const [trends, setTrends] = useState<Record<string, unknown> | null>(null);
  const [slaStatus, setSlaStatus] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [analyticsRes, roiRes, trendsRes, slaRes] = await Promise.all([
        api.get('/analytics/dashboard?days=30'),
        api.get('/costs/roi?days=30'),
        api.get('/trends/summary?days=30'),
        api.get('/sla/status?days=30').catch(() => ({ data: [] })),
      ]);
      setAnalytics(analyticsRes.data);
      setRoi(roiRes.data);
      setTrends(trendsRes.data);
      setSlaStatus(slaRes.data);
    } catch { /* empty */ }
    setLoading(false);
  };

  if (loading) {
    return (
      <DashboardShell>
        <div style={{ padding: 32, color: colors.textMuted, fontSize: 14 }}>Loading executive dashboard...</div>
      </DashboardShell>
    );
  }

  const mttr = (analytics as Record<string, Record<string, number>>)?.mttr;
  const effectiveness = (analytics as Record<string, Record<string, number>>)?.effectiveness;
  const freq = (analytics as Record<string, Record<string, unknown>>)?.frequency;
  const reliability = (analytics as Record<string, Record<string, Record<string, number>>>)?.reliability || {};

  const resRate = effectiveness?.resolution_rate || 0;
  const autoRate = effectiveness?.auto_remediation_rate || 0;
  const predRate = effectiveness?.prediction_prevention_rate || 0;
  const overallScore = Math.round((resRate * 0.3 + autoRate * 0.3 + predRate * 0.2 + Math.min(100, (roi as Record<string, number>)?.roi_percent || 0) * 0.2));
  const slasMet = slaStatus.filter(s => (s as Record<string, boolean>).sla_met).length;
  const slasTotal = slaStatus.length;

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Executive Dashboard</h1>
          <p style={{ fontSize: 13, color: colors.textMuted }}>System health, business impact, and ROI — last 30 days</p>
        </div>

        {/* Health Scores */}
        <div className="slide-up-d1" style={{
          background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14,
          padding: isMobile ? 16 : 24, marginBottom: 24, display: 'flex', justifyContent: 'space-around', alignItems: 'center', flexWrap: 'wrap' as const, gap: isMobile ? 16 : 0,
          position: 'relative', overflow: 'hidden',
        }}>
          <div style={{ position: 'absolute', top: -30, left: '50%', transform: 'translateX(-50%)', width: 200, height: 60, background: 'radial-gradient(circle, rgba(139,92,246,0.12), transparent)', filter: 'blur(20px)', animation: 'breathe 4s ease-in-out infinite' }} />
          <HealthScore score={overallScore} label="Overall Health" size={140} />
          <HealthScore score={Math.round(resRate)} label="Resolution Rate" />
          <HealthScore score={Math.round(autoRate)} label="Automation" />
          <HealthScore score={Math.round(predRate)} label="Prevention" />
          <HealthScore score={slasTotal > 0 ? Math.round(slasMet / slasTotal * 100) : 100} label="SLA Compliance" />
        </div>

        {/* Key Metrics */}
        <div className="slide-up-d2" style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(5, 1fr)', gap: 12, marginBottom: 24 }}>
          <MetricCard title="Total Incidents" value={effectiveness?.total_incidents || 0} subtitle="last 30 days"
            trend={(freq?.trend as string) === 'decreasing' ? 'up' : (freq?.trend as string) === 'increasing' ? 'down' : 'stable'}
            trendValue={`${freq?.trend_pct || 0}%`} icon="📋" />
          <MetricCard title="MTTR" value={`${mttr?.mttr_minutes?.toFixed(1) || 0}m`}
            subtitle={`${mttr?.count || 0} resolved`} color="#2563eb" icon="⏱" />
          <MetricCard title="Auto-Resolved" value={`${autoRate.toFixed(0)}%`}
            subtitle={`${effectiveness?.auto_resolved || 0} incidents`} color="#16a34a" icon="🤖" />
          <MetricCard title="Total Savings" value={`$${((roi as Record<string, number>)?.total_savings || 0).toFixed(0)}`}
            subtitle={`ROI: ${((roi as Record<string, number>)?.roi_percent || 0).toFixed(0)}%`} color="#16a34a" trend="up" icon="💰" />
          <MetricCard title="Hours Saved" value={`${(roi as Record<string, number>)?.engineer_hours_saved || 0}h`}
            subtitle="engineer time" color="#8b5cf6" icon="⚡" />
        </div>

        {/* Charts */}
        <div className="slide-up-d3" style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 14, marginBottom: 24 }}>
          <TrendChart data={((trends as Record<string, number[]>)?.daily_counts) || []}
            title="Incident Trend (30d)" color="#3b82f6" height={180} trend={(trends as Record<string, string>)?.trend} />
          <div style={{ background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14, padding: 20 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: colors.text, marginBottom: 14 }}>Service Reliability</h3>
            {Object.keys(reliability).length === 0 ? (
              <p style={{ color: colors.textMuted, fontSize: 13, textAlign: 'center', padding: '40px 0' }}>No service data yet</p>
            ) : (
              Object.entries(reliability).map(([svc, data]) => {
                const score = data.score as number;
                const gradeColor = score >= 90 ? colors.success : score >= 75 ? colors.accent : score >= 60 ? colors.warning : colors.danger;
                return (
                  <div key={svc} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                    <span style={{
                      width: 24, height: 24, borderRadius: 6, display: 'flex',
                      alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 12,
                      background: gradeColor + '20', color: gradeColor,
                    }}>{data.grade}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                        <span style={{ fontWeight: 500, color: colors.text }}>{svc}</span>
                        <span style={{ color: colors.textDim }}>{score}/100</span>
                      </div>
                      <div style={{ height: 4, background: colors.bgElevated, borderRadius: 2, marginTop: 3 }}>
                        <div style={{ height: '100%', borderRadius: 2, background: gradeColor, width: `${score}%` }} />
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* SLA + Business Impact */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 14 }}>
          <div style={{ background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14, padding: 20 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: colors.text, marginBottom: 14 }}>SLA Status</h3>
            {slaStatus.length === 0 ? (
              <p style={{ color: colors.textMuted, fontSize: 13, textAlign: 'center', padding: '20px 0' }}>No SLA targets configured</p>
            ) : (
              slaStatus.map((s, i) => {
                const sla = s as Record<string, unknown>;
                const met = sla.sla_met as boolean;
                return (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '10px 0', borderBottom: `1px solid ${colors.border}`,
                  }}>
                    <div>
                      <span style={{ fontWeight: 500, fontSize: 13, color: colors.text }}>{sla.service_name as string}</span>
                      <div style={{ fontSize: 11, color: colors.textDim }}>{(sla.uptime_percent as number)?.toFixed(3)}% uptime</div>
                    </div>
                    <span style={{
                      padding: '3px 10px', borderRadius: 10, fontSize: 11, fontWeight: 600,
                      background: met ? colors.successBg : colors.dangerBg,
                      color: met ? colors.success : colors.danger,
                    }}>{met ? 'Met' : 'Breached'}</span>
                  </div>
                );
              })
            )}
          </div>

          <div style={{ background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14, padding: 20 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: colors.text, marginBottom: 14 }}>Business Impact</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: 'Engineer Cost Saved', value: `$${((roi as Record<string, number>)?.engineer_cost_saved || 0).toFixed(0)}`, color: colors.success },
                { label: 'Downtime Cost Saved', value: `$${((roi as Record<string, number>)?.downtime_cost_saved || 0).toFixed(0)}`, color: colors.accent },
                { label: 'Auto-Resolved', value: (roi as Record<string, number>)?.auto_resolved || 0, color: '#8b5cf6' },
                { label: 'Incidents Prevented', value: (roi as Record<string, number>)?.incidents_prevented || 0, color: colors.warning },
              ].map(item => (
                <div key={item.label} style={{
                  padding: 14, background: item.color + '10', borderRadius: 10, textAlign: 'center',
                  border: `1px solid ${item.color}20`,
                }}>
                  <div style={{ fontSize: 22, fontWeight: 700, color: item.color }}>{item.value}</div>
                  <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 4 }}>{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
