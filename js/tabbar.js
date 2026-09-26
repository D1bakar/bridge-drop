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
    window.addEventListener('resize', function () {
      var c = bar.querySelector('a[aria-current="page"]');
      if (c) place(ind, c);
    });
    bar.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a') : null;
      if (!a || a.getAttribute('aria-current') === 'page') return;
      e.preventDefault();
      place(ind, a);
      var href = a.getAttribute('href');
      setTimeout(function () { window.location.href = href; }, 230);
    });
  });
})();
