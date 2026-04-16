'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardShell from '@/components/DashboardShell';
import { colors, card as cardStyle, btn, btnActive } from '@/lib/theme';
import useWebSocket from '@/lib/useWebSocket';
import ConnectionStatus from '@/components/ConnectionStatus';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  cpu: number;
  memory: number;
  responseTime: number;
  errorRate: number;
  requests: number;
}

export default function PerformancePage() {
  const router = useRouter();
  const { lastMessage, connectionStatus } = useWebSocket();
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('1h');

  // Generate demo service data
  useEffect(() => {
    const updateServices = () => {
      setServices([
        {
          name: 'api-server',
          status: 'healthy',
          cpu: 25 + Math.random() * 20,
          memory: 55 + Math.random() * 15,
          responseTime: 80 + Math.random() * 60,
          errorRate: Math.random() * 2,
          requests: 150 + Math.floor(Math.random() * 100),
        },
        {
          name: 'database',
          status: 'healthy',
          cpu: 15 + Math.random() * 10,
          memory: 70 + Math.random() * 10,
          responseTime: 5 + Math.random() * 15,
          errorRate: Math.random() * 0.5,
          requests: 300 + Math.floor(Math.random() * 200),
        },
        {
          name: 'redis',
          status: 'healthy',
          cpu: 5 + Math.random() * 5,
          memory: 30 + Math.random() * 10,
          responseTime: 1 + Math.random() * 3,
          errorRate: 0,
          requests: 500 + Math.floor(Math.random() * 300),
        },
        {
          name: 'worker',
          status: Math.random() > 0.9 ? 'degraded' : 'healthy',
          cpu: 40 + Math.random() * 30,
          memory: 60 + Math.random() * 20,
          responseTime: 200 + Math.random() * 300,
          errorRate: Math.random() * 5,
          requests: 50 + Math.floor(Math.random() * 50),
        },
      ]);
    };

    updateServices();
    const interval = setInterval(updateServices, 5000);
    return () => clearInterval(interval);
  }, []);

  const statusColorMap = { healthy: colors.success, degraded: colors.warning, down: colors.danger };

  const getHealthColor = (value: number, thresholds: [number, number]) => {
    if (value < thresholds[0]) return colors.success;
    if (value < thresholds[1]) return colors.warning;
    return colors.danger;
  };

  // Aggregate stats
  const totalRequests = services.reduce((sum, s) => sum + s.requests, 0);
  const avgResponse = services.length ? services.reduce((sum, s) => sum + s.responseTime, 0) / services.length : 0;
  const avgErrorRate = services.length ? services.reduce((sum, s) => sum + s.errorRate, 0) / services.length : 0;

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
        {/* Header */}
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #f59e0b)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Performance Monitoring</h1>
            <ConnectionStatus status={connectionStatus} />
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {['1h', '6h', '24h', '7d'].map(t => (
              <button key={t} onClick={() => setTimeRange(t)} style={timeRange === t ? btnActive : btn}>
                {t}
              </button>
            ))}
            <button onClick={() => router.push('/live')} style={btn}>
              Live View
            </button>
            <button onClick={() => router.push('/dashboard')} style={btn}>
              Dashboard
            </button>
          </div>
        </div>

        {/* System-wide stats */}
        <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
          <div style={{...cardStyle, position: 'relative', overflow: 'hidden', borderTop: '2px solid #f59e0b'}}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(245,158,11,0.18), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div style={{ fontSize: 12, color: colors.textMuted }}>Total Requests/s</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: colors.text }}>{totalRequests}</div>
          </div>
          <div style={{...cardStyle, position: 'relative', overflow: 'hidden', borderTop: '2px solid #f59e0b'}}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(245,158,11,0.18), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div style={{ fontSize: 12, color: colors.textMuted }}>Avg Response Time</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: getHealthColor(avgResponse, [100, 300]) }}>
              {avgResponse.toFixed(0)}ms
            </div>
          </div>
          <div style={{...cardStyle, position: 'relative', overflow: 'hidden', borderTop: '2px solid #f59e0b'}}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(245,158,11,0.18), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div style={{ fontSize: 12, color: colors.textMuted }}>Error Rate</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: getHealthColor(avgErrorRate, [1, 5]) }}>
              {avgErrorRate.toFixed(2)}%
            </div>
          </div>
          <div style={{...cardStyle, position: 'relative', overflow: 'hidden', borderTop: '2px solid #f59e0b'}}>
            <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: 'radial-gradient(circle, rgba(245,158,11,0.18), transparent)', filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite' }} />
            <div style={{ fontSize: 12, color: colors.textMuted }}>Services</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: colors.text }}>
              {services.filter(s => s.status === 'healthy').length}/{services.length}
              <span style={{ fontSize: 14, color: colors.success, marginLeft: 4 }}>healthy</span>
            </div>
          </div>
        </div>

        {/* Service Grid */}
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: colors.text }}>Services</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginBottom: 32 }}>
          {services.map(svc => (
            <div
              key={svc.name}
              onClick={() => setSelectedService(svc.name === selectedService ? null : svc.name)}
              role="button"
              tabIndex={0}
              aria-label={`${svc.name} service details`}
              style={{
                background: colors.bgCard,
                borderRadius: 14,
                padding: 16,
                border: `2px solid ${svc.name === selectedService ? colors.accent : colors.border}`,
                cursor: 'pointer',
                transition: 'border-color 0.2s',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    width: 10, height: 10, borderRadius: '50%',
                    background: statusColorMap[svc.status],
                    boxShadow: `0 0 6px ${statusColorMap[svc.status]}40`,
                  }} />
                  <span style={{ fontWeight: 600, fontSize: 15, color: colors.text }}>{svc.name}</span>
                </div>
                <span style={{
                  fontSize: 11, padding: '2px 8px', borderRadius: 10,
                  background: svc.status === 'healthy' ? colors.successBg : colors.warningBg,
                  color: svc.status === 'healthy' ? colors.success : colors.warning,
                  fontWeight: 600,
                }}>
                  {svc.status}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                <div>
                  <div style={{ fontSize: 10, color: colors.textMuted }}>CPU</div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: getHealthColor(svc.cpu, [50, 80]) }}>
                    {svc.cpu.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: colors.textMuted }}>Memory</div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: getHealthColor(svc.memory, [70, 90]) }}>
                    {svc.memory.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: colors.textMuted }}>Latency</div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: getHealthColor(svc.responseTime, [100, 300]) }}>
                    {svc.responseTime.toFixed(0)}ms
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 10, color: colors.textMuted }}>Errors</div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: getHealthColor(svc.errorRate, [1, 5]) }}>
                    {svc.errorRate.toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Dependency Graph */}
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: colors.text }}>Service Dependencies</h2>
        <div style={{
          background: colors.bgCard,
          borderRadius: 14,
          border: `1px solid ${colors.border}`,
          padding: 24,
          textAlign: 'center',
        }}>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <div style={{
              padding: '12px 20px', borderRadius: 8,
              background: 'rgba(59,130,246,0.1)', border: `2px solid ${colors.accent}`,
              fontWeight: 600, color: colors.accent,
            }}>
              Frontend
            </div>
            <span style={{ color: colors.textMuted, fontSize: 20 }}>&rarr;</span>
            <div style={{
              padding: '12px 20px', borderRadius: 8,
              background: colors.successBg, border: `2px solid ${colors.success}`,
              fontWeight: 600, color: colors.success,
            }}>
              API Server
            </div>
            <span style={{ color: colors.textMuted, fontSize: 20 }}>&rarr;</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{
                padding: '8px 16px', borderRadius: 8, fontSize: 13,
                background: colors.warningBg, border: `1px solid ${colors.warning}`, color: colors.warning,
              }}>
                PostgreSQL
              </div>
              <div style={{
                padding: '8px 16px', borderRadius: 8, fontSize: 13,
                background: colors.dangerBg, border: `1px solid ${colors.danger}`, color: colors.danger,
              }}>
                Redis
              </div>
              <div style={{
                padding: '8px 16px', borderRadius: 8, fontSize: 13,
                background: 'rgba(139,92,246,0.1)', border: '1px solid #8b5cf6', color: '#8b5cf6',
              }}>
                Prometheus
              </div>
            </div>
          </div>
          <div style={{ marginTop: 16, fontSize: 12, color: colors.textMuted }}>
            Arrows show request flow direction
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
