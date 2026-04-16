'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI, incidentsAPI } from '@/lib/api';
import { colors, severityColor, statusColor } from '@/lib/theme';
import DashboardShell from '@/components/DashboardShell';
import LiveMetrics from '@/components/LiveMetrics';
import IncidentDetail from '@/components/IncidentDetail';
import ActionLog from '@/components/ActionLog';

interface User {
  id: string; email: string; full_name: string | null;
  company: string | null; is_active: boolean; created_at: string;
}
interface Incident {
  id: string; title: string; description: string | null;
  severity: string; status: string; service_name: string | null;
  root_cause: string | null; solution: string | null;
  detected_at: string; resolved_at: string | null; auto_resolved: boolean;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'metrics' | 'remediations'>('overview');
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);
  const [hoveredStat, setHoveredStat] = useState<number | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) { router.push('/login'); return; }
      const userResponse = await authAPI.getCurrentUser();
      setUser(userResponse.data);
      const incidentsResponse = await incidentsAPI.getAll();
      setIncidents(incidentsResponse.data);
    } catch {
      localStorage.removeItem('token');
      router.push('/login');
    } finally { setLoading(false); }
  };

  const handleLogout = () => { localStorage.removeItem('token'); router.push('/login'); };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh', background: '#04040c', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 48, height: 48, borderRadius: 14,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 24, marginBottom: 20,
            boxShadow: '0 0 30px rgba(59,130,246,0.3)',
            animation: 'glow-pulse 2s ease-in-out infinite',
          }}>⚡</div>
          <div style={{ fontSize: 14, color: '#52525b' }}>Loading dashboard...</div>
        </div>
      </div>
    );
  }

  const open = incidents.filter(i => i.status === 'open').length;
  const resolved = incidents.filter(i => i.status === 'resolved').length;
  const autoResolved = incidents.filter(i => i.auto_resolved).length;
  const criticals = incidents.filter(i => i.severity === 'critical' && i.status !== 'resolved').length;

  const stats = [
    { label: 'Total Incidents', value: incidents.length, color: '#3b82f6', icon: '📋', glow: 'rgba(59,130,246,0.15)' },
    { label: 'Open', value: open, color: '#f59e0b', icon: '⚠️', glow: 'rgba(245,158,11,0.15)' },
    { label: 'Resolved', value: resolved, color: '#10b981', icon: '✅', glow: 'rgba(16,185,129,0.15)' },
    { label: 'Auto-Healed', value: autoResolved, color: '#8b5cf6', icon: '🤖', glow: 'rgba(139,92,246,0.15)' },
  ];

  const tabs = [
    { id: 'overview' as const, label: 'Incidents', icon: '🔥' },
    { id: 'metrics' as const, label: 'Live Metrics', icon: '📈' },
    { id: 'remediations' as const, label: 'Remediations', icon: '🛠️' },
  ];

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
        {/* ═══ Top Bar ═══ */}
        <div className="slide-up" style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 36,
        }}>
          <div>
            <h1 style={{
              fontSize: 30, fontWeight: 800, letterSpacing: '-0.5px', marginBottom: 6,
              background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>
              Dashboard
            </h1>
            <p style={{ fontSize: 13, color: '#3f3f46' }}>
              Welcome back, {user?.full_name || user?.email}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {criticals > 0 && (
              <div style={{
                padding: '7px 14px', borderRadius: 10,
                background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)',
                color: '#f87171', fontSize: 12, fontWeight: 700,
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%', background: '#ef4444',
                  animation: 'breathe 2s ease-in-out infinite',
                  boxShadow: '0 0 8px rgba(239,68,68,0.5)',
                }} />
                {criticals} Critical
              </div>
            )}
            <button onClick={handleLogout}
              style={{
                padding: '8px 18px', borderRadius: 10,
                border: '1px solid rgba(255,255,255,0.06)',
                background: 'transparent', color: '#52525b',
                cursor: 'pointer', fontSize: 13, transition: 'all 0.2s',
              }}>Logout</button>
          </div>
        </div>

        {/* ═══ Stats Grid ═══ */}
        <div className="slide-up-d1" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
          {stats.map((stat, i) => (
            <div
              key={stat.label}
              onMouseEnter={() => setHoveredStat(i)}
              onMouseLeave={() => setHoveredStat(null)}
              style={{
                background: colors.bgCard,
                borderLeft: `1px solid ${hoveredStat === i ? 'rgba(255,255,255,0.08)' : colors.border}`,
                borderRight: `1px solid ${hoveredStat === i ? 'rgba(255,255,255,0.08)' : colors.border}`,
                borderBottom: `1px solid ${hoveredStat === i ? 'rgba(255,255,255,0.08)' : colors.border}`,
                borderTop: `2px solid ${stat.color}`,
                borderRadius: 18, padding: '24px 22px',
                transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
                transform: hoveredStat === i ? 'translateY(-3px)' : 'none',
                boxShadow: hoveredStat === i ? `0 12px 40px ${stat.glow}` : 'none',
                position: 'relative', overflow: 'hidden',
              }}
            >
              {/* Top glow accent */}
              <div style={{
                position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)',
                width: 80, height: 40,
                background: `radial-gradient(circle, ${stat.glow}, transparent)`,
                filter: 'blur(12px)', pointerEvents: 'none',
              }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative' }}>
                <div>
                  <div style={{ fontSize: 11, color: '#52525b', marginBottom: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                    {stat.label}
                  </div>
                  <div style={{
                    fontSize: 38, fontWeight: 900, color: stat.color, letterSpacing: '-1px',
                    textShadow: hoveredStat === i ? `0 0 20px ${stat.glow}` : 'none',
                    transition: 'text-shadow 0.3s',
                  }}>
                    {stat.value}
                  </div>
                </div>
                <span style={{
                  fontSize: 28, position: 'relative',
                  filter: hoveredStat === i ? 'drop-shadow(0 0 8px rgba(255,255,255,0.2))' : 'none',
                  transition: 'filter 0.3s',
                }}>{stat.icon}</span>
              </div>
            </div>
          ))}
        </div>

        {/* ═══ Tabs ═══ */}
        <div className="slide-up-d2" style={{
          display: 'flex', gap: 4, marginBottom: 28, padding: 4,
          background: 'rgba(255,255,255,0.015)', borderRadius: 14,
          border: '1px solid rgba(255,255,255,0.04)',
          width: 'fit-content',
        }}>
          {tabs.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 20px', borderRadius: 10, border: 'none',
                background: activeTab === tab.id ? 'linear-gradient(135deg, #3b82f6, #8b5cf6)' : 'transparent',
                color: activeTab === tab.id ? '#fff' : '#52525b',
                cursor: 'pointer', fontSize: 13,
                fontWeight: activeTab === tab.id ? 700 : 400,
                transition: 'all 0.3s',
                display: 'flex', alignItems: 'center', gap: 8,
                boxShadow: activeTab === tab.id ? '0 4px 16px rgba(59,130,246,0.2)' : 'none',
              }}>
              <span style={{ fontSize: 14 }}>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* ═══ Content ═══ */}
        <div className="slide-up-d3">
          {activeTab === 'remediations' ? (
            <ActionLog />
          ) : activeTab === 'metrics' ? (
            <LiveMetrics />
          ) : (
            <div style={{
              background: 'rgba(255,255,255,0.015)',
              border: '1px solid rgba(255,255,255,0.04)',
              borderRadius: 18, overflow: 'hidden',
            }}>
              <div style={{
                padding: '18px 22px',
                borderBottom: '1px solid rgba(255,255,255,0.04)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <h2 style={{
                  fontSize: 16, fontWeight: 700,
                  background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                }}>Recent Incidents</h2>
                <span style={{
                  fontSize: 11, color: '#3b82f6', fontWeight: 600,
                  padding: '4px 12px', borderRadius: 8,
                  background: 'rgba(59,130,246,0.06)',
                }}>
                  {incidents.length} total
                </span>
              </div>
              {incidents.length === 0 ? (
                <div style={{ padding: 60, textAlign: 'center', color: '#3f3f46' }}>
                  <div style={{ fontSize: 48, marginBottom: 16 }}>🎉</div>
                  <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 6, color: '#71717a' }}>All clear!</div>
                  <div style={{ fontSize: 13 }}>No incidents detected. System is healthy.</div>
                </div>
              ) : (
                incidents.slice(0, 15).map((incident, idx) => {
                  const sev = severityColor(incident.severity);
                  const stat = statusColor(incident.status);
                  const hovered = hoveredRow === incident.id;
                  return (
                    <div
                      key={incident.id}
                      onClick={() => setSelectedIncident(incident)}
                      onMouseEnter={() => setHoveredRow(incident.id)}
                      onMouseLeave={() => setHoveredRow(null)}
                      style={{
                        padding: '16px 22px',
                        borderBottom: '1px solid rgba(255,255,255,0.03)',
                        cursor: 'pointer',
                        background: hovered ? 'rgba(59,130,246,0.03)' : 'transparent',
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        transition: 'all 0.2s ease',
                        animation: `slide-up 0.4s ease-out ${idx * 0.03}s both`,
                        position: 'relative',
                      }}
                    >
                      {/* Left hover indicator */}
                      {hovered && (
                        <div style={{
                          position: 'absolute', left: 0, top: '20%', bottom: '20%', width: 2,
                          background: sev.color,
                          boxShadow: `0 0 6px ${sev.color}`,
                          borderRadius: 2,
                        }} />
                      )}
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: 14, fontWeight: 600, marginBottom: 4,
                          color: hovered ? '#f0f0f0' : '#a1a1aa',
                          transition: 'color 0.2s',
                        }}>
                          {incident.title}
                        </div>
                        <div style={{ fontSize: 12, color: '#3f3f46' }}>
                          {incident.service_name} &middot; {new Date(incident.detected_at).toLocaleString()}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{
                          padding: '4px 12px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                          background: sev.bg, color: sev.color, border: `1px solid ${sev.border}`,
                        }}>{incident.severity}</span>
                        <span style={{
                          padding: '4px 12px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                          background: stat.bg, color: stat.color,
                        }}>{incident.status}</span>
                        {incident.auto_resolved && (
                          <span style={{ fontSize: 14, filter: 'drop-shadow(0 0 4px rgba(139,92,246,0.4))' }} title="Auto-resolved by AI">🤖</span>
                        )}
                        <span style={{
                          fontSize: 16, color: hovered ? '#3b82f6' : '#27272a',
                          transition: 'all 0.2s',
                          transform: hovered ? 'translateX(2px)' : 'none',
                        }}>›</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>

      {selectedIncident && (
        <IncidentDetail
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
        />
      )}
    </DashboardShell>
  );
}
