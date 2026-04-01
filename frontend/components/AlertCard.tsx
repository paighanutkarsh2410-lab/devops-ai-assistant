'use client';

interface Alert {
  id: string;
  title: string;
  message: string;
  severity: string;
  acknowledged: boolean;
  resolved: boolean;
  triggered_at: string;
}

interface AlertCardProps {
  alert: Alert;
  onAcknowledge?: (id: string) => void;
}

export default function AlertCard({ alert, onAcknowledge }: AlertCardProps) {
  const severityColors: Record<string, string> = {
    critical: 'border-red-500 bg-red-50',
    warning: 'border-yellow-500 bg-yellow-50',
    info: 'border-blue-500 bg-blue-50',
  };

  const severityBadge: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    info: 'bg-blue-100 text-blue-800',
  };

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    return `${hours}h ago`;
  };

  return (
    <div className={`border-l-4 p-4 rounded-r-lg ${severityColors[alert.severity] || 'border-gray-300 bg-gray-50'}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityBadge[alert.severity] || 'bg-gray-100 text-gray-800'}`}>
              {alert.severity.toUpperCase()}
            </span>
            <span className="text-xs text-gray-500">{timeAgo(alert.triggered_at)}</span>
            {alert.acknowledged && (
              <span className="text-xs text-green-600">Acknowledged</span>
            )}
          </div>
          <h4 className="font-medium text-sm">{alert.title}</h4>
          <p className="text-xs text-gray-600 mt-1">{alert.message}</p>
        </div>
        {!alert.acknowledged && onAcknowledge && (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className="ml-2 px-3 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            Ack
          </button>
        )}
      </div>
    </div>
  );
}
