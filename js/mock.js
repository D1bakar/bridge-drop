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

async function refreshRecentFromServer() {
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 1500);
    const res = await fetch(`${apiBase()}/v1/files`, { signal: ctrl.signal });
    clearTimeout(t);
    if (!res.ok) return false;
    const data = await res.json();
    if (!data.files || data.files.length === 0) return false;
    renderRecent(
      data.files.slice(0, 5).map((f) => ({
        id: f.name,
        name: f.name,
        time: fmtTime(f.mtime),
        meta: fmtSize(f.size),
        direction: 'In',
      }))
    );
    return true;
  } catch {
    return false; // backend down → keep mock, main stays usable
  }
}

window.BridgeRecent = { refresh: refreshRecentFromServer };

function renderRecent(items = MOCK_RECENT) {
  const list = document.getElementById('recent-list');
  if (!list) return;
  list.textContent = '';
  items.forEach((r) => {
    const li = document.createElement('li');
    li.className = 'recent-row';

    const main = document.createElement('div');
    main.className = 'recent-main';

    const time = document.createElement('span');
    time.className = 'recent-time';
    time.textContent = r.time;

    const name = document.createElement('span');
    name.className = 'recent-name';
    name.textContent = r.name;

    const meta = document.createElement('span');
    meta.className = 'recent-meta';
    meta.textContent = r.meta;

    main.appendChild(time);
    main.appendChild(name);
    main.appendChild(meta);

    const pill = document.createElement('span');
    pill.className = 'pill';
    pill.textContent = r.direction;

    li.appendChild(main);
    li.appendChild(pill);
    list.appendChild(li);
  });
}
