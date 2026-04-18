'use client';

import { useEffect } from 'react';

export default function ServiceWorkerRegister() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').then((reg) => {
        // Check for updates immediately and every 60 seconds
        reg.update();
        setInterval(() => reg.update(), 60000);
      }).catch(() => {
        // Service worker registration failed — not critical
      });
    }
  }, []);

  return null;
}
