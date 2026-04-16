'use client';

import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

const NAV_SECTIONS: { title: string; items: NavItem[] }[] = [
  {
    title: 'Overview',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: '\u{1F4CA}' },
      { label: 'Live Monitor', path: '/live', icon: '\u{1F4E1}' },
      { label: 'Executive', path: '/executive', icon: '\u{1F451}' },
    ],
  },
  {
    title: 'Analysis',
    items: [
      { label: 'Analytics', path: '/analytics', icon: '\u{1F4C8}' },
      { label: 'Visualizations', path: '/visualizations', icon: '\u{1F4CA}' },
      { label: 'Predictions', path: '/predictions', icon: '\u{1F52E}' },
      { label: 'Costs', path: '/costs', icon: '\u{1F4B0}' },
      { label: 'SLA', path: '/sla', icon: '\u{1F3AF}' },
    ],
  },
  {
    title: 'Operations',
    items: [
      { label: 'Workflows', path: '/workflows', icon: '\u{26A1}' },
      { label: 'Runbooks', path: '/runbooks', icon: '\u{1F4D6}' },
      { label: 'Maintenance', path: '/maintenance', icon: '\u{1F527}' },
      { label: 'Chaos', path: '/chaos', icon: '\u{1F9EA}' },
    ],
  },
  {
    title: 'Configuration',
    items: [
      { label: 'Integrations', path: '/integrations', icon: '\u{1F517}' },
      { label: 'Reports', path: '/reports', icon: '\u{1F4C4}' },
      { label: 'Learning', path: '/learning', icon: '\u{1F9E0}' },
      { label: 'AI Chat', path: '/chat', icon: '\u{1F916}' },
    ],
  },
  {
    title: 'Settings',
    items: [
      { label: 'Theme', path: '/settings/theme', icon: '\u{1F3A8}' },
      { label: 'Notifications', path: '/settings/notifications', icon: '\u{1F514}' },
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
          background: '#0f172a',
          borderBottom: '1px solid #1e293b',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          zIndex: 1000,
        }}
      >
        <button
          onClick={() => setDrawerOpen(true)}
          style={{ background: 'none', border: 'none', color: '#e2e8f0', fontSize: 22, cursor: 'pointer', padding: 4 }}
          aria-label="Open navigation menu"
        >
          {'\u2630'}
        </button>
        <span style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 15 }}>DevOps AI</span>
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
              background: '#0f172a',
              borderRight: '1px solid #1e293b',
              overflowY: 'auto',
              animation: 'slideRight 0.25s ease-out',
              padding: '16px 0',
            }}
          >
            <div style={{ padding: '0 16px 16px', borderBottom: '1px solid #1e293b', marginBottom: 8 }}>
              <span style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 16 }}>DevOps AI Assistant</span>
            </div>

            {NAV_SECTIONS.map((section) => (
              <div key={section.title} style={{ marginBottom: 8 }}>
                <div style={{ padding: '8px 16px', fontSize: 10, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: 1 }}>
                  {section.title}
                </div>
                {section.items.map((item) => (
                  <button
                    key={item.path}
                    onClick={() => navigate(item.path)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      width: '100%',
                      padding: '10px 16px',
                      border: 'none',
                      background: pathname === item.path ? '#1e293b' : 'transparent',
                      color: pathname === item.path ? '#e2e8f0' : '#94a3b8',
                      cursor: 'pointer',
                      fontSize: 13,
                      textAlign: 'left',
                      borderLeft: pathname === item.path ? '3px solid #3b82f6' : '3px solid transparent',
                    }}
                  >
                    <span style={{ fontSize: 16 }}>{item.icon}</span>
                    {item.label}
                  </button>
                ))}
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
          background: '#0f172a',
          borderTop: '1px solid #1e293b',
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center',
          zIndex: 1000,
          paddingBottom: 'env(safe-area-inset-bottom, 0)',
        }}
      >
        {BOTTOM_BAR.map((item) => (
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
              color: pathname === item.path ? '#3b82f6' : '#64748b',
              fontSize: 10,
              padding: '4px 12px',
              minWidth: 60,
            }}
          >
            <span style={{ fontSize: 20 }}>{item.icon}</span>
            {item.label}
          </button>
        ))}
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
            color: '#64748b',
            fontSize: 10,
            padding: '4px 12px',
            minWidth: 60,
          }}
        >
          <span style={{ fontSize: 20 }}>{'\u2026'}</span>
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
