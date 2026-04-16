/**
 * Design System — Consistent tokens for the DevOps AI Assistant UI.
 */

export const colors = {
  // Primary
  primary: { 50: '#eff6ff', 100: '#dbeafe', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8' },
  // Severity
  critical: { bg: '#fef2f2', text: '#991b1b', border: '#fca5a5', badge: '#dc2626' },
  high: { bg: '#fff7ed', text: '#9a3412', border: '#fdba74', badge: '#ea580c' },
  medium: { bg: '#fefce8', text: '#854d0e', border: '#fde047', badge: '#d97706' },
  low: { bg: '#f0fdf4', text: '#166534', border: '#86efac', badge: '#16a34a' },
  // Status
  healthy: '#16a34a',
  degraded: '#d97706',
  down: '#dc2626',
  // Neutral
  bg: { light: '#f9fafb', dark: '#111827' },
  card: { light: '#ffffff', dark: '#1f2937' },
  text: { light: '#1f2937', dark: '#f9fafb' },
  muted: { light: '#6b7280', dark: '#9ca3af' },
  border: { light: '#e5e7eb', dark: '#374151' },
};

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
};

export const typography = {
  h1: { fontSize: '28px', fontWeight: 700, lineHeight: '36px' },
  h2: { fontSize: '22px', fontWeight: 600, lineHeight: '28px' },
  h3: { fontSize: '18px', fontWeight: 600, lineHeight: '24px' },
  body: { fontSize: '14px', fontWeight: 400, lineHeight: '20px' },
  small: { fontSize: '12px', fontWeight: 400, lineHeight: '16px' },
  label: { fontSize: '13px', fontWeight: 500, lineHeight: '18px' },
};

export const radius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  full: '9999px',
};

export const shadows = {
  sm: '0 1px 2px rgba(0,0,0,0.05)',
  md: '0 4px 6px -1px rgba(0,0,0,0.1)',
  lg: '0 10px 15px -3px rgba(0,0,0,0.1)',
};

export const breakpoints = {
  mobile: '640px',
  tablet: '768px',
  desktop: '1024px',
  wide: '1280px',
};

export const severityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return colors.critical;
    case 'high': return colors.high;
    case 'medium': return colors.medium;
    case 'low': return colors.low;
    default: return { bg: '#f3f4f6', text: '#374151', border: '#d1d5db', badge: '#6b7280' };
  }
};
