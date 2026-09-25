/* Bridge feed — history of files + snippets (PRD FR-23/FR-24).
 * Search, open/download, copy snippet, delete, accept/decline pending.
 * Binds #feed-list on history.html and .snippet-form composers anywhere.
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

  async function copyText(t) {
    try {
      await navigator.clipboard.writeText(t);
      window.BridgeApi.toast('Copied →');
    } catch (_) {
      var ta = document.createElement('textarea');
      ta.value = t;
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand('copy');
        window.BridgeApi.toast('Copied →');
      } catch (__) {
        window.BridgeApi.toast('Copy failed — select the text.');
      }
      ta.remove();
    }
  }

  function fileRow(item, base) {
    var li = document.createElement('li');
    li.className = 'recent-row';
    var path = item.saved_path || item.name;
    var url = base + '/v1/files/' + path.split('/').map(encodeURIComponent).join('/');
    var mime = (item.mime || '').toLowerCase();
    if (mime.indexOf('image/') === 0) {
      var thumb = document.createElement('img');
      thumb.className = 'recent-thumb';
      thumb.src = url;
      thumb.alt = '';
      thumb.loading = 'lazy';
      li.appendChild(thumb);
    }
    var main = document.createElement('div');
    main.className = 'recent-main';
    var name = document.createElement('a');
    name.className = 'recent-name';
    name.textContent = item.name;
    name.href = url;
    name.target = '_blank';
    name.rel = 'noopener';
    var meta = document.createElement('span');
    meta.className = 'recent-meta';
    meta.textContent = window.BridgeApi.fmtTime(item.created_at) + ' · ' +
      window.BridgeApi.fmtSize(item.size || 0);
    main.appendChild(name);
    main.appendChild(meta);
    li.appendChild(main);
    if (item.status === 'pending') {
      li.appendChild(pill('Waiting', true));
      var acc = link('Accept');
      acc.addEventListener('click', function (e) {
        e.preventDefault();
        acceptPending(item);
      });
      var dec = link('Decline');
      dec.addEventListener('click', function (e) {
        e.preventDefault();
        declinePending(item);
      });
      li.appendChild(acc);
      li.appendChild(dec);
    } else {
      li.appendChild(pill(item.direction === 'out' ? 'Out' : 'In'));
      var del = link('Delete');
      del.addEventListener('click', function (e) {
        e.preventDefault();
        delItem('file', item.id, li);
      });
      li.appendChild(del);
    }
    return li;
  }

  function snippetRow(item) {
    var li = document.createElement('li');
    li.className = 'recent-row';
    var main = document.createElement('div');
    main.className = 'recent-main';
    var body;
    if (item.kind === 'link') {
      body = document.createElement('a');
      body.className = 'recent-name';
      body.textContent = item.body;
      body.href = item.body;
      body.target = '_blank';
      body.rel = 'noopener';
    } else {
      body = document.createElement('span');
      body.className = 'recent-name';
      body.textContent = item.body;
    }
    var meta = document.createElement('span');
    meta.className = 'recent-meta';
    meta.textContent = window.BridgeApi.fmtTime(item.created_at);
    main.appendChild(body);
    main.appendChild(meta);
    li.appendChild(main);
    li.appendChild(pill(item.kind === 'link' ? 'Link' : 'Text'));
    var copy = link('Copy');
    copy.addEventListener('click', function (e) {
      e.preventDefault();
      copyText(item.body);
    });
    var del = link('Delete');
    del.addEventListener('click', function (e) {
      e.preventDefault();
      delItem('snippet', item.id, li);
    });
    li.appendChild(copy);
    li.appendChild(del);
    return li;
  }

  async function delItem(kind, id, li) {
    try {
      // Files: delete row + disk together, otherwise boot reconcile
      // re-creates the row from the orphan file and it "comes back".
      var path = '/v1/feed/' + kind + '/' + encodeURIComponent(id);
      if (kind === 'file') path += '?delete_file=1';
      await window.BridgeApi.json(path, { method: 'DELETE' });
      li.remove();
      window.BridgeApi.toast('Deleted →');
    } catch (e) {
      window.BridgeApi.toast('Delete failed — try again.');
    }
  }

  async function acceptPending(item) {
    return acceptById(item.id);
  }

  async function acceptById(id) {
    try {
      // Pending feed rows store the transfer id; the server resolves the
      // staged upload from it.
      window.BridgeApi.toast('Accepting…');
      await window.BridgeApi.json('/v1/feed/accept/' + encodeURIComponent(id), { method: 'POST' });
      loadFeed(currentQ());
      window.BridgeApi.toast('Received →');
      return true;
    } catch (e) {
      window.BridgeApi.toast('Accept failed — try again.');
      return false;
    }
  }

  async function declinePending(item) {
    return declineById(item.id);
  }

  async function declineById(id) {
    try {
      await window.BridgeApi.json('/v1/feed/decline/' + encodeURIComponent(id), { method: 'POST' });
      loadFeed(currentQ());
      window.BridgeApi.toast('Declined →');
      return true;
    } catch (e) {
      window.BridgeApi.toast('Decline failed — try again.');
      return false;
    }
  }

  async function delById(kind, id) {
    try {
      var path = '/v1/feed/' + kind + '/' + encodeURIComponent(id);
      if (kind === 'file') path += '?delete_file=1';
      await window.BridgeApi.json(path, { method: 'DELETE' });
      loadFeed(currentQ());
      window.BridgeApi.toast('Deleted →');
      return true;
    } catch (e) {
      window.BridgeApi.toast('Delete failed — try again.');
      return false;
    }
  }

  function currentQ() {
    var s = el('feed-search');
    return s ? s.value : '';
  }

  async function loadFeed(q) {
    var list = el('feed-list');
    if (!list) return;
    try {
      var out = await window.BridgeApi.json('/v1/feed' + (q ? '?q=' + encodeURIComponent(q) : ''));
      list.textContent = '';
      if (!out.data.items.length) {
        var li = document.createElement('li');
        li.className = 'recent-empty';
        var t = document.createElement('span');
        t.className = 'recent-empty-title';
        t.textContent = q ? 'No matches.' : 'Nothing here yet.';
        li.appendChild(t);
        list.appendChild(li);
        return;
      }
      out.data.items.forEach(function (item) {
        list.appendChild(item.type === 'snippet' ? snippetRow(item) : fileRow(item, out.base));
      });
    } catch (e) {
      window.BridgeApi.toast('History offline — is :8000 running?');
    }
  }

  async function postSnippet(form) {
    var input = form.querySelector('textarea, input');
    var err = form.querySelector('.field-error');
    var body = input ? input.value : '';
    if (!body.trim()) {
      if (err) err.textContent = 'Write something first.';
      return;
    }
    try {
      await window.BridgeApi.json('/v1/snippets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body: body }),
      });
      input.value = '';
      if (err) err.textContent = '';
      window.BridgeApi.toast('Sent →');
      loadFeed(currentQ());
      if (window.BridgeRecent) window.BridgeRecent.refresh();
    } catch (e) {
      if (err) err.textContent = 'Send failed — is :8000 running?';
    }
  }

  function initFeed() {
    if (el('feed-list')) loadFeed('');
    var search = el('feed-search');
    if (search) {
      var timer = null;
      search.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(function () { loadFeed(search.value); }, 250);
      });
    }
    document.querySelectorAll('.snippet-form').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        postSnippet(form);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', initFeed);
  window.BridgeFeed = { load: loadFeed, del: delById, accept: acceptById, decline: declineById };
})();
