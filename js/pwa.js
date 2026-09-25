/* Bridge PWA registration — no-op where SW is unsupported.
 * Keeps installability (manifest + SW) without changing UI.
 */
(function () {
  'use strict';
  if (!('serviceWorker' in navigator)) return;
  // Only register on http(s) — file:// has no SW scope.
  if (window.location.protocol !== 'http:' && window.location.protocol !== 'https:') return;
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/sw.js').catch(function () {});
  });
})();
