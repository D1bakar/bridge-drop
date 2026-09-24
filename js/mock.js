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
