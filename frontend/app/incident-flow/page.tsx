'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors } from '@/lib/theme';
import { useBreakpoint } from '@/lib/useMediaQuery';

/* ── Agent pipeline definition ──────────────────────────────── */

interface PipelineStep {
  id: string;
  agent: string;
  icon: string;
  color: string;
  title: string;
  description: string;
  details: string[];
  duration: number; // seconds this step takes in real scenario
}

interface Scenario {
  id: string;
  name: string;
  icon: string;
  description: string;
  trigger: string;
  steps: PipelineStep[];
}

const SCENARIOS: Scenario[] = [
  {
    id: 'cpu_spike',
    name: 'CPU Spike on API Server',
    icon: '🔥',
    description: 'A sudden CPU spike is detected on the api-server, diagnosed, and auto-remediated by the AI agent pipeline.',
    trigger: 'cpu_percent exceeded 95% threshold on api-server',
    steps: [
      {
        id: 'detect', agent: 'Monitor Agent', icon: '📡', color: '#3b82f6',
        title: 'Anomaly Detected',
        description: 'Monitor Agent detects CPU usage anomaly using z-score analysis (2.5σ deviation from baseline).',
        details: [
          'cpu_percent: 95.2% (baseline: 32%)',
          'Z-score: 4.8 — exceeds threshold of 2.5',
          'Anomaly confirmed across 3 consecutive checks',
          'Alert event published to event bus',
        ],
        duration: 15,
      },
      {
        id: 'diagnose', agent: 'Diagnostic Agent', icon: '🔬', color: '#8b5cf6',
        title: 'Root Cause Analysis',
        description: 'Diagnostic Agent uses Claude AI to analyze logs, metrics, and deployment history to identify root cause.',
        details: [
          'Scanned 2,847 log entries from api-server',
          'Correlated with 4 related metric anomalies',
          'Found: Runaway regex in /api/search endpoint',
          'Confidence: 94% — matched 7 similar past incidents',
          'Severity: HIGH — user-facing latency impact',
        ],
        duration: 12,
      },
      {
        id: 'alert', agent: 'Communication Agent', icon: '📢', color: '#ef4444',
        title: 'Team Notified',
        description: 'Communication Agent sends alerts to on-call engineers via configured channels.',
        details: [
          'Slack #incidents: Alert posted with severity & context',
          'PagerDuty: P2 incident created, on-call paged',
          'Email: Incident summary sent to team leads',
          'Escalation timer: 15 min to P1 if unresolved',
        ],
        duration: 2,
      },
      {
        id: 'remediate', agent: 'Remediation Agent', icon: '🔧', color: '#10b981',
        title: 'Auto-Remediation',
        description: 'Remediation Agent executes safe fix with rollback capability and checkpoint validation.',
        details: [
          'Action: Scale horizontally — adding 2 instances',
          'Safety check: Rollback point created',
          'Executing: kubectl scale deployment api-server --replicas=4',
          'Health check: New instances passing readiness probe',
          'CPU dropping: 95% → 62% → 38%',
        ],
        duration: 45,
      },
      {
        id: 'verify', agent: 'Monitor Agent', icon: '✅', color: '#3b82f6',
        title: 'Resolution Verified',
        description: 'Monitor Agent confirms metrics have returned to normal operating range.',
        details: [
          'cpu_percent: 34% (within normal range)',
          'api_response_time: 120ms (baseline: 95ms)',
          'error_rate: 0.02% (baseline: 0.01%)',
          'All health checks passing for 5 minutes',
        ],
        duration: 60,
      },
      {
        id: 'learn', agent: 'Learning Agent', icon: '🧠', color: '#f59e0b',
        title: 'Pattern Recorded',
        description: 'Learning Agent stores incident pattern and updates recommendation models for future incidents.',
        details: [
          'Incident pattern saved to knowledge base',
          'Similar incident count: 7 → 8',
          'Recommendation model accuracy: +1.2%',
          'Auto-remediation confidence for this pattern: 96%',
          'Suggested: Add regex timeout to prevent recurrence',
        ],
        duration: 5,
      },
      {
        id: 'predict', agent: 'Prediction Agent', icon: '🔮', color: '#06b6d4',
        title: 'Future Forecast Updated',
        description: 'Prediction Agent adjusts forecasting models and sets preventive thresholds.',
        details: [
          'Prediction: 78% chance of recurrence within 14 days',
          'Recommendation: Deploy regex timeout fix within 48h',
          'Adjusted monitoring: CPU threshold lowered to 85%',
          'Preventive scaling rule: Auto-scale at 80% CPU',
        ],
        duration: 3,
      },
    ],
  },
  {
    id: 'memory_leak',
    name: 'Memory Leak in Auth Service',
    icon: '🧠',
    description: 'A gradual memory leak is detected in auth-service, diagnosed as unreleased JWT cache entries, and resolved.',
    trigger: 'memory_percent growing 2% per hour on auth-service',
    steps: [
      {
        id: 'detect', agent: 'Monitor Agent', icon: '📡', color: '#3b82f6',
        title: 'Trend Anomaly Detected',
        description: 'Monitor Agent detects sustained upward memory trend exceeding normal growth patterns.',
        details: [
          'memory_percent: 78% and rising (baseline: 45%)',
          'Growth rate: 2.1% per hour (normal: <0.1%)',
          'Trend analysis: Will hit OOM in ~11 hours',
          'Pattern classified as: GRADUAL_LEAK',
        ],
        duration: 30,
      },
      {
        id: 'diagnose', agent: 'Diagnostic Agent', icon: '🔬', color: '#8b5cf6',
        title: 'Root Cause Analysis',
        description: 'Diagnostic Agent traces memory allocation patterns and identifies the leak source.',
        details: [
          'Heap dump analysis: JWT token cache growing unbounded',
          'Cache entries: 847,000 (expected: <10,000)',
          'No TTL set on token validation cache',
          'Leak introduced in commit abc123 (2 days ago)',
          'Confidence: 91% — heap profile confirms',
        ],
        duration: 20,
      },
      {
        id: 'alert', agent: 'Communication Agent', icon: '📢', color: '#ef4444',
        title: 'Team Notified',
        description: 'Communication Agent alerts the team with full context and estimated time to failure.',
        details: [
          'Slack #incidents: Memory leak alert with heap analysis',
          'Estimated OOM in 11 hours — non-critical urgency',
          'Tagged: @auth-team for code-level fix',
          'Runbook link attached: memory-leak-response.md',
        ],
        duration: 2,
      },
      {
        id: 'remediate', agent: 'Remediation Agent', icon: '🔧', color: '#10b981',
        title: 'Graceful Restart',
        description: 'Remediation Agent performs rolling restart to clear leaked memory while maintaining availability.',
        details: [
          'Strategy: Rolling restart (zero-downtime)',
          'Draining connections from auth-service-1...',
          'Restarting auth-service-1: memory 78% → 12%',
          'Draining connections from auth-service-2...',
          'Restarting auth-service-2: memory 76% → 11%',
          'All instances healthy with normal memory usage',
        ],
        duration: 120,
      },
      {
        id: 'verify', agent: 'Monitor Agent', icon: '✅', color: '#3b82f6',
        title: 'Resolution Verified',
        description: 'Monitor Agent confirms memory usage is stable at normal levels.',
        details: [
          'memory_percent: 14% (stable, no growth)',
          'Auth latency: 8ms (normal)',
          'No dropped connections during restart',
          'Monitoring for re-leak over next 4 hours',
        ],
        duration: 60,
      },
      {
        id: 'learn', agent: 'Learning Agent', icon: '🧠', color: '#f59e0b',
        title: 'Pattern Recorded',
        description: 'Learning Agent stores the memory leak pattern and links to the causal commit.',
        details: [
          'Pattern: Unbounded cache growth in auth-service',
          'Root cause linked to commit abc123',
          'Recommended permanent fix: Add TTL to JWT cache',
          'Created JIRA ticket AUTH-456 for permanent fix',
        ],
        duration: 5,
      },
      {
        id: 'predict', agent: 'Prediction Agent', icon: '🔮', color: '#06b6d4',
        title: 'Recurrence Prevention',
        description: 'Prediction Agent sets up early warning triggers for this pattern.',
        details: [
          'Added: Memory growth rate alert (>0.5%/hour)',
          'Prediction: Leak will recur until code fix deployed',
          'Scheduled: Auto-restart every 8h as stopgap',
          'Priority recommendation: Deploy cache TTL fix',
        ],
        duration: 3,
      },
    ],
  },
  {
    id: 'cascade',
    name: 'Cascading Failure from DB Overload',
    icon: '💥',
    description: 'Database connection pool exhaustion triggers cascading failures across dependent services.',
    trigger: 'db_connections at 98/100 on db-primary, error_rate spiking on 4 services',
    steps: [
      {
        id: 'detect', agent: 'Monitor Agent', icon: '📡', color: '#3b82f6',
        title: 'Multi-Service Anomaly',
        description: 'Monitor Agent detects correlated anomalies across multiple services simultaneously.',
        details: [
          'db-primary: 98/100 connections used (CRITICAL)',
          'api-server: error_rate 34% (baseline: 0.1%)',
          'auth-service: response_time 4200ms (baseline: 15ms)',
          'worker-queue: job failures 89% (baseline: 0.5%)',
          'Pattern: CASCADING_FAILURE detected',
        ],
        duration: 10,
      },
      {
        id: 'diagnose', agent: 'Diagnostic Agent', icon: '🔬', color: '#8b5cf6',
        title: 'Cascade Analysis',
        description: 'Diagnostic Agent maps the failure propagation path and identifies the origin point.',
        details: [
          'Origin: db-primary connection pool exhaustion',
          'Cause: Long-running analytics query holding 45 connections',
          'Propagation: db → api-server → auth-service → worker',
          'Blast radius: 4 services, ~12,000 users affected',
          'Confidence: 97% — connection trace confirms',
        ],
        duration: 8,
      },
      {
        id: 'alert', agent: 'Communication Agent', icon: '📢', color: '#ef4444',
        title: 'P1 Incident Declared',
        description: 'Communication Agent escalates immediately to P1 due to multi-service impact.',
        details: [
          'P1 INCIDENT: Cascading failure from DB overload',
          'PagerDuty: All on-call engineers paged',
          'Slack #incidents: War room thread created',
          'Status page: Updated to "Major Outage"',
          'Executive notification: CTO briefed',
        ],
        duration: 1,
      },
      {
        id: 'remediate', agent: 'Remediation Agent', icon: '🔧', color: '#10b981',
        title: 'Multi-Step Remediation',
        description: 'Remediation Agent executes coordinated fix: kill queries, scale pool, enable circuit breakers.',
        details: [
          'Step 1: Kill long-running analytics queries (45 freed)',
          'Step 2: Increase connection pool to 200',
          'Step 3: Enable circuit breakers on affected services',
          'Step 4: Drain and restart api-server instances',
          'Connections: 98/100 → 52/200 (healthy)',
          'Error rates normalizing across all services',
        ],
        duration: 90,
      },
      {
        id: 'verify', agent: 'Monitor Agent', icon: '✅', color: '#3b82f6',
        title: 'Full Recovery Confirmed',
        description: 'Monitor Agent verifies all services have returned to normal operation.',
        details: [
          'db-primary: 45/200 connections (healthy)',
          'api-server: error_rate 0.08% (normal)',
          'auth-service: response_time 12ms (normal)',
          'worker-queue: job success 99.8% (normal)',
          'Status page: Updated to "All Systems Operational"',
        ],
        duration: 120,
      },
      {
        id: 'learn', agent: 'Learning Agent', icon: '🧠', color: '#f59e0b',
        title: 'Cascade Pattern Learned',
        description: 'Learning Agent maps the full failure chain for future prevention.',
        details: [
          'Failure chain mapped: analytics query → pool exhaust → cascade',
          'Added: Query timeout of 30s for analytics queries',
          'Added: Connection pool monitoring at 70% threshold',
          'Runbook generated: db-cascade-response.md',
        ],
        duration: 5,
      },
      {
        id: 'predict', agent: 'Prediction Agent', icon: '🔮', color: '#06b6d4',
        title: 'Prevention Rules Set',
        description: 'Prediction Agent establishes early warning system for similar cascade patterns.',
        details: [
          'Early warning: Alert at 70% pool capacity',
          'Auto-kill: Queries exceeding 30s in analytics',
          'Circuit breaker: Auto-enable at 5% error rate',
          'Prediction: 15% chance of recurrence (down from 60%)',
        ],
        duration: 3,
      },
    ],
  },
];

/* ── Animated Canvas ────────────────────────────────────────── */

interface FlowCanvasProps {
  steps: PipelineStep[];
  activeStep: number;
  width: number;
  height: number;
}

function FlowCanvas({ steps, activeStep, width, height }: FlowCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrame = useRef(0);
  const pulseRef = useRef(0);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const nodeCount = steps.length;
    const centerX = width / 2;
    const centerY = height / 2;
    const radiusX = Math.min(width, height) * 0.36;
    const radiusY = Math.min(width, height) * 0.32;
    const nodeRadius = Math.min(width, height) < 400 ? 22 : 28;
    const time = pulseRef.current;

    // Calculate node positions in a circle
    const positions = steps.map((_, i) => {
      const angle = (i / nodeCount) * Math.PI * 2 - Math.PI / 2;
      return {
        x: centerX + Math.cos(angle) * radiusX,
        y: centerY + Math.sin(angle) * radiusY,
      };
    });

    // Draw connection lines
    for (let i = 0; i < nodeCount; i++) {
      const next = (i + 1) % nodeCount;
      if (i >= nodeCount - 1) continue; // Don't connect last to first
      const from = positions[i];
      const to = positions[next];

      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);

      if (i < activeStep) {
        // Completed connection — bright
        ctx.strokeStyle = steps[i].color + '80';
        ctx.lineWidth = 3;
      } else if (i === activeStep) {
        // Active connection — animated dash
        ctx.strokeStyle = steps[i].color;
        ctx.lineWidth = 3;
        ctx.setLineDash([8, 6]);
        ctx.lineDashOffset = -time * 2;
      } else {
        // Future connection — dim
        ctx.strokeStyle = 'rgba(255,255,255,0.06)';
        ctx.lineWidth = 1.5;
      }
      ctx.stroke();
      ctx.setLineDash([]);

      // Arrow on active/completed edges
      if (i <= activeStep) {
        const angle = Math.atan2(to.y - from.y, to.x - from.x);
        const midX = (from.x + to.x) / 2;
        const midY = (from.y + to.y) / 2;
        ctx.beginPath();
        ctx.moveTo(midX + 6 * Math.cos(angle), midY + 6 * Math.sin(angle));
        ctx.lineTo(midX - 6 * Math.cos(angle - 0.5), midY - 6 * Math.sin(angle - 0.5));
        ctx.lineTo(midX - 6 * Math.cos(angle + 0.5), midY - 6 * Math.sin(angle + 0.5));
        ctx.closePath();
        ctx.fillStyle = i < activeStep ? steps[i].color + '80' : steps[i].color;
        ctx.fill();
      }
    }

    // Draw nodes
    steps.forEach((step, i) => {
      const pos = positions[i];
      const isActive = i === activeStep;
      const isCompleted = i < activeStep;
      const isFuture = i > activeStep;

      // Glow for active node
      if (isActive) {
        const pulse = Math.sin(time * 0.08) * 0.3 + 0.7;
        const gradient = ctx.createRadialGradient(pos.x, pos.y, nodeRadius, pos.x, pos.y, nodeRadius + 20);
        gradient.addColorStop(0, step.color + Math.round(pulse * 60).toString(16).padStart(2, '0'));
        gradient.addColorStop(1, step.color + '00');
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, nodeRadius + 20, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();
      }

      // Node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeRadius, 0, Math.PI * 2);
      if (isActive) {
        ctx.fillStyle = step.color;
        ctx.shadowColor = step.color;
        ctx.shadowBlur = 20;
      } else if (isCompleted) {
        ctx.fillStyle = step.color + '90';
        ctx.shadowBlur = 0;
      } else {
        ctx.fillStyle = 'rgba(255,255,255,0.04)';
        ctx.shadowBlur = 0;
      }
      ctx.fill();
      ctx.shadowBlur = 0;

      // Border
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeRadius, 0, Math.PI * 2);
      ctx.strokeStyle = isActive ? step.color : isCompleted ? step.color + '60' : 'rgba(255,255,255,0.08)';
      ctx.lineWidth = isActive ? 3 : 2;
      ctx.stroke();

      // Icon text
      ctx.font = `${nodeRadius < 24 ? 14 : 18}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isActive || isCompleted ? '#fff' : 'rgba(255,255,255,0.2)';
      ctx.fillText(step.icon, pos.x, pos.y);

      // Check mark for completed
      if (isCompleted) {
        ctx.beginPath();
        ctx.arc(pos.x + nodeRadius * 0.7, pos.y - nodeRadius * 0.7, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#10b981';
        ctx.fill();
        ctx.font = 'bold 10px sans-serif';
        ctx.fillStyle = '#fff';
        ctx.fillText('✓', pos.x + nodeRadius * 0.7, pos.y - nodeRadius * 0.7 + 1);
      }

      // Label below
      ctx.font = `${isFuture ? 'normal' : 'bold'} ${nodeRadius < 24 ? 9 : 11}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isActive ? '#fff' : isCompleted ? '#a1a1aa' : 'rgba(255,255,255,0.15)';
      ctx.fillText(step.agent.replace(' Agent', ''), pos.x, pos.y + nodeRadius + 8);
    });

    pulseRef.current += 1;
    animFrame.current = requestAnimationFrame(draw);
  }, [steps, activeStep, width, height]);

  useEffect(() => {
    animFrame.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animFrame.current);
  }, [draw]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width, height }}
    />
  );
}

/* ── Main Page ──────────────────────────────────────────────── */

export default function IncidentFlowPage() {
  const { isMobile } = useBreakpoint();
  const [selectedScenario, setSelectedScenario] = useState(0);
  const [activeStep, setActiveStep] = useState(-1);
  const [playing, setPlaying] = useState(false);
  const [stepTime, setStepTime] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const scenario = SCENARIOS[selectedScenario];
  const currentStep = activeStep >= 0 && activeStep < scenario.steps.length ? scenario.steps[activeStep] : null;

  // Auto-play logic
  useEffect(() => {
    if (!playing) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    timerRef.current = setInterval(() => {
      setStepTime(prev => {
        if (prev >= 100) {
          // Move to next step
          setActiveStep(s => {
            const next = s + 1;
            if (next >= scenario.steps.length) {
              setPlaying(false);
              return s;
            }
            return next;
          });
          return 0;
        }
        return prev + 2;
      });
    }, 60);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [playing, scenario.steps.length]);

  const handlePlay = () => {
    setActiveStep(0);
    setStepTime(0);
    setPlaying(true);
  };

  const handlePause = () => setPlaying(false);
  const handleResume = () => setPlaying(true);

  const handleReset = () => {
    setPlaying(false);
    setActiveStep(-1);
    setStepTime(0);
  };

  const handleStepClick = (i: number) => {
    setPlaying(false);
    setActiveStep(i);
    setStepTime(100);
  };

  const totalDuration = scenario.steps.reduce((sum, s) => sum + s.duration, 0);

  return (
    <DashboardShell>
      <div style={{ padding: isMobile ? '16px 14px' : 32, maxWidth: 1400, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 24 }}>
          <h1 style={{
            fontSize: isMobile ? 20 : 26, fontWeight: 800, margin: '0 0 6px',
            background: 'linear-gradient(135deg, #f0f0f0, #10b981)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>AI Agent Incident Flow</h1>
          <p style={{ color: colors.textMuted, fontSize: 13 }}>
            Watch how AI agents collaborate to detect, diagnose, and resolve infrastructure incidents in real-time
          </p>
        </div>

        {/* Scenario Picker */}
        <div className="slide-up-d1" style={{
          display: 'grid',
          gridTemplateColumns: isMobile ? '1fr' : `repeat(${SCENARIOS.length}, 1fr)`,
          gap: 10, marginBottom: 20,
        }}>
          {SCENARIOS.map((s, i) => (
            <button key={s.id} onClick={() => { setSelectedScenario(i); handleReset(); }}
              style={{
                padding: 14, borderRadius: 10, textAlign: 'left' as const, cursor: 'pointer',
                border: selectedScenario === i ? `1px solid ${colors.accent}` : `1px solid ${colors.border}`,
                background: selectedScenario === i ? 'rgba(59,130,246,0.08)' : colors.bgCard,
                transition: 'all 0.2s',
              }}>
              <div style={{ fontSize: 20, marginBottom: 4 }}>{s.icon}</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: colors.text }}>{s.name}</div>
              <div style={{ fontSize: 11, color: colors.textDim, marginTop: 2 }}>{s.trigger}</div>
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 16 }}>
          {/* Left: Canvas + Controls */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* Canvas */}
            <div className="slide-up-d2" style={{
              background: colors.bgCard, borderRadius: 14,
              border: `1px solid ${colors.border}`, overflow: 'hidden', marginBottom: 16,
            }}>
              <div style={{
                padding: '14px 20px', borderBottom: `1px solid ${colors.border}`,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: colors.text }}>Agent Pipeline</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {activeStep >= 0 && (
                    <span style={{ fontSize: 11, color: colors.textDim }}>
                      Step {activeStep + 1}/{scenario.steps.length}
                    </span>
                  )}
                  <span style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: playing ? '#10b981' : activeStep >= 0 ? '#f59e0b' : colors.textDim,
                    boxShadow: playing ? '0 0 8px rgba(16,185,129,0.5)' : 'none',
                    animation: playing ? 'pulse 1.5s infinite' : 'none',
                  }} />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', padding: 16 }}>
                <FlowCanvas
                  steps={scenario.steps}
                  activeStep={activeStep}
                  width={isMobile ? 340 : 550}
                  height={isMobile ? 280 : 380}
                />
              </div>
            </div>

            {/* Playback Controls */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: 14, borderRadius: 10,
              background: colors.bgCard, border: `1px solid ${colors.border}`,
              marginBottom: 16,
            }}>
              {activeStep < 0 ? (
                <button onClick={handlePlay} style={{
                  padding: '8px 24px', borderRadius: 8, border: 'none',
                  background: colors.accentGradient, color: '#fff',
                  fontWeight: 600, fontSize: 13, cursor: 'pointer',
                }}>▶ Play Incident Flow</button>
              ) : (
                <>
                  <button onClick={playing ? handlePause : handleResume} style={{
                    padding: '8px 16px', borderRadius: 8, border: `1px solid ${colors.border}`,
                    background: colors.bgElevated, color: colors.text,
                    fontSize: 13, cursor: 'pointer',
                  }}>{playing ? '⏸ Pause' : '▶ Resume'}</button>
                  <button onClick={handleReset} style={{
                    padding: '8px 16px', borderRadius: 8, border: `1px solid ${colors.border}`,
                    background: colors.bgElevated, color: colors.textSecondary,
                    fontSize: 13, cursor: 'pointer',
                  }}>↺ Reset</button>
                </>
              )}

              {/* Progress bar */}
              <div style={{ flex: 1, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.06)' }}>
                <div style={{
                  width: activeStep < 0 ? '0%' : `${((activeStep + stepTime / 100) / scenario.steps.length) * 100}%`,
                  height: '100%', borderRadius: 2,
                  background: 'linear-gradient(90deg, #3b82f6, #8b5cf6, #10b981)',
                  transition: 'width 0.1s linear',
                }} />
              </div>

              <span style={{ fontSize: 11, color: colors.textDim, whiteSpace: 'nowrap' }}>
                ~{totalDuration}s real time
              </span>
            </div>

            {/* Step selector pills */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? 'repeat(4, 1fr)' : `repeat(${scenario.steps.length}, 1fr)`,
              gap: 4,
            }}>
              {scenario.steps.map((step, i) => {
                const isActive = i === activeStep;
                const isCompleted = i < activeStep;
                return (
                  <button key={step.id + i} onClick={() => handleStepClick(i)}
                    style={{
                      padding: '6px 4px', borderRadius: 6, cursor: 'pointer',
                      border: isActive ? `1px solid ${step.color}` : `1px solid ${colors.borderLight}`,
                      background: isActive ? `${step.color}15` : isCompleted ? `${step.color}08` : colors.bgElevated,
                      fontSize: 10, fontWeight: 600,
                      color: isActive ? step.color : isCompleted ? colors.textSecondary : colors.textDim,
                      transition: 'all 0.2s',
                    }}>
                    {isCompleted ? '✓ ' : ''}{step.agent.replace(' Agent', '')}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right: Step Detail */}
          <div style={{ width: isMobile ? '100%' : 380, flexShrink: 0 }}>
            {currentStep ? (
              <div className="slide-up" key={activeStep} style={{
                background: colors.bgCard, borderRadius: 14,
                border: `1px solid ${colors.border}`, overflow: 'hidden',
              }}>
                {/* Color bar */}
                <div style={{ height: 3, background: `linear-gradient(90deg, ${currentStep.color}, ${currentStep.color}60)` }} />

                <div style={{ padding: 20 }}>
                  {/* Header */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                    <div style={{
                      width: 40, height: 40, borderRadius: 10,
                      background: `${currentStep.color}15`,
                      border: `1px solid ${currentStep.color}30`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 20,
                    }}>{currentStep.icon}</div>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: colors.text }}>{currentStep.title}</div>
                      <div style={{ fontSize: 12, color: currentStep.color, fontWeight: 600 }}>{currentStep.agent}</div>
                    </div>
                  </div>

                  {/* Description */}
                  <p style={{
                    fontSize: 13, color: colors.textSecondary, lineHeight: 1.6,
                    margin: '0 0 16px', padding: 12, borderRadius: 8,
                    background: 'rgba(255,255,255,0.02)',
                    borderLeft: `3px solid ${currentStep.color}40`,
                  }}>
                    {currentStep.description}
                  </p>

                  {/* Detail lines */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {currentStep.details.map((detail, j) => (
                      <div key={j} style={{
                        display: 'flex', alignItems: 'flex-start', gap: 8,
                        animation: `slide-up 0.3s ease-out ${j * 0.06}s both`,
                      }}>
                        <div style={{
                          width: 6, height: 6, borderRadius: '50%', marginTop: 5, flexShrink: 0,
                          background: currentStep.color,
                          boxShadow: `0 0 6px ${currentStep.color}40`,
                        }} />
                        <span style={{ fontSize: 12, color: colors.textSecondary, lineHeight: 1.5, fontFamily: 'monospace' }}>
                          {detail}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Timing */}
                  <div style={{
                    marginTop: 16, padding: '8px 12px', borderRadius: 8,
                    background: `${currentStep.color}08`,
                    border: `1px solid ${currentStep.color}15`,
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}>
                    <span style={{ fontSize: 11, color: colors.textDim }}>Typical duration</span>
                    <span style={{ fontSize: 13, fontWeight: 700, color: currentStep.color }}>
                      {currentStep.duration < 60 ? `${currentStep.duration}s` : `${Math.round(currentStep.duration / 60)}m ${currentStep.duration % 60}s`}
                    </span>
                  </div>

                  {/* Step progress */}
                  {playing && (
                    <div style={{ marginTop: 10 }}>
                      <div style={{ height: 3, borderRadius: 2, background: 'rgba(255,255,255,0.06)' }}>
                        <div style={{
                          width: `${stepTime}%`, height: '100%', borderRadius: 2,
                          background: currentStep.color,
                          transition: 'width 0.06s linear',
                        }} />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{
                background: colors.bgCard, borderRadius: 14,
                border: `1px solid ${colors.border}`,
                padding: 40, textAlign: 'center' as const,
              }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>{scenario.icon}</div>
                <div style={{ fontSize: 15, fontWeight: 600, color: colors.text, marginBottom: 8 }}>
                  {scenario.name}
                </div>
                <p style={{ fontSize: 13, color: colors.textSecondary, lineHeight: 1.6, marginBottom: 16 }}>
                  {scenario.description}
                </p>
                <div style={{
                  padding: '8px 14px', borderRadius: 8, display: 'inline-block',
                  background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.12)',
                  fontSize: 12, color: '#f87171', fontFamily: 'monospace',
                }}>
                  Trigger: {scenario.trigger}
                </div>
                <div style={{ marginTop: 20 }}>
                  <button onClick={handlePlay} style={{
                    padding: '10px 32px', borderRadius: 10, border: 'none',
                    background: colors.accentGradient, color: '#fff',
                    fontWeight: 600, fontSize: 14, cursor: 'pointer',
                    boxShadow: '0 4px 16px rgba(59,130,246,0.3)',
                  }}>▶ Start Simulation</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
