'use client';

import { useRef, useEffect, useState } from 'react';

interface BubbleData {
  id: string;
  label: string;
  x: number;
  y: number;
  size: number;
  group?: string;
  color?: string;
}

interface BubbleChartProps {
  data: BubbleData[];
  xLabel?: string;
  yLabel?: string;
  title?: string;
  width?: number;
  height?: number;
  onBubbleClick?: (bubble: BubbleData) => void;
}

const COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];

export default function BubbleChart({
  data,
  xLabel = 'X',
  yLabel = 'Y',
  title,
  width = 700,
  height = 400,
  onBubbleClick,
}: BubbleChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; bubble: BubbleData } | null>(null);

  const pad = { top: 20, bottom: 50, left: 60, right: 30 };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const xs = data.map((d) => d.x);
    const ys = data.map((d) => d.y);
    const sizes = data.map((d) => d.size);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const maxSize = Math.max(...sizes);

    const chartW = width - pad.left - pad.right;
    const chartH = height - pad.top - pad.bottom;
    const xRange = maxX - minX || 1;
    const yRange = maxY - minY || 1;

    const scaleX = (v: number) => pad.left + ((v - minX) / xRange) * chartW;
    const scaleY = (v: number) => pad.top + chartH - ((v - minY) / yRange) * chartH;
    const scaleR = (v: number) => 6 + (v / (maxSize || 1)) * 30;

    // Grid
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = pad.top + (i / 5) * chartH;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(width - pad.right, y);
      ctx.stroke();
    }

    // Axes labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= 5; i++) {
      const val = minY + ((5 - i) / 5) * yRange;
      ctx.fillText(val.toFixed(1), pad.left - 8, pad.top + (i / 5) * chartH);
    }
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (let i = 0; i <= 5; i++) {
      const val = minX + (i / 5) * xRange;
      ctx.fillText(val.toFixed(1), pad.left + (i / 5) * chartW, height - pad.bottom + 8);
    }

    // Axis names
    ctx.font = '11px Inter, sans-serif';
    ctx.fillStyle = '#cbd5e1';
    ctx.textAlign = 'center';
    ctx.fillText(xLabel, pad.left + chartW / 2, height - 10);

    ctx.save();
    ctx.translate(14, pad.top + chartH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(yLabel, 0, 0);
    ctx.restore();

    // Groups for legend
    const groups = [...new Set(data.map((d) => d.group || d.id))];
    const groupColorMap = new Map<string, string>();
    groups.forEach((g, i) => groupColorMap.set(g, COLORS[i % COLORS.length]));

    // Bubbles
    const sorted = [...data].sort((a, b) => b.size - a.size); // draw large first
    sorted.forEach((d) => {
      const cx = scaleX(d.x);
      const cy = scaleY(d.y);
      const r = scaleR(d.size);
      const color = d.color || groupColorMap.get(d.group || d.id) || '#64748b';

      // Glow
      ctx.beginPath();
      ctx.arc(cx, cy, r + 2, 0, Math.PI * 2);
      ctx.fillStyle = color + '20';
      ctx.fill();

      // Fill
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = color + '99';
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Label
      if (r > 14) {
        ctx.fillStyle = '#fff';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const maxChars = Math.floor((r * 2) / 6);
        const label = d.label.length > maxChars ? d.label.slice(0, maxChars - 1) + '\u2026' : d.label;
        ctx.fillText(label, cx, cy);
      }
    });

    // Legend
    if (groups.length > 1 && groups.length <= 8) {
      let lx = width - pad.right - 10;
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.font = '10px Inter, sans-serif';
      groups.reverse().forEach((g) => {
        const color = groupColorMap.get(g) || '#64748b';
        const textW = ctx.measureText(g).width;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(lx - textW - 10, pad.top + 10, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#94a3b8';
        ctx.fillText(g, lx, pad.top + 10);
        // Next line for legend items doesn't stack - keep simple
      });
    }
  }, [data, width, height, xLabel, yLabel, pad.top, pad.bottom, pad.left, pad.right]);

  const findBubble = (mx: number, my: number): BubbleData | null => {
    if (!data.length) return null;
    const xs = data.map((d) => d.x);
    const ys = data.map((d) => d.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const maxSize = Math.max(...data.map((d) => d.size));
    const chartW = width - pad.left - pad.right;
    const chartH = height - pad.top - pad.bottom;
    const xRange = maxX - minX || 1;
    const yRange = maxY - minY || 1;

    for (const d of data) {
      const cx = pad.left + ((d.x - minX) / xRange) * chartW;
      const cy = pad.top + chartH - ((d.y - minY) / yRange) * chartH;
      const r = 6 + (d.size / (maxSize || 1)) * 30;
      const dx = mx - cx, dy = my - cy;
      if (dx * dx + dy * dy <= r * r) return d;
    }
    return null;
  };

  return (
    <div style={{ position: 'relative' }}>
      {title && (
        <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{title}</div>
      )}
      <canvas
        ref={canvasRef}
        style={{ width, height, cursor: onBubbleClick ? 'pointer' : 'default' }}
        onMouseMove={(e) => {
          const rect = canvasRef.current?.getBoundingClientRect();
          if (!rect) return;
          const mx = e.clientX - rect.left;
          const my = e.clientY - rect.top;
          const bubble = findBubble(mx, my);
          if (bubble) setTooltip({ x: mx, y: my, bubble });
          else setTooltip(null);
        }}
        onMouseLeave={() => setTooltip(null)}
        onClick={(e) => {
          if (!onBubbleClick) return;
          const rect = canvasRef.current?.getBoundingClientRect();
          if (!rect) return;
          const b = findBubble(e.clientX - rect.left, e.clientY - rect.top);
          if (b) onBubbleClick(b);
        }}
      />
      {tooltip && (
        <div
          style={{
            position: 'absolute',
            left: tooltip.x + 14,
            top: tooltip.y - 40,
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: 6,
            padding: '6px 10px',
            color: '#e2e8f0',
            fontSize: 12,
            pointerEvents: 'none',
            zIndex: 10,
          }}
        >
          <strong>{tooltip.bubble.label}</strong>
          <div style={{ color: '#94a3b8' }}>
            {xLabel}: {tooltip.bubble.x} / {yLabel}: {tooltip.bubble.y} / Size: {tooltip.bubble.size}
          </div>
        </div>
      )}
    </div>
  );
}
