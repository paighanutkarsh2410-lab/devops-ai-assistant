'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
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
    if (!token) {
      router.push('/login');
      return;
    }
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

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Audit & Approvals</h1>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            Back to Dashboard
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Total Actions</div>
              <div className="text-2xl font-bold">{stats.total_actions}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Success Rate</div>
              <div className="text-2xl font-bold text-green-600">{stats.success_rate}%</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Failures</div>
              <div className="text-2xl font-bold text-red-600">{stats.failure_count}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Rollbacks</div>
              <div className="text-2xl font-bold text-orange-600">{stats.rollback_count}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Avg Duration</div>
              <div className="text-2xl font-bold">{stats.avg_duration}s</div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('actions')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'actions' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Action Log
          </button>
          <button
            onClick={() => setActiveTab('approvals')}
            className={`px-4 py-2 rounded-lg font-medium relative ${
              activeTab === 'approvals' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
          >
            Approvals
            {pendingCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                {pendingCount}
              </span>
            )}
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'actions' ? (
          <ActionLog />
        ) : (
          <div className="space-y-4">
            {approvals.length === 0 ? (
              <div className="bg-white rounded-lg shadow px-6 py-8 text-center text-gray-500">
                No approval requests yet.
              </div>
            ) : (
              approvals.map((approval) => (
                <ApprovalCard
                  key={approval.id}
                  approval={approval}
                  onAction={loadData}
                />
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
}
