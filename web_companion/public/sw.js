// MailProcessor Companion — Pre-build SW shell
// NOTE: Once `npm run build` runs, vite-plugin-pwa generates a full SW that
//       supersedes this file. Do NOT add complex caching logic here.
const CACHE_NAME = 'mailprocessor-v1';
const OFFLINE_URL = '/offline.html';

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      cache.addAll([OFFLINE_URL, '/', '/icon-192.png', '/icon-512.png'])
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', event => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(OFFLINE_URL))
    );
  }
});
