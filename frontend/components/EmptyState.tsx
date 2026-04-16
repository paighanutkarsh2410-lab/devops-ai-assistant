'use client';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: string;
  action?: { label: string; onClick: () => void };
}

export default function EmptyState({ title, description, icon = '📭', action }: EmptyStateProps) {
  return (
    <div
      role="status"
      style={{
        textAlign: 'center',
        padding: '60px 24px',
        background: 'rgba(255,255,255,0.03)',
        borderRadius: '12px',
        border: '2px dashed rgba(255,255,255,0.06)',
      }}
    >
      <div style={{ fontSize: '48px', marginBottom: '16px' }}>{icon}</div>
      <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#f0f0f0', marginBottom: '8px' }}>
        {title}
      </h3>
      <p style={{ color: '#a1a1aa', fontSize: '14px', maxWidth: '400px', margin: '0 auto 16px' }}>
        {description}
      </p>
      {action && (
        <button
          onClick={action.onClick}
          style={{
            padding: '8px 24px',
            background: '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
