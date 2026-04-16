'use client';

import { useRef, useEffect, useState } from 'react';

interface TreeMapItem {
  id: string;
  label: string;
  value: number;
  group?: string;
  color?: string;
}

interface TreeMapProps {
  data: TreeMapItem[];
  title?: string;
  width?: number;
  height?: number;
  onItemClick?: (item: TreeMapItem) => void;
}

const GROUP_COLORS = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#64748b'];

interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
  item: TreeMapItem;
}

function squarify(items: TreeMapItem[], x: number, y: number, w: number, h: number): Rect[] {
  if (!items.length) return [];
  const total = items.reduce((s, i) => s + i.value, 0);
  if (total === 0) return [];

  const rects: Rect[] = [];
  let remaining = [...items].sort((a, b) => b.value - a.value);
  let cx = x, cy = y, cw = w, ch = h;

  while (remaining.length > 0) {
    const isWide = cw >= ch;
    const side = isWide ? ch : cw;
    const remTotal = remaining.reduce((s, i) => s + i.value, 0);

    // Find best row
    let row: TreeMapItem[] = [];
    let rowArea = 0;
    let bestRatio = Infinity;

    for (let i = 0; i < remaining.length; i++) {
      row.push(remaining[i]);
      rowArea += remaining[i].value;
      const rowSide = (rowArea / remTotal) * (isWide ? cw : ch);

      let worstRatio = 0;
      let offset = 0;
      for (const item of row) {
        const itemSide = (item.value / rowArea) * side;
        const ratio = Math.max(rowSide / itemSide, itemSide / rowSide);
        worstRatio = Math.max(worstRatio, ratio);
        offset += itemSide;
      }

      if (worstRatio > bestRatio && row.length > 1) {
        row.pop();
        rowArea -= remaining[i].value;
        break;
      }
      bestRatio = worstRatio;
    }

    // Layout row
    const rowSide = (rowArea / remTotal) * (isWide ? cw : ch);
    let offset = 0;
    for (const item of row) {
      const itemSide = (item.value / rowArea) * side;
      if (isWide) {
        rects.push({ x: cx, y: cy + offset, w: rowSide, h: itemSide, item });
      } else {
        rects.push({ x: cx + offset, y: cy, w: itemSide, h: rowSide, item });
      }
      offset += itemSide;
    }

    // Shrink remaining area
    if (isWide) {
      cx += rowSide;
      cw -= rowSide;
    } else {
      cy += rowSide;
      ch -= rowSide;
    }

    remaining = remaining.slice(row.length);
  }

  return rects;
}

export default function TreeMap({ data, title, width = 700, height = 400, onItemClick }: TreeMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rectsRef = useRef<Rect[]>([]);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; item: TreeMapItem } | null>(null);

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

    const pad = 4;
    const rects = squarify(data, pad, pad, width - pad * 2, height - pad * 2);
    rectsRef.current = rects;

    const groups = [...new Set(data.map((d) => d.group || d.id))];
    const groupColorMap = new Map<string, string>();
    groups.forEach((g, i) => groupColorMap.set(g, GROUP_COLORS[i % GROUP_COLORS.length]));

    rects.forEach((r) => {
      const color = r.item.color || groupColorMap.get(r.item.group || r.item.id) || '#64748b';
      const gap = 2;

      ctx.fillStyle = color + 'cc';
      ctx.beginPath();
      ctx.roundRect(r.x + gap, r.y + gap, Math.max(0, r.w - gap * 2), Math.max(0, r.h - gap * 2), 4);
      ctx.fill();

      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(r.x + gap, r.y + gap, Math.max(0, r.w - gap * 2), Math.max(0, r.h - gap * 2), 4);
      ctx.stroke();

      // Label
      if (r.w > 50 && r.h > 30) {
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const maxChars = Math.floor((r.w - 10) / 7);
        const label = r.item.label.length > maxChars ? r.item.label.slice(0, maxChars - 1) + '\u2026' : r.item.label;
        ctx.fillText(label, r.x + r.w / 2, r.y + r.h / 2 - 7);

        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = '#ffffffcc';
        ctx.fillText(String(r.item.value), r.x + r.w / 2, r.y + r.h / 2 + 8);
      }
    });
  }, [data, width, height]);

  const findRect = (mx: number, my: number): TreeMapItem | null => {
    for (const r of rectsRef.current) {
      if (mx >= r.x && mx <= r.x + r.w && my >= r.y && my <= r.y + r.h) return r.item;
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
        style={{ width, height, cursor: onItemClick ? 'pointer' : 'default' }}
        onMouseMove={(e) => {
          const rect = canvasRef.current?.getBoundingClientRect();
          if (!rect) return;
          const mx = e.clientX - rect.left;
          const my = e.clientY - rect.top;
          const item = findRect(mx, my);
          if (item) setTooltip({ x: mx, y: my, item });
          else setTooltip(null);
        }}
        onMouseLeave={() => setTooltip(null)}
        onClick={(e) => {
          if (!onItemClick) return;
          const rect = canvasRef.current?.getBoundingClientRect();
          if (!rect) return;
          const item = findRect(e.clientX - rect.left, e.clientY - rect.top);
          if (item) onItemClick(item);
        }}
      />
      {tooltip && (
        <div
          style={{
            position: 'absolute',
            left: tooltip.x + 12,
            top: tooltip.y - 36,
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
          <strong>{tooltip.item.label}</strong>: {tooltip.item.value}
          {tooltip.item.group && <span style={{ color: '#94a3b8' }}> ({tooltip.item.group})</span>}
        </div>
      )}
    </div>
  );
}
