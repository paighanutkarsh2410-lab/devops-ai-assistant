'use client';

import { useRef, useEffect } from 'react';

interface GaugeChartProps {
  value: number;
  min?: number;
  max?: number;
  thresholds?: { value: number; color: string; label?: string }[];
  label?: string;
  unit?: string;
  width?: number;
  height?: number;
  animated?: boolean;
}

export default function GaugeChart({
  value,
  min = 0,
  max = 100,
  thresholds = [
    { value: 30, color: '#10b981', label: 'Good' },
    { value: 70, color: '#f59e0b', label: 'Warning' },
    { value: 100, color: '#ef4444', label: 'Critical' },
  ],
  label,
  unit = '',
  width = 260,
  height = 180,
  animated = true,
}: GaugeChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const currentRef = useRef(min);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    const cx = width / 2;
    const cy = height - 20;
    const radius = Math.min(width / 2, height) - 30;
    const startAngle = Math.PI;
    const endAngle = 2 * Math.PI;
    const range = max - min;
    const lineW = 16;

    const drawFrame = (currentValue: number) => {
      ctx.clearRect(0, 0, width, height);

      // Track background
      ctx.beginPath();
      ctx.arc(cx, cy, radius, startAngle, endAngle);
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = lineW;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Threshold segments
      let prevAngle = startAngle;
      thresholds.forEach((th, i) => {
        const nextVal = Math.min(th.value, max);
        const prevVal = i === 0 ? min : thresholds[i - 1].value;
        const segStart = startAngle + ((prevVal - min) / range) * Math.PI;
        const segEnd = startAngle + ((nextVal - min) / range) * Math.PI;

        ctx.beginPath();
        ctx.arc(cx, cy, radius, segStart, segEnd);
        ctx.strokeStyle = th.color + '30';
        ctx.lineWidth = lineW;
        ctx.lineCap = 'butt';
        ctx.stroke();
        prevAngle = segEnd;
      });

      // Active arc
      const clampedValue = Math.max(min, Math.min(max, currentValue));
      const valueAngle = startAngle + ((clampedValue - min) / range) * Math.PI;

      // Determine current color
      let activeColor = thresholds[thresholds.length - 1]?.color || '#3b82f6';
      for (const th of thresholds) {
        if (clampedValue <= th.value) {
          activeColor = th.color;
          break;
        }
      }

      ctx.beginPath();
      ctx.arc(cx, cy, radius, startAngle, valueAngle);
      ctx.strokeStyle = activeColor;
      ctx.lineWidth = lineW;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Needle
      const needleLen = radius - lineW;
      const nx = cx + Math.cos(valueAngle) * needleLen;
      const ny = cy + Math.sin(valueAngle) * needleLen;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(nx, ny);
      ctx.strokeStyle = '#e2e8f0';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Center dot
      ctx.beginPath();
      ctx.arc(cx, cy, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#e2e8f0';
      ctx.fill();

      // Value text
      ctx.fillStyle = activeColor;
      ctx.font = 'bold 28px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.fillText(`${Math.round(currentValue)}${unit}`, cx, cy - 10);

      // Label
      if (label) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px Inter, sans-serif';
        ctx.textBaseline = 'top';
        ctx.fillText(label, cx, cy + 4);
      }

      // Min/Max labels
      ctx.fillStyle = '#64748b';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      ctx.fillText(String(min), cx - radius - 5, cy + 4);
      ctx.textAlign = 'right';
      ctx.fillText(String(max), cx + radius + 5, cy + 4);
    };

    if (animated) {
      const target = value;
      const start = currentRef.current;
      const duration = 800;
      const startTime = performance.now();

      const animate = (time: number) => {
        const elapsed = time - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + (target - start) * eased;
        currentRef.current = current;
        drawFrame(current);
        if (progress < 1) {
          animRef.current = requestAnimationFrame(animate);
        }
      };

      animRef.current = requestAnimationFrame(animate);
    } else {
      currentRef.current = value;
      drawFrame(value);
    }

    return () => cancelAnimationFrame(animRef.current);
  }, [value, min, max, thresholds, label, unit, width, height, animated]);

  return (
    <div>
      <canvas ref={canvasRef} style={{ width, height }} />
      {thresholds.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginTop: 4 }}>
          {thresholds.map((th) => (
            <div key={th.label || th.value} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: th.color }} />
              <span style={{ color: '#94a3b8', fontSize: 10 }}>{th.label || `< ${th.value}`}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
