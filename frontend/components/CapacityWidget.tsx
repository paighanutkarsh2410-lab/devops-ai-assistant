'use client';

interface ServiceCapacity {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  peak_utilization: number;
  buffer_percent: number;
  status: string;
}

interface CapacityWidgetProps {
  services: Record<string, ServiceCapacity>;
  overall?: {
    avg_utilization: number;
    total_services: number;
    critical_count: number;
    healthy_count: number;
  };
}

export default function CapacityWidget({ services, overall }: CapacityWidgetProps) {
  const statusColor = (status: string) => {
    if (status === 'critical') return 'bg-red-500';
    if (status === 'warning') return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const statusBg = (status: string) => {
    if (status === 'critical') return 'bg-red-50 border-red-200';
    if (status === 'warning') return 'bg-yellow-50 border-yellow-200';
    return 'bg-green-50 border-green-200';
  };

  const barColor = (pct: number) => {
    if (pct >= 90) return 'bg-red-500';
    if (pct >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-4">
      {/* Overall Summary */}
      {overall && (
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold">{overall.avg_utilization}%</div>
            <div className="text-xs text-gray-500">Avg Utilization</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold">{overall.total_services}</div>
            <div className="text-xs text-gray-500">Services</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{overall.healthy_count}</div>
            <div className="text-xs text-gray-500">Healthy</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{overall.critical_count}</div>
            <div className="text-xs text-gray-500">Critical</div>
          </div>
        </div>
      )}

      {/* Per-Service Capacity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">Service Capacity</h3>
        </div>
        <div className="divide-y">
          {Object.entries(services).length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No capacity data available
            </div>
          ) : (
            Object.entries(services).map(([name, svc]) => (
              <div key={name} className={`px-6 py-4 border-l-4 ${statusBg(svc.status)}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${statusColor(svc.status)}`} />
                    <span className="font-medium">{name}</span>
                  </div>
                  <span className="text-sm text-gray-500">
                    Buffer: {svc.buffer_percent.toFixed(0)}%
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: 'CPU', value: svc.cpu_percent },
                    { label: 'Memory', value: svc.memory_percent },
                    { label: 'Disk', value: svc.disk_percent },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>{label}</span>
                        <span>{value.toFixed(0)}%</span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${barColor(value)}`}
                          style={{ width: `${Math.min(value, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
