// CalorieAI service worker (PWA offline support)
const CACHE = "calorieai-v1";
const PRECACHE = ["/", "/index.html"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // Pass through API calls and do not cache them.
  if (event.request.url.includes("/api/")) return;

  event.respondWith(
    caches.match(event.request).then(
      (cached) => cached || fetch(event.request).catch(() => caches.match("/index.html"))
    )
  );
});
