'use client';

import { useEffect, useCallback, useState } from 'react';

/**
 * Accessibility utilities hook
 * - Detects keyboard vs mouse navigation
 * - Manages focus indicators
 * - Provides ARIA live region announcements
 * - Reduced motion detection
 */
export function useA11y() {
  const [isKeyboardNav, setIsKeyboardNav] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  // Detect keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        setIsKeyboardNav(true);
        document.documentElement.setAttribute('data-keyboard-nav', 'true');
      }
    };
    const handleMouseDown = () => {
      setIsKeyboardNav(false);
      document.documentElement.removeAttribute('data-keyboard-nav');
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('mousedown', handleMouseDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  // Detect reduced motion preference
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  // ARIA live announcements
  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    let region = document.getElementById(`a11y-live-${priority}`);
    if (!region) {
      region = document.createElement('div');
      region.id = `a11y-live-${priority}`;
      region.setAttribute('role', 'status');
      region.setAttribute('aria-live', priority);
      region.setAttribute('aria-atomic', 'true');
      Object.assign(region.style, {
        position: 'absolute',
        width: '1px',
        height: '1px',
        overflow: 'hidden',
        clip: 'rect(0,0,0,0)',
        whiteSpace: 'nowrap',
        border: '0',
      });
      document.body.appendChild(region);
    }
    // Clear and re-set to trigger announcement
    region.textContent = '';
    requestAnimationFrame(() => { region!.textContent = message; });
  }, []);

  return {
    isKeyboardNav,
    prefersReducedMotion,
    announce,
  };
}
