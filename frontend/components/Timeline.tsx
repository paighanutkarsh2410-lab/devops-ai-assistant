'use client';

interface TimelineEvent {
  timestamp: string;
  event_type: string;
  description: string;
  metadata?: Record<string, unknown>;
}

interface TimelineProps {
  events: TimelineEvent[];
  summary?: string | null;
}

const EVENT_COLORS: Record<string, string> = {
  detection: 'bg-red-500',
  alert: 'bg-orange-500',
  metric_spike: 'bg-yellow-500',
  deployment: 'bg-purple-500',
  error_log: 'bg-red-400',
  diagnosis: 'bg-blue-500',
  resolution: 'bg-green-500',
};

const EVENT_LABELS: Record<string, string> = {
  detection: 'Detected',
  alert: 'Alert',
  metric_spike: 'Metric Spike',
  deployment: 'Deployment',
  error_log: 'Error Log',
  diagnosis: 'Diagnosis',
  resolution: 'Resolved',
};

export default function Timeline({ events, summary }: TimelineProps) {
  const formatTime = (ts: string) =>
    new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  return (
    <div>
      {summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h4 className="text-sm font-medium text-blue-800 mb-1">AI Summary</h4>
          <p className="text-sm text-blue-700">{summary}</p>
        </div>
      )}

      <div className="relative">
        {events.map((event, i) => (
          <div key={i} className="flex gap-4 mb-4 last:mb-0">
            {/* Timeline dot and line */}
            <div className="flex flex-col items-center">
              <div className={`w-3 h-3 rounded-full ${EVENT_COLORS[event.event_type] || 'bg-gray-400'}`} />
              {i < events.length - 1 && <div className="w-0.5 flex-1 bg-gray-200 mt-1" />}
            </div>

            {/* Event content */}
            <div className="flex-1 pb-2">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-xs font-medium text-gray-500">
                  {formatTime(event.timestamp)}
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  EVENT_COLORS[event.event_type]?.replace('bg-', 'bg-opacity-20 text-') || 'bg-gray-100 text-gray-600'
                }`}>
                  {EVENT_LABELS[event.event_type] || event.event_type}
                </span>
              </div>
              <p className="text-sm text-gray-800">{event.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
