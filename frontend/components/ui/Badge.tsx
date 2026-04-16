'use client';

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  pulse?: boolean;
  onClick?: () => void;
}

const VARIANT_STYLES: Record<BadgeVariant, { bg: string; color: string; dot: string }> = {
  default: { bg: '#3b82f620', color: '#60a5fa', dot: '#3b82f6' },
  success: { bg: '#10b98120', color: '#34d399', dot: '#10b981' },
  warning: { bg: '#f59e0b20', color: '#fbbf24', dot: '#f59e0b' },
  danger: { bg: '#ef444420', color: '#f87171', dot: '#ef4444' },
  info: { bg: '#06b6d420', color: '#22d3ee', dot: '#06b6d4' },
  neutral: { bg: '#64748b20', color: '#94a3b8', dot: '#64748b' },
};

const SIZE_STYLES: Record<BadgeSize, { padding: string; fontSize: number }> = {
  sm: { padding: '1px 6px', fontSize: 10 },
  md: { padding: '2px 8px', fontSize: 11 },
  lg: { padding: '4px 12px', fontSize: 12 },
};

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  pulse = false,
  onClick,
}: BadgeProps) {
  const v = VARIANT_STYLES[variant];
  const s = SIZE_STYLES[size];

  return (
    <span
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: s.padding,
        borderRadius: 12,
        background: v.bg,
        color: v.color,
        fontSize: s.fontSize,
        fontWeight: 600,
        cursor: onClick ? 'pointer' : 'default',
        lineHeight: 1.4,
        whiteSpace: 'nowrap',
      }}
    >
      {dot && (
        <span style={{ position: 'relative', display: 'inline-block', width: 6, height: 6 }}>
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: v.dot,
              display: 'block',
            }}
          />
          {pulse && (
            <span
              style={{
                position: 'absolute',
                inset: -2,
                borderRadius: '50%',
                background: v.dot,
                animation: 'badgePulse 1.5s infinite',
                opacity: 0.4,
              }}
            />
          )}
        </span>
      )}
      {children}
      {pulse && !dot && (
        <style>{`
          @keyframes badgePulse {
            0%, 100% { transform: scale(1); opacity: 0.4; }
            50% { transform: scale(1.8); opacity: 0; }
          }
        `}</style>
      )}
      {pulse && dot && (
        <style>{`
          @keyframes badgePulse {
            0%, 100% { transform: scale(1); opacity: 0.4; }
            50% { transform: scale(2); opacity: 0; }
          }
        `}</style>
      )}
    </span>
  );
}
