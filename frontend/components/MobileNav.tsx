'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { colors } from '@/lib/theme';

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

const NAV_SECTIONS: { title: string; items: NavItem[] }[] = [
  {
    title: 'Overview',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: '📊' },
      { label: 'Live Metrics', path: '/live', icon: '⚡' },
      { label: 'AI Chat', path: '/chat', icon: '💬' },
    ],
  },
  {
    title: 'Monitoring',
    items: [
      { label: 'System Health', path: '/system-health', icon: '🫀' },
      { label: 'Analytics', path: '/analytics', icon: '📈' },
      { label: 'Performance', path: '/performance', icon: '🏎️' },
      { label: 'Predictions', path: '/predictions', icon: '🔮' },
    ],
  },
  {
    title: 'AI Agents',
    items: [
      { label: 'Agent Status', path: '/agents/status', icon: '🤖' },
      { label: 'Intelligence', path: '/agent-intelligence', icon: '🧠' },
      { label: 'Decision Graph', path: '/decision-graph', icon: '🕸️' },
      { label: 'Incident Flow', path: '/incident-flow', icon: '▶️' },
      { label: 'Agent Builder', path: '/agents/builder', icon: '🏗️' },
      { label: 'Marketplace', path: '/marketplace', icon: '🛒' },
      { label: 'Learning', path: '/learning', icon: '📚' },
    ],
  },
  {
    title: 'Operations',
    items: [
      { label: 'Workflows', path: '/workflows', icon: '🔄' },
      { label: 'Runbooks', path: '/runbooks', icon: '📋' },
      { label: 'Maintenance', path: '/maintenance', icon: '🔧' },
      { label: 'Chaos Testing', path: '/chaos', icon: '💥' },
      { label: 'Scenarios', path: '/scenarios', icon: '🔮' },
      { label: 'Post-Mortem', path: '/postmortem', icon: '📝' },
      { label: 'Log Analysis', path: '/log-analysis', icon: '📄' },
      { label: 'Capacity Planning', path: '/capacity-planning', icon: '📐' },
    ],
  },
  {
    title: 'Security',
    items: [
      { label: 'Security', path: '/security', icon: '🛡️' },
      { label: 'Compliance', path: '/compliance', icon: '✅' },
      { label: 'Audit Log', path: '/audit', icon: '📝' },
      { label: 'Disaster Recovery', path: '/disaster-recovery', icon: '🔥' },
    ],
  },
  {
    title: 'Insights',
    items: [
      { label: 'Reports', path: '/reports', icon: '📊' },
      { label: 'Cost Analysis', path: '/costs', icon: '💰' },
      { label: 'SLA Tracking', path: '/sla', icon: '📉' },
      { label: 'Executive View', path: '/executive', icon: '👔' },
      { label: 'Visualizations', path: '/visualizations', icon: '📉' },
    ],
  },
  {
    title: 'Settings',
    items: [
      { label: 'Notifications', path: '/notifications', icon: '🔔' },
      { label: 'Integrations', path: '/integrations', icon: '🔌' },
      { label: 'Settings', path: '/settings/notifications', icon: '⚙️' },
    ],
  },
];

export default function MobileNav() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const navigate = (path: string) => {
    router.push(path);
    setDrawerOpen(false);
  };

  return (
    <>
      {/* Top header bar */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: 52,
          background: 'rgba(6,6,15,0.95)',
          backdropFilter: 'blur(20px)',
          borderBottom: `1px solid ${colors.border}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          zIndex: 1000,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <img src="/logo.svg" alt="SentryAI" style={{ width: 28, height: 28, filter: 'drop-shadow(0 0 6px rgba(139,92,246,0.4))' }} />
          <span style={{
            fontWeight: 800, fontSize: 15,
            background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>SentryAI</span>
        </div>
        <div
          onClick={() => setDrawerOpen(true)}
          style={{
            cursor: 'pointer', padding: 10,
            display: 'flex', flexDirection: 'column' as const, gap: 5,
            alignItems: 'flex-end',
          }}
        >
          <span style={{ width: 22, height: 2, borderRadius: 2, background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)', display: 'block' }} />
          <span style={{ width: 16, height: 2, borderRadius: 2, background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)', display: 'block' }} />
          <span style={{ width: 22, height: 2, borderRadius: 2, background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)', display: 'block' }} />
        </div>
      </div>

      {/* Drawer overlay */}
      {drawerOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 2000,
            animation: 'fadeIn 0.2s ease-out',
          }}
          onClick={() => setDrawerOpen(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              bottom: 0,
              width: 280,
              background: 'rgba(6,6,15,0.98)',
              borderRight: `1px solid ${colors.border}`,
              overflowY: 'auto',
              animation: 'slideRight 0.25s ease-out',
              padding: '16px 0',
            }}
          >
            <div style={{ padding: '0 16px 16px', borderBottom: `1px solid ${colors.border}`, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 10 }}>
              <img src="/logo.svg" alt="SentryAI" style={{ width: 32, height: 32, filter: 'drop-shadow(0 0 8px rgba(139,92,246,0.4))' }} />
              <div>
                <span style={{
                  fontWeight: 800, fontSize: 15, display: 'block', lineHeight: 1,
                  background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                }}>SentryAI</span>
                <span style={{ fontSize: 8, fontWeight: 700, color: '#3b82f680', letterSpacing: 2, textTransform: 'uppercase' as const }}>PLATFORM</span>
              </div>
            </div>

            {NAV_SECTIONS.map((section) => (
              <div key={section.title} style={{ marginBottom: 4 }}>
                <div style={{ padding: '10px 16px 4px', fontSize: 10, fontWeight: 700, color: '#3b82f650', textTransform: 'uppercase', letterSpacing: 2 }}>
                  {section.title}
                </div>
                {section.items.map((item) => {
                  const active = pathname === item.path || pathname.startsWith(item.path + '/');
                  return (
                    <button
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        width: '100%',
                        padding: '9px 16px',
                        border: 'none',
                        background: active ? 'rgba(59,130,246,0.1)' : 'transparent',
                        color: active ? '#60a5fa' : colors.textSecondary,
                        cursor: 'pointer',
                        fontSize: 13,
                        fontWeight: active ? 600 : 400,
                        textAlign: 'left',
                        borderLeft: active ? '3px solid #3b82f6' : '3px solid transparent',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <span style={{ fontSize: 16, filter: active ? 'drop-shadow(0 0 4px rgba(59,130,246,0.4))' : 'none' }}>{item.icon}</span>
                      {item.label}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideRight { from { transform: translateX(-100%); } to { transform: translateX(0); } }
      `}</style>
    </>
  );
}
