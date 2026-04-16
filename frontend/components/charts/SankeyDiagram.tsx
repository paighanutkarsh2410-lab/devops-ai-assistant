'use client';

import { useRef, useEffect, useState } from 'react';

interface SankeyNode {
  id: string;
  label: string;
  color?: string;
}

interface SankeyLink {
  source: string;
  target: string;
  value: number;
}

interface SankeyProps {
  nodes: SankeyNode[];
  links: SankeyLink[];
  title?: string;
  width?: number;
  height?: number;
  onNodeClick?: (node: SankeyNode) => void;
}

interface LayoutNode extends SankeyNode {
  x: number;
  y: number;
  w: number;
  h: number;
  layer: number;
  totalValue: number;
}

export default function SankeyDiagram({
  nodes,
  links,
  title,
  width = 700,
  height = 400,
  onNodeClick,
}: SankeyProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);
  const layoutRef = useRef<LayoutNode[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !nodes.length) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const pad = { top: 20, bottom: 20, left: 30, right: 30 };
    const nodeW = 18;

    // Assign layers using topological ordering
    const outgoing = new Map<string, string[]>();
    const incoming = new Map<string, string[]>();
    nodes.forEach((n) => {
      outgoing.set(n.id, []);
      incoming.set(n.id, []);
    });
    links.forEach((l) => {
      outgoing.get(l.source)?.push(l.target);
      incoming.get(l.target)?.push(l.source);
    });

    const layers = new Map<string, number>();
    const sources = nodes.filter((n) => !incoming.get(n.id)?.length);
    const queue = sources.map((n) => n.id);
    queue.forEach((id) => layers.set(id, 0));
    const visited = new Set<string>(queue);

    let idx = 0;
    while (idx < queue.length) {
      const cur = queue[idx++];
      const curLayer = layers.get(cur) || 0;
      for (const next of outgoing.get(cur) || []) {
        const nextLayer = Math.max(layers.get(next) || 0, curLayer + 1);
        layers.set(next, nextLayer);
        if (!visited.has(next)) {
          visited.add(next);
          queue.push(next);
        }
      }
    }
    // Nodes with no assigned layer get layer 0
    nodes.forEach((n) => {
      if (!layers.has(n.id)) layers.set(n.id, 0);
    });

    const maxLayer = Math.max(...layers.values(), 0);
    const layerGap = maxLayer > 0 ? (width - pad.left - pad.right - nodeW) / maxLayer : 0;

    // Calculate node values
    const nodeValues = new Map<string, number>();
    nodes.forEach((n) => {
      const outVal = links.filter((l) => l.source === n.id).reduce((s, l) => s + l.value, 0);
      const inVal = links.filter((l) => l.target === n.id).reduce((s, l) => s + l.value, 0);
      nodeValues.set(n.id, Math.max(outVal, inVal, 1));
    });

    // Position nodes in each layer
    const layerNodes = new Map<number, SankeyNode[]>();
    nodes.forEach((n) => {
      const l = layers.get(n.id) || 0;
      if (!layerNodes.has(l)) layerNodes.set(l, []);
      layerNodes.get(l)!.push(n);
    });

    const availH = height - pad.top - pad.bottom;
    const layoutNodes: LayoutNode[] = [];

    layerNodes.forEach((layerGroup, layer) => {
      const totalVal = layerGroup.reduce((s, n) => s + (nodeValues.get(n.id) || 1), 0);
      const gap = 8;
      const usableH = availH - gap * (layerGroup.length - 1);
      let y = pad.top;

      layerGroup.forEach((n) => {
        const val = nodeValues.get(n.id) || 1;
        const h = Math.max(12, (val / totalVal) * usableH);
        layoutNodes.push({
          ...n,
          x: pad.left + layer * layerGap,
          y,
          w: nodeW,
          h,
          layer,
          totalValue: val,
        });
        y += h + gap;
      });
    });

    layoutRef.current = layoutNodes;
    const nodeMap = new Map<string, LayoutNode>();
    layoutNodes.forEach((n) => nodeMap.set(n.id, n));

    // Track how much vertical space is used per side of each node
    const sourceOffsets = new Map<string, number>();
    const targetOffsets = new Map<string, number>();
    layoutNodes.forEach((n) => {
      sourceOffsets.set(n.id, 0);
      targetOffsets.set(n.id, 0);
    });

    // Draw links
    const defaultColors = ['#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];

    links.forEach((link, i) => {
      const src = nodeMap.get(link.source);
      const tgt = nodeMap.get(link.target);
      if (!src || !tgt) return;

      const srcVal = src.totalValue || 1;
      const tgtVal = tgt.totalValue || 1;
      const linkH_src = (link.value / srcVal) * src.h;
      const linkH_tgt = (link.value / tgtVal) * tgt.h;

      const srcOff = sourceOffsets.get(link.source) || 0;
      const tgtOff = targetOffsets.get(link.target) || 0;

      const x0 = src.x + src.w;
      const y0 = src.y + srcOff + linkH_src / 2;
      const x1 = tgt.x;
      const y1 = tgt.y + tgtOff + linkH_tgt / 2;
      const cpx = (x0 + x1) / 2;

      ctx.beginPath();
      ctx.moveTo(x0, src.y + srcOff);
      ctx.bezierCurveTo(cpx, src.y + srcOff, cpx, tgt.y + tgtOff, x1, tgt.y + tgtOff);
      ctx.lineTo(x1, tgt.y + tgtOff + linkH_tgt);
      ctx.bezierCurveTo(cpx, tgt.y + tgtOff + linkH_tgt, cpx, src.y + srcOff + linkH_src, x0, src.y + srcOff + linkH_src);
      ctx.closePath();

      const color = src.color || defaultColors[i % defaultColors.length];
      ctx.fillStyle = color + '40';
      ctx.fill();
      ctx.strokeStyle = color + '60';
      ctx.lineWidth = 0.5;
      ctx.stroke();

      sourceOffsets.set(link.source, srcOff + linkH_src);
      targetOffsets.set(link.target, tgtOff + linkH_tgt);
    });

    // Draw nodes
    layoutNodes.forEach((n, i) => {
      const color = n.color || defaultColors[i % defaultColors.length];
      ctx.fillStyle = color;
      ctx.fillRect(n.x, n.y, n.w, n.h);

      // Label
      ctx.fillStyle = '#e2e8f0';
      ctx.font = '11px Inter, sans-serif';
      ctx.textBaseline = 'middle';
      if (n.layer === 0) {
        ctx.textAlign = 'right';
        ctx.fillText(n.label, n.x - 6, n.y + n.h / 2);
      } else if (n.layer === maxLayer) {
        ctx.textAlign = 'left';
        ctx.fillText(n.label, n.x + n.w + 6, n.y + n.h / 2);
      } else {
        ctx.textAlign = 'center';
        ctx.fillText(n.label, n.x + n.w / 2, n.y - 8);
      }
    });
  }, [nodes, links, width, height]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    for (const n of layoutRef.current) {
      if (mx >= n.x && mx <= n.x + n.w && my >= n.y && my <= n.y + n.h) {
        setTooltip({ x: mx, y: my, text: `${n.label}: ${n.totalValue}` });
        return;
      }
    }
    setTooltip(null);
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onNodeClick) return;
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    for (const n of layoutRef.current) {
      if (mx >= n.x && mx <= n.x + n.w && my >= n.y && my <= n.y + n.h) {
        onNodeClick(n);
        return;
      }
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      {title && (
        <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{title}</div>
      )}
      <canvas
        ref={canvasRef}
        style={{ width, height, cursor: onNodeClick ? 'pointer' : 'default' }}
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
          }}
        >
          {tooltip.text}
        </div>
      )}
    </div>
  );
}
