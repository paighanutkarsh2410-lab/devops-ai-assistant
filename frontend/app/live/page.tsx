'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardShell from '@/components/DashboardShell';
import { colors, btn } from '@/lib/theme';
import useWebSocket from '@/lib/useWebSocket';
import LiveChart from '@/components/LiveChart';
import ConnectionStatus from '@/components/ConnectionStatus';

interface DataPoint {
  time: string;
  value: number;
}

export default function LiveMonitoringPage() {
  const router = useRouter();
  const { lastMessage, connectionStatus } = useWebSocket();
  const [metricData, setMetricData] = useState<Record<string, Record<string, DataPoint[]>>>({});

  // Process incoming metric updates
  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'metric_update') return;

    const data = lastMessage.data as { services?: Record<string, Record<string, number>>; timestamp?: string };
    if (!data?.services) return;

    const time = data.timestamp || new Date().toISOString();

    setMetricData(prev => {
      const next = { ...prev };
      for (const [service, metrics] of Object.entries(data.services!)) {
        if (!next[service]) next[service] = {};
        for (const [metric, value] of Object.entries(metrics)) {
          if (!next[service][metric]) next[service][metric] = [];
          next[service][metric] = [
            ...next[service][metric].slice(-59),
            { time, value: value as number },
          ];
        }
      }
      return next;
    });
  }, [lastMessage]);

  // Generate demo data if no real data
  useEffect(() => {
    if (Object.keys(metricData).length > 0) return;

    const interval = setInterval(() => {
      const time = new Date().toISOString();
      setMetricData(prev => {
        const next = { ...prev };
        const services = ['api-server', 'database', 'redis', 'worker'];
        for (const svc of services) {
          if (!next[svc]) next[svc] = { cpu: [], memory: [], response_time: [] };
          next[svc].cpu = [...(next[svc].cpu || []).slice(-59), { time, value: 20 + Math.random() * 40 }];
          next[svc].memory = [...(next[svc].memory || []).slice(-59), { time, value: 40 + Math.random() * 30 }];
          next[svc].response_time = [...(next[svc].response_time || []).slice(-59), { time, value: 50 + Math.random() * 150 }];
        }
        return next;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [metricData]);

  const services = Object.keys(metricData);
  const chartColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
        {/* Header */}
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #ef4444)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Live Monitoring</h1>
            <ConnectionStatus status={connectionStatus} />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => router.push('/dashboard')} style={btn}>
              Dashboard
            </button>
            <button onClick={() => router.push('/performance')} style={btn}>
              Performance
            </button>
          </div>
        </div>

        {/* Charts Grid */}
        {services.map((service, si) => (
          <div key={service} className={`slide-up-d${Math.min(si + 1, 4)}`} style={{ marginBottom: 32 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: colors.text }}>{service}</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              <LiveChart
                title="CPU"
                data={metricData[service]?.cpu || []}
                color={chartColors[si % chartColors.length]}
                unit="%"
                type="area"
              />
              <LiveChart
                title="Memory"
                data={metricData[service]?.memory || []}
                color="#10b981"
                unit="%"
                type="area"
              />
              <LiveChart
                title="Response Time"
                data={metricData[service]?.response_time || []}
                color="#f59e0b"
                unit="ms"
                type="line"
              />
            </div>
          </div>
        ))}
      </div>
    </DashboardShell>
  );
}
