'use client';

import { useRef, useEffect, useState, useCallback } from 'react';

interface GraphNode {
  id: string;
  label: string;
  group?: string;
  size?: number;
  color?: string;
}

interface GraphEdge {
  source: string;
  target: string;
  weight?: number;
  label?: string;
}

interface NetworkGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  title?: string;
  width?: number;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
}

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

const GROUP_COLORS: Record<string, string> = {
  service: '#3b82f6',
  database: '#8b5cf6',
  cache: '#06b6d4',
  queue: '#10b981',
  gateway: '#f59e0b',
  external: '#ef4444',
  default: '#64748b',
};

export default function NetworkGraph({
  nodes,
  edges,
  title,
  width = 700,
  height = 450,
  onNodeClick,
}: NetworkGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const simNodesRef = useRef<SimNode[]>([]);
  const animRef = useRef<number>(0);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);
  const [dragNode, setDragNode] = useState<string | null>(null);
  const isDragging = useRef(false);

  const draw = useCallback(
    (simNodes: SimNode[]) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);

      const nodeMap = new Map<string, SimNode>();
      simNodes.forEach((n) => nodeMap.set(n.id, n));

      // Edges
      edges.forEach((edge) => {
        const src = nodeMap.get(edge.source);
        const tgt = nodeMap.get(edge.target);
        if (!src || !tgt) return;

        const w = Math.min(4, (edge.weight || 1) * 1.5);
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle = '#475569';
        ctx.lineWidth = w;
        ctx.stroke();

        // Arrow
        const angle = Math.atan2(tgt.y - src.y, tgt.x - src.x);
        const tgtR = (tgt.size || 8) + 4;
        const ax = tgt.x - Math.cos(angle) * tgtR;
        const ay = tgt.y - Math.sin(angle) * tgtR;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(ax - 8 * Math.cos(angle - 0.4), ay - 8 * Math.sin(angle - 0.4));
        ctx.lineTo(ax - 8 * Math.cos(angle + 0.4), ay - 8 * Math.sin(angle + 0.4));
        ctx.closePath();
        ctx.fillStyle = '#475569';
        ctx.fill();

        // Edge label
        if (edge.label) {
          const mx = (src.x + tgt.x) / 2;
          const my = (src.y + tgt.y) / 2;
          ctx.fillStyle = '#94a3b8';
          ctx.font = '9px Inter, sans-serif';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'bottom';
          ctx.fillText(edge.label, mx, my - 4);
        }
      });

      // Nodes
      simNodes.forEach((n) => {
        const r = n.size || 8;
        const color = n.color || GROUP_COLORS[n.group || 'default'] || GROUP_COLORS.default;

        // Glow
        ctx.beginPath();
        ctx.arc(n.x, n.y, r + 4, 0, Math.PI * 2);
        ctx.fillStyle = color + '20';
        ctx.fill();

        // Circle
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = color + 'aa';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Label
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(n.label, n.x, n.y + r + 5);
      });
    },
    [edges, width, height]
  );

  // Force simulation
  useEffect(() => {
    const cx = width / 2;
    const cy = height / 2;

    const simNodes: SimNode[] = nodes.map((n, i) => ({
      ...n,
      x: cx + (Math.cos((i / nodes.length) * Math.PI * 2) * width) / 3.5,
      y: cy + (Math.sin((i / nodes.length) * Math.PI * 2) * height) / 3.5,
      vx: 0,
      vy: 0,
    }));
    simNodesRef.current = simNodes;

    const nodeMap = new Map<string, SimNode>();
    simNodes.forEach((n) => nodeMap.set(n.id, n));

    let iterations = 0;
    const maxIter = 150;

    const tick = () => {
      if (iterations >= maxIter) {
        draw(simNodes);
        return;
      }
      iterations++;
      const alpha = 1 - iterations / maxIter;

      // Repulsion
      for (let i = 0; i < simNodes.length; i++) {
        for (let j = i + 1; j < simNodes.length; j++) {
          const a = simNodes[i];
          const b = simNodes[j];
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (800 * alpha) / (dist * dist);
          dx = (dx / dist) * force;
          dy = (dy / dist) * force;
          a.vx -= dx;
          a.vy -= dy;
          b.vx += dx;
          b.vy += dy;
        }
      }

      // Attraction via edges
      edges.forEach((e) => {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (!src || !tgt) return;
        let dx = tgt.x - src.x;
        let dy = tgt.y - src.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 100) * 0.02 * alpha;
        dx = (dx / dist) * force;
        dy = (dy / dist) * force;
        src.vx += dx;
        src.vy += dy;
        tgt.vx -= dx;
        tgt.vy -= dy;
      });

      // Center gravity
      simNodes.forEach((n) => {
        n.vx += (cx - n.x) * 0.005 * alpha;
        n.vy += (cy - n.y) * 0.005 * alpha;
      });

      // Apply velocity
      simNodes.forEach((n) => {
        n.vx *= 0.6;
        n.vy *= 0.6;
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.max(30, Math.min(width - 30, n.x));
        n.y = Math.max(30, Math.min(height - 30, n.y));
      });

      draw(simNodes);
      animRef.current = requestAnimationFrame(tick);
    };

    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [nodes, edges, width, height, draw]);

  const findNode = (mx: number, my: number): SimNode | null => {
    for (const n of simNodesRef.current) {
      const r = n.size || 8;
      const dx = mx - n.x;
      const dy = my - n.y;
      if (dx * dx + dy * dy <= (r + 4) * (r + 4)) return n;
    }
    return null;
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    if (isDragging.current && dragNode) {
      const n = simNodesRef.current.find((sn) => sn.id === dragNode);
      if (n) {
        n.x = mx;
        n.y = my;
        draw(simNodesRef.current);
      }
      return;
    }

    const node = findNode(mx, my);
    if (node) {
      const edgeCount = edges.filter((e) => e.source === node.id || e.target === node.id).length;
      setTooltip({ x: mx, y: my, text: `${node.label} (${node.group || 'node'}) \u2014 ${edgeCount} connections` });
    } else {
      setTooltip(null);
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const node = findNode(e.clientX - rect.left, e.clientY - rect.top);
    if (node) {
      isDragging.current = true;
      setDragNode(node.id);
    }
  };

  const handleMouseUp = () => {
    if (isDragging.current && !dragNode) return;
    isDragging.current = false;
    setDragNode(null);
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onNodeClick) return;
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const node = findNode(e.clientX - rect.left, e.clientY - rect.top);
    if (node) onNodeClick(node);
  };

  return (
    <div style={{ position: 'relative' }}>
      {title && (
        <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{title}</div>
      )}
      <canvas
        ref={canvasRef}
        style={{ width, height, cursor: dragNode ? 'grabbing' : 'grab' }}
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={() => {
          setTooltip(null);
          isDragging.current = false;
          setDragNode(null);
        }}
        onClick={handleClick}
      />
      {tooltip && !isDragging.current && (
        <div
          style={{
            position: 'absolute',
            left: tooltip.x + 14,
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
