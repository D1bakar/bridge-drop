/* Dropzone visual state only — no upload yet.
 * Adds .is-dragover on dragenter/dragover, removes on dragleave/drop.
 * Design: design.md §6 (2px Ink + heading-sm via CSS). No backend calls.
 */

function initDropzone() {
  const zone = document.getElementById('dropzone');
  if (!zone) return;
  const on = (e) => {
    e.preventDefault();
    zone.classList.add('is-dragover');
  };
  const off = (e) => {
    e.preventDefault();
    zone.classList.remove('is-dragover');
  };
  zone.addEventListener('dragenter', on);
  zone.addEventListener('dragover', on);
  zone.addEventListener('dragleave', off);
  zone.addEventListener('drop', off);
}

document.addEventListener('DOMContentLoaded', initDropzone);
