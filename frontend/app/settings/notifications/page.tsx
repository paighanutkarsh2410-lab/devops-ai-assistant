'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardShell from '@/components/DashboardShell';
import { colors, btn, btnPrimary, card as cardStyle, input as inputStyle } from '@/lib/theme';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface NotificationPref {
  channel: string;
  enabled: boolean;
  severity_threshold: string;
  services: string[];
  quiet_hours_start: number | null;
  quiet_hours_end: number | null;
  digest_frequency: string;
}

const defaultPrefs: NotificationPref[] = [
  { channel: 'slack', enabled: true, severity_threshold: 'medium', services: [], quiet_hours_start: 23, quiet_hours_end: 7, digest_frequency: 'daily' },
  { channel: 'email', enabled: true, severity_threshold: 'high', services: [], quiet_hours_start: null, quiet_hours_end: null, digest_frequency: 'weekly' },
];

const severityLevels = ['low', 'medium', 'high', 'critical'];
const knownServices = ['api-server', 'web-server', 'worker-service', 'database', 'cache', 'payment-api'];

export default function NotificationSettingsPage() {
  const router = useRouter();
  const [prefs, setPrefs] = useState<NotificationPref[]>(defaultPrefs);
  const [saving, setSaving] = useState(false);
  const [testSent, setTestSent] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    fetch(`${API_BASE}/preferences/notifications`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setPrefs(data.map((p: Record<string, unknown>) => ({
            channel: p.channel as string,
            enabled: p.enabled as boolean,
            severity_threshold: p.severity_threshold as string,
            services: (p.services as string[]) || [],
            quiet_hours_start: p.quiet_hours_start as number | null,
            quiet_hours_end: p.quiet_hours_end as number | null,
            digest_frequency: p.digest_frequency as string,
          })));
        }
      })
      .catch(() => {});
  }, []);

  const updatePref = (index: number, field: string, value: unknown) => {
    setPrefs(prev => prev.map((p, i) => i === index ? { ...p, [field]: value } : p));
  };

  const toggleService = (index: number, service: string) => {
    setPrefs(prev => prev.map((p, i) => {
      if (i !== index) return p;
      const services = p.services.includes(service)
        ? p.services.filter(s => s !== service)
        : [...p.services, service];
      return { ...p, services };
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    const token = localStorage.getItem('token');
    try {
      await fetch(`${API_BASE}/preferences/notifications`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(prefs),
      });
    } catch (e) { console.error(e); }
    setSaving(false);
  };

  const handleTest = async () => {
    const token = localStorage.getItem('token');
    await fetch(`${API_BASE}/preferences/notifications/test`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    setTestSent(true);
    setTimeout(() => setTestSent(false), 3000);
  };

  const selectStyle: React.CSSProperties = {
    width: '100%',
    padding: '8px 12px',
    borderRadius: 8,
    border: `1px solid ${colors.border}`,
    background: colors.bgInput,
    color: colors.text,
    fontSize: 13,
    outline: 'none',
  };

  const numberInputStyle: React.CSSProperties = {
    ...selectStyle,
  };

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 800, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Notification Settings</h1>
            <p style={{ fontSize: 13, color: colors.textMuted, margin: '4px 0 0' }}>Configure how and when you receive alerts</p>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            style={btn}
          >
            Back to Dashboard
          </button>
        </div>

        {prefs.map((pref, idx) => (
          <div key={pref.channel} style={{
            background: colors.bgCard,
            backdropFilter: 'blur(12px)',
            borderRadius: 14,
            padding: 24,
            marginBottom: 16,
            border: `1px solid ${colors.border}`,
            transition: 'all 0.2s ease',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, fontWeight: 600, color: colors.text, textTransform: 'capitalize' as const, margin: 0 }}>
                {pref.channel === 'slack' ? 'Slack' : 'Email'} Notifications
              </h2>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', color: colors.textSecondary, fontSize: 13 }}>
                <input
                  type="checkbox"
                  checked={pref.enabled}
                  onChange={e => updatePref(idx, 'enabled', e.target.checked)}
                  style={{ width: 18, height: 18, accentColor: colors.accent }}
                />
                Enabled
              </label>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div>
                <label style={{ fontSize: 12, color: colors.textMuted, display: 'block', marginBottom: 6 }}>
                  Severity Threshold
                </label>
                <select
                  value={pref.severity_threshold}
                  onChange={e => updatePref(idx, 'severity_threshold', e.target.value)}
                  style={selectStyle}
                >
                  {severityLevels.map(s => (
                    <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)} and above</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: 12, color: colors.textMuted, display: 'block', marginBottom: 6 }}>
                  Digest Frequency
                </label>
                <select
                  value={pref.digest_frequency}
                  onChange={e => updatePref(idx, 'digest_frequency', e.target.value)}
                  style={selectStyle}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>

              {pref.channel === 'slack' && (
                <>
                  <div>
                    <label style={{ fontSize: 12, color: colors.textMuted, display: 'block', marginBottom: 6 }}>
                      Quiet Hours Start
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={23}
                      value={pref.quiet_hours_start ?? ''}
                      onChange={e => updatePref(idx, 'quiet_hours_start', e.target.value ? Number(e.target.value) : null)}
                      placeholder="e.g. 23"
                      style={numberInputStyle}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, color: colors.textMuted, display: 'block', marginBottom: 6 }}>
                      Quiet Hours End
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={23}
                      value={pref.quiet_hours_end ?? ''}
                      onChange={e => updatePref(idx, 'quiet_hours_end', e.target.value ? Number(e.target.value) : null)}
                      placeholder="e.g. 7"
                      style={numberInputStyle}
                    />
                  </div>
                </>
              )}
            </div>

            <div style={{ marginTop: 16 }}>
              <label style={{ fontSize: 12, color: colors.textMuted, display: 'block', marginBottom: 8 }}>
                Service Subscriptions (empty = all services)
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {knownServices.map(svc => (
                  <button
                    key={svc}
                    onClick={() => toggleService(idx, svc)}
                    style={{
                      padding: '4px 12px', borderRadius: 16, fontSize: 13,
                      border: `1px solid ${pref.services.includes(svc) ? colors.accent : colors.border}`,
                      background: pref.services.includes(svc) ? 'rgba(59,130,246,0.15)' : colors.bgCard,
                      color: pref.services.includes(svc) ? colors.accent : colors.textSecondary,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {svc}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}

        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
          <button
            onClick={handleTest}
            style={btn}
          >
            {testSent ? 'Test Sent!' : 'Send Test Notification'}
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            style={{
              ...btnPrimary,
              cursor: saving ? 'not-allowed' : 'pointer',
              opacity: saving ? 0.7 : 1,
            }}
          >
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </div>
    </DashboardShell>
  );
}
