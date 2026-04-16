'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import DashboardShell from '@/components/DashboardShell';
import { colors, card as cardStyle, btn, btnActive } from '@/lib/theme';
import ForecastChart from '@/components/ForecastChart';
import CapacityWidget from '@/components/CapacityWidget';
import PredictiveAlerts from '@/components/PredictiveAlerts';

interface AlertStats {
  total: number;
  prevented: number;
  prevention_rate: number;
  active: number;
}

export default function PredictionsPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'alerts' | 'forecasts' | 'capacity'>('alerts');
  const [alerts, setAlerts] = useState([]);
  const [alertStats, setAlertStats] = useState<AlertStats | null>(null);
  const [forecasts, setForecasts] = useState([]);
  const [capacity, setCapacity] = useState<{ services: Record<string, any>; overall?: any } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          router.push('/login');
          return;
        }

        const [alertsRes, statsRes, forecastsRes] = await Promise.all([
          api.get('/alerts/predictive', { params: { limit: 30 } }),
          api.get('/alerts/predictive/stats'),
          api.get('/predictions/metrics', { params: { limit: 12 } }),
        ]);
        setAlerts(alertsRes.data);
        setAlertStats(statsRes.data);
        setForecasts(forecastsRes.data);

        // Try to load capacity data
        try {
          const capRes = await api.get('/predictions/capacity');
          if (capRes.data && Array.isArray(capRes.data) && capRes.data.length > 0) {
            const services: Record<string, any> = {};
            for (const plan of capRes.data) {
              services[plan.service_name] = {
                cpu_percent: plan.current_utilization || 50,
                memory_percent: plan.predicted_utilization || 60,
                disk_percent: 40,
                peak_utilization: Math.max(plan.current_utilization || 50, plan.predicted_utilization || 60),
                buffer_percent: 100 - Math.max(plan.current_utilization || 50, plan.predicted_utilization || 60),
                status: plan.current_utilization > 80 ? 'critical' : plan.current_utilization > 60 ? 'warning' : 'healthy',
              };
            }
            setCapacity({ services });
          }
        } catch {
          // Capacity data is optional
        }
      } catch (error) {
        console.error('Failed to load prediction data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [router]);

  const refreshAlerts = async () => {
    try {
      const [alertsRes, statsRes] = await Promise.all([
        api.get('/alerts/predictive', { params: { limit: 30 } }),
        api.get('/alerts/predictive/stats'),
      ]);
      setAlerts(alertsRes.data);
      setAlertStats(statsRes.data);
    } catch {
      // ignore
    }
  };

  if (loading) {
    return (
      <DashboardShell>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div style={{ fontSize: 18, color: colors.textMuted }}>Loading predictions...</div>
        </div>
      </DashboardShell>
    );
  }

  const statItems = alertStats ? [
    { label: 'Predictions', value: alertStats.total, color: '#8b5cf6' },
    { label: 'Active Alerts', value: alertStats.active, color: colors.warning },
    { label: 'Prevented', value: alertStats.prevented, color: colors.success },
    { label: 'Prevention Rate', value: `${alertStats.prevention_rate}%`, color: colors.text },
  ] : [];

  const tabs: { key: typeof activeTab; label: string }[] = [
    { key: 'alerts', label: 'Predictive Alerts' },
    { key: 'forecasts', label: 'Forecasts' },
    { key: 'capacity', label: 'Capacity' },
  ];

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
        {/* Header */}
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, background: 'linear-gradient(135deg, #f0f0f0, #ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Predictions</h1>
            <p style={{ fontSize: 13, color: colors.textMuted }}>Proactive issue prevention and capacity planning</p>
          </div>
          <button onClick={() => router.push('/dashboard')} style={btn}>
            Back to Dashboard
          </button>
        </div>

        {/* Stats */}
        {alertStats && (
          <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 28 }}>
            {statItems.map((s, i) => (
              <div key={i} style={{...cardStyle, position: 'relative', overflow: 'hidden', borderTop: `2px solid ${s.color}`, transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)'}}>
                <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', width: 80, height: 40, background: `radial-gradient(circle, ${s.color}18, transparent)`, filter: 'blur(12px)', animation: 'breathe 4s ease-in-out infinite', animationDelay: `${i * 0.5}s` }} />
                <div style={{ fontSize: 12, color: colors.textMuted, marginBottom: 4, position: 'relative', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600 }}>{s.label}</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: s.color, position: 'relative', textShadow: `0 0 20px ${s.color}25` }}>{s.value}</div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="slide-up-d2" style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              style={activeTab === t.key ? btnActive : btn}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'alerts' && (
          <PredictiveAlerts alerts={alerts} onRefresh={refreshAlerts} />
        )}

        {activeTab === 'forecasts' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {forecasts.length === 0 ? (
              <div style={{
                gridColumn: '1 / -1',
                ...cardStyle,
                textAlign: 'center',
                padding: 40,
                color: colors.textMuted,
              }}>
                No forecast data yet. The Prediction Agent generates forecasts hourly.
              </div>
            ) : (
              forecasts.map((f: any) => (
                <ForecastChart
                  key={f.id}
                  service={f.service_name}
                  metric={f.metric_name}
                  forecast={f.forecast_data || []}
                  threshold={f.breach_predicted ? undefined : undefined}
                  breachPredicted={f.breach_predicted}
                  hoursUntilBreach={f.hours_until_breach}
                  method={f.method}
                />
              ))
            )}
          </div>
        )}

        {activeTab === 'capacity' && (
          capacity ? (
            <CapacityWidget services={capacity.services} overall={capacity.overall} />
          ) : (
            <div style={{
              ...cardStyle,
              textAlign: 'center',
              padding: 40,
              color: colors.textMuted,
            }}>
              No capacity data yet. Run the Prediction Agent to generate capacity analysis.
            </div>
          )
        )}
      </div>
    </DashboardShell>
  );
}
