{% load static %}const CACHE = 'training-tracker-v2';
const OFFLINE_URL = '{% url "plan_app:offline" %}';
const ASSETS = [
  OFFLINE_URL,
  '{% static "plan_app/style.css" %}',
  '{% static "plan_app/app.js" %}',
  '{% static "plan_app/theme.js" %}',
  '{% static "plan_app/icons/icon-192.png" %}',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE_URL)));
    return;
  }

  if (ASSETS.includes(url.pathname)) {
    event.respondWith(
      fetch(request, { cache: 'no-cache' })
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE).then(async (cache) => {
              await cache.delete(request, { ignoreSearch: true });
              await cache.put(request, copy);
            });
          }
          return response;
        })
        .catch(() => caches.match(request, { ignoreSearch: true }))
    );
  }
});
