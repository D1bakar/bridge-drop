/* Bridge clarity — iOS 27 ultra-clear ↔ frosted glass slider.
 * Stored per device (localStorage), applied on every page before paint matters.
 * 0 = ultra-clear (alpha .16, blur 12px), 100 = frosted (alpha .92, blur 28px).
 * Note: true pixel refraction isn't possible in CSS — liquid feel comes from
 * low alpha + blur/saturate + specular edge light (css/apple.css).
 */
(function () {
  'use strict';

  var KEY = 'bridge-clarity';
  var DEFAULT = 8;

  function read() {
    try {
      var v = parseInt(localStorage.getItem(KEY), 10);
      if (!isNaN(v)) return Math.max(0, Math.min(100, v));
    } catch (_) {}
    return DEFAULT;
  }

  function apply(v) {
    var alpha = (0.16 + (v / 100) * 0.76).toFixed(2);
    var blur = Math.round(12 + (v / 100) * 16) + 'px';
    var root = document.documentElement;
    root.style.setProperty('--glass-alpha', alpha);
    root.style.setProperty('--glass-blur', blur);
    try {
      localStorage.setItem(KEY, String(v));
    } catch (_) {}
    var label = document.getElementById('clarity-value');
    if (label) label.textContent = v <= 25 ? 'Ultra-clear' : (v <= 65 ? 'Balanced' : 'Frosted');
  }

  function init() {
    apply(read());
    var slider = document.getElementById('clarity');
    if (slider) {
      slider.value = read();
      slider.addEventListener('input', function () { apply(parseInt(slider.value, 10)); });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
  window.BridgeClarity = { read: read, apply: apply };
})();
