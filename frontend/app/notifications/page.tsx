'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardShell from '@/components/DashboardShell';
import { colors, btn, btnPrimary, card as cardStyle, glassCard, severityColor } from '@/lib/theme';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Notification {
  id: string;
  event_type: string;
  channel: string;
  severity: string | null;
  title: string | null;
  status: string;
  read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    fetch(`${API_BASE}/alerts/`)
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
          setNotifications(data.map((a: Record<string, unknown>) => ({
            id: a.id as string,
            event_type: 'alert',
            channel: 'system',
            severity: a.severity as string,
            title: a.title as string,
            status: 'sent',
            read: (a.resolved as boolean) || false,
            created_at: a.created_at as string,
          })));
        }
      })
      .catch(() => {});
  }, []);

  const filtered = notifications.filter(n => {
    if (filter === 'unread') return !n.read;
    if (filter === 'critical') return n.severity === 'critical';
    return true;
  });

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 800, margin: '0 auto' }}>
        {/* Header */}
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Notifications</h1>
            <p style={{ fontSize: 13, color: colors.textMuted, margin: '4px 0 0' }}>Stay updated on alerts and incidents</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => router.push('/settings/notifications')}
              style={btn}
            >
              Settings
            </button>
            <button
              onClick={() => router.push('/dashboard')}
              style={btn}
            >
              Dashboard
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="slide-up-d1" style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          {['all', 'unread', 'critical'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '6px 16px',
                borderRadius: 20,
                border: `1px solid ${filter === f ? colors.accent : colors.border}`,
                background: filter === f ? 'rgba(59,130,246,0.15)' : colors.bgCard,
                color: filter === f ? colors.accent : colors.textSecondary,
                cursor: 'pointer',
                fontSize: 13,
                textTransform: 'capitalize' as const,
                transition: 'all 0.2s ease',
              }}
            >
              {f} {f === 'all' ? `(${notifications.length})` : ''}
            </button>
          ))}
        </div>

        {/* Notification List */}
        <div className="slide-up-d2">
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: colors.textDim }}>
            <p style={{ fontSize: 16 }}>No notifications</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {filtered.map(n => (
              <div
                key={n.id}
                style={{
                  background: n.read ? colors.bgCard : 'rgba(59,130,246,0.05)',
                  border: `1px solid ${n.read ? colors.border : 'rgba(59,130,246,0.15)'}`,
                  borderRadius: 10,
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  transition: 'all 0.2s ease',
                }}
              >
                {!n.read && (
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: colors.accent, flexShrink: 0,
                    boxShadow: `0 0 8px ${colors.accent}`,
                  }} />
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: 14, color: colors.text }}>{n.title || 'Notification'}</div>
                  <div style={{ fontSize: 12, color: colors.textMuted, marginTop: 2 }}>
                    {n.channel} &middot; {new Date(n.created_at).toLocaleString()}
                  </div>
                </div>
                {n.severity && (() => {
                  const sc = severityColor(n.severity);
                  return (
                    <span style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: 12,
                      color: sc.color,
                      background: sc.bg,
                    }}>
                      {n.severity.toUpperCase()}
                    </span>
                  );
                })()}
              </div>
            ))}
          </div>
        )}
        </div>
      </div>
    </DashboardShell>
  );
}
