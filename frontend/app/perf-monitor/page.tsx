'use client';

import { usePerformance } from '@/lib/usePerformance';
import { apiCache } from '@/lib/cache';
import { useState, useEffect } from 'react';
import DashboardShell from '@/components/DashboardShell';
import { colors, btn } from '@/lib/theme';

function MetricBox({ label, value, unit, good, warn }: {
  label: string;
  value: number | null;
  unit: string;
  good: number;
  warn: number;
}) {
  const getColor = () => {
    if (value === null) return colors.textMuted;
    if (value <= good) return colors.success;
    if (value <= warn) return colors.warning;
    return colors.danger;
  };
  const getGrade = () => {
    if (value === null) return '-';
    if (value <= good) return 'Good';
    if (value <= warn) return 'Needs Work';
    return 'Poor';
  };

  return (
    <div style={{
      background: colors.bgCard,
      borderRadius: 14,
      padding: 16,
      border: `1px solid ${colors.border}`,
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 11, color: colors.textMuted, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 32, fontWeight: 700, color: getColor() }}>
        {value !== null ? value : '\u2014'}
        <span style={{ fontSize: 14, fontWeight: 400, marginLeft: 2 }}>{value !== null ? unit : ''}</span>
      </div>
      <div style={{ fontSize: 11, color: getColor(), marginTop: 4, fontWeight: 500 }}>
        {getGrade()}
      </div>
      <div style={{ marginTop: 8, height: 4, borderRadius: 2, background: colors.bgElevated, overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: value !== null ? `${Math.min(100, (value / (warn * 1.5)) * 100)}%` : '0',
          background: getColor(),
          borderRadius: 2,
          transition: 'width 0.5s ease',
        }} />
      </div>
    </div>
  );
}

export default function PerfMonitorPage() {
  const metrics = usePerformance();
  const [cacheSize, setCacheSize] = useState(0);
  const [memoryInfo, setMemoryInfo] = useState<{ usedJSHeapSize: number; jsHeapSizeLimit: number } | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setCacheSize(apiCache.size());
      // @ts-expect-error - memory is a non-standard API
      if (performance.memory) {
        // @ts-expect-error
        setMemoryInfo({ usedJSHeapSize: performance.memory.usedJSHeapSize, jsHeapSizeLimit: performance.memory.jsHeapSizeLimit });
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const tips = [
    { check: metrics.lcp !== null && metrics.lcp > 2500, msg: 'LCP > 2.5s: Consider lazy-loading images and deferring non-critical resources.' },
    { check: metrics.fcp !== null && metrics.fcp > 1800, msg: 'FCP > 1.8s: Reduce server response time and minimize render-blocking resources.' },
    { check: metrics.cls !== null && metrics.cls > 0.1, msg: 'CLS > 0.1: Set explicit dimensions on images/videos to prevent layout shifts.' },
    { check: metrics.fid !== null && metrics.fid > 100, msg: 'FID > 100ms: Break up long tasks and reduce main-thread work.' },
    { check: memoryInfo !== null && memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit > 0.8, msg: 'Memory usage > 80%: Watch for memory leaks in event listeners and detached DOM nodes.' },
  ].filter((t) => t.check);

  return (
    <DashboardShell>
      <div style={{ padding: 32, maxWidth: 1000, margin: '0 auto' }}>
        <div className="slide-up" style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, background: 'linear-gradient(135deg, #f0f0f0, #f59e0b)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Frontend Performance
          </h1>
          <p style={{ color: colors.textMuted, fontSize: 13, margin: '4px 0 0' }}>
            Core Web Vitals and runtime performance metrics
          </p>
        </div>

        {/* Core Web Vitals */}
        <div style={{
          background: colors.bgCard,
          borderRadius: 14,
          border: `1px solid ${colors.border}`,
          padding: 20,
          marginBottom: 20,
        }}>
          <h2 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: '0 0 16px' }}>
            Core Web Vitals
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
            <MetricBox label="FCP" value={metrics.fcp} unit="ms" good={1800} warn={3000} />
            <MetricBox label="LCP" value={metrics.lcp} unit="ms" good={2500} warn={4000} />
            <MetricBox label="FID" value={metrics.fid} unit="ms" good={100} warn={300} />
            <MetricBox label="CLS" value={metrics.cls} unit="" good={0.1} warn={0.25} />
          </div>
        </div>

        {/* Navigation Timing */}
        <div style={{
          background: colors.bgCard,
          borderRadius: 14,
          border: `1px solid ${colors.border}`,
          padding: 20,
          marginBottom: 20,
        }}>
          <h2 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: '0 0 16px' }}>
            Navigation Timing
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
            <MetricBox label="TTFB" value={metrics.ttfb} unit="ms" good={200} warn={600} />
            <MetricBox label="DOM Ready" value={metrics.domReady} unit="ms" good={1500} warn={3000} />
            <MetricBox label="Page Load" value={metrics.pageLoad} unit="ms" good={3000} warn={6000} />
          </div>
        </div>

        {/* Runtime */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
          <div style={{
            background: colors.bgCard,
            borderRadius: 14,
            border: `1px solid ${colors.border}`,
            padding: 20,
          }}>
            <h2 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: '0 0 12px' }}>
              API Cache
            </h2>
            <div style={{ fontSize: 36, fontWeight: 700, color: colors.accent }}>{cacheSize}</div>
            <div style={{ color: colors.textMuted, fontSize: 12 }}>cached entries</div>
            <button
              onClick={() => { apiCache.clear(); setCacheSize(0); }}
              style={{ ...btn, marginTop: 12 }}
            >
              Clear Cache
            </button>
          </div>

          <div style={{
            background: colors.bgCard,
            borderRadius: 14,
            border: `1px solid ${colors.border}`,
            padding: 20,
          }}>
            <h2 style={{ color: colors.text, fontSize: 16, fontWeight: 600, margin: '0 0 12px' }}>
              Memory Usage
            </h2>
            {memoryInfo ? (
              <>
                <div style={{ fontSize: 36, fontWeight: 700, color: memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit > 0.8 ? colors.danger : colors.success }}>
                  {Math.round(memoryInfo.usedJSHeapSize / 1024 / 1024)}
                  <span style={{ fontSize: 14, fontWeight: 400 }}>MB</span>
                </div>
                <div style={{ color: colors.textMuted, fontSize: 12 }}>
                  of {Math.round(memoryInfo.jsHeapSizeLimit / 1024 / 1024)}MB limit
                </div>
                <div style={{ marginTop: 8, height: 6, borderRadius: 3, background: colors.bgElevated, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${(memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit) * 100}%`,
                    background: memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit > 0.8 ? colors.danger : colors.success,
                    borderRadius: 3,
                  }} />
                </div>
              </>
            ) : (
              <div style={{ color: colors.textMuted, fontSize: 13 }}>
                Memory API not available in this browser
              </div>
            )}
          </div>
        </div>

        {/* Performance Tips */}
        {tips.length > 0 && (
          <div style={{
            background: colors.warningBg,
            borderRadius: 14,
            border: `1px solid ${colors.warningBorder}`,
            padding: 20,
          }}>
            <h2 style={{ color: colors.warning, fontSize: 16, fontWeight: 600, margin: '0 0 12px' }}>
              Optimization Suggestions
            </h2>
            {tips.map((tip, i) => (
              <div key={i} style={{
                padding: '8px 0',
                color: colors.textSecondary,
                fontSize: 13,
                borderBottom: i < tips.length - 1 ? `1px solid ${colors.border}` : 'none',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 8,
              }}>
                <span style={{ color: colors.warning }}>{'\u26A0'}</span>
                {tip.msg}
              </div>
            ))}
          </div>
        )}

        {tips.length === 0 && (
          <div style={{
            background: colors.successBg,
            borderRadius: 14,
            border: `1px solid ${colors.successBorder}`,
            padding: 20,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 28, marginBottom: 8, color: colors.success }}>{'\u2713'}</div>
            <div style={{ color: colors.success, fontWeight: 600 }}>Performance looks great!</div>
            <div style={{ color: colors.textMuted, fontSize: 12, marginTop: 4 }}>All metrics are within acceptable thresholds.</div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
