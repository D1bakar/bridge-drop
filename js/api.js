/* Bridge shared API — same-origin first (:8000), Live Server fallback.
 * Paired device token in localStorage; sent as X-Device-Token.
 * ?code= on landing hands off to pair.html for claiming.
 */

(function () {
  'use strict';

  function candidates() {
    try {
      if (window.location.port === '8000' && window.location.origin.indexOf('http') === 0) {
        var origin = window.location.origin.replace(/\/$/, '');
        return dedupe([origin, 'http://127.0.0.1:8000', 'http://localhost:8000']);
      }
      // Hosted origin (https / default port, e.g. Vercel): same origin serves /v1/*.
      if ((window.location.protocol || '').indexOf('https') === 0 || !window.location.port) {
        var hosted = window.location.origin.replace(/\/$/, '');
        return dedupe([hosted, 'http://127.0.0.1:8000', 'http://localhost:8000']);
      }
    } catch (_) {}
    var raw = (window.location.hostname || 'localhost').toLowerCase();
    var host = raw === 'localhost' ? '127.0.0.1' : raw;
    return dedupe(['http://' + host + ':8000', 'http://127.0.0.1:8000', 'http://localhost:8000']);
  }

  function dedupe(list) {
    return list.filter(function (v, i) { return list.indexOf(v) === i; });
  }

  function base() {
    if (window.BridgeUpload && window.BridgeUpload.API_BASE) return window.BridgeUpload.API_BASE;
    return candidates()[0];
  }

  function token() {
    try {
      return localStorage.getItem('bridge-device') || '';
    } catch (_) {
      return '';
    }
  }

  function saveToken(t) {
    try {
      localStorage.setItem('bridge-device', t);
    } catch (_) {}
  }

  function clearToken() {
    try {
      localStorage.removeItem('bridge-device');
    } catch (_) {}
  }

  async function fetchFirst(path, options) {
    // Try each candidate base; return {base, res} for the first that connects.
    var errors = [];
    var list = candidates();
    for (var i = 0; i < list.length; i++) {
      var ctrl = new AbortController();
      var timer = setTimeout(function () { ctrl.abort(); }, 6000);
      try {
        var headers = {};
        if (options && options.headers) {
          Object.keys(options.headers).forEach(function (k) { headers[k] = options.headers[k]; });
        }
        var t = token();
        if (t) headers['X-Device-Token'] = t;
        var res = await fetch(list[i] + path, Object.assign({}, options, {
          headers: headers,
          signal: options && options.signal ? options.signal : ctrl.signal,
        }));
        clearTimeout(timer);
        return { base: list[i], res: res };
      } catch (e) {
        clearTimeout(timer);
        errors.push(list[i]);
      }
    }
    throw new Error('backend unreachable (' + errors.join(', ') + ')');
  }

  async function json(path, options) {
    var out = await fetchFirst(path, options);
    if (!out.res.ok) {
      var err = new Error('HTTP ' + out.res.status);
      err.status = out.res.status;
      err.base = out.base;
      throw err;
    }
    return { base: out.base, data: await out.res.json() };
  }

  function toast(text) {
    var old = document.querySelector('.toast');
    if (old) old.remove();
    var el = document.createElement('div');
    el.className = 'toast';
    el.setAttribute('role', 'status');
    el.textContent = text;
    document.body.appendChild(el);
    setTimeout(function () {
      el.classList.add('is-fading');
      setTimeout(function () { el.remove(); }, 250);
    }, 4000);
  }

  function fmtSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (Math.round((bytes / 1024) * 10) / 10) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (Math.round((bytes / (1024 * 1024)) * 10) / 10) + ' MB';
    return (Math.round((bytes / (1024 * 1024 * 1024)) * 100) / 100) + ' GB';
  }

  function fmtTime(ts) {
    try {
      var d = new Date(ts * 1000);
      return 'Today ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
    } catch (_) {
      return 'Today';
    }
  }

  // Guest landing: ?code=XXXXXX → pair page claims it. Keeps index clean.
  function handoffCode() {
    try {
      var m = /[?&]code=(\d{6})/.exec(window.location.search || '');
      if (m && !token() && /index\.html$|\/$|^\/$/.test(window.location.pathname)) {
        window.location.replace('pair.html?code=' + m[1]);
        return true;
      }
    } catch (_) {}
    return false;
  }

  window.BridgeApi = {
    candidates: candidates,
    base: base,
    token: token,
    saveToken: saveToken,
    clearToken: clearToken,
    fetchFirst: fetchFirst,
    json: json,
    toast: toast,
    fmtSize: fmtSize,
    fmtTime: fmtTime,
    handoffCode: handoffCode,
  };
})();
