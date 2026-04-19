'use client';

import { ReactNode } from 'react';
import { useBreakpoint } from '@/lib/useMediaQuery';
import { useA11y } from '@/lib/useA11y';
import MobileNav from './MobileNav';
import CommandPalette from './ui/CommandPalette';
import { SkipLink } from './a11y';

interface ResponsiveLayoutProps {
  children: ReactNode;
}

export default function ResponsiveLayout({ children }: ResponsiveLayoutProps) {
  const { isMobile } = useBreakpoint();
  useA11y(); // Initialize keyboard nav detection and reduced motion

  return (
    <>
      <SkipLink />
      <CommandPalette />
      {isMobile && <MobileNav />}
      <main
        id="main-content"
        role="main"
        style={{
          paddingTop: isMobile ? 52 : 0,
          paddingBottom: 0,
          minHeight: '100vh',
        }}
      >
        {children}
      </main>
    </>
  );
}
