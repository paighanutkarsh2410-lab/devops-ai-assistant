'use client';

import { useEffect, useState, useCallback } from 'react';
import { metricsAPI, alertsAPI } from '@/lib/api';
import { WebSocketClient } from '@/lib/websocket';
import MetricsChart from './MetricsChart';
import AlertCard from './AlertCard';

interface Metric {
  id: string;
  service_name: string;
  metric_name: string;
  value: number;
  unit: string | null;
  timestamp: string;
}

interface Alert {
  id: string;
  title: string;
  message: string;
  severity: string;
  acknowledged: boolean;
  resolved: boolean;
  triggered_at: string;
}

export default function LiveMetrics() {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [metricsRes, alertsRes] = await Promise.all([
        metricsAPI.getAll({ hours: 1, limit: 1000 }),
        alertsAPI.getAll({ limit: 20 }),
      ]);
      setMetrics(metricsRes.data);
      setAlerts(alertsRes.data);
    } catch (err) {
      console.error('Failed to load metrics/alerts:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    // Auto-refresh every 15 seconds
    const interval = setInterval(loadData, 15000);

    // WebSocket for real-time alerts
    const ws = new WebSocketClient();
    ws.connect();
    ws.on('alert', (alert: Alert) => {
      setAlerts(prev => [alert, ...prev].slice(0, 20));
    });
    ws.on('metrics', () => {
      loadData();
    });

    return () => {
      clearInterval(interval);
      ws.disconnect();
    };
  }, [loadData]);

  const handleAcknowledge = async (alertId: string) => {
    try {
      await alertsAPI.update(alertId, { acknowledged: true });
      setAlerts(prev =>
        prev.map(a => a.id === alertId ? { ...a, acknowledged: true } : a)
      );
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  // Group metrics by service + metric_name for charts
  const getChartData = (serviceName: string, metricName: string) => {
    return metrics
      .filter(m => m.service_name === serviceName && m.metric_name === metricName)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .slice(-30);
  };

  // Get unique services
  const services = [...new Set(metrics.map(m => m.service_name))];
  const activeAlerts = alerts.filter(a => !a.resolved);

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Loading metrics...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Alerts Section */}
      {activeAlerts.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Active Alerts ({activeAlerts.length})</h2>
          <div className="space-y-2">
            {activeAlerts.slice(0, 5).map(alert => (
              <AlertCard key={alert.id} alert={alert} onAcknowledge={handleAcknowledge} />
            ))}
          </div>
        </div>
      )}

      {/* Metrics Charts */}
      {services.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No metrics data yet. Start the Monitor Agent to begin collecting data.
        </div>
      ) : (
        services.slice(0, 3).map(service => (
          <div key={service}>
            <h2 className="text-lg font-semibold mb-3">{service}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <MetricsChart
                data={getChartData(service, 'cpu')}
                title="CPU Usage"
                color="#ef4444"
                unit="%"
              />
              <MetricsChart
                data={getChartData(service, 'memory')}
                title="Memory Usage"
                color="#8b5cf6"
                unit="%"
              />
              <MetricsChart
                data={getChartData(service, 'response_time')}
                title="Response Time"
                color="#f59e0b"
                unit="ms"
              />
              <MetricsChart
                data={getChartData(service, 'error_rate')}
                title="Error Rate"
                color="#10b981"
                unit="/min"
              />
            </div>
          </div>
        ))
      )}
    </div>
  );
}
