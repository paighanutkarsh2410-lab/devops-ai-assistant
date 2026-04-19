'use client';

import { useEffect } from 'react';

export default function ServiceWorkerRegister() {
  useEffect(() => {
    if (!('serviceWorker' in navigator)) return;

    navigator.serviceWorker
      .register('/sw.js', { updateViaCache: 'none' })
      .then((reg) => {
        // Check for updates immediately
        reg.update();

        // Poll for updates every 60 seconds
        const interval = setInterval(() => reg.update(), 60000);

        // When a new SW is found and installed, activate it and reload
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          if (!newWorker) return;

          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'activated' && navigator.serviceWorker.controller) {
              // New SW activated — reload to get fresh content
              window.location.reload();
            }
          });
        });

        return () => clearInterval(interval);
      })
      .catch(() => {
        // Service worker registration failed — not critical
      });

    // Also reload if controller changes (another tab triggered update)
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;
      refreshing = true;
      window.location.reload();
    });
  }, []);

  return null;
}
