'use client';

import { useRef, useState, useEffect, ReactNode } from 'react';

interface LazyLoadProps {
  children: ReactNode;
  placeholder?: ReactNode;
  rootMargin?: string;
  threshold?: number;
}

/**
 * Lazy-loads children when they enter the viewport via IntersectionObserver.
 */
export default function LazyLoad({
  children,
  placeholder,
  rootMargin = '200px',
  threshold = 0,
}: LazyLoadProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin, threshold }
    );
    observer.observe(el);

    return () => observer.disconnect();
  }, [rootMargin, threshold]);

  return (
    <div ref={ref}>
      {visible ? children : (placeholder || <div style={{ minHeight: 100 }} />)}
    </div>
  );
}
