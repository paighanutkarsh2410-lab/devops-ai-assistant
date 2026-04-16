'use client';

interface SkipLinkProps {
  targetId?: string;
  label?: string;
}

export default function SkipLink({ targetId = 'main-content', label = 'Skip to main content' }: SkipLinkProps) {
  return (
    <a
      href={`#${targetId}`}
      style={{
        position: 'fixed',
        top: -100,
        left: 16,
        zIndex: 99999,
        padding: '10px 20px',
        background: '#3b82f6',
        color: '#fff',
        borderRadius: 8,
        fontSize: 14,
        fontWeight: 600,
        textDecoration: 'none',
        transition: 'top 0.2s',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
      }}
      onFocus={(e) => { e.currentTarget.style.top = '16px'; }}
      onBlur={(e) => { e.currentTarget.style.top = '-100px'; }}
    >
      {label}
    </a>
  );
}
