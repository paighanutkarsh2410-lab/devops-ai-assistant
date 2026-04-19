const CACHE_NAME = 'devops-ai-v3';
const STATIC_ASSETS = [
  '/manifest.json',
  '/icon-192.svg',
];

// Install — cache only truly static assets (not HTML pages)
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate — clean ALL old caches immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Message handler — force reload all clients when requested
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Fetch — network first for everything, cache only immutable static assets
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.hostname !== self.location.hostname) return;

  // Never cache API calls or Next.js data routes
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/_next/data')) return;

  // For navigation requests (HTML pages) — ALWAYS network, bypass HTTP cache
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request, { cache: 'no-cache' }).catch(() => caches.match('/') || new Response('Offline', { status: 503 }))
    );
    return;
  }

  // For hashed static assets (_next/static) — cache-first (they're immutable by hash)
  if (url.pathname.startsWith('/_next/static')) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // Everything else — network first, no caching
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
