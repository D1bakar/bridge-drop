/* Bridge settings page — device name, auto-accept, visibility, save rules.
 * PRD FR-30 + FR-16. Toggles are text links (design §6), switch role for AT.
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

  function toggleRow(labelText, get, set) {
    var li = document.createElement('li');
    li.className = 'settings-row';
    var label = document.createElement('span');
    label.className = 'settings-name';
    label.textContent = labelText;
    var t = link(get() ? 'On' : 'Off');
    t.setAttribute('role', 'switch');
    t.setAttribute('aria-checked', get() ? 'true' : 'false');
    t.addEventListener('click', async function (e) {
      e.preventDefault();
      await set(!get());
      t.innerHTML = (get() ? 'On' : 'Off') + ' <span aria-hidden="true">→</span>';
      t.setAttribute('aria-checked', get() ? 'true' : 'false');
    });
    li.appendChild(label);
    li.appendChild(t);
    return li;
  }

  var state = { auto_accept: true, visibility: 'visible' };

  async function load() {
    try {
      var out = await window.BridgeApi.json('/v1/settings');
      var s = out.data;
      el('set-name').value = s.device_name || '';
      state.auto_accept = !!s.auto_accept;
      state.visibility = s.visibility || 'visible';
      el('save-root').textContent = 'Files land in ' + (s.save_root || '');
      renderToggles();
      loadRules();
    } catch (e) {
      window.BridgeApi.toast('Settings offline — is :8000 running?');
    }
  }

  function renderToggles() {
    var list = el('toggle-list');
    list.textContent = '';
    list.appendChild(toggleRow('Auto-accept from guests', function () {
      return state.auto_accept;
    }, async function (v) {
      await window.BridgeApi.json('/v1/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_accept: v }),
      });
      state.auto_accept = v;
      window.BridgeApi.toast(v ? 'Auto-accept on →' : 'New guests wait for accept →');
    }));
    var visLi = document.createElement('li');
    visLi.className = 'settings-row';
    var visLabel = document.createElement('span');
    visLabel.className = 'settings-name';
    visLabel.textContent = 'Visibility';
    var vis = link(state.visibility === 'visible' ? 'Visible' : 'Hidden');
    vis.addEventListener('click', async function (e) {
      e.preventDefault();
      var next = state.visibility === 'visible' ? 'hidden' : 'visible';
      await window.BridgeApi.json('/v1/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ visibility: next }),
      });
      state.visibility = next;
      vis.innerHTML = (next === 'visible' ? 'Visible' : 'Hidden') + ' <span aria-hidden="true">→</span>';
    });
    visLi.appendChild(visLabel);
    visLi.appendChild(vis);
    list.appendChild(visLi);
  }

  async function loadRules() {
    var list = el('rules-list');
    list.textContent = '';
    try {
      var out = await window.BridgeApi.json('/v1/rules');
      if (!out.data.rules.length) {
        var li = document.createElement('li');
        li.className = 'recent-empty';
        var t = document.createElement('span');
        t.className = 'recent-empty-title';
        t.textContent = 'Everything lands in one folder.';
        li.appendChild(t);
        list.appendChild(li);
        return;
      }
      out.data.rules.forEach(function (r) {
        var li = document.createElement('li');
        li.className = 'settings-row';
        var label = document.createElement('span');
        label.className = 'settings-name';
        label.textContent = r.ext + ' → ' + r.dir;
        var rm = link('Remove');
        rm.addEventListener('click', async function (e) {
          e.preventDefault();
          await window.BridgeApi.json('/v1/rules?ext=' + encodeURIComponent(r.ext), { method: 'DELETE' });
          loadRules();
        });
        li.appendChild(label);
        li.appendChild(rm);
        list.appendChild(li);
      });
    } catch (e) {
      window.BridgeApi.toast('Rules offline — is :8000 running?');
    }
  }

  function init() {
    load();
    el('name-save').addEventListener('click', async function (e) {
      e.preventDefault();
      var err = el('name-error');
      try {
        await window.BridgeApi.json('/v1/settings', {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ device_name: el('set-name').value }),
        });
        err.textContent = '';
        window.BridgeApi.toast('Saved →');
      } catch (ex) {
        err.textContent = 'Name required.';
      }
    });
    el('rule-add').addEventListener('click', async function (e) {
      e.preventDefault();
      var err = el('rule-error');
      var ext = el('rule-ext').value.trim();
      var dir = el('rule-dir').value.trim();
      try {
        await window.BridgeApi.json('/v1/rules', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ext: ext, dir: dir }),
        });
        err.textContent = '';
        el('rule-ext').value = '';
        el('rule-dir').value = '';
        loadRules();
      } catch (ex) {
        err.textContent = 'Need an extension like .mp4 and a folder name.';
      }
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
