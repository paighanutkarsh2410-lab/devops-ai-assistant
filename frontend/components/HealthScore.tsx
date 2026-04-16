'use client';

import { useRef, useEffect } from 'react';

interface Props {
  score: number;
  label: string;
  size?: number;
}

export default function HealthScore({ score, label, size = 120 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const color = score >= 90 ? '#16a34a' : score >= 75 ? '#2563eb' : score >= 60 ? '#d97706' : '#dc2626';
  const grade = score >= 90 ? 'A' : score >= 75 ? 'B' : score >= 60 ? 'C' : score >= 40 ? 'D' : 'F';

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 10;
    const lineWidth = 8;

    // Background arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, -Math.PI * 0.75, Math.PI * 0.75);
    ctx.strokeStyle = 'rgba(255,255,255,0.08)';
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Score arc
    const totalAngle = Math.PI * 1.5;
    const scoreAngle = (score / 100) * totalAngle;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, -Math.PI * 0.75, -Math.PI * 0.75 + scoreAngle);
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Score text
    ctx.fillStyle = color;
    ctx.font = `bold ${size * 0.28}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(grade, cx, cy - 4);

    // Score number
    ctx.fillStyle = '#71717a';
    ctx.font = `${size * 0.12}px sans-serif`;
    ctx.fillText(`${score}`, cx, cy + size * 0.18);
  }, [score, size, color, grade]);

  return (
    <div style={{ textAlign: 'center' }}>
      <canvas
        ref={canvasRef}
        style={{ width: `${size}px`, height: `${size}px` }}
      />
      <div style={{ fontSize: '12px', color: '#71717a', marginTop: '-4px' }}>{label}</div>
    </div>
  );
}
