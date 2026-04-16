'use client';

interface ConnectionStatusProps {
  status: 'connected' | 'reconnecting' | 'disconnected';
}

export default function ConnectionStatus({ status }: ConnectionStatusProps) {
  const config = {
    connected: { color: '#16a34a', label: 'Connected', pulse: false },
    reconnecting: { color: '#d97706', label: 'Reconnecting...', pulse: true },
    disconnected: { color: '#dc2626', label: 'Disconnected', pulse: false },
  };

  const { color, label, pulse } = config[status];

  return (
    <div
      role="status"
      aria-label={`Connection status: ${label}`}
      style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#6b7280' }}
    >
      <span
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: color,
          display: 'inline-block',
          boxShadow: `0 0 4px ${color}`,
          animation: pulse ? 'pulse 1.5s infinite' : 'none',
        }}
      />
      <style>{`@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }`}</style>
      {label}
    </div>
  );
}
