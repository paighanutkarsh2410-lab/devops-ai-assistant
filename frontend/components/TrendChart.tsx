'use client';

import { useRef, useEffect } from 'react';

interface Props {
  data: number[];
  labels?: string[];
  title: string;
  color?: string;
  height?: number;
  showArea?: boolean;
  trend?: string;
}

export default function TrendChart({
  data,
  labels,
  title,
  color = '#3b82f6',
  height = 160,
  showArea = true,
  trend,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const w = rect.width;
    const h = rect.height;

    ctx.clearRect(0, 0, w, h);

    const padTop = 10;
    const padBottom = 24;
    const padLeft = 32;
    const padRight = 8;
    const chartW = w - padLeft - padRight;
    const chartH = h - padTop - padBottom;

    const maxVal = Math.max(...data, 1);
    const minVal = Math.min(...data, 0);
    const range = maxVal - minVal || 1;

    const xStep = chartW / Math.max(data.length - 1, 1);

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padTop + (chartH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(w - padRight, y);
      ctx.stroke();

      // Y-axis labels
      const val = maxVal - (range / 4) * i;
      ctx.fillStyle = '#71717a';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(val.toFixed(0), padLeft - 4, y + 3);
    }

    // Data points
    const points = data.map((v, i) => ({
      x: padLeft + i * xStep,
      y: padTop + chartH - ((v - minVal) / range) * chartH,
    }));

    // Area fill
    if (showArea) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, padTop + chartH);
      points.forEach(p => ctx.lineTo(p.x, p.y));
      ctx.lineTo(points[points.length - 1].x, padTop + chartH);
      ctx.closePath();
      const grad = ctx.createLinearGradient(0, padTop, 0, padTop + chartH);
      grad.addColorStop(0, color + '30');
      grad.addColorStop(1, color + '05');
      ctx.fillStyle = grad;
      ctx.fill();
    }

    // Line
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    points.forEach((p, i) => (i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)));
    ctx.stroke();

    // Dots
    points.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    });

    // X-axis labels (sparse)
    if (labels && labels.length > 0) {
      ctx.fillStyle = '#71717a';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      const step = Math.max(1, Math.floor(labels.length / 6));
      for (let i = 0; i < labels.length; i += step) {
        ctx.fillText(labels[i], padLeft + i * xStep, h - 4);
      }
    }
  }, [data, labels, color, height, showArea]);

  const trendColor = trend === 'increasing' || trend === 'degrading'
    ? '#dc2626'
    : trend === 'decreasing' || trend === 'improving'
    ? '#16a34a'
    : '#6b7280';

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.06)', padding: '14px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: '#f0f0f0' }}>{title}</span>
        {trend && (
          <span style={{
            fontSize: '11px', padding: '2px 8px', borderRadius: '10px',
            background: trendColor + '15', color: trendColor, fontWeight: 600,
          }}>
            {trend}
          </span>
        )}
      </div>
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: `${height}px`, display: 'block' }}
      />
    </div>
  );
}
