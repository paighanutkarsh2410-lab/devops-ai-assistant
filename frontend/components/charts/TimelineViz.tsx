'use client';

import { useRef, useEffect, useState } from 'react';

interface TimelineEvent {
  id: string;
  label: string;
  start: string; // ISO date
  end?: string;  // ISO date
  category?: string;
  color?: string;
  description?: string;
}

interface TimelineVizProps {
  events: TimelineEvent[];
  title?: string;
  width?: number;
  height?: number;
  onEventClick?: (event: TimelineEvent) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  incident: '#ef4444',
  deployment: '#3b82f6',
  maintenance: '#f59e0b',
  alert: '#f97316',
  resolution: '#10b981',
  default: '#8b5cf6',
};

export default function TimelineViz({
  events,
  title,
  width = 800,
  height = 350,
  onEventClick,
}: TimelineVizProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; event: TimelineEvent } | null>(null);

  const sortedEvents = [...events].sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

  const pad = { top: 40, bottom: 50, left: 40, right: 20 };
  const laneH = 32;
  const barH = 22;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !sortedEvents.length) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const times = sortedEvents.map((e) => new Date(e.start).getTime());
    const endTimes = sortedEvents.map((e) => e.end ? new Date(e.end).getTime() : new Date(e.start).getTime() + 3600000);
    const minT = Math.min(...times);
    const maxT = Math.max(...endTimes);
    const range = maxT - minT || 3600000;

    const xScale = (t: number) => pad.left + ((t - minT) / range) * (width - pad.left - pad.right);

    // Time axis
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.left, height - pad.bottom);
    ctx.lineTo(width - pad.right, height - pad.bottom);
    ctx.stroke();

    // Ticks
    const tickCount = Math.min(8, sortedEvents.length);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center';
    for (let i = 0; i <= tickCount; i++) {
      const t = minT + (i / tickCount) * range;
      const x = xScale(t);
      ctx.beginPath();
      ctx.moveTo(x, height - pad.bottom);
      ctx.lineTo(x, height - pad.bottom + 5);
      ctx.strokeStyle = '#475569';
      ctx.stroke();

      const d = new Date(t);
      const label = range > 86400000 * 2
        ? `${d.getMonth() + 1}/${d.getDate()}`
        : `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
      ctx.fillText(label, x, height - pad.bottom + 18);
    }

    // Assign lanes (greedy)
    const lanes: number[][] = []; // each lane tracks end times
    const eventLanes: number[] = [];

    sortedEvents.forEach((evt) => {
      const start = new Date(evt.start).getTime();
      let placed = false;
      for (let l = 0; l < lanes.length; l++) {
        if (lanes[l].every((end) => start >= end)) {
          lanes[l].push(evt.end ? new Date(evt.end).getTime() : start + 3600000);
          eventLanes.push(l);
          placed = true;
          break;
        }
      }
      if (!placed) {
        lanes.push([evt.end ? new Date(evt.end).getTime() : start + 3600000]);
        eventLanes.push(lanes.length - 1);
      }
    });

    // Lane backgrounds
    const totalLanes = lanes.length;
    for (let l = 0; l < totalLanes; l++) {
      if (l % 2 === 0) {
        ctx.fillStyle = '#0f172a40';
        ctx.fillRect(pad.left, pad.top + l * laneH, width - pad.left - pad.right, laneH);
      }
    }

    // Event bars
    sortedEvents.forEach((evt, i) => {
      const startT = new Date(evt.start).getTime();
      const endT = evt.end ? new Date(evt.end).getTime() : startT + 3600000;
      const x1 = xScale(startT);
      const x2 = xScale(endT);
      const lane = eventLanes[i];
      const y = pad.top + lane * laneH + (laneH - barH) / 2;
      const w = Math.max(x2 - x1, 6);

      const color = evt.color || CATEGORY_COLORS[evt.category || 'default'] || CATEGORY_COLORS.default;

      // Bar
      ctx.fillStyle = color + 'cc';
      ctx.beginPath();
      ctx.roundRect(x1, y, w, barH, 4);
      ctx.fill();

      // Border
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(x1, y, w, barH, 4);
      ctx.stroke();

      // Label
      if (w > 40) {
        ctx.fillStyle = '#fff';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        const maxChars = Math.floor((w - 10) / 6);
        const label = evt.label.length > maxChars ? evt.label.slice(0, maxChars - 1) + '\u2026' : evt.label;
        ctx.fillText(label, x1 + 5, y + barH / 2);
      }
    });
  }, [sortedEvents, width, height, laneH, barH, pad.top, pad.bottom, pad.left, pad.right]);

  const findEvent = (mx: number, my: number): TimelineEvent | null => {
    if (!sortedEvents.length) return null;
    const times = sortedEvents.map((e) => new Date(e.start).getTime());
    const endTimes = sortedEvents.map((e) => e.end ? new Date(e.end).getTime() : new Date(e.start).getTime() + 3600000);
    const minT = Math.min(...times);
    const maxT = Math.max(...endTimes);
    const range = maxT - minT || 3600000;
    const xScale = (t: number) => pad.left + ((t - minT) / range) * (width - pad.left - pad.right);

    // Recalculate lanes
    const lanes: number[][] = [];
    const eventLanes: number[] = [];
    sortedEvents.forEach((evt) => {
      const start = new Date(evt.start).getTime();
      let placed = false;
      for (let l = 0; l < lanes.length; l++) {
        if (lanes[l].every((end) => start >= end)) {
          lanes[l].push(evt.end ? new Date(evt.end).getTime() : start + 3600000);
          eventLanes.push(l);
          placed = true;
          break;
        }
      }
      if (!placed) {
        lanes.push([evt.end ? new Date(evt.end).getTime() : start + 3600000]);
        eventLanes.push(lanes.length - 1);
      }
    });

    for (let i = 0; i < sortedEvents.length; i++) {
      const evt = sortedEvents[i];
      const startT = new Date(evt.start).getTime();
      const endT = evt.end ? new Date(evt.end).getTime() : startT + 3600000;
      const x1 = xScale(startT);
      const x2 = xScale(endT);
      const lane = eventLanes[i];
      const y = pad.top + lane * laneH + (laneH - barH) / 2;
      const w = Math.max(x2 - x1, 6);

      if (mx >= x1 && mx <= x1 + w && my >= y && my <= y + barH) return evt;
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
        style={{ width, height, cursor: onEventClick ? 'pointer' : 'default' }}
        onMouseMove={(e) => {
          const rect = canvasRef.current?.getBoundingClientRect();
          if (!rect) return;
          const mx = e.clientX - rect.left;
          const my = e.clientY - rect.top;
          const evt = findEvent(mx, my);
          if (evt) {
            setTooltip({ x: mx, y: my, event: evt });
          } else {
            setTooltip(null);
          }
        }}
        onMouseLeave={() => setTooltip(null)}
        onClick={(e) => {
          if (!onEventClick) return;
          const rect = canvasRef.current?.getBoundingClientRect();
          if (!rect) return;
          const evt = findEvent(e.clientX - rect.left, e.clientY - rect.top);
          if (evt) onEventClick(evt);
        }}
      />
      {tooltip && (
        <div
          style={{
            position: 'absolute',
            left: Math.min(tooltip.x + 12, width - 200),
            top: tooltip.y - 50,
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: 6,
            padding: '8px 12px',
            color: '#e2e8f0',
            fontSize: 12,
            pointerEvents: 'none',
            zIndex: 10,
            maxWidth: 220,
          }}
        >
          <div style={{ fontWeight: 600 }}>{tooltip.event.label}</div>
          {tooltip.event.category && (
            <div style={{ color: '#94a3b8', fontSize: 10 }}>{tooltip.event.category}</div>
          )}
          {tooltip.event.description && (
            <div style={{ marginTop: 4, color: '#cbd5e1' }}>{tooltip.event.description}</div>
          )}
        </div>
      )}
    </div>
  );
}
