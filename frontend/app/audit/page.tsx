'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { colors } from '@/lib/theme';
import DashboardShell from '@/components/DashboardShell';
import ActionLog from '@/components/ActionLog';
import ApprovalCard from '@/components/ApprovalCard';

interface Stats {
  total_actions: number;
  success_count: number;
  failure_count: number;
  rollback_count: number;
  success_rate: number;
  avg_duration: number;
  avg_impact: number;
}

interface Approval {
  id: string;
  incident_id: string;
  action_name: string;
  action_description: string | null;
  risk_level: string;
  requested_by: string;
  requested_at: string;
  status: string;
  approved_by: string | null;
  approved_at: string | null;
  expiry_minutes: number;
}

export default function AuditPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [activeTab, setActiveTab] = useState<'actions' | 'approvals'>('actions');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) { router.push('/login'); return; }
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsResp, approvalsResp] = await Promise.all([
        api.get('/audit/stats'),
        api.get('/approvals/', { params: { limit: 20 } }),
      ]);
      setStats(statsResp.data);
      setApprovals(approvalsResp.data);
    } catch (error) {
      console.error('Failed to load audit data:', error);
    }
  };

  const pendingCount = approvals.filter(a => a.status === 'pending').length;

  const statItems = stats ? [
    { label: 'Total Actions', value: stats.total_actions, color: colors.accent, icon: '📋' },
    { label: 'Success Rate', value: `${stats.success_rate}%`, color: colors.success, icon: '✅' },
    { label: 'Failures', value: stats.failure_count, color: colors.danger, icon: '❌' },
    { label: 'Rollbacks', value: stats.rollback_count, color: colors.warning, icon: '🔄' },
    { label: 'Avg Duration', value: `${stats.avg_duration}s`, color: '#8b5cf6', icon: '⏱️' },
  ] : [];

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #f59e0b)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Audit & Approvals</h1>
          <p style={{ fontSize: 13, color: colors.textMuted }}>Action history, approval workflows, and compliance tracking</p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 24 }}>
            {statItems.map(s => (
              <div key={s.label} style={{
                background: colors.bgCard, border: `1px solid ${colors.border}`,
                borderRadius: 14, padding: 18, borderTop: `2px solid ${s.color}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: 11, color: colors.textMuted, marginBottom: 6 }}>{s.label}</div>
                    <div style={{ fontSize: 26, fontWeight: 700, color: s.color }}>{s.value}</div>
                  </div>
                  <span style={{ fontSize: 20 }}>{s.icon}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div style={{
          display: 'flex', gap: 4, marginBottom: 24, padding: 4,
          background: 'rgba(255,255,255,0.02)', borderRadius: 10,
          border: `1px solid ${colors.border}`, width: 'fit-content',
        }}>
          {(['actions', 'approvals'] as const).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              padding: '8px 18px', borderRadius: 8, border: 'none',
              background: activeTab === tab ? colors.accentGradient : 'transparent',
              color: activeTab === tab ? '#fff' : colors.textMuted,
              cursor: 'pointer', fontSize: 13, fontWeight: activeTab === tab ? 600 : 400,
              position: 'relative',
            }}>
              {tab === 'actions' ? 'Action Log' : 'Approvals'}
              {tab === 'approvals' && pendingCount > 0 && (
                <span style={{
                  position: 'absolute', top: -4, right: -4,
                  width: 18, height: 18, borderRadius: '50%',
                  background: colors.danger, color: '#fff',
                  fontSize: 10, fontWeight: 700,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>{pendingCount}</span>
              )}
            </button>
          ))}
        </div>

        {activeTab === 'actions' ? (
          <ActionLog />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {approvals.length === 0 ? (
              <div style={{
                background: colors.bgCard, border: `1px solid ${colors.border}`,
                borderRadius: 14, padding: 48, textAlign: 'center', color: colors.textMuted,
              }}>
                No approval requests yet.
              </div>
            ) : (
              approvals.map((approval) => (
                <ApprovalCard key={approval.id} approval={approval} onAction={loadData} />
              ))
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
