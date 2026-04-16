'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

interface PredictiveAlertItem {
  id: string;
  title: string;
  message: string | null;
  severity: string;
  prediction_type: string;
  service_name: string | null;
  confidence: number;
  hours_until_issue: number | null;
  prevented: boolean;
  prevention_action: string | null;
  preventive_actions: Array<{ action: string; description: string; effort: string }> | null;
  created_at: string;
}

interface PredictiveAlertsProps {
  alerts: PredictiveAlertItem[];
  onRefresh: () => void;
}

export default function PredictiveAlerts({ alerts, onRefresh }: PredictiveAlertsProps) {
  const [preventing, setPreventing] = useState<string | null>(null);

  const handlePrevent = async (alertId: string) => {
    setPreventing(alertId);
    try {
      await api.post(`/alerts/predictive/${alertId}/prevent`, {
        action_taken: 'manual_prevention',
      });
      onRefresh();
    } catch (error) {
      console.error('Failed to mark as prevented:', error);
    } finally {
      setPreventing(null);
    }
  };

  const severityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-400 bg-red-50';
      case 'high': return 'border-orange-400 bg-orange-50';
      case 'medium': return 'border-yellow-400 bg-yellow-50';
      default: return 'border-blue-400 bg-blue-50';
    }
  };

  const typeLabel = (type: string) => {
    const labels: Record<string, string> = {
      resource_exhaustion: 'Resource Exhaustion',
      capacity_breach: 'Capacity Breach',
      degrading_trend: 'Degrading Trend',
      cost_overrun: 'Cost Overrun',
      anomaly_forecast: 'Anomaly Forecast',
    };
    return labels[type] || type;
  };

  const sortedAlerts = [...alerts].sort((a, b) => {
    if (a.prevented !== b.prevented) return a.prevented ? 1 : -1;
    const ha = a.hours_until_issue ?? 9999;
    const hb = b.hours_until_issue ?? 9999;
    return ha - hb;
  });

  return (
    <div className="space-y-3">
      {sortedAlerts.length === 0 ? (
        <div className="bg-white rounded-lg shadow px-6 py-8 text-center text-gray-500">
          No predictive alerts. System is looking healthy!
        </div>
      ) : (
        sortedAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`rounded-lg shadow border-l-4 p-4 ${
              alert.prevented ? 'bg-gray-50 border-gray-300 opacity-70' : severityColor(alert.severity)
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium">{alert.title}</span>
                  {alert.prevented && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                      Prevented
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600">{alert.message}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                  <span className="bg-gray-100 px-2 py-0.5 rounded">{typeLabel(alert.prediction_type)}</span>
                  {alert.service_name && <span>{alert.service_name}</span>}
                  <span>Confidence: {alert.confidence}%</span>
                  {alert.hours_until_issue != null && (
                    <span className="font-medium text-red-600">
                      {alert.hours_until_issue < 24
                        ? `${alert.hours_until_issue.toFixed(0)}h until issue`
                        : `${(alert.hours_until_issue / 24).toFixed(1)}d until issue`}
                    </span>
                  )}
                </div>

                {/* Preventive Actions */}
                {!alert.prevented && alert.preventive_actions && alert.preventive_actions.length > 0 && (
                  <div className="mt-2">
                    <span className="text-xs font-medium text-gray-500">Suggested actions:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {alert.preventive_actions.map((action, i) => (
                        <span key={i} className="text-xs bg-white px-2 py-0.5 rounded border">
                          {action.description}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {!alert.prevented && (
                <button
                  onClick={() => handlePrevent(alert.id)}
                  disabled={preventing === alert.id}
                  className="ml-4 px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50 whitespace-nowrap"
                >
                  {preventing === alert.id ? 'Saving...' : 'Mark Prevented'}
                </button>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
