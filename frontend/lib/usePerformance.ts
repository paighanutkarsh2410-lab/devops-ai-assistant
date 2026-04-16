'use client';

import { useEffect, useRef, useCallback, useState } from 'react';

interface PerformanceMetrics {
  fcp: number | null;       // First Contentful Paint
  lcp: number | null;       // Largest Contentful Paint
  fid: number | null;       // First Input Delay
  cls: number | null;       // Cumulative Layout Shift
  ttfb: number | null;      // Time to First Byte
  domReady: number | null;  // DOM interactive time
  pageLoad: number | null;  // Full page load time
}

/**
 * Hook that collects Core Web Vitals and page performance metrics.
 */
export function usePerformance(): PerformanceMetrics {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fcp: null, lcp: null, fid: null, cls: null, ttfb: null, domReady: null, pageLoad: null,
  });

  useEffect(() => {
    if (typeof window === 'undefined' || !window.performance) return;

    // Navigation timing
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
    if (nav) {
      setMetrics((m) => ({
        ...m,
        ttfb: Math.round(nav.responseStart - nav.requestStart),
        domReady: Math.round(nav.domInteractive - nav.startTime),
        pageLoad: Math.round(nav.loadEventEnd - nav.startTime) || null,
      }));
    }

    // FCP
    const fcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      if (entries.length > 0) {
        setMetrics((m) => ({ ...m, fcp: Math.round(entries[0].startTime) }));
      }
    });
    try { fcpObserver.observe({ type: 'paint', buffered: true }); } catch {}

    // LCP
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      if (entries.length > 0) {
        setMetrics((m) => ({ ...m, lcp: Math.round(entries[entries.length - 1].startTime) }));
      }
    });
    try { lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true }); } catch {}

    // FID
    const fidObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries() as PerformanceEventTiming[];
      if (entries.length > 0) {
        setMetrics((m) => ({ ...m, fid: Math.round(entries[0].processingStart - entries[0].startTime) }));
      }
    });
    try { fidObserver.observe({ type: 'first-input', buffered: true }); } catch {}

    // CLS
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries() as (PerformanceEntry & { hadRecentInput?: boolean; value?: number })[]) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value || 0;
          setMetrics((m) => ({ ...m, cls: Math.round(clsValue * 1000) / 1000 }));
        }
      }
    });
    try { clsObserver.observe({ type: 'layout-shift', buffered: true }); } catch {}

    return () => {
      fcpObserver.disconnect();
      lcpObserver.disconnect();
      fidObserver.disconnect();
      clsObserver.disconnect();
    };
  }, []);

  return metrics;
}

/**
 * Debounce hook
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

/**
 * Throttle callback
 */
export function useThrottle<T extends (...args: unknown[]) => unknown>(fn: T, delay: number): T {
  const lastRun = useRef(0);
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  return useCallback(
    ((...args: unknown[]) => {
      const now = Date.now();
      if (now - lastRun.current >= delay) {
        lastRun.current = now;
        fn(...args);
      } else if (!timeoutRef.current) {
        timeoutRef.current = setTimeout(() => {
          lastRun.current = Date.now();
          timeoutRef.current = undefined;
          fn(...args);
        }, delay - (now - lastRun.current));
      }
    }) as T,
    [fn, delay]
  );
}
