/* Bridge tab bar glide — iOS-like liquid selection.
 * Tap: pill slides to the tapped tab, page follows after the glide (230ms).
 * No-JS phones keep the static per-link pill from CSS (no has-glide class).
 */
(function () {
  'use strict';

  function place(ind, a) {
    ind.style.left = a.offsetLeft + 'px';
    ind.style.width = a.offsetWidth + 'px';
  }

  document.addEventListener('DOMContentLoaded', function () {
    var bar = document.querySelector('.tabbar');
    if (!bar) return;
    var ind = document.createElement('span');
    ind.className = 'tab-indicator';
    ind.setAttribute('aria-hidden', 'true');
    bar.appendChild(ind);
    bar.classList.add('has-glide');
    var cur = bar.querySelector('a[aria-current="page"]');
    // First paint: park under active tab with no slide (else it glides in from Home/left:0).
    ind.style.transition = 'none';
    if (cur) place(ind, cur);
    void ind.offsetWidth;
    requestAnimationFrame(function () { ind.style.transition = ''; });
    function repin() {
      var c = bar.querySelector('a[aria-current="page"]');
      if (c) place(ind, c);
    }
    window.addEventListener('resize', repin);
    window.addEventListener('load', repin);
    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(repin); }
    // Scroll edge: densify separation once content slides beneath the bar.
    function onScroll() {
      bar.classList.toggle('is-scrolled', window.scrollY > 8);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    bar.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a') : null;
      if (!a || a.getAttribute('aria-current') === 'page') return;
      // Let new-tab / new-window gestures use the browser default.
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || (e.button !== undefined && e.button !== 0)) return;
      var href = a.getAttribute('href');
      // Reduced-motion users: no glide delay, navigate instantly (design.md S7).
      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      e.preventDefault();
      place(ind, a);
      setTimeout(function () { window.location.href = href; }, 230);
    });
  });
})();
