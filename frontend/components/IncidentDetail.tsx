'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import Timeline from './Timeline';
import RootCauseCard from './RootCauseCard';

interface Incident {
  id: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  service_name: string | null;
  root_cause: string | null;
  solution: string | null;
  detected_at: string;
  resolved_at: string | null;
  auto_resolved: boolean;
}

interface TimelineEvent {
  timestamp: string;
  event_type: string;
  description: string;
  metadata?: Record<string, unknown>;
}

interface TimelineData {
  incident_id: string;
  events: TimelineEvent[];
  summary: string | null;
}

interface IncidentDetailProps {
  incident: Incident;
  onClose: () => void;
}

export default function IncidentDetail({ incident, onClose }: IncidentDetailProps) {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [loadingTimeline, setLoadingTimeline] = useState(true);

  useEffect(() => {
    loadTimeline();
  }, [incident.id]);

  const loadTimeline = async () => {
    try {
      const resp = await api.get(`/incidents/${incident.id}/timeline`);
      setTimeline(resp.data);
    } catch (err) {
      console.error('Failed to load timeline:', err);
    } finally {
      setLoadingTimeline(false);
    }
  };

  const severityColors: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-gray-100 text-gray-800',
  };

  const statusColors: Record<string, string> = {
    open: 'bg-yellow-100 text-yellow-800',
    investigating: 'bg-blue-100 text-blue-800',
    resolved: 'bg-green-100 text-green-800',
    closed: 'bg-gray-100 text-gray-800',
  };

  // Parse solution string into actions list
  const actions = incident.solution?.split(';').map(s => s.trim()).filter(Boolean) || [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold">{incident.title}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[incident.severity] || ''}`}>
                {incident.severity}
              </span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColors[incident.status] || ''}`}>
                {incident.status}
              </span>
              {incident.service_name && (
                <span className="text-xs text-gray-500">{incident.service_name}</span>
              )}
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
        </div>

        <div className="p-6 space-y-6">
          {/* Description */}
          {incident.description && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-1">Description</h3>
              <p className="text-sm text-gray-600">{incident.description}</p>
            </div>
          )}

          {/* Root Cause Analysis */}
          <RootCauseCard
            rootCause={incident.root_cause}
            actions={actions}
          />

          {/* Timeline */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Timeline</h3>
            {loadingTimeline ? (
              <p className="text-sm text-gray-500">Loading timeline...</p>
            ) : timeline && timeline.events.length > 0 ? (
              <Timeline events={timeline.events} summary={timeline.summary} />
            ) : (
              <p className="text-sm text-gray-500">No timeline events yet.</p>
            )}
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Detected:</span>
              <span className="ml-2">{new Date(incident.detected_at).toLocaleString()}</span>
            </div>
            {incident.resolved_at && (
              <div>
                <span className="text-gray-500">Resolved:</span>
                <span className="ml-2">{new Date(incident.resolved_at).toLocaleString()}</span>
              </div>
            )}
            <div>
              <span className="text-gray-500">Auto-resolved:</span>
              <span className="ml-2">{incident.auto_resolved ? 'Yes' : 'No'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
