'use client';

import { useState, useEffect, useRef } from 'react';

interface DataPoint {
  time: string;
  value: number;
}

interface Props {
  title: string;
  data: DataPoint[];
  color?: string;
  unit?: string;
  height?: number;
  maxPoints?: number;
  type?: 'line' | 'area' | 'sparkline';
}

export default function LiveChart({
  title,
  data,
  color = '#3b82f6',
  unit = '',
  height = 200,
  maxPoints = 60,
  type = 'line',
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [displayData, setDisplayData] = useState<DataPoint[]>([]);

  useEffect(() => {
    if (!isPaused) {
      setDisplayData(data.slice(-maxPoints));
    }
  }, [data, isPaused, maxPoints]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || displayData.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const padding = { top: 10, right: 10, bottom: 25, left: 45 };
    const plotW = w - padding.left - padding.right;
    const plotH = h - padding.top - padding.bottom;

    // Clear
    ctx.clearRect(0, 0, w, h);

    // Data bounds
    const values = displayData.map(d => d.value);
    const minV = Math.min(...values) * 0.9;
    const maxV = Math.max(...values) * 1.1 || 1;

    // Scale functions
    const xScale = (i: number) => padding.left + (i / (displayData.length - 1)) * plotW;
    const yScale = (v: number) => padding.top + plotH - ((v - minV) / (maxV - minV)) * plotH;

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (plotH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(w - padding.right, y);
      ctx.stroke();

      // Y-axis labels
      const val = maxV - (i / 4) * (maxV - minV);
      ctx.fillStyle = '#71717a';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(val.toFixed(1), padding.left - 5, y + 3);
    }

    // Area fill
    if (type === 'area') {
      ctx.beginPath();
      ctx.moveTo(xScale(0), yScale(displayData[0].value));
      displayData.forEach((d, i) => ctx.lineTo(xScale(i), yScale(d.value)));
      ctx.lineTo(xScale(displayData.length - 1), padding.top + plotH);
      ctx.lineTo(xScale(0), padding.top + plotH);
      ctx.closePath();
      ctx.fillStyle = `${color}20`;
      ctx.fill();
    }

    // Line
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    displayData.forEach((d, i) => {
      const x = xScale(i);
      const y = yScale(d.value);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Current value dot
    if (displayData.length > 0) {
      const last = displayData[displayData.length - 1];
      const lx = xScale(displayData.length - 1);
      const ly = yScale(last.value);
      ctx.beginPath();
      ctx.arc(lx, ly, 4, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#18181b';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }, [displayData, color, type]);

  const currentValue = displayData.length > 0 ? displayData[displayData.length - 1].value : 0;

  if (type === 'sparkline') {
    return (
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '40px' }}
        aria-label={`${title}: ${currentValue}${unit}`}
      />
    );
  }

  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)', padding: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div>
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#f0f0f0' }}>{title}</span>
          <span style={{ fontSize: '20px', fontWeight: 700, marginLeft: '12px', color }}>
            {currentValue.toFixed(1)}{unit}
          </span>
        </div>
        <button
          onClick={() => setIsPaused(!isPaused)}
          aria-label={isPaused ? 'Resume chart' : 'Pause chart'}
          style={{
            padding: '4px 12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)',
            background: isPaused ? 'rgba(220,38,38,0.15)' : 'rgba(255,255,255,0.05)', cursor: 'pointer', fontSize: '12px', color: '#a1a1aa',
          }}
        >
          {isPaused ? '\u25B6 Resume' : '\u23F8 Pause'}
        </button>
      </div>
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: `${height}px` }}
        aria-label={`${title} chart showing ${displayData.length} data points`}
      />
    </div>
  );
}
