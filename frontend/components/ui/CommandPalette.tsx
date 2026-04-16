'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon?: string;
  shortcut?: string;
  action: () => void;
  category?: string;
}

const DEFAULT_COMMANDS: CommandItem[] = [
  { id: 'dashboard', label: 'Go to Dashboard', icon: '\u{1F4CA}', category: 'Navigation', action: () => {}, shortcut: 'G D' },
  { id: 'incidents', label: 'View Incidents', icon: '\u{1F6A8}', category: 'Navigation', action: () => {} },
  { id: 'analytics', label: 'Analytics', icon: '\u{1F4C8}', category: 'Navigation', action: () => {} },
  { id: 'sla', label: 'SLA Dashboard', icon: '\u{1F3AF}', category: 'Navigation', action: () => {} },
  { id: 'costs', label: 'Cost Analysis', icon: '\u{1F4B0}', category: 'Navigation', action: () => {} },
  { id: 'visualizations', label: 'Visualizations', icon: '\u{1F4CA}', category: 'Navigation', action: () => {} },
  { id: 'workflows', label: 'Workflows', icon: '\u{26A1}', category: 'Navigation', action: () => {} },
  { id: 'runbooks', label: 'Runbooks', icon: '\u{1F4D6}', category: 'Navigation', action: () => {} },
  { id: 'chaos', label: 'Chaos Engineering', icon: '\u{1F9EA}', category: 'Navigation', action: () => {} },
  { id: 'integrations', label: 'Integrations', icon: '\u{1F517}', category: 'Navigation', action: () => {} },
  { id: 'maintenance', label: 'Maintenance', icon: '\u{1F527}', category: 'Navigation', action: () => {} },
  { id: 'settings', label: 'Theme Settings', icon: '\u{1F3A8}', category: 'Settings', action: () => {} },
  { id: 'notifications', label: 'Notification Settings', icon: '\u{1F514}', category: 'Settings', action: () => {} },
  { id: 'reports', label: 'Reports', icon: '\u{1F4C4}', category: 'Navigation', action: () => {} },
  { id: 'predictions', label: 'Predictions', icon: '\u{1F52E}', category: 'Navigation', action: () => {} },
  { id: 'executive', label: 'Executive Dashboard', icon: '\u{1F451}', category: 'Navigation', action: () => {} },
  { id: 'live', label: 'Live Monitor', icon: '\u{1F4E1}', category: 'Navigation', action: () => {} },
  { id: 'chat', label: 'AI Chat', icon: '\u{1F916}', category: 'Actions', action: () => {} },
];

const ROUTE_MAP: Record<string, string> = {
  dashboard: '/dashboard',
  incidents: '/dashboard',
  analytics: '/analytics',
  sla: '/sla',
  costs: '/costs',
  visualizations: '/visualizations',
  workflows: '/workflows',
  runbooks: '/runbooks',
  chaos: '/chaos',
  integrations: '/integrations',
  maintenance: '/maintenance',
  settings: '/settings/theme',
  notifications: '/settings/notifications',
  reports: '/reports',
  predictions: '/predictions',
  executive: '/executive',
  live: '/live',
  chat: '/chat',
};

export default function CommandPalette({ extraCommands = [] }: { extraCommands?: CommandItem[] }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const commands: CommandItem[] = [...DEFAULT_COMMANDS, ...extraCommands].map((cmd) => ({
    ...cmd,
    action: cmd.action.toString() === '() => {}' && ROUTE_MAP[cmd.id]
      ? () => { router.push(ROUTE_MAP[cmd.id]); setOpen(false); }
      : () => { cmd.action(); setOpen(false); },
  }));

  const filtered = query
    ? commands.filter((c) =>
        c.label.toLowerCase().includes(query.toLowerCase()) ||
        (c.description || '').toLowerCase().includes(query.toLowerCase()) ||
        (c.category || '').toLowerCase().includes(query.toLowerCase())
      )
    : commands;

  const grouped = filtered.reduce<Record<string, CommandItem[]>>((acc, item) => {
    const cat = item.category || 'General';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {});

  const flatFiltered = Object.values(grouped).flat();

  // Keyboard shortcut to open
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
        setQuery('');
        setSelectedIndex(0);
      }
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, flatFiltered.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === 'Enter' && flatFiltered[selectedIndex]) {
        flatFiltered[selectedIndex].action();
      }
    },
    [flatFiltered, selectedIndex]
  );

  if (!open) return null;

  let globalIndex = -1;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        justifyContent: 'center',
        paddingTop: 100,
        background: 'rgba(0,0,0,0.5)',
        backdropFilter: 'blur(4px)',
      }}
      onClick={() => setOpen(false)}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 560,
          maxHeight: 480,
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: 14,
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Input */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #334155', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ color: '#94a3b8', fontSize: 16 }}>{'\u{1F50D}'}</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
            onKeyDown={handleKeyDown}
            placeholder="Type a command or search..."
            style={{
              flex: 1,
              background: 'none',
              border: 'none',
              outline: 'none',
              color: '#f1f5f9',
              fontSize: 15,
            }}
          />
          <kbd style={{ padding: '2px 6px', borderRadius: 4, background: '#334155', color: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}>
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div style={{ overflowY: 'auto', flex: 1, padding: '8px 0' }}>
          {Object.entries(grouped).map(([category, items]) => (
            <div key={category}>
              <div style={{ padding: '8px 16px 4px', fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                {category}
              </div>
              {items.map((item) => {
                globalIndex++;
                const idx = globalIndex;
                return (
                  <div
                    key={item.id}
                    onClick={item.action}
                    style={{
                      padding: '8px 16px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      cursor: 'pointer',
                      background: selectedIndex === idx ? '#334155' : 'transparent',
                      borderLeft: selectedIndex === idx ? '2px solid #3b82f6' : '2px solid transparent',
                    }}
                    onMouseEnter={() => setSelectedIndex(idx)}
                  >
                    <span style={{ fontSize: 16, width: 22, textAlign: 'center' }}>{item.icon || '\u{25B8}'}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 500 }}>{item.label}</div>
                      {item.description && (
                        <div style={{ color: '#64748b', fontSize: 11 }}>{item.description}</div>
                      )}
                    </div>
                    {item.shortcut && (
                      <kbd style={{ padding: '2px 6px', borderRadius: 4, background: '#0f172a', color: '#64748b', fontSize: 10, fontFamily: 'monospace' }}>
                        {item.shortcut}
                      </kbd>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
          {flatFiltered.length === 0 && (
            <div style={{ padding: 24, textAlign: 'center', color: '#64748b', fontSize: 13 }}>
              No commands found for &quot;{query}&quot;
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '8px 16px', borderTop: '1px solid #334155', display: 'flex', gap: 16, justifyContent: 'center' }}>
          {[
            { label: 'Navigate', keys: ['\u2191', '\u2193'] },
            { label: 'Select', keys: ['\u23CE'] },
            { label: 'Close', keys: ['ESC'] },
          ].map((h) => (
            <div key={h.label} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              {h.keys.map((k) => (
                <kbd key={k} style={{ padding: '1px 5px', borderRadius: 3, background: '#0f172a', color: '#64748b', fontSize: 10, fontFamily: 'monospace' }}>
                  {k}
                </kbd>
              ))}
              <span style={{ color: '#64748b', fontSize: 10 }}>{h.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
