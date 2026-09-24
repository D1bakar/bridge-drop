/* Frontend-only mock. Backend untouched per rule.
 * BACKEND CONTRACT (prd.md §9, do not call yet):
 *   GET /v1/info — device info + capabilities
 *   POST /v1/session — sender offers files
 * Frontend uses MOCK_DEVICES until backend pairing exists.
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
});

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
