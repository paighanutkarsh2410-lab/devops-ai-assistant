'use client';

import { useState, useRef, useCallback, useEffect, ReactNode } from 'react';

interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  renderItem: (item: T, index: number) => ReactNode;
  height?: number;
  overscan?: number;
  onEndReached?: () => void;
  endReachedThreshold?: number;
}

export default function VirtualList<T>({
  items,
  itemHeight,
  renderItem,
  height = 500,
  overscan = 5,
  onEndReached,
  endReachedThreshold = 200,
}: VirtualListProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const endReachedRef = useRef(false);

  const totalHeight = items.length * itemHeight;
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(items.length - 1, Math.ceil((scrollTop + height) / itemHeight) + overscan);
  const visibleItems = items.slice(startIndex, endIndex + 1);

  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    setScrollTop(container.scrollTop);

    if (onEndReached && !endReachedRef.current) {
      const distanceToEnd = totalHeight - container.scrollTop - height;
      if (distanceToEnd < endReachedThreshold) {
        endReachedRef.current = true;
        onEndReached();
        // Reset after a short delay to allow re-triggering
        setTimeout(() => { endReachedRef.current = false; }, 1000);
      }
    }
  }, [totalHeight, height, onEndReached, endReachedThreshold]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  return (
    <div
      ref={containerRef}
      style={{
        height,
        overflow: 'auto',
        position: 'relative',
      }}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ position: 'absolute', top: startIndex * itemHeight, left: 0, right: 0 }}>
          {visibleItems.map((item, i) => (
            <div key={startIndex + i} style={{ height: itemHeight }}>
              {renderItem(item, startIndex + i)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
