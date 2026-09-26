/* Dropzone visual state + page drag mode — no upload yet.
 * Zone .is-dragover as before; any drag over the window raises
 * body.is-dragging so nav + siblings recede and the field expands.
 * Design: transfer canvas. No backend calls.
 */

function initDropzone() {
  const zone = document.getElementById('dropzone');
  // Page-level drag depth: entering child nodes must not flicker the mode.
  let pageDepth = 0;
  function setPageDragging(on) {
    document.body.classList.toggle('is-dragging', on);
  }
  window.addEventListener('dragenter', (e) => {
    if (!zone) return;
    e.preventDefault();
    pageDepth += 1;
    setPageDragging(true);
  });
  window.addEventListener('dragleave', (e) => {
    if (!zone) return;
    e.preventDefault();
    pageDepth = Math.max(0, pageDepth - 1);
    if (pageDepth === 0) setPageDragging(false);
  });
  window.addEventListener('drop', () => {
    pageDepth = 0;
    setPageDragging(false);
  });
  if (!zone) return;
  let depth = 0;
  zone.addEventListener('dragenter', (e) => {
    e.preventDefault();
    depth += 1;
    zone.classList.add('is-dragover');
  });
  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
  });
  zone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    depth = Math.max(0, depth - 1);
    if (depth === 0) zone.classList.remove('is-dragover');
  });
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    depth = 0;
    zone.classList.remove('is-dragover');
    pageDepth = 0;
    setPageDragging(false);
  });
  document.addEventListener('dragend', () => {
    depth = 0;
    zone.classList.remove('is-dragover');
    pageDepth = 0;
    setPageDragging(false);
  });
  // Keyboard: Enter/Space on the picker label opens the file dialog.
  zone.querySelectorAll('label.action-secondary[for]').forEach((lab) => {
    lab.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        const input = document.getElementById(lab.getAttribute('for'));
        if (input) input.click();
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', initDropzone);
