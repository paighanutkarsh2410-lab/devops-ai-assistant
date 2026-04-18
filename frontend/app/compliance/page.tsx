'use client';

import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function authHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const STATUS_COLORS: Record<string, string> = {
  compliant: '#10b981', partial: '#f59e0b', non_compliant: '#ef4444', not_applicable: '#64748b',
};

function Card({ title, children, style }: { title: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{
      background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`,
      overflow: 'hidden', ...style,
    }}>
      <div style={{
        padding: '14px 20px', borderBottom: `1px solid ${colors.border}`,
        fontSize: 14, fontWeight: 600, color: colors.text,
      }}>{title}</div>
      <div style={{ padding: 20 }}>{children}</div>
    </div>
  );
}

export default function CompliancePage() {
  const { isMobile } = useBreakpoint();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeStandard, setActiveStandard] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/compliance/status`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <DashboardShell>
      <div style={{ padding: 32, color: colors.textMuted }}>Loading compliance data...</div>
    </DashboardShell>
  );
  if (!data) return (
    <DashboardShell>
      <div style={{ padding: 32, color: colors.textMuted }}>No compliance data available</div>
    </DashboardShell>
  );

  const standards = data.standards || {};
  const gaps = data.gaps || [];
  const checks = data.checks || [];
  const filteredChecks = activeStandard
    ? checks.filter((c: any) => c.standard === activeStandard)
    : checks;

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1400, margin: '0 auto' }}>
        <div style={{ marginBottom: 28 }} className="slide-up">
          <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: '0 0 6px', background: 'linear-gradient(135deg, #f0f0f0, #10b981)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Compliance Dashboard</h1>
          <p style={{ color: colors.textMuted, fontSize: 14 }}>
            Security standards compliance status and gap analysis
          </p>
        </div>

        {/* Overall Score */}
        <div className="slide-up-d1" style={{
          background: colors.bgCard, borderRadius: 14, border: `1px solid ${colors.border}`,
          padding: 24, marginBottom: 24, textAlign: 'center', position: 'relative', overflow: 'hidden',
          borderTop: '2px solid #10b981',
        }}>
          <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(16,185,129,0.18), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
          <div style={{ fontSize: 48, fontWeight: 700, color: data.overall_score >= 90 ? colors.success : colors.warning }}>
            {data.overall_score}%
          </div>
          <div style={{ fontSize: 14, color: colors.textSecondary }}>Overall Compliance Score</div>
          <div style={{ fontSize: 12, color: colors.textMuted, marginTop: 4 }}>{data.total_controls} controls assessed</div>
        </div>

        {/* Standards Grid */}
        <div className="slide-up-d2" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 16, marginBottom: 24 }}>
          {Object.entries(standards).map(([name, info]: [string, any]) => (
            <button key={name} onClick={() => setActiveStandard(activeStandard === name ? null : name)} style={{
              background: activeStandard === name ? colors.bgCardHover : colors.bgCard,
              borderRadius: 14, border: `1px solid ${activeStandard === name ? colors.accent : colors.border}`,
              padding: 20, cursor: 'pointer', textAlign: 'left',
            }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: colors.text, marginBottom: 8 }}>{name}</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: info.score >= 90 ? colors.success : info.score >= 70 ? colors.warning : colors.danger }}>
                {info.score}%
              </div>
              <div style={{ display: 'flex', gap: 12, marginTop: 10, fontSize: 11 }}>
                <span style={{ color: colors.success }}>{info.compliant} pass</span>
                <span style={{ color: colors.warning }}>{info.partial} partial</span>
                <span style={{ color: colors.danger }}>{info.non_compliant} fail</span>
              </div>
            </button>
          ))}
        </div>

        {/* Gaps */}
        {gaps.length > 0 && (
          <Card title={`Compliance Gaps (${gaps.length})`} style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {gaps.map((gap: any, i: number) => (
                <div key={i} style={{
                  padding: 12, borderRadius: 8, background: colors.bgElevated,
                  borderLeft: `3px solid ${gap.status === 'non_compliant' ? colors.danger : colors.warning}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontSize: 12, color: '#60a5fa', fontWeight: 600 }}>[{gap.standard}] {gap.control}</span>
                      <div style={{ fontSize: 13, color: colors.text, marginTop: 2 }}>{gap.title}</div>
                    </div>
                    <span style={{
                      padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                      background: (STATUS_COLORS[gap.status] || '#64748b') + '20',
                      color: STATUS_COLORS[gap.status] || '#64748b',
                    }}>{gap.status.replace('_', ' ')}</span>
                  </div>
                  {gap.remediation && (
                    <div style={{ fontSize: 11, color: colors.textSecondary, marginTop: 6 }}>
                      Remediation: {gap.remediation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Controls Detail */}
        <div className="slide-up-d3">
        <Card title={`Controls ${activeStandard ? `- ${activeStandard}` : '(All)'} (${filteredChecks.length})`}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {filteredChecks.map((check: any, i: number) => (
              <div key={i} style={{
                padding: 10, borderRadius: 6, background: colors.bgElevated,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 11, color: '#60a5fa', fontWeight: 600, minWidth: 60 }}>{check.control_id}</span>
                    <span style={{ fontSize: 12, color: colors.text }}>{check.title}</span>
                  </div>
                  {check.evidence && (
                    <div style={{ fontSize: 10, color: colors.textMuted, marginTop: 2, marginLeft: 68 }}>{check.evidence.slice(0, 100)}</div>
                  )}
                </div>
                <span style={{
                  padding: '3px 10px', borderRadius: 6, fontSize: 10, fontWeight: 600, whiteSpace: 'nowrap',
                  background: (STATUS_COLORS[check.status] || '#64748b') + '20',
                  color: STATUS_COLORS[check.status] || '#64748b',
                }}>{check.status.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
