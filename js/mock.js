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
  renderDevices();
  renderRecent();
  refreshRecentFromServer();
});

function apiBase() {
  if (window.BridgeUpload && window.BridgeUpload.API_BASE) return window.BridgeUpload.API_BASE;
  return `http://${window.location.hostname || 'localhost'}:8000`;
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

function setNetStatus(live) {
  // Design §6 status without color: words + border weight carry the meaning.
  const pill = document.getElementById('net-status');
  if (!pill) return;
  pill.textContent = live ? 'Live' : 'Mock';
  if (live) {
    pill.classList.remove('pill-attention');
  } else {
    pill.classList.add('pill-attention');
  }
}

async function refreshRecentFromServer() {
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 1500);
    const res = await fetch(`${apiBase()}/v1/files`, { signal: ctrl.signal });
    clearTimeout(t);
    if (!res.ok) {
      setNetStatus(false);
      return false;
    }
    const data = await res.json();
    if (!data.files) {
      setNetStatus(false);
      return false;
    }
    setNetStatus(true);
    if (data.files.length === 0) {
      renderRecentEmpty(); // server up, nothing shared yet — no fake mock
      return true;
    }
    renderRecent(
      data.files.slice(0, 5).map((f) => {
        const url = `${apiBase()}/v1/files/${encodeURIComponent(f.name)}`;
        return {
          id: f.name,
          name: f.name,
          time: fmtTime(f.mtime),
          meta: fmtSize(f.size),
          direction: 'In',
          url,
          thumb: f.kind === 'image' ? url : null,
        };
      })
    );
    return true;
  } catch {
    setNetStatus(false); // backend down → mock shown, pill says so
    return false;
  }
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

function renderRecent(items = MOCK_RECENT) {
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
    pill.className = 'pill';
    pill.textContent = r.direction;

    li.appendChild(main);
    li.appendChild(pill);
    list.appendChild(li);
  });
}
