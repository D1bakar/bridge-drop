/* Bridge service worker — app shell cache, LAN-first.
 * API (/v1/*) is always network-only: transfers must never serve stale bytes.
 * Bump CACHE when the shell changes.
 */
const CACHE = 'bridge-v17';
const SHELL = [
  '/',
  '/send.html',
  '/history.html',
  '/pair.html',
  '/settings.html',
  '/manifest.webmanifest',
  '/css/tokens.css',
  '/css/home.css',
  '/css/pages.css',
  '/css/apple.css',
  '/js/api.js',
  '/js/mock.js',
  '/js/dropzone.js',
  '/js/upload.js',
  '/js/batch.js',
  '/js/feed.js',
  '/js/pair-page.js',
  '/js/settings-page.js',
  '/js/pwa.js',
  '/js/tabbar.js',
  '/js/clarity.js',
  '/icons/bridge-192.png',
  '/icons/bridge-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // API + uploads/downloads: never cache.
  if (url.pathname.startsWith('/v1/')) return;
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: false }).then((hit) => {
      const net = fetch(e.request).then((res) => {
        if (res.ok && url.origin === self.location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      }).catch(() => hit);
      return hit || net;
    }),
  );
});
