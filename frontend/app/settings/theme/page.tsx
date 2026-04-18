'use client';

import { useTheme, THEME_PRESETS, ThemeMode } from '@/lib/theme-context';
import ThemeToggle from '@/components/ThemeToggle';
import DashboardShell from '@/components/DashboardShell';
import { colors as themeColors } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

export default function ThemeSettingsPage() {
  const { theme, preset, colors, resolvedMode, setTheme, setPreset } = useTheme();
  const { isMobile } = useBreakpoint();

  const modes: { key: ThemeMode; icon: string; label: string; desc: string }[] = [
    { key: 'light', icon: '\u{2600}\uFE0F', label: 'Light', desc: 'Bright theme for daytime use' },
    { key: 'dark', icon: '\u{1F319}', label: 'Dark', desc: 'Easy on the eyes for low-light' },
    { key: 'system', icon: '\u{1F4BB}', label: 'System', desc: 'Follows your OS preference' },
  ];

  const colorSamples = [
    { label: 'Accent', color: colors.accent },
    { label: 'Success', color: colors.success },
    { label: 'Warning', color: colors.warning },
    { label: 'Danger', color: colors.danger },
    { label: 'Info', color: colors.info },
    { label: 'Chart 1', color: colors.chart1 },
    { label: 'Chart 2', color: colors.chart2 },
    { label: 'Chart 3', color: colors.chart3 },
  ];

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 900, margin: '0 auto' }}>
        <div className="slide-up" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <h1 style={{ fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Theme Settings
            </h1>
            <p style={{ color: themeColors.textMuted, fontSize: 13, margin: '4px 0 0' }}>
              Customize the look and feel of your dashboard
            </p>
          </div>
          <ThemeToggle />
        </div>

        {/* Mode Selection */}
        <div
          style={{
            background: themeColors.bgCard,
            backdropFilter: 'blur(12px)',
            border: `1px solid ${themeColors.border}`,
            borderRadius: 14,
            padding: 20,
            marginBottom: 20,
          }}
        >
          <h2 style={{ fontSize: 16, fontWeight: 600, color: themeColors.text, margin: '0 0 14px' }}>
            Appearance Mode
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 12 }}>
            {modes.map((m) => (
              <button
                key={m.key}
                onClick={() => setTheme(m.key)}
                style={{
                  padding: 16,
                  borderRadius: 10,
                  border: theme === m.key ? `2px solid ${themeColors.accent}` : `1px solid ${themeColors.border}`,
                  background: theme === m.key ? 'rgba(59,130,246,0.1)' : themeColors.bgElevated,
                  cursor: 'pointer',
                  textAlign: 'center' as const,
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ fontSize: 28, marginBottom: 8 }}>{m.icon}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: themeColors.text }}>{m.label}</div>
                <div style={{ fontSize: 11, color: themeColors.textMuted, marginTop: 4 }}>{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Theme Presets */}
        <div
          style={{
            background: themeColors.bgCard,
            backdropFilter: 'blur(12px)',
            border: `1px solid ${themeColors.border}`,
            borderRadius: 14,
            padding: 20,
            marginBottom: 20,
            opacity: resolvedMode === 'dark' ? 1 : 0.5,
            pointerEvents: resolvedMode === 'dark' ? 'auto' : 'none',
          }}
        >
          <h2 style={{ fontSize: 16, fontWeight: 600, color: themeColors.text, margin: '0 0 4px' }}>
            Color Theme
          </h2>
          <p style={{ color: themeColors.textMuted, fontSize: 12, margin: '0 0 14px' }}>
            {resolvedMode === 'dark' ? 'Choose a color scheme for dark mode' : 'Switch to dark mode to select a color theme'}
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 12 }}>
            {THEME_PRESETS.map((p) => (
              <button
                key={p.key}
                onClick={() => setPreset(p.key)}
                style={{
                  padding: 16,
                  borderRadius: 10,
                  border: preset === p.key ? `2px solid ${p.accent}` : `1px solid ${themeColors.border}`,
                  background: p.bg,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ display: 'flex', gap: 4, marginBottom: 10, justifyContent: 'center' }}>
                  <div style={{ width: 20, height: 20, borderRadius: '50%', background: p.accent, boxShadow: preset === p.key ? `0 0 10px ${p.accent}` : 'none' }} />
                  <div style={{ width: 20, height: 20, borderRadius: '50%', background: p.accent + '60' }} />
                  <div style={{ width: 20, height: 20, borderRadius: '50%', background: p.accent + '30' }} />
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#e2e8f0' }}>{p.label}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Preview */}
        <div
          style={{
            background: themeColors.bgCard,
            backdropFilter: 'blur(12px)',
            border: `1px solid ${themeColors.border}`,
            borderRadius: 14,
            padding: 20,
            marginBottom: 20,
          }}
        >
          <h2 style={{ fontSize: 16, fontWeight: 600, color: themeColors.text, margin: '0 0 14px' }}>
            Color Palette Preview
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: 12 }}>
            {colorSamples.map((s) => (
              <div key={s.label} style={{ textAlign: 'center' as const }}>
                <div
                  style={{
                    width: '100%',
                    height: 48,
                    borderRadius: 8,
                    background: s.color,
                    marginBottom: 6,
                    boxShadow: `0 2px 8px ${s.color}40`,
                  }}
                />
                <div style={{ fontSize: 11, color: themeColors.textMuted }}>{s.label}</div>
                <div style={{ fontSize: 10, color: themeColors.textDim, fontFamily: 'monospace' }}>{s.color}</div>
              </div>
            ))}
          </div>

          {/* Background previews */}
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: themeColors.textMuted, marginBottom: 8 }}>Backgrounds</div>
            <div style={{ display: 'flex', gap: 8 }}>
              {[
                { label: 'Primary', bg: colors.bgPrimary },
                { label: 'Secondary', bg: colors.bgSecondary },
                { label: 'Tertiary', bg: colors.bgTertiary },
                { label: 'Card', bg: colors.bgCard },
                { label: 'Hover', bg: colors.bgHover },
              ].map((b) => (
                <div key={b.label} style={{ flex: 1, textAlign: 'center' as const }}>
                  <div
                    style={{
                      height: 36,
                      borderRadius: 6,
                      background: b.bg,
                      border: `1px solid ${themeColors.border}`,
                      marginBottom: 4,
                    }}
                  />
                  <div style={{ fontSize: 10, color: themeColors.textMuted }}>{b.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Text preview */}
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: themeColors.textMuted, marginBottom: 8 }}>Typography</div>
            <div style={{ background: themeColors.bgElevated, borderRadius: 8, padding: 12, border: `1px solid ${themeColors.border}` }}>
              <div style={{ color: themeColors.text, fontSize: 14, fontWeight: 600 }}>Primary text -- headings and important content</div>
              <div style={{ color: themeColors.textSecondary, fontSize: 13, marginTop: 4 }}>Secondary text -- body content and descriptions</div>
              <div style={{ color: themeColors.textMuted, fontSize: 12, marginTop: 4 }}>Muted text -- timestamps, labels, and metadata</div>
            </div>
          </div>

          {/* Component preview */}
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: themeColors.textMuted, marginBottom: 8 }}>Components</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button style={{ padding: '8px 16px', borderRadius: 8, border: 'none', background: themeColors.accentGradient, color: '#fff', cursor: 'pointer', fontWeight: 500, fontSize: 13 }}>
                Primary Button
              </button>
              <button style={{ padding: '8px 16px', borderRadius: 8, border: `1px solid ${themeColors.border}`, background: themeColors.bgElevated, color: themeColors.text, cursor: 'pointer', fontSize: 13 }}>
                Secondary
              </button>
              <span style={{ padding: '4px 10px', borderRadius: 12, background: themeColors.successBg, color: themeColors.success, fontSize: 12, fontWeight: 500, display: 'inline-flex', alignItems: 'center' }}>
                Resolved
              </span>
              <span style={{ padding: '4px 10px', borderRadius: 12, background: themeColors.warningBg, color: themeColors.warning, fontSize: 12, fontWeight: 500, display: 'inline-flex', alignItems: 'center' }}>
                Warning
              </span>
              <span style={{ padding: '4px 10px', borderRadius: 12, background: themeColors.dangerBg, color: themeColors.danger, fontSize: 12, fontWeight: 500, display: 'inline-flex', alignItems: 'center' }}>
                Critical
              </span>
            </div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
