'use client';

import { api } from '@/lib/api';

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

interface ApprovalCardProps {
  approval: Approval;
  onAction: () => void;
}

export default function ApprovalCard({ approval, onAction }: ApprovalCardProps) {
  const riskColors: Record<string, string> = {
    LOW: 'bg-green-100 text-green-800',
    MEDIUM: 'bg-yellow-100 text-yellow-800',
    HIGH: 'bg-red-100 text-red-800',
  };

  const handleApprove = async () => {
    try {
      await api.post(`/approvals/${approval.id}/approve`, {});
      onAction();
    } catch (error) {
      console.error('Approve failed:', error);
    }
  };

  const handleReject = async () => {
    try {
      await api.post(`/approvals/${approval.id}/reject`, {});
      onAction();
    } catch (error) {
      console.error('Reject failed:', error);
    }
  };

  const isPending = approval.status === 'pending';
  const requestedAt = new Date(approval.requested_at);
  const expiresAt = new Date(requestedAt.getTime() + approval.expiry_minutes * 60000);
  const isExpired = new Date() > expiresAt;

  return (
    <div className={`bg-white rounded-lg shadow border-l-4 p-4 ${
      isPending ? 'border-l-yellow-500' :
      approval.status === 'approved' ? 'border-l-green-500' :
      'border-l-red-500'
    }`}>
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-medium">{approval.action_name.replace(/_/g, ' ')}</h4>
          {approval.action_description && (
            <p className="text-sm text-gray-500 mt-1">{approval.action_description}</p>
          )}
          <div className="flex items-center gap-3 mt-2">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${riskColors[approval.risk_level] || 'bg-gray-100'}`}>
              {approval.risk_level} RISK
            </span>
            <span className="text-xs text-gray-500">
              Incident: {approval.incident_id.slice(0, 8)}
            </span>
            <span className="text-xs text-gray-500">
              Requested: {requestedAt.toLocaleTimeString()}
            </span>
          </div>
        </div>

        {isPending && !isExpired ? (
          <div className="flex gap-2">
            <button
              onClick={handleApprove}
              className="px-4 py-2 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700"
            >
              Approve
            </button>
            <button
              onClick={handleReject}
              className="px-4 py-2 bg-red-100 text-red-700 rounded text-sm font-medium hover:bg-red-200"
            >
              Reject
            </button>
          </div>
        ) : (
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            approval.status === 'approved' ? 'bg-green-100 text-green-800' :
            approval.status === 'rejected' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {isExpired && isPending ? 'Expired' : approval.status}
          </span>
        )}
      </div>
    </div>
  );
}
