'use client';

import { useState } from 'react';

interface ActionLog {
  id: string;
  incident_id: string;
  action_name: string;
  action_type: string;
  executed_by: string;
  executed_at: string;
  duration_seconds: number;
  status: string;
  impact_score: number;
  rollback_performed: boolean;
  error_message: string | null;
}

interface RemediationCardProps {
  action: ActionLog;
  onRollback?: (actionId: string) => void;
}

export default function RemediationCard({ action, onRollback }: RemediationCardProps) {
  const [expanded, setExpanded] = useState(false);

  const statusColors: Record<string, string> = {
    success: 'bg-green-100 text-green-800',
    failure: 'bg-red-100 text-red-800',
    rollback: 'bg-orange-100 text-orange-800',
    in_progress: 'bg-blue-100 text-blue-800',
  };

  const impactColor = action.impact_score > 10
    ? 'text-green-600'
    : action.impact_score < -10
      ? 'text-red-600'
      : 'text-gray-600';

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${
            action.status === 'success' ? 'bg-green-500' :
            action.status === 'failure' ? 'bg-red-500' :
            action.status === 'rollback' ? 'bg-orange-500' :
            'bg-blue-500'
          }`} />
          <div>
            <h4 className="font-medium">{action.action_name.replace(/_/g, ' ')}</h4>
            <p className="text-sm text-gray-500">
              {new Date(action.executed_at).toLocaleString()} · {action.duration_seconds.toFixed(1)}s
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[action.status] || 'bg-gray-100'}`}>
            {action.status}
          </span>
          <span className={`text-sm font-medium ${impactColor}`}>
            Impact: {action.impact_score > 0 ? '+' : ''}{action.impact_score.toFixed(0)}
          </span>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {expanded ? 'Hide' : 'Details'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Executed by:</span>
              <span className="ml-2 font-medium">{action.executed_by}</span>
            </div>
            <div>
              <span className="text-gray-500">Type:</span>
              <span className="ml-2 font-medium">{action.action_type}</span>
            </div>
            <div>
              <span className="text-gray-500">Rollback:</span>
              <span className="ml-2 font-medium">{action.rollback_performed ? 'Yes' : 'No'}</span>
            </div>
            <div>
              <span className="text-gray-500">Incident:</span>
              <span className="ml-2 font-medium">{action.incident_id?.slice(0, 8) || 'N/A'}</span>
            </div>
          </div>
          {action.error_message && (
            <div className="mt-3 p-3 bg-red-50 rounded text-sm text-red-700">
              {action.error_message}
            </div>
          )}
          {action.status === 'success' && onRollback && (
            <button
              onClick={() => onRollback(action.id)}
              className="mt-3 px-3 py-1 bg-orange-100 text-orange-700 rounded text-sm hover:bg-orange-200"
            >
              Rollback Action
            </button>
          )}
        </div>
      )}
    </div>
  );
}
