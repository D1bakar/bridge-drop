/* Frontend-only mock. Backend untouched per rule.
 * BACKEND CONTRACT (prd.md §9, do not call yet):
 *   GET /v1/info — device info + capabilities
 *   POST /v1/session — sender offers files
 * Frontend uses MOCK_DEVICES until backend pairing exists.
 */

const MOCK_DEVICES = [];
