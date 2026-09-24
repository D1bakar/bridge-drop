/* Dropzone visual state only — no upload yet.
 * Adds .is-dragover on dragenter/dragover, removes on dragleave/drop.
 * Design: design.md §6 (2px Ink + heading-sm via CSS). No backend calls.
 */

function initDropzone() {
  const zone = document.getElementById('dropzone');
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
  });
  document.addEventListener('dragend', () => {
    depth = 0;
    zone.classList.remove('is-dragover');
  });
}

document.addEventListener('DOMContentLoaded', initDropzone);
