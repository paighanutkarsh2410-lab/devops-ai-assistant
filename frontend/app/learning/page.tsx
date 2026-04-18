'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import { colors, card as cardStyle, btn, btnActive, th as thStyle, td as tdStyle } from '@/lib/theme';
import PatternInsights from '@/components/PatternInsights';
import { useBreakpoint } from '@/lib/useMediaQuery';

interface LearningStats {
  total_patterns_discovered: number;
  total_outcomes_tracked: number;
  total_learning_entries: number;
  overall_success_rate: number;
  avg_resolution_time_seconds: number;
  recommendation_accuracy: number;
  most_effective_action: string | null;
}

interface WeeklyReport {
  summary: {
    incidents_handled: number;
    successful_remediations: number;
    success_rate: number;
    new_patterns_discovered: number;
    top_performing_action: string | null;
  };
  action_breakdown: Array<{
    action_name: string;
    total: number;
    successes: number;
    success_rate: number;
    avg_duration: number;
  }>;
}

interface Insights {
  insights: string[];
  generated_at: string;
}

export default function LearningPage() {
  const router = useRouter();
  const { isMobile } = useBreakpoint();
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [weeklyReport, setWeeklyReport] = useState<WeeklyReport | null>(null);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'patterns' | 'insights'>('overview');

  useEffect(() => {
    const loadData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          router.push('/login');
          return;
        }

        const [statsRes, weeklyRes, insightsRes] = await Promise.all([
          api.get('/learning/stats'),
          api.get('/reports/learning/weekly'),
          api.get('/reports/learning/insights'),
        ]);
        setStats(statsRes.data);
        setWeeklyReport(weeklyRes.data);
        setInsights(insightsRes.data);
      } catch (error) {
        console.error('Failed to load learning data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [router]);

  if (loading) {
    return (
      <DashboardShell>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div style={{ fontSize: 18, color: colors.textMuted }}>Loading learning data...</div>
        </div>
      </DashboardShell>
    );
  }

  const rateColor = (rate: number) =>
    rate >= 80 ? colors.success : rate >= 50 ? colors.warning : colors.danger;

  const statItems = stats ? [
    { label: 'Patterns Discovered', value: stats.total_patterns_discovered, color: '#8b5cf6' },
    { label: 'Success Rate', value: `${stats.overall_success_rate}%`, color: rateColor(stats.overall_success_rate) },
    { label: 'Outcomes Tracked', value: stats.total_outcomes_tracked, color: colors.accent },
    {
      label: 'Avg Resolution',
      value: stats.avg_resolution_time_seconds < 60
        ? `${stats.avg_resolution_time_seconds.toFixed(0)}s`
        : `${(stats.avg_resolution_time_seconds / 60).toFixed(1)}m`,
      color: colors.text,
    },
  ] : [];

  const tabs: { key: typeof activeTab; label: string }[] = [
    { key: 'overview', label: 'Weekly Report' },
    { key: 'patterns', label: 'Patterns & Actions' },
    { key: 'insights', label: 'Insights' },
  ];

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1200, margin: '0 auto' }}>
        {/* Header */}
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 12 : 0, marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #10b981)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Learning Agent</h1>
            <p style={{ fontSize: 13, color: colors.textMuted }}>System intelligence and continuous improvement</p>
          </div>
          <button onClick={() => router.push('/dashboard')} style={btn}>
            Back to Dashboard
          </button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: 12, marginBottom: 28 }}>
            {statItems.map((s, i) => (
              <div key={i} style={{...cardStyle, position: 'relative', overflow: 'hidden', borderTop: '2px solid #10b981'}}>
                <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(16,185,129,0.15), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
                <div style={{ fontSize: 12, color: colors.textMuted, marginBottom: 4 }}>{s.label}</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="slide-up-d2" style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              style={activeTab === t.key ? btnActive : btn}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && weeklyReport && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Weekly Summary */}
            <div style={cardStyle}>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: colors.text }}>This Week</h3>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: 16 }}>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: colors.text }}>{weeklyReport.summary.incidents_handled}</div>
                  <div style={{ fontSize: 12, color: colors.textMuted }}>Incidents Handled</div>
                </div>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: colors.success }}>
                    {weeklyReport.summary.successful_remediations}
                  </div>
                  <div style={{ fontSize: 12, color: colors.textMuted }}>Successful Fixes</div>
                </div>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: colors.text }}>
                    {weeklyReport.summary.success_rate}%
                  </div>
                  <div style={{ fontSize: 12, color: colors.textMuted }}>Success Rate</div>
                </div>
                <div>
                  <div style={{ fontSize: 24, fontWeight: 700, color: '#8b5cf6' }}>
                    {weeklyReport.summary.new_patterns_discovered}
                  </div>
                  <div style={{ fontSize: 12, color: colors.textMuted }}>New Patterns</div>
                </div>
              </div>
              {weeklyReport.summary.top_performing_action && (
                <div style={{
                  marginTop: 16, padding: 12, background: colors.successBg,
                  borderRadius: 10, border: `1px solid ${colors.successBorder}`,
                }}>
                  <span style={{ fontSize: 13, color: colors.success }}>
                    Top performer: <strong>{weeklyReport.summary.top_performing_action}</strong>
                  </span>
                </div>
              )}
            </div>

            {/* Action Breakdown */}
            {weeklyReport.action_breakdown.length > 0 && (
              <div style={{ ...cardStyle, padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '16px 24px', borderBottom: `1px solid ${colors.border}` }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: colors.text, margin: 0 }}>Action Performance This Week</h3>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        <th style={thStyle}>Action</th>
                        <th style={thStyle}>Uses</th>
                        <th style={thStyle}>Successes</th>
                        <th style={thStyle}>Rate</th>
                        <th style={thStyle}>Avg Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {weeklyReport.action_breakdown.map((action) => (
                        <tr key={action.action_name}>
                          <td style={{ ...tdStyle, fontWeight: 500, color: colors.text }}>{action.action_name}</td>
                          <td style={tdStyle}>{action.total}</td>
                          <td style={tdStyle}>{action.successes}</td>
                          <td style={tdStyle}>
                            <span style={{ fontWeight: 500, color: rateColor(action.success_rate) }}>
                              {action.success_rate}%
                            </span>
                          </td>
                          <td style={tdStyle}>{action.avg_duration.toFixed(1)}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'patterns' && <PatternInsights />}

        {activeTab === 'insights' && insights && (
          <div style={cardStyle}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: colors.text }}>Learning Insights</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {insights.insights.length === 0 ? (
                <p style={{ color: colors.textMuted, fontSize: 13 }}>
                  No insights yet. The system learns from resolved incidents over time.
                </p>
              ) : (
                insights.insights.map((insight, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    padding: 12, background: colors.bgElevated, borderRadius: 10,
                  }}>
                    <span style={{ color: '#8b5cf6', marginTop: 1 }}>*</span>
                    <p style={{ fontSize: 13, color: colors.textSecondary, margin: 0 }}>{insight}</p>
                  </div>
                ))
              )}
            </div>
            <div style={{ marginTop: 16, fontSize: 11, color: colors.textDim }}>
              Generated: {new Date(insights.generated_at).toLocaleString()}
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
