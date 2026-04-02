'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface ActionEntry {
  id: string;
  incident_id: string | null;
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

export default function ActionLog() {
  const [actions, setActions] = useState<ActionEntry[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActions();
  }, [filter]);

  const loadActions = async () => {
    try {
      const params: Record<string, string> = {};
      if (filter !== 'all') params.status = filter;
      const resp = await api.get('/audit/actions', { params });
      setActions(resp.data);
    } catch (error) {
      console.error('Failed to load actions:', error);
    } finally {
      setLoading(false);
    }
  };

  const statusColors: Record<string, string> = {
    success: 'text-green-600',
    failure: 'text-red-600',
    rollback: 'text-orange-600',
    in_progress: 'text-blue-600',
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b flex items-center justify-between">
        <h3 className="text-lg font-semibold">Action Log</h3>
        <div className="flex gap-2">
          {['all', 'success', 'failure', 'rollback'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded text-sm ${
                filter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="px-6 py-8 text-center text-gray-500">Loading...</div>
      ) : actions.length === 0 ? (
        <div className="px-6 py-8 text-center text-gray-500">No actions recorded yet.</div>
      ) : (
        <div className="divide-y">
          {actions.map((action) => (
            <div key={action.id} className="px-6 py-3 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`font-medium ${statusColors[action.status] || 'text-gray-600'}`}>
                    {action.status === 'success' ? '✓' : action.status === 'failure' ? '✗' : '↺'}
                  </span>
                  <div>
                    <span className="font-medium">{action.action_name.replace(/_/g, ' ')}</span>
                    <span className="text-sm text-gray-500 ml-2">by {action.executed_by}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-gray-500">{action.duration_seconds.toFixed(1)}s</span>
                  <span className={action.impact_score > 0 ? 'text-green-600' : action.impact_score < 0 ? 'text-red-600' : 'text-gray-500'}>
                    {action.impact_score > 0 ? '+' : ''}{action.impact_score.toFixed(0)}
                  </span>
                  <span className="text-gray-400">
                    {new Date(action.executed_at).toLocaleString()}
                  </span>
                </div>
              </div>
              {action.error_message && (
                <p className="text-sm text-red-500 mt-1 ml-8">{action.error_message}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
