/* Home data — mock first, server when reachable.
 * BACKEND CONTRACT (prd.md §9):
 *   GET /v1/info — device info + capabilities
 *   GET /v1/files — uploaded files (M0 recent source)
 *   POST /v1/files — upload (see js/upload.js)
 * Shape mirrors PRD §9 Device {id, name, platform, fingerprint, trusted}.
 */

const MOCK_DEVICES = [
  { id: 'pc-1', name: 'My PC', platform: 'Windows', status: 'PAIRED', trusted: true },
  { id: 'ph-1', name: 'My Phone', platform: 'Android', status: 'LAN', trusted: true },
];

const MOCK_RECENT = [
  { id: 'r-1', name: 'IMG_2041.jpg', time: 'Today 12:40', meta: '24.2 MB', direction: 'In' },
  { id: 'r-2', name: 'notes.txt', time: 'Today 09:12', meta: '2 KB', direction: 'Out' },
];

function renderDevices(devices = MOCK_DEVICES) {
  const list = document.getElementById('devices-list');
  if (!list) return;
  list.textContent = '';
  devices.forEach((d, i) => {
    const li = document.createElement('li');
    li.className = i === 0 ? 'device is-selected' : 'device';

    const main = document.createElement('div');
    main.className = 'device-main';

    const meta = document.createElement('span');
    meta.className = 'device-meta';
    meta.textContent = `${d.platform} · LAN`;

    const name = document.createElement('span');
    name.className = 'device-name';
    name.textContent = d.name;
    if (i === 0) {
      const arrow = document.createElement('span');
      arrow.setAttribute('aria-hidden', 'true');
      arrow.textContent = ' →';
      name.appendChild(arrow);
    }

    main.appendChild(meta);
    main.appendChild(name);

    const pill = document.createElement('span');
    pill.className = 'pill';
    pill.textContent = d.trusted ? 'Paired' : d.status;

    li.appendChild(main);
    li.appendChild(pill);
    list.appendChild(li);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  if (window.BridgeApi && window.BridgeApi.handoffCode()) return; // guest → pair page
  renderDevices();
  renderRecent();
  refreshDevicesFromServer();
  refreshRecentFromServer();
});

async function refreshDevicesFromServer() {
  // Real paired names when the backend is up; mock row otherwise.
  try {
    if (!window.BridgeApi) return;
    const out = await window.BridgeApi.json('/v1/devices');
    const info = await window.BridgeApi.json('/v1/info').catch(() => null);
    const devs = [{ name: (info && info.data.name) || 'My PC', platform: 'Windows', trusted: true }];
    (out.data.devices || []).forEach((d) => {
      devs.push({ name: d.name, platform: d.platform || 'Device', trusted: true });
    });
    renderDevices(devs);
  } catch (_) {
    /* mock stays */
  }
}

function apiCandidates() {
  // Single-terminal mode: page served from :8000 → same origin, no guessing.
  // Live Server mode (:5500 / file://): backend is :8000 on same host.
  // localhost → ::1 often misses a 127.0.0.1-only uvicorn, so try IPv4 first.
  try {
    const port = window.location.port;
    if (port === "8000" && window.location.origin && window.location.origin.startsWith("http")) {
      const origin = window.location.origin.replace(/\/$/, "");
      return [origin, "http://127.0.0.1:8000", "http://localhost:8000"].filter(
        (v, i, a) => a.indexOf(v) === i
      );
    }
    // Hosted origin (https / default port, e.g. Vercel): same origin serves /v1/*.
    if ((window.location.protocol || "").indexOf("https") === 0 || !port) {
      const hosted = window.location.origin.replace(/\/$/, "");
      return [hosted, "http://127.0.0.1:8000", "http://localhost:8000"].filter(
        (v, i, a) => a.indexOf(v) === i
      );
    }
  } catch (_) {}
  const raw = (window.location.hostname || "localhost").toLowerCase();
  const host = raw === "localhost" ? "127.0.0.1" : raw;
  const list = [`http://${host}:8000`];
  if (!list.includes("http://127.0.0.1:8000")) list.push("http://127.0.0.1:8000");
  if (!list.includes("http://localhost:8000")) list.push("http://localhost:8000");
  return list;
}

function apiBase() {
  if (window.BridgeUpload && window.BridgeUpload.API_BASE) return window.BridgeUpload.API_BASE;
  return apiCandidates()[0];
}

function fmtSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round((bytes / 1024) * 10) / 10} KB`;
  return `${Math.round((bytes / (1024 * 1024)) * 10) / 10} MB`;
}

function fmtTime(mtime) {
  try {
    const d = new Date(mtime * 1000);
    return `Today ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  } catch {
    return 'Today';
  }
}

function setNetStatus(live, reason) {
  // Design §6 status without color: words + border weight carry the meaning.
  const pill = document.getElementById('net-status');
  if (!pill) return;
  pill.textContent = live ? 'Live' : 'Mock';
  if (live) {
    pill.classList.remove('pill-attention');
    pill.removeAttribute('title');
  } else {
    pill.classList.add('pill-attention');
    if (reason) pill.title = reason;
  }
}

async function fetchJsonFrom(base, path, timeoutMs) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const headers = {};
    try {
      const tok = localStorage.getItem('bridge-device');
      if (tok) headers['X-Device-Token'] = tok;
    } catch (_) {}
    const res = await fetch(`${base}${path}`, { signal: ctrl.signal, headers });
    if (!res.ok) return { ok: false, reason: `HTTP ${res.status} from ${base}` };
    return { ok: true, base, data: await res.json() };
  } catch (e) {
    const why = e && e.name === 'AbortError' ? `timeout ${timeoutMs}ms to ${base}` : `unreachable ${base}`;
    return { ok: false, reason: why };
  } finally {
    clearTimeout(t);
  }
}

function actionLink(label) {
  const a = document.createElement('a');
  a.className = 'action-secondary';
  a.href = '#';
  a.innerHTML = `${label} <span aria-hidden="true">→</span>`;
  return a;
}

async function apiDelete(path, base) {
  const headers = {};
  try {
    const tok = localStorage.getItem('bridge-device');
    if (tok) headers['X-Device-Token'] = tok;
  } catch (_) {}
  const res = await fetch(`${base}${path}`, { method: 'DELETE', headers });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}

function toast(text, opts) {
  if (window.BridgeApi) window.BridgeApi.toast(text, opts);
}

async function refreshRecentFromServer() {
  const reasons = [];
  for (const base of apiCandidates()) {
    // Preferred: persistent feed (ids → full delete of row + file, pending states).
    const feed = await fetchJsonFrom(base, '/v1/feed?kind=file&limit=5', 2500);
    if (feed.ok && feed.data.items) {
      setNetStatus(true);
      if (!feed.data.items.length) {
        renderRecentEmpty(); // server up, nothing shared yet — no fake mock
        return true;
      }
      // Home shows the latest 3 only — full feed lives on history.html.
      renderRecent(feed.data.items.slice(0, 3).map((f) => {
        const rel = f.saved_path || f.name;
        const url = `${base}/v1/files/${rel.split('/').map(encodeURIComponent).join('/')}`;
        const mime = (f.mime || '').toLowerCase();
        return {
          name: f.name,
          time: fmtTime(f.created_at),
          meta: fmtSize(f.size || 0),
          direction: f.direction === 'out' ? 'Out' : 'In',
          url,
          thumb: mime.indexOf('image/') === 0 ? url : null,
          pending: f.status === 'pending',
          onDelete: async () => {
            await apiDelete(`/v1/feed/file/${encodeURIComponent(f.id)}?delete_file=1`, base);
          },
          acceptId: f.status === 'pending' ? f.id : null,
          declineId: f.status === 'pending' ? f.id : null,
        };
      }), base);
      return true;
    }
    // Fallback: plain file list (older server or feed hiccup).
    const r = await fetchJsonFrom(base, '/v1/files', 2500);
    if (!r.ok || !r.data.files) {
      reasons.push((feed.ok ? r.reason : feed.reason) || 'backend off');
      continue;
    }
    setNetStatus(true);
    if (!r.data.files.length) {
      renderRecentEmpty();
      return true;
    }
    renderRecent(
      r.data.files.slice(0, 5).map((f) => {
        const rel = f.path || f.name;
        const url = `${base}/v1/files/${rel.split('/').map(encodeURIComponent).join('/')}`;
        return {
          name: f.name,
          time: fmtTime(f.mtime),
          meta: fmtSize(f.size),
          direction: 'In',
          url,
          thumb: f.kind === 'image' ? url : null,
          onDelete: async () => {
            await apiDelete(`/v1/files/${rel.split('/').map(encodeURIComponent).join('/')}`, base);
          },
        };
      }), base);
    return true;
  }
  const reason = reasons.join(' · ') || 'backend off';
  setNetStatus(false, reason); // backend down → mock shown, pill says so
  if (window.console && console.warn) console.warn('[bridge] recent fallback to mock:', reason);
  return false;
}

window.BridgeRecent = { refresh: refreshRecentFromServer };

function renderRecentEmpty() {
  // Design §6 empty state: heading text, one → link. No illustration.
  const list = document.getElementById('recent-list');
  if (!list) return;
  list.textContent = '';
  const li = document.createElement('li');
  li.className = 'recent-empty';
  const title = document.createElement('span');
  title.className = 'recent-empty-title';
  title.textContent = 'Nothing here yet.';
  const link = document.createElement('a');
  link.className = 'action-secondary';
  link.href = '#dropzone';
  link.textContent = 'Share a file ';
  const arrow = document.createElement('span');
  arrow.setAttribute('aria-hidden', 'true');
  arrow.textContent = '→';
  link.appendChild(arrow);
  li.appendChild(title);
  li.appendChild(link);
  list.appendChild(li);
}

function renderRecent(items = MOCK_RECENT, base = '') {
  const list = document.getElementById('recent-list');
  if (!list) return;
  list.textContent = '';
  items.forEach((r) => {
    const li = document.createElement('li');
    li.className = 'recent-row';

    // Design §6: 48px square thumbnail, original color — images only, never icons.
    if (r.thumb) {
      const thumb = document.createElement('img');
      thumb.className = 'recent-thumb';
      thumb.src = r.thumb;
      thumb.alt = '';
      thumb.loading = 'lazy';
      li.appendChild(thumb);
    }

    const main = document.createElement('div');
    main.className = 'recent-main';

    const nameEl = r.url ? document.createElement('a') : document.createElement('span');
    nameEl.className = 'recent-name';
    nameEl.textContent = r.name;
    if (r.url) {
      nameEl.href = r.url;
      nameEl.target = '_blank';
      nameEl.rel = 'noopener';
    }

    // One calm meta line instead of two stacked captions.
    const meta = document.createElement('span');
    meta.className = 'recent-meta';
    meta.textContent = `${r.time} · ${r.meta}`;

    main.appendChild(nameEl);
    main.appendChild(meta);

    const pill = document.createElement('span');
    pill.className = 'pill' + (r.pending ? ' pill-attention' : '');
    pill.textContent = r.pending ? 'Waiting' : r.direction;

    li.appendChild(main);
    li.appendChild(pill);

    // Every row you shared or received can go: history row + file, together.
    if (r.acceptId && base) {
      const acc = actionLink('Accept');
      acc.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
          await apiPost(`/v1/feed/accept/${encodeURIComponent(r.acceptId)}`, base);
          toast('Received →');
          refreshRecentFromServer();
        } catch (_) {
          toast('Accept failed — try again.', { sticky: true });
        }
      });
      const dec = actionLink('Decline');
      dec.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
          await apiPost(`/v1/feed/decline/${encodeURIComponent(r.declineId)}`, base);
          toast('Declined →');
          refreshRecentFromServer();
        } catch (_) {
          toast('Decline failed — try again.', { sticky: true });
        }
      });
      li.appendChild(acc);
      li.appendChild(dec);
    } else if (r.onDelete && base) {
      const del = actionLink('Delete');
      del.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
          await r.onDelete();
          toast('Deleted →');
          refreshRecentFromServer();
        } catch (_) {
          toast('Delete failed — try again.', { sticky: true });
        }
      });
      li.appendChild(del);
    }
    list.appendChild(li);
  });
}

async function apiPost(path, base) {
  const headers = {};
  try {
    const tok = localStorage.getItem('bridge-device');
    if (tok) headers['X-Device-Token'] = tok;
  } catch (_) {}
  const res = await fetch(`${base}${path}`, { method: 'POST', headers });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
}
