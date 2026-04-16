'use client';

import { useRef, useEffect, useState } from 'react';

interface RadarDataset {
  label: string;
  values: number[];
  color?: string;
}

interface RadarChartProps {
  labels: string[];
  datasets: RadarDataset[];
  maxValue?: number;
  title?: string;
  width?: number;
  height?: number;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function RadarChart({
  labels,
  datasets,
  maxValue,
  title,
  width = 400,
  height = 400,
}: RadarChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoverDataset, setHoverDataset] = useState<number | null>(null);

  const max = maxValue || Math.max(...datasets.flatMap((d) => d.values), 100);
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) / 2 - 50;
  const n = labels.length;
  const angleStep = (Math.PI * 2) / n;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !labels.length) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Grid rings
    const rings = 5;
    for (let r = 1; r <= rings; r++) {
      const ringR = (r / rings) * radius;
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const x = cx + Math.cos(angle) * ringR;
        const y = cy + Math.sin(angle) * ringR;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.strokeStyle = r === rings ? '#334155' : '#1e293b';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Value label
      ctx.fillStyle = '#64748b';
      ctx.font = '9px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'bottom';
      ctx.fillText(String(Math.round((r / rings) * max)), cx + 4, cy - ringR - 2);
    }

    // Spokes
    for (let i = 0; i < n; i++) {
      const angle = i * angleStep - Math.PI / 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Labels
      const lx = cx + Math.cos(angle) * (radius + 18);
      const ly = cy + Math.sin(angle) * (radius + 18);
      ctx.fillStyle = '#cbd5e1';
      ctx.font = '11px Inter, sans-serif';
      ctx.textAlign = Math.abs(Math.cos(angle)) < 0.1 ? 'center' : Math.cos(angle) > 0 ? 'left' : 'right';
      ctx.textBaseline = Math.abs(Math.sin(angle)) < 0.1 ? 'middle' : Math.sin(angle) > 0 ? 'top' : 'bottom';
      ctx.fillText(labels[i], lx, ly);
    }

    // Datasets
    datasets.forEach((ds, di) => {
      const color = ds.color || COLORS[di % COLORS.length];
      const isHighlighted = hoverDataset === null || hoverDataset === di;
      const alpha = isHighlighted ? 1 : 0.2;

      // Filled area
      ctx.beginPath();
      ds.values.forEach((val, i) => {
        const r = (Math.min(val, max) / max) * radius;
        const angle = i * angleStep - Math.PI / 2;
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = color + (isHighlighted ? '30' : '10');
      ctx.fill();
      ctx.strokeStyle = color + (isHighlighted ? 'cc' : '40');
      ctx.lineWidth = 2;
      ctx.stroke();

      // Data points
      ds.values.forEach((val, i) => {
        const r = (Math.min(val, max) / max) * radius;
        const angle = i * angleStep - Math.PI / 2;
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = isHighlighted ? color : color + '40';
        ctx.fill();
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });
    });
  }, [labels, datasets, max, width, height, hoverDataset, cx, cy, radius, n, angleStep]);

  return (
    <div>
      {title && (
        <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{title}</div>
      )}
      <canvas ref={canvasRef} style={{ width, height }} />
      {datasets.length > 1 && (
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 8 }}>
          {datasets.map((ds, i) => {
            const color = ds.color || COLORS[i % COLORS.length];
            return (
              <div
                key={ds.label}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  cursor: 'pointer',
                  opacity: hoverDataset === null || hoverDataset === i ? 1 : 0.4,
                  transition: 'opacity 0.2s',
                }}
                onMouseEnter={() => setHoverDataset(i)}
                onMouseLeave={() => setHoverDataset(null)}
              >
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
                <span style={{ color: '#cbd5e1', fontSize: 12 }}>{ds.label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
