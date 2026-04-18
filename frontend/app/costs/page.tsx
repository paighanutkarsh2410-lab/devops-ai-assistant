'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { colors } from '@/lib/theme';
import DashboardShell from '@/components/DashboardShell';
import TrendChart from '@/components/TrendChart';
import { useBreakpoint } from '@/lib/useMediaQuery';

interface ROI {
  incidents_total: number;
  auto_resolved: number;
  engineer_hours_saved: number;
  engineer_cost_saved: number;
  incidents_prevented: number;
  downtime_cost_saved: number;
  total_savings: number;
  platform_cost: number;
  roi_percent: number;
}

interface Optimization {
  type: string;
  service: string;
  title: string;
  description: string;
  impact: string;
  potential_savings: number;
}

export default function CostsPage() {
  const router = useRouter();
  const { isMobile } = useBreakpoint();
  const [roi, setRoi] = useState<ROI | null>(null);
  const [serviceCosts, setServiceCosts] = useState<Record<string, Record<string, unknown>>>({});
  const [costTrend, setCostTrend] = useState<{ week: string; net_cost: number; automation_savings: number }[]>([]);
  const [optimizations, setOptimizations] = useState<Optimization[]>([]);
  const [totalPotential, setTotalPotential] = useState(0);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [days]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [roiRes, svcRes, trendRes, optRes] = await Promise.all([
        api.get(`/costs/roi?days=${days}`),
        api.get(`/costs/by-service?days=${days}`),
        api.get(`/costs/trend?days=${Math.max(days, 30)}`),
        api.get(`/costs/optimizations?days=${days}`),
      ]);
      setRoi(roiRes.data);
      setServiceCosts(svcRes.data.services || {});
      setCostTrend(trendRes.data.weekly_costs || []);
      setOptimizations(optRes.data.recommendations || []);
      setTotalPotential(optRes.data.total_potential_savings || 0);
    } catch { /* empty */ }
    setLoading(false);
  };

  const impactColor = (impact: string) =>
    impact === 'high' ? colors.danger : impact === 'medium' ? colors.warning : colors.textMuted;

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 12 : 0, marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #f59e0b)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Cost Analytics</h1>
            <p style={{ fontSize: 13, color: colors.textMuted }}>ROI tracking, cost allocation, and optimization</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {[7, 30, 90].map(d => (
              <button key={d} onClick={() => setDays(d)} style={{
                padding: '6px 14px', borderRadius: 8, fontSize: 12, cursor: 'pointer',
                border: 'none',
                background: days === d ? colors.accentGradient : colors.bgElevated,
                color: days === d ? '#fff' : colors.textMuted, fontWeight: days === d ? 600 : 400,
              }}>{d}d</button>
            ))}
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 60, color: colors.textMuted }}>Loading cost data...</div>
        ) : (
          <>
            {/* ROI Summary */}
            <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
              {[
                { label: 'Total Savings', value: `$${roi?.total_savings?.toFixed(0) || 0}`, sub: `${days} day period`, color: colors.success },
                { label: 'ROI', value: `${roi?.roi_percent?.toFixed(0) || 0}%`, sub: `vs $${roi?.platform_cost || 0}/mo`, color: (roi?.roi_percent || 0) > 0 ? colors.success : colors.danger },
                { label: 'Hours Saved', value: `${roi?.engineer_hours_saved || 0}h`, sub: `$${roi?.engineer_cost_saved?.toFixed(0) || 0} cost`, color: '#8b5cf6' },
                { label: 'Downtime Prevented', value: `$${roi?.downtime_cost_saved?.toFixed(0) || 0}`, sub: `${roi?.incidents_prevented || 0} incidents`, color: colors.warning },
              ].map(s => (
                <div key={s.label} style={{
                  background: colors.bgCard, border: `1px solid ${colors.border}`,
                  borderRadius: 14, padding: 20, borderTop: `2px solid ${s.color}`,
                  position: 'relative', overflow: 'hidden',
                }}>
                  <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: `radial-gradient(circle, ${s.color}18, transparent)`, filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
                  <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 6 }}>{s.label}</div>
                  <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
                  <div style={{ fontSize: 11, color: colors.textDim, marginTop: 4 }}>{s.sub}</div>
                </div>
              ))}
            </div>

            {/* Cost Trend */}
            <div className="slide-up-d2" style={{ marginBottom: 24 }}>
              <TrendChart data={costTrend.map(w => w.net_cost)} labels={costTrend.map(w => w.week)} title="Weekly Net Cost" color="#dc2626" height={180} />
            </div>

            <div className="slide-up-d3" style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 14, marginBottom: 24 }}>
              {/* Cost by service */}
              <div style={{ background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14, padding: 20 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: colors.text, marginBottom: 14 }}>Cost by Service</h3>
                {Object.entries(serviceCosts).length === 0 ? (
                  <p style={{ color: colors.textMuted, fontSize: 13 }}>No service cost data yet</p>
                ) : (
                  Object.entries(serviceCosts).map(([svc, data]) => (
                    <div key={svc} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: `1px solid ${colors.border}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontWeight: 500, fontSize: 13, color: colors.text }}>{svc}</span>
                        <span style={{ fontSize: 13, fontWeight: 600, color: colors.danger }}>${(data.total_cost as number)?.toFixed(0) || 0}</span>
                      </div>
                      <div style={{ display: 'flex', gap: 12, fontSize: 11, color: colors.textDim }}>
                        <span>{data.incidents as number} incidents</span>
                        <span>{(data.downtime_hours as number)?.toFixed(1)}h downtime</span>
                        <span style={{ color: colors.success }}>-${(data.automation_savings as number)?.toFixed(0)} saved</span>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Optimizations */}
              <div style={{ background: colors.bgCard, border: `1px solid ${colors.border}`, borderRadius: 14, padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: colors.text }}>Optimization Opportunities</h3>
                  <span style={{ fontSize: 12, color: colors.success, fontWeight: 600 }}>${totalPotential.toFixed(0)} potential</span>
                </div>
                {optimizations.length === 0 ? (
                  <p style={{ color: colors.textMuted, fontSize: 13 }}>No optimizations identified</p>
                ) : (
                  optimizations.map((opt, i) => (
                    <div key={i} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: `1px solid ${colors.border}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 4 }}>
                        <span style={{ fontWeight: 500, fontSize: 13, color: colors.text }}>{opt.title}</span>
                        <span style={{
                          padding: '2px 8px', borderRadius: 10, fontSize: 10, fontWeight: 600,
                          background: impactColor(opt.impact) + '20', color: impactColor(opt.impact),
                        }}>{opt.impact}</span>
                      </div>
                      <p style={{ fontSize: 12, color: colors.textMuted, marginBottom: 4 }}>{opt.description}</p>
                      <span style={{ fontSize: 11, color: colors.success, fontWeight: 600 }}>Potential: ${opt.potential_savings.toFixed(0)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
