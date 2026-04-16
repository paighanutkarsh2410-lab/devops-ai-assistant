// Shared dark theme styles - import into any page
// Premium dark glass-morphism aesthetic

import { CSSProperties } from 'react';

// ── Color Palette ──────────────────────────────────────────
export const colors = {
  // Backgrounds
  bg: '#04040c',
  bgCard: 'rgba(255,255,255,0.025)',
  bgCardHover: 'rgba(255,255,255,0.05)',
  bgElevated: 'rgba(255,255,255,0.04)',
  bgInput: 'rgba(255,255,255,0.04)',
  bgSidebar: 'rgba(6,6,15,0.95)',
  bgOverlay: 'rgba(0,0,0,0.7)',

  // Text
  text: '#f0f0f0',
  textSecondary: '#a1a1aa',
  textMuted: '#71717a',
  textDim: '#52525b',

  // Borders
  border: 'rgba(255,255,255,0.06)',
  borderLight: 'rgba(255,255,255,0.04)',
  borderHover: 'rgba(255,255,255,0.12)',
  borderFocus: '#3b82f6',

  // Accent gradient
  accent: '#3b82f6',
  accentHover: '#2563eb',
  accentGradient: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
  accentGradientHover: 'linear-gradient(135deg, #2563eb, #7c3aed)',
  accentGlow: '0 0 20px rgba(59,130,246,0.3)',

  // Status
  success: '#10b981',
  successBg: 'rgba(16,185,129,0.1)',
  successBorder: 'rgba(16,185,129,0.2)',
  warning: '#f59e0b',
  warningBg: 'rgba(245,158,11,0.1)',
  warningBorder: 'rgba(245,158,11,0.2)',
  danger: '#ef4444',
  dangerBg: 'rgba(239,68,68,0.1)',
  dangerBorder: 'rgba(239,68,68,0.2)',
  info: '#06b6d4',
  infoBg: 'rgba(6,182,212,0.1)',
  infoBorder: 'rgba(6,182,212,0.2)',
};

// ── Reusable Style Objects ─────────────────────────────────

export const pageContainer: CSSProperties = {
  minHeight: '100vh',
  background: colors.bg,
  color: colors.text,
  fontFamily: 'var(--font-geist-sans), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
};

export const pageContent: CSSProperties = {
  padding: '32px',
  maxWidth: 1400,
  margin: '0 auto',
};

export const pageHeader: CSSProperties = {
  marginBottom: 32,
};

export const pageTitle: CSSProperties = {
  fontSize: 28,
  fontWeight: 700,
  color: colors.text,
  marginBottom: 4,
};

export const pageSubtitle: CSSProperties = {
  fontSize: 14,
  color: colors.textMuted,
};

export const card: CSSProperties = {
  background: colors.bgCard,
  border: `1px solid ${colors.border}`,
  borderRadius: 16,
  padding: 24,
  transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
  position: 'relative' as const,
  overflow: 'hidden' as const,
};

export const cardHover: CSSProperties = {
  ...card,
  background: colors.bgCardHover,
  borderColor: colors.borderHover,
  boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
  transform: 'translateY(-2px)',
};

export const glassCard: CSSProperties = {
  background: 'rgba(255,255,255,0.025)',
  backdropFilter: 'blur(16px)',
  WebkitBackdropFilter: 'blur(16px)',
  border: `1px solid ${colors.border}`,
  borderRadius: 16,
  padding: 24,
  position: 'relative' as const,
  overflow: 'hidden' as const,
};

export const statCard = (accentColor: string = colors.accent): CSSProperties => ({
  background: colors.bgCard,
  border: `1px solid ${colors.border}`,
  borderRadius: 16,
  padding: 22,
  position: 'relative' as const,
  overflow: 'hidden' as const,
  borderTop: `2px solid ${accentColor}`,
});

export const sectionTitle: CSSProperties = {
  fontSize: 18,
  fontWeight: 600,
  color: colors.text,
  marginBottom: 16,
};

export const badge = (color: string, bg: string): CSSProperties => ({
  display: 'inline-flex',
  alignItems: 'center',
  padding: '4px 10px',
  borderRadius: 6,
  fontSize: 12,
  fontWeight: 500,
  color,
  background: bg,
});

export const btn: CSSProperties = {
  padding: '8px 16px',
  borderRadius: 8,
  border: `1px solid ${colors.border}`,
  background: colors.bgElevated,
  color: colors.text,
  cursor: 'pointer',
  fontSize: 13,
  fontWeight: 500,
  transition: 'all 0.2s ease',
};

export const btnPrimary: CSSProperties = {
  padding: '10px 20px',
  borderRadius: 10,
  border: 'none',
  background: colors.accentGradient,
  color: '#fff',
  cursor: 'pointer',
  fontSize: 13,
  fontWeight: 600,
  transition: 'all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)',
  boxShadow: '0 4px 16px rgba(59,130,246,0.2)',
};

export const btnActive: CSSProperties = {
  ...btn,
  background: colors.accentGradient,
  border: '1px solid transparent',
  color: '#fff',
  fontWeight: 600,
};

export const input: CSSProperties = {
  width: '100%',
  padding: '10px 14px',
  borderRadius: 8,
  border: `1px solid ${colors.border}`,
  background: colors.bgInput,
  color: colors.text,
  fontSize: 14,
  outline: 'none',
  transition: 'border-color 0.2s',
};

export const table: CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse' as const,
};

export const th: CSSProperties = {
  textAlign: 'left' as const,
  padding: '12px 16px',
  fontSize: 12,
  fontWeight: 600,
  color: colors.textMuted,
  textTransform: 'uppercase' as const,
  letterSpacing: 1,
  borderBottom: `1px solid ${colors.border}`,
};

export const td: CSSProperties = {
  padding: '14px 16px',
  fontSize: 14,
  color: colors.textSecondary,
  borderBottom: `1px solid ${colors.borderLight}`,
};

export const grid = (cols: number = 4, gap: number = 16): CSSProperties => ({
  display: 'grid',
  gridTemplateColumns: `repeat(${cols}, 1fr)`,
  gap,
});

export const flexBetween: CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
};

export const flexCenter: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

export const flexGap = (gap: number = 8): CSSProperties => ({
  display: 'flex',
  alignItems: 'center',
  gap,
});

// ── Severity helpers ───────────────────────────────────────

export const severityColor = (sev: string) => {
  switch (sev) {
    case 'critical': return { color: colors.danger, bg: colors.dangerBg, border: colors.dangerBorder };
    case 'high': return { color: '#f97316', bg: 'rgba(249,115,22,0.1)', border: 'rgba(249,115,22,0.2)' };
    case 'medium': return { color: colors.warning, bg: colors.warningBg, border: colors.warningBorder };
    case 'low': return { color: colors.success, bg: colors.successBg, border: colors.successBorder };
    default: return { color: colors.textMuted, bg: colors.bgCard, border: colors.border };
  }
};

export const statusColor = (status: string) => {
  switch (status) {
    case 'resolved': return { color: colors.success, bg: colors.successBg };
    case 'investigating': return { color: colors.info, bg: colors.infoBg };
    case 'open': return { color: colors.warning, bg: colors.warningBg };
    case 'critical': return { color: colors.danger, bg: colors.dangerBg };
    default: return { color: colors.textMuted, bg: colors.bgCard };
  }
};

// ── Loading skeleton ───────────────────────────────────────

export const skeleton: CSSProperties = {
  background: 'linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.06) 50%, rgba(255,255,255,0.03) 75%)',
  backgroundSize: '200% 100%',
  borderRadius: 8,
  animation: 'shimmer 1.5s infinite',
};
