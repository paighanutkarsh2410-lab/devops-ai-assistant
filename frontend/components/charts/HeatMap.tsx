'use client';

import { useRef, useEffect, useState, useCallback } from 'react';

interface HeatMapCell {
  row: string;
  col: string;
  value: number;
}

interface HeatMapProps {
  data: HeatMapCell[];
  rows?: string[];
  cols?: string[];
  colorRange?: [string, string, string]; // [low, mid, high]
  title?: string;
  width?: number;
  height?: number;
  onCellClick?: (cell: HeatMapCell) => void;
}

export default function HeatMap({
  data,
  rows: propRows,
  cols: propCols,
  colorRange = ['#1a237e', '#ffeb3b', '#d32f2f'],
  title,
  width = 700,
  height = 400,
  onCellClick,
}: HeatMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; cell: HeatMapCell } | null>(null);

  const rows = propRows || [...new Set(data.map((d) => d.row))];
  const cols = propCols || [...new Set(data.map((d) => d.col))];

  const values = data.map((d) => d.value);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);

  const interpolateColor = useCallback(
    (value: number) => {
      const t = maxVal === minVal ? 0.5 : (value - minVal) / (maxVal - minVal);
      const [low, mid, high] = colorRange;
      const parse = (hex: string) => {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return [r, g, b];
      };
      const lerp = (a: number[], b: number[], f: number) =>
        a.map((v, i) => Math.round(v + (b[i] - v) * f));
      const c = t < 0.5 ? lerp(parse(low), parse(mid), t * 2) : lerp(parse(mid), parse(high), (t - 0.5) * 2);
      return `rgb(${c[0]},${c[1]},${c[2]})`;
    },
    [colorRange, minVal, maxVal]
  );

  const labelW = 100;
  const labelH = 60;
  const cellW = Math.max(30, (width - labelW - 20) / cols.length);
  const cellH = Math.max(20, (height - labelH - 40) / rows.length);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Row labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    rows.forEach((row, i) => {
      const y = labelH + i * cellH + cellH / 2;
      const label = row.length > 12 ? row.slice(0, 11) + '...' : row;
      ctx.fillText(label, labelW - 8, y);
    });

    // Col labels
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    cols.forEach((col, j) => {
      const x = labelW + j * cellW + cellW / 2;
      ctx.save();
      ctx.translate(x, labelH - 6);
      ctx.rotate(-Math.PI / 6);
      const label = col.length > 10 ? col.slice(0, 9) + '...' : col;
      ctx.fillText(label, 0, 0);
      ctx.restore();
    });

    // Cells
    const dataMap = new Map<string, number>();
    data.forEach((d) => dataMap.set(`${d.row}|${d.col}`, d.value));

    rows.forEach((row, i) => {
      cols.forEach((col, j) => {
        const key = `${row}|${col}`;
        const val = dataMap.get(key);
        const x = labelW + j * cellW;
        const y = labelH + i * cellH;

        if (val !== undefined) {
          ctx.fillStyle = interpolateColor(val);
          ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);

          // Value text
          if (cellW > 35 && cellH > 18) {
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 10px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(String(Math.round(val)), x + cellW / 2, y + cellH / 2);
          }
        } else {
          ctx.fillStyle = '#1e293b';
          ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);
        }
      });
    });

    // Legend bar
    const legendY = height - 18;
    const legendW = 160;
    const legendX = width - legendW - 20;
    const gradient = ctx.createLinearGradient(legendX, 0, legendX + legendW, 0);
    gradient.addColorStop(0, colorRange[0]);
    gradient.addColorStop(0.5, colorRange[1]);
    gradient.addColorStop(1, colorRange[2]);
    ctx.fillStyle = gradient;
    ctx.fillRect(legendX, legendY, legendW, 10);
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(String(Math.round(minVal)), legendX, legendY - 3);
    ctx.textAlign = 'right';
    ctx.fillText(String(Math.round(maxVal)), legendX + legendW, legendY - 3);
  }, [data, rows, cols, width, height, interpolateColor, cellW, cellH, colorRange, labelH, labelW, minVal, maxVal]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const col = Math.floor((mx - labelW) / cellW);
    const row = Math.floor((my - labelH) / cellH);
    if (row >= 0 && row < rows.length && col >= 0 && col < cols.length) {
      const cell = data.find((d) => d.row === rows[row] && d.col === cols[col]);
      if (cell) {
        setTooltip({ x: mx, y: my, cell });
        return;
      }
    }
    setTooltip(null);
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onCellClick || !tooltip) return;
    onCellClick(tooltip.cell);
  };

  return (
    <div style={{ position: 'relative' }}>
      {title && (
        <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{title}</div>
      )}
      <canvas
        ref={canvasRef}
        style={{ width, height, cursor: onCellClick ? 'pointer' : 'default' }}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setTooltip(null)}
        onClick={handleClick}
      />
      {tooltip && (
        <div
          style={{
            position: 'absolute',
            left: tooltip.x + 12,
            top: tooltip.y - 30,
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: 6,
            padding: '6px 10px',
            color: '#e2e8f0',
            fontSize: 12,
            pointerEvents: 'none',
            zIndex: 10,
            whiteSpace: 'nowrap',
          }}
        >
          <strong>{tooltip.cell.row}</strong> / {tooltip.cell.col}: <strong>{tooltip.cell.value}</strong>
        </div>
      )}
    </div>
  );
}
