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

// Bottom bar items for quick access
const BOTTOM_BAR: NavItem[] = [
  { label: 'Home', path: '/dashboard', icon: '\u{1F3E0}' },
  { label: 'Monitor', path: '/live', icon: '\u{1F4E1}' },
  { label: 'Analytics', path: '/analytics', icon: '\u{1F4C8}' },
  { label: 'Alerts', path: '/predictions', icon: '\u{1F514}' },
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
        <button
          onClick={() => setDrawerOpen(true)}
          style={{ background: 'none', border: 'none', color: colors.text, fontSize: 22, cursor: 'pointer', padding: 4 }}
          aria-label="Open navigation menu"
        >
          ☰
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 14, boxShadow: '0 0 10px rgba(59,130,246,0.3)',
          }}>⚡</div>
          <span style={{
            fontWeight: 800, fontSize: 15,
            background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>DevOps AI</span>
        </div>
        <div style={{ width: 30 }} />
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
              <div style={{
                width: 32, height: 32, borderRadius: 9,
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 16, boxShadow: '0 0 12px rgba(59,130,246,0.3)',
              }}>⚡</div>
              <div>
                <span style={{
                  fontWeight: 800, fontSize: 15, display: 'block', lineHeight: 1,
                  background: 'linear-gradient(135deg, #f0f0f0, #a1a1aa)',
                  WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                }}>DevOps AI</span>
                <span style={{ fontSize: 8, fontWeight: 700, color: '#3b82f680', letterSpacing: 2, textTransform: 'uppercase' as const }}>ASSISTANT</span>
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

      {/* Bottom tab bar */}
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: 56,
          background: 'rgba(6,6,15,0.95)',
          backdropFilter: 'blur(20px)',
          borderTop: `1px solid ${colors.border}`,
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center',
          zIndex: 1000,
          paddingBottom: 'env(safe-area-inset-bottom, 0)',
        }}
      >
        {BOTTOM_BAR.map((item) => {
          const active = pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 2,
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: active ? '#60a5fa' : colors.textDim,
                fontSize: 10,
                fontWeight: active ? 600 : 400,
                padding: '4px 12px',
                minWidth: 60,
                transition: 'color 0.15s ease',
              }}
            >
              <span style={{ fontSize: 20, filter: active ? 'drop-shadow(0 0 4px rgba(59,130,246,0.5))' : 'none' }}>{item.icon}</span>
              {item.label}
            </button>
          );
        })}
        <button
          onClick={() => setDrawerOpen(true)}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: colors.textDim,
            fontSize: 10,
            padding: '4px 12px',
            minWidth: 60,
          }}
        >
          <span style={{ fontSize: 20 }}>⋯</span>
          More
        </button>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideRight { from { transform: translateX(-100%); } to { transform: translateX(0); } }
      `}</style>
    </>
  );
}
