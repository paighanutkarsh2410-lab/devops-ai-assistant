'use client';

import { useState, ReactNode } from 'react';

interface Tab {
  key: string;
  label: string;
  icon?: string;
  badge?: number;
  content: ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
  onChange?: (key: string) => void;
  variant?: 'default' | 'pills' | 'underline';
}

export default function Tabs({ tabs, defaultTab, onChange, variant = 'default' }: TabsProps) {
  const [active, setActive] = useState(defaultTab || tabs[0]?.key || '');

  const handleChange = (key: string) => {
    setActive(key);
    onChange?.(key);
  };

  const activeTab = tabs.find((t) => t.key === active);

  const getTabStyle = (isActive: boolean) => {
    const base = {
      padding: '8px 16px',
      cursor: 'pointer',
      fontSize: 13,
      fontWeight: isActive ? 600 : 400,
      border: 'none',
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      transition: 'all 0.2s',
      whiteSpace: 'nowrap' as const,
    };

    if (variant === 'pills') {
      return {
        ...base,
        borderRadius: 8,
        background: isActive ? '#3b82f6' : 'transparent',
        color: isActive ? '#fff' : '#94a3b8',
      };
    }
    if (variant === 'underline') {
      return {
        ...base,
        background: 'transparent',
        color: isActive ? '#e2e8f0' : '#94a3b8',
        borderBottom: isActive ? '2px solid #3b82f6' : '2px solid transparent',
        borderRadius: 0,
        paddingBottom: 10,
      };
    }
    // default
    return {
      ...base,
      borderRadius: 8,
      background: isActive ? '#1e293b' : 'transparent',
      color: isActive ? '#e2e8f0' : '#64748b',
    };
  };

  return (
    <div>
      <div
        style={{
          display: 'flex',
          gap: variant === 'underline' ? 0 : 4,
          background: variant === 'underline' ? 'transparent' : '#0f172a',
          borderRadius: variant === 'underline' ? 0 : 10,
          padding: variant === 'underline' ? 0 : 4,
          borderBottom: variant === 'underline' ? '1px solid #1e293b' : 'none',
          overflowX: 'auto',
          marginBottom: 16,
        }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => handleChange(tab.key)}
            style={getTabStyle(active === tab.key)}
          >
            {tab.icon && <span>{tab.icon}</span>}
            {tab.label}
            {tab.badge != null && tab.badge > 0 && (
              <span
                style={{
                  padding: '1px 6px',
                  borderRadius: 10,
                  background: active === tab.key ? '#ffffff30' : '#334155',
                  color: active === tab.key ? '#fff' : '#94a3b8',
                  fontSize: 10,
                  fontWeight: 600,
                  minWidth: 18,
                  textAlign: 'center',
                }}
              >
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>
      <div>{activeTab?.content}</div>
    </div>
  );
}
