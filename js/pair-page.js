/* Bridge pair page — QR code, short code, claim, trusted devices.
 * PRD FR-2/FR-3: scan → open ?code= → claim → token stored → trusted.
 */

(function () {
  'use strict';

  function el(id) { return document.getElementById(id); }

  function link(text) {
    var a = document.createElement('a');
    a.className = 'action-secondary';
    a.href = '#';
    a.innerHTML = text + ' <span aria-hidden="true">→</span>';
    return a;
  }

  function pill(text, attention) {
    var s = document.createElement('span');
    s.className = 'pill' + (attention ? ' pill-attention' : '');
    s.textContent = text;
    return s;
  }

  function queryCode() {
    var m = /[?&]code=(\d{6})/.exec(window.location.search || '');
    return m ? m[1] : '';
  }

  async function showCode(code) {
    el('pair-code').textContent = code.split('').join(' ');
    el('pair-qr').src = window.BridgeApi.base() + '/v1/pair/qr?code=' + encodeURIComponent(code);
    el('pair-hint').textContent = 'Scan with the phone camera. Expires in 5 minutes, one use.';
  }

  async function newCode() {
    try {
      var out = await window.BridgeApi.json('/v1/pair/code', { method: 'POST' });
      showCode(out.data.code);
    } catch (e) {
      window.BridgeApi.toast('Pairing offline — is :8000 running?');
    }
  }

  async function claim(code) {
    var name = el('pair-name').value.trim() || 'Guest phone';
    var err = el('pair-error');
    try {
      var out = await window.BridgeApi.json('/v1/pair/claim', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code, name: name, platform: browserPlatform() }),
      });
      window.BridgeApi.saveToken(out.data.deviceToken);
      el('claim-block').style.display = 'none';
      var done = el('paired-block');
      done.style.display = '';
      el('pair-fingerprint').textContent = out.data.fingerprint;
    } catch (e) {
      if (err) err.textContent = e.status === 403 ? 'Bad or expired code — ask for a new one.' : 'Claim failed — try again.';
    }
  }

  function browserPlatform() {
    var ua = navigator.userAgent || '';
    if (/Android/i.test(ua)) return 'Android';
    if (/iPhone|iPad|iPod/i.test(ua)) return 'iOS';
    return 'Browser';
  }

  async function loadDevices() {
    var list = el('devices-list');
    if (!list) return;
    list.textContent = '';
    try {
      var out = await window.BridgeApi.json('/v1/devices');
      if (!out.data.devices.length) {
        var li = document.createElement('li');
        li.className = 'recent-empty';
        var t = document.createElement('span');
        t.className = 'recent-empty-title';
        t.textContent = 'No paired devices yet.';
        li.appendChild(t);
        list.appendChild(li);
        return;
      }
      out.data.devices.forEach(function (d) {
        var li = document.createElement('li');
        li.className = 'device';
        var main = document.createElement('div');
        main.className = 'device-main';
        var meta = document.createElement('span');
        meta.className = 'device-meta';
        meta.textContent = (d.platform || 'Device') + ' · ' + (d.fingerprint || '');
        var name = document.createElement('span');
        name.className = 'device-name';
        name.textContent = d.name;
        main.appendChild(meta);
        main.appendChild(name);
        li.appendChild(main);
        li.appendChild(pill('Paired'));
        var rename = link('Rename');
        rename.addEventListener('click', function (e) {
          e.preventDefault();
          renameRow(li, d);
        });
        var revoke = link('Revoke');
        revoke.addEventListener('click', function (e) {
          e.preventDefault();
          if (revoke.dataset.armed) {
            revokeDevice(d.id);
          } else {
            revoke.dataset.armed = '1';
            revoke.innerHTML = 'Confirm revoke <span aria-hidden="true">→</span>';
          }
        });
        li.appendChild(rename);
        li.appendChild(revoke);
        list.appendChild(li);
      });
    } catch (e) {
      window.BridgeApi.toast('Devices offline — is :8000 running?');
    }
  }

  function renameRow(li, d) {
    li.textContent = '';
    var input = document.createElement('input');
    input.className = 'field-input';
    input.value = d.name;
    input.setAttribute('aria-label', 'Device name');
    var save = link('Save');
    save.addEventListener('click', async function (e) {
      e.preventDefault();
      try {
        await window.BridgeApi.json('/v1/devices/' + encodeURIComponent(d.id), {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: input.value }),
        });
        loadDevices();
      } catch (err) {
        window.BridgeApi.toast('Rename failed — try again.');
      }
    });
    li.appendChild(input);
    li.appendChild(save);
    input.focus();
    input.select();
  }

  async function revokeDevice(id) {
    try {
      await window.BridgeApi.json('/v1/devices/' + encodeURIComponent(id), { method: 'DELETE' });
      loadDevices();
      window.BridgeApi.toast('Revoked →');
    } catch (e) {
      window.BridgeApi.toast('Revoke failed — try again.');
    }
  }

  function init() {
    var code = queryCode();
    if (code && !window.BridgeApi.token()) {
      el('show-block').style.display = 'none';
      el('claim-block').style.display = '';
      el('claim-code').textContent = code.split('').join(' ');
      el('claim-go').addEventListener('click', function (e) {
        e.preventDefault();
        claim(code);
      });
      el('paired-home').addEventListener('click', function () {
        window.location.href = '/';
      });
    } else {
      newCode();
      el('new-code').addEventListener('click', function (e) {
        e.preventDefault();
        newCode();
      });
    }
    loadDevices();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
