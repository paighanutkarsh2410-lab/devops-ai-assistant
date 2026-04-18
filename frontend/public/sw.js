const CACHE_NAME = 'devops-ai-v2';
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

// Activate — clean old caches immediately
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch — always network first for HTML/navigation, cache static assets only
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.hostname !== self.location.hostname) return;

  // Never cache API calls
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/_next/data')) return;

  // For navigation requests (HTML pages) — always go to network, no cache
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/'))
    );
    return;
  }

  // For static assets (_next/static, images, etc.) — cache with network first
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok && url.pathname.startsWith('/_next/static')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
