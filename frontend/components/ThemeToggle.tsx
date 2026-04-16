'use client';

import { useState } from 'react';
import { useTheme, THEME_PRESETS, ThemeMode } from '@/lib/theme-context';

export default function ThemeToggle() {
  const { theme, preset, resolvedMode, setTheme, setPreset, colors } = useTheme();
  const [showPanel, setShowPanel] = useState(false);

  const modeIcon = theme === 'dark' ? '\u{1F319}' : theme === 'light' ? '\u{2600}\uFE0F' : '\u{1F4BB}';
  const modeLabel = theme === 'dark' ? 'Dark' : theme === 'light' ? 'Light' : 'System';

  const modes: { key: ThemeMode; icon: string; label: string }[] = [
    { key: 'light', icon: '\u{2600}\uFE0F', label: 'Light' },
    { key: 'dark', icon: '\u{1F319}', label: 'Dark' },
    { key: 'system', icon: '\u{1F4BB}', label: 'System' },
  ];

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setShowPanel(!showPanel)}
        aria-label="Theme settings"
        style={{
          background: colors.bgSecondary,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
          padding: '6px 12px',
          cursor: 'pointer',
          fontSize: 14,
          color: colors.textSecondary,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          transition: 'all 0.2s',
        }}
      >
        {modeIcon} {modeLabel}
      </button>

      {showPanel && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 90 }}
            onClick={() => setShowPanel(false)}
          />
          <div
            style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: 8,
              width: 260,
              background: colors.bgCard,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
              boxShadow: colors.shadowLg,
              padding: 16,
              zIndex: 100,
            }}
          >
            {/* Mode */}
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                Mode
              </div>
              <div style={{ display: 'flex', gap: 4, background: colors.bgPrimary, borderRadius: 8, padding: 3 }}>
                {modes.map((m) => (
                  <button
                    key={m.key}
                    onClick={() => setTheme(m.key)}
                    style={{
                      flex: 1,
                      padding: '6px 0',
                      borderRadius: 6,
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: 12,
                      fontWeight: 500,
                      background: theme === m.key ? colors.accent : 'transparent',
                      color: theme === m.key ? '#fff' : colors.textMuted,
                      transition: 'all 0.2s',
                    }}
                  >
                    {m.icon} {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Presets (only for dark mode) */}
            {resolvedMode === 'dark' && (
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                  Theme
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  {THEME_PRESETS.map((p) => (
                    <button
                      key={p.key}
                      onClick={() => setPreset(p.key)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '8px 10px',
                        borderRadius: 8,
                        border: preset === p.key ? `2px solid ${p.accent}` : `1px solid ${colors.border}`,
                        background: preset === p.key ? p.bg : colors.bgPrimary,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                    >
                      <div
                        style={{
                          width: 14,
                          height: 14,
                          borderRadius: '50%',
                          background: p.accent,
                          boxShadow: preset === p.key ? `0 0 8px ${p.accent}` : 'none',
                        }}
                      />
                      <span style={{ fontSize: 12, color: colors.textSecondary, fontWeight: preset === p.key ? 600 : 400 }}>
                        {p.label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
