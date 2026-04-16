'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

// ── Theme Types ───────────────────────────────────────────────────────
export type ThemeMode = 'light' | 'dark' | 'system';
export type ThemePreset = 'default' | 'midnight' | 'ocean' | 'forest' | 'sunset' | 'cyberpunk';

export interface ThemeColors {
  // Backgrounds
  bgPrimary: string;
  bgSecondary: string;
  bgTertiary: string;
  bgCard: string;
  bgHover: string;
  bgInput: string;
  bgOverlay: string;

  // Text
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  textInverse: string;

  // Borders
  border: string;
  borderLight: string;
  borderFocus: string;

  // Brand / Accent
  accent: string;
  accentHover: string;
  accentMuted: string;

  // Status
  success: string;
  successBg: string;
  warning: string;
  warningBg: string;
  danger: string;
  dangerBg: string;
  info: string;
  infoBg: string;

  // Chart
  chart1: string;
  chart2: string;
  chart3: string;
  chart4: string;
  chart5: string;
  chart6: string;

  // Shadows
  shadow: string;
  shadowLg: string;
}

export interface ThemeConfig {
  mode: ThemeMode;
  preset: ThemePreset;
  colors: ThemeColors;
  resolvedMode: 'light' | 'dark'; // actual mode after resolving 'system'
}

// ── Theme Presets ─────────────────────────────────────────────────────

const DARK_THEMES: Record<string, ThemeColors> = {
  default: {
    bgPrimary: '#0f172a', bgSecondary: '#1e293b', bgTertiary: '#334155', bgCard: '#1e293b',
    bgHover: '#334155', bgInput: '#0f172a', bgOverlay: 'rgba(0,0,0,0.6)',
    textPrimary: '#f1f5f9', textSecondary: '#cbd5e1', textMuted: '#94a3b8', textInverse: '#0f172a',
    border: '#334155', borderLight: '#1e293b', borderFocus: '#3b82f6',
    accent: '#3b82f6', accentHover: '#2563eb', accentMuted: '#1e40af',
    success: '#10b981', successBg: '#10b98120', warning: '#f59e0b', warningBg: '#f59e0b20',
    danger: '#ef4444', dangerBg: '#ef444420', info: '#06b6d4', infoBg: '#06b6d420',
    chart1: '#3b82f6', chart2: '#10b981', chart3: '#f59e0b', chart4: '#ef4444', chart5: '#8b5cf6', chart6: '#06b6d4',
    shadow: '0 1px 3px rgba(0,0,0,0.4)', shadowLg: '0 10px 30px rgba(0,0,0,0.5)',
  },
  midnight: {
    bgPrimary: '#09090b', bgSecondary: '#18181b', bgTertiary: '#27272a', bgCard: '#18181b',
    bgHover: '#27272a', bgInput: '#09090b', bgOverlay: 'rgba(0,0,0,0.7)',
    textPrimary: '#fafafa', textSecondary: '#d4d4d8', textMuted: '#a1a1aa', textInverse: '#09090b',
    border: '#27272a', borderLight: '#18181b', borderFocus: '#a78bfa',
    accent: '#a78bfa', accentHover: '#8b5cf6', accentMuted: '#6d28d9',
    success: '#34d399', successBg: '#34d39920', warning: '#fbbf24', warningBg: '#fbbf2420',
    danger: '#f87171', dangerBg: '#f8717120', info: '#67e8f9', infoBg: '#67e8f920',
    chart1: '#a78bfa', chart2: '#34d399', chart3: '#fbbf24', chart4: '#f87171', chart5: '#fb923c', chart6: '#67e8f9',
    shadow: '0 1px 3px rgba(0,0,0,0.6)', shadowLg: '0 10px 30px rgba(0,0,0,0.7)',
  },
  ocean: {
    bgPrimary: '#0c1222', bgSecondary: '#152238', bgTertiary: '#1e3a5f', bgCard: '#152238',
    bgHover: '#1e3a5f', bgInput: '#0c1222', bgOverlay: 'rgba(12,18,34,0.7)',
    textPrimary: '#e0f2fe', textSecondary: '#bae6fd', textMuted: '#7dd3fc', textInverse: '#0c1222',
    border: '#1e3a5f', borderLight: '#152238', borderFocus: '#0ea5e9',
    accent: '#0ea5e9', accentHover: '#0284c7', accentMuted: '#0369a1',
    success: '#2dd4bf', successBg: '#2dd4bf20', warning: '#fcd34d', warningBg: '#fcd34d20',
    danger: '#fb7185', dangerBg: '#fb718520', info: '#38bdf8', infoBg: '#38bdf820',
    chart1: '#0ea5e9', chart2: '#2dd4bf', chart3: '#fcd34d', chart4: '#fb7185', chart5: '#a78bfa', chart6: '#38bdf8',
    shadow: '0 1px 3px rgba(0,0,0,0.5)', shadowLg: '0 10px 30px rgba(0,0,0,0.6)',
  },
  forest: {
    bgPrimary: '#0a1a0e', bgSecondary: '#132a18', bgTertiary: '#1a3d22', bgCard: '#132a18',
    bgHover: '#1a3d22', bgInput: '#0a1a0e', bgOverlay: 'rgba(10,26,14,0.7)',
    textPrimary: '#ecfdf5', textSecondary: '#bbf7d0', textMuted: '#86efac', textInverse: '#0a1a0e',
    border: '#1a3d22', borderLight: '#132a18', borderFocus: '#22c55e',
    accent: '#22c55e', accentHover: '#16a34a', accentMuted: '#15803d',
    success: '#4ade80', successBg: '#4ade8020', warning: '#facc15', warningBg: '#facc1520',
    danger: '#f87171', dangerBg: '#f8717120', info: '#67e8f9', infoBg: '#67e8f920',
    chart1: '#22c55e', chart2: '#4ade80', chart3: '#facc15', chart4: '#f87171', chart5: '#c084fc', chart6: '#67e8f9',
    shadow: '0 1px 3px rgba(0,0,0,0.5)', shadowLg: '0 10px 30px rgba(0,0,0,0.6)',
  },
  sunset: {
    bgPrimary: '#1a0e0a', bgSecondary: '#2a1810', bgTertiary: '#3d2418', bgCard: '#2a1810',
    bgHover: '#3d2418', bgInput: '#1a0e0a', bgOverlay: 'rgba(26,14,10,0.7)',
    textPrimary: '#fff7ed', textSecondary: '#fed7aa', textMuted: '#fdba74', textInverse: '#1a0e0a',
    border: '#3d2418', borderLight: '#2a1810', borderFocus: '#f97316',
    accent: '#f97316', accentHover: '#ea580c', accentMuted: '#c2410c',
    success: '#4ade80', successBg: '#4ade8020', warning: '#fbbf24', warningBg: '#fbbf2420',
    danger: '#ef4444', dangerBg: '#ef444420', info: '#38bdf8', infoBg: '#38bdf820',
    chart1: '#f97316', chart2: '#fb923c', chart3: '#fbbf24', chart4: '#ef4444', chart5: '#a78bfa', chart6: '#38bdf8',
    shadow: '0 1px 3px rgba(0,0,0,0.5)', shadowLg: '0 10px 30px rgba(0,0,0,0.6)',
  },
  cyberpunk: {
    bgPrimary: '#0a0a1a', bgSecondary: '#14142b', bgTertiary: '#1e1e3f', bgCard: '#14142b',
    bgHover: '#1e1e3f', bgInput: '#0a0a1a', bgOverlay: 'rgba(10,10,26,0.8)',
    textPrimary: '#f0f0ff', textSecondary: '#c4b5fd', textMuted: '#a78bfa', textInverse: '#0a0a1a',
    border: '#2e1e5e', borderLight: '#1e1e3f', borderFocus: '#e879f9',
    accent: '#e879f9', accentHover: '#d946ef', accentMuted: '#a21caf',
    success: '#4ade80', successBg: '#4ade8020', warning: '#facc15', warningBg: '#facc1520',
    danger: '#fb7185', dangerBg: '#fb718520', info: '#22d3ee', infoBg: '#22d3ee20',
    chart1: '#e879f9', chart2: '#22d3ee', chart3: '#facc15', chart4: '#fb7185', chart5: '#a78bfa', chart6: '#4ade80',
    shadow: '0 1px 3px rgba(100,0,200,0.3)', shadowLg: '0 10px 30px rgba(100,0,200,0.4)',
  },
};

const LIGHT_THEMES: Record<string, ThemeColors> = {
  default: {
    bgPrimary: '#ffffff', bgSecondary: '#f8fafc', bgTertiary: '#f1f5f9', bgCard: '#ffffff',
    bgHover: '#f1f5f9', bgInput: '#ffffff', bgOverlay: 'rgba(0,0,0,0.3)',
    textPrimary: '#0f172a', textSecondary: '#475569', textMuted: '#94a3b8', textInverse: '#ffffff',
    border: '#e2e8f0', borderLight: '#f1f5f9', borderFocus: '#3b82f6',
    accent: '#3b82f6', accentHover: '#2563eb', accentMuted: '#93c5fd',
    success: '#16a34a', successBg: '#dcfce7', warning: '#d97706', warningBg: '#fef3c7',
    danger: '#dc2626', dangerBg: '#fee2e2', info: '#0891b2', infoBg: '#cffafe',
    chart1: '#3b82f6', chart2: '#16a34a', chart3: '#d97706', chart4: '#dc2626', chart5: '#7c3aed', chart6: '#0891b2',
    shadow: '0 1px 3px rgba(0,0,0,0.1)', shadowLg: '0 10px 30px rgba(0,0,0,0.12)',
  },
};

function getThemeColors(mode: 'light' | 'dark', preset: ThemePreset): ThemeColors {
  if (mode === 'light') return LIGHT_THEMES.default;
  return DARK_THEMES[preset] || DARK_THEMES.default;
}

// ── Apply CSS variables ───────────────────────────────────────────────
function applyThemeCSS(colors: ThemeColors) {
  const root = document.documentElement;
  Object.entries(colors).forEach(([key, value]) => {
    root.style.setProperty(`--${camelToKebab(key)}`, value);
  });
}

function camelToKebab(str: string): string {
  return str.replace(/([A-Z0-9])/g, '-$1').toLowerCase();
}

// ── Context ───────────────────────────────────────────────────────────

interface ThemeContextType {
  theme: ThemeMode;
  preset: ThemePreset;
  colors: ThemeColors;
  resolvedMode: 'light' | 'dark';
  setTheme: (mode: ThemeMode) => void;
  setPreset: (preset: ThemePreset) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'dark',
  preset: 'default',
  colors: DARK_THEMES.default,
  resolvedMode: 'dark',
  setTheme: () => {},
  setPreset: () => {},
  toggleTheme: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>('dark');
  const [preset, setPresetState] = useState<ThemePreset>('default');
  const [resolvedMode, setResolvedMode] = useState<'light' | 'dark'>('dark');

  // Resolve system preference
  const resolveMode = useCallback((m: ThemeMode): 'light' | 'dark' => {
    if (m === 'system') {
      if (typeof window !== 'undefined') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      return 'dark';
    }
    return m;
  }, []);

  // Load saved preferences
  useEffect(() => {
    const savedMode = localStorage.getItem('theme-mode') as ThemeMode | null;
    const savedPreset = localStorage.getItem('theme-preset') as ThemePreset | null;
    if (savedMode) setMode(savedMode);
    if (savedPreset) setPresetState(savedPreset);

    const resolved = resolveMode(savedMode || 'dark');
    setResolvedMode(resolved);
    applyThemeCSS(getThemeColors(resolved, savedPreset || 'default'));
    document.documentElement.setAttribute('data-theme', resolved);
  }, [resolveMode]);

  // Listen for system theme changes
  useEffect(() => {
    if (mode !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => {
      const resolved = e.matches ? 'dark' : 'light';
      setResolvedMode(resolved);
      applyThemeCSS(getThemeColors(resolved, preset));
      document.documentElement.setAttribute('data-theme', resolved);
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [mode, preset]);

  const setTheme = useCallback((newMode: ThemeMode) => {
    setMode(newMode);
    localStorage.setItem('theme-mode', newMode);
    const resolved = resolveMode(newMode);
    setResolvedMode(resolved);
    applyThemeCSS(getThemeColors(resolved, preset));
    document.documentElement.setAttribute('data-theme', resolved);
  }, [preset, resolveMode]);

  const setPreset = useCallback((newPreset: ThemePreset) => {
    setPresetState(newPreset);
    localStorage.setItem('theme-preset', newPreset);
    applyThemeCSS(getThemeColors(resolvedMode, newPreset));
  }, [resolvedMode]);

  const toggleTheme = useCallback(() => {
    const next: ThemeMode = mode === 'dark' ? 'light' : mode === 'light' ? 'system' : 'dark';
    setTheme(next);
  }, [mode, setTheme]);

  const colors = getThemeColors(resolvedMode, preset);

  return (
    <ThemeContext.Provider value={{ theme: mode, preset, colors, resolvedMode, setTheme, setPreset, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);

export const THEME_PRESETS: { key: ThemePreset; label: string; accent: string; bg: string }[] = [
  { key: 'default', label: 'Slate', accent: '#3b82f6', bg: '#0f172a' },
  { key: 'midnight', label: 'Midnight', accent: '#a78bfa', bg: '#09090b' },
  { key: 'ocean', label: 'Ocean', accent: '#0ea5e9', bg: '#0c1222' },
  { key: 'forest', label: 'Forest', accent: '#22c55e', bg: '#0a1a0e' },
  { key: 'sunset', label: 'Sunset', accent: '#f97316', bg: '#1a0e0a' },
  { key: 'cyberpunk', label: 'Cyberpunk', accent: '#e879f9', bg: '#0a0a1a' },
];
