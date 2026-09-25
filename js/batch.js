/* Bridge batch sender — multi-file + folders over the chunked protocol.
 * PRD FR-8/FR-9/FR-17/FR-18/FR-21: 1MB chunks (bounded RAM, multi-GB safe),
 * per-file progress + speed + ETA + cancel, 2 parallel uploads, resume on
 * retry (server reports confirmed offset). Integrity: server SHA-256 on
 * complete (FR-20); TCP already guards transit, so no whole-file client hash.
 */

(function () {
  'use strict';

  var CHUNK = 1024 * 1024;
  var PARALLEL = 2;

  var queue = [];
  var active = 0;
  var batchTotal = 0;
  var batchDone = 0;

  function el(id) { return document.getElementById(id); }

  function fmtSpeed(bps) {
    if (!bps || bps <= 0) return '—';
    return window.BridgeApi.fmtSize(Math.round(bps)) + '/s';
  }

  function fmtEta(sec) {
    if (!isFinite(sec) || sec < 0) return '—';
    if (sec < 60) return Math.ceil(sec) + 's left';
    return Math.floor(sec / 60) + 'm ' + Math.ceil(sec % 60) + 's left';
  }

  function batchRender() {
    var pct = el('batch-pct');
    var fill = el('batch-fill');
    if (!batchTotal) {
      if (pct) pct.textContent = '';
      if (fill) fill.style.width = '0%';
      return;
    }
    var p = Math.min(100, Math.round((batchDone / batchTotal) * 100));
    if (pct) pct.textContent = p + '%';
    if (fill) fill.style.width = p + '%';
  }

  function addRow(file) {
    var list = el('batch-list');
    var li = document.createElement('li');
    li.className = 'batch-row';
    var name = document.createElement('span');
    name.className = 'recent-name';
    name.textContent = (file.webkitRelativePath || file.name);
    var meta = document.createElement('span');
    meta.className = 'recent-meta';
    meta.textContent = window.BridgeApi.fmtSize(file.size);
    var main = document.createElement('div');
    main.className = 'recent-main';
    main.appendChild(name);
    main.appendChild(meta);
    var line = document.createElement('div');
    line.className = 'batch-line';
    var fill = document.createElement('div');
    fill.className = 'batch-fill';
    line.appendChild(fill);
    var cancel = document.createElement('a');
    cancel.className = 'action-secondary';
    cancel.href = '#';
    cancel.innerHTML = 'Cancel <span aria-hidden="true">→</span>';
    li.appendChild(main);
    li.appendChild(line);
    li.appendChild(cancel);
    if (list) list.appendChild(li);
    return { file: file, li: li, meta: meta, fill: fill, cancel: cancel, cancelled: false };
  }

  function enqueue(files) {
    if (!files || !files.length) return;
    for (var i = 0; i < files.length; i++) {
      if (!files[i].size && files[i].size !== 0) continue;
      var job = addRow(files[i]);
      job.cancel.addEventListener('click', (function (j) {
        return function (e) {
          e.preventDefault();
          j.cancelled = true;
          if (j.uploadId) {
            window.BridgeApi.fetchFirst('/v1/uploads/' + j.uploadId, { method: 'DELETE' }).catch(function () {});
          }
          j.meta.textContent = 'Cancelled.';
          j.cancel.remove();
        };
      })(job));
      queue.push(job);
      batchTotal += files[i].size || 0;
    }
    batchRender();
    pump();
  }

  function pump() {
    while (active < PARALLEL && queue.length) {
      var job = queue.shift();
      if (job.cancelled) continue;
      active++;
      send(job).finally(function () {
        active--;
        pump();
      });
    }
  }

  async function send(job) {
    var file = job.file;
    var rel = file.webkitRelativePath || file.name;
    var seen = job.seen || 0;
    try {
      var init = await window.BridgeApi.json('/v1/uploads/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: file.name, relPath: rel, size: file.size, mime: file.type || '' }),
      });
      var uid = init.data.uploadId;
      job.uploadId = uid;
      var offset = init.data.offset || 0;
      seen = offset;
      var t0 = Date.now();
      while (offset < file.size) {
        if (job.cancelled) return;
        // Resume: if a chunk fails, re-ask the server where it stands.
        var end = Math.min(offset + CHUNK, file.size);
        var slice = file.slice(offset, end);
        var buf = await slice.arrayBuffer();
        var put = await window.BridgeApi.fetchFirst('/v1/uploads/' + uid + '/chunk?offset=' + offset, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/octet-stream' },
          body: buf,
        });
        if (put.res.status === 409) {
          var st = await window.BridgeApi.json('/v1/uploads/' + uid + '/status');
          offset = st.data.offset;
          continue;
        }
        if (!put.res.ok) throw new Error('chunk HTTP ' + put.res.status);
        var body = await put.res.json();
        var delta = body.offset - offset;
        offset = body.offset;
        seen = offset;
        batchDone += delta;
        var p = file.size ? Math.round((offset / file.size) * 100) : 100;
        job.fill.style.width = p + '%';
        var secs = (Date.now() - t0) / 1000;
        var bps = secs > 0.5 ? offset / secs : 0;
        job.meta.textContent = window.BridgeApi.fmtSize(offset) + ' of ' +
          window.BridgeApi.fmtSize(file.size) + ' · ' + fmtSpeed(bps) + ' · ' + fmtEta((file.size - offset) / (bps || 1));
        batchRender();
      }
      var done = await window.BridgeApi.json('/v1/uploads/' + uid + '/complete', { method: 'POST' });
      job.seen = file.size;
      if (done.data.pending) {
        job.meta.textContent = 'Waiting for accept on the other device.';
      } else {
        job.meta.textContent = 'Received →';
      }
      job.cancel.remove();
      if (window.BridgeRecent) window.BridgeRecent.refresh();
    } catch (e) {
      if (!job.cancelled) {
        job.meta.textContent = 'Failed — try again (' + (e.message || 'network') + ').';
      }
    }
  }

  function initBatch() {
    if (!el('batch-list')) return;
    var picker = el('batch-input');
    if (picker) picker.addEventListener('change', function () {
      enqueue(picker.files);
      picker.value = '';
    });
    var folder = el('folder-input');
    if (folder) folder.addEventListener('change', function () {
      enqueue(folder.files);
      folder.value = '';
    });
    var zone = el('batch-drop');
    if (zone) {
      zone.addEventListener('dragover', function (e) { e.preventDefault(); });
      zone.addEventListener('drop', function (e) {
        e.preventDefault();
        if (e.dataTransfer && e.dataTransfer.files) enqueue(e.dataTransfer.files);
      });
    }
  }

  document.addEventListener('DOMContentLoaded', initBatch);
  window.BridgeBatch = { enqueue: enqueue };
})();
