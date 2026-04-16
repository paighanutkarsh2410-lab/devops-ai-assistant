'use client';

interface SkeletonProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  count?: number;
}

function SkeletonLine({ width = '100%', height = '16px', borderRadius = '4px' }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      style={{
        width,
        height,
        borderRadius,
        background: 'linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.5s infinite',
      }}
    />
  );
}

export function CardSkeleton() {
  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '12px', padding: '24px', border: '1px solid rgba(255,255,255,0.06)' }}>
      <SkeletonLine width="40%" height="12px" />
      <div style={{ marginTop: '12px' }}>
        <SkeletonLine width="60%" height="32px" />
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.06)' }}>
      <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <SkeletonLine width="30%" height="20px" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.04)', display: 'flex', gap: '16px', alignItems: 'center' }}>
          <SkeletonLine width="40%" height="14px" />
          <SkeletonLine width="20%" height="14px" />
          <SkeletonLine width="15%" height="24px" borderRadius="12px" />
        </div>
      ))}
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <>
      <style>{`@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }`}</style>
      <div aria-label="Loading dashboard" role="status">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
        <TableSkeleton rows={6} />
      </div>
    </>
  );
}

export function ChartSkeleton() {
  return (
    <>
      <style>{`@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }`}</style>
      <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '12px', padding: '24px', border: '1px solid rgba(255,255,255,0.06)' }}>
        <SkeletonLine width="30%" height="20px" />
        <div style={{ marginTop: '16px' }}>
          <SkeletonLine width="100%" height="200px" borderRadius="8px" />
        </div>
      </div>
    </>
  );
}

export default SkeletonLine;
