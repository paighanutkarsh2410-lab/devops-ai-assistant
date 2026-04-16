'use client';

interface StepResult {
  order: number;
  name: string;
  type: string;
  status?: string;
  success?: boolean;
  message?: string;
  instruction?: string;
  started_at?: string;
}

interface Props {
  stepResults: StepResult[];
  status: string;
}

export default function RunbookExecution({ stepResults, status }: Props) {
  const getStepColor = (step: StepResult) => {
    if (step.status === 'pending_manual' || step.status === 'pending_approval') return '#d97706';
    if (step.success === false) return '#dc2626';
    if (step.success === true || step.status === 'completed') return '#16a34a';
    return '#6b7280';
  };

  const getStepIcon = (step: StepResult) => {
    if (step.type === 'automated') return '⚡';
    if (step.type === 'manual') return '👤';
    if (step.type === 'approval') return '✋';
    if (step.type === 'conditional') return '🔀';
    return '📋';
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <span style={{
          width: '8px', height: '8px', borderRadius: '50%',
          background: status === 'completed' ? '#16a34a' : status === 'failed' ? '#dc2626' : status === 'paused' ? '#d97706' : '#3b82f6',
        }} />
        <span style={{ fontSize: '13px', fontWeight: 600, textTransform: 'capitalize', color: '#f0f0f0' }}>{status}</span>
        <span style={{ fontSize: '12px', color: '#71717a' }}>
          {stepResults.length} step{stepResults.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div style={{ position: 'relative' }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute', left: '15px', top: '8px', bottom: '8px', width: '2px',
          background: 'rgba(255,255,255,0.06)', zIndex: 0,
        }} />

        {stepResults.map((step, idx) => {
          const color = getStepColor(step);
          return (
            <div key={idx} style={{
              display: 'flex', gap: '12px', marginBottom: '8px', position: 'relative', zIndex: 1,
            }}>
              {/* Step dot */}
              <div style={{
                width: '30px', height: '30px', borderRadius: '50%', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: `${color}15`, border: `2px solid ${color}`,
                fontSize: '14px',
              }}>
                {getStepIcon(step)}
              </div>

              {/* Content */}
              <div style={{
                flex: 1, padding: '8px 12px', borderRadius: '8px',
                border: `1px solid ${color}30`, background: 'rgba(255,255,255,0.03)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#f0f0f0' }}>
                    #{step.order}. {step.name}
                  </span>
                  <span style={{
                    fontSize: '10px', padding: '1px 6px', borderRadius: '8px',
                    background: `${color}15`, color, fontWeight: 600,
                  }}>
                    {step.status || (step.success ? 'done' : 'failed')}
                  </span>
                </div>

                {step.message && (
                  <p style={{ fontSize: '12px', color: '#a1a1aa', marginTop: '2px' }}>{step.message}</p>
                )}
                {step.instruction && (
                  <p style={{ fontSize: '12px', color: '#d97706', marginTop: '2px', fontStyle: 'italic' }}>
                    Manual: {step.instruction}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
