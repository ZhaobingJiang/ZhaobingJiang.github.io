/* ============================================================================
   《不确定年代的生存经济学》网页版交互层
   正文已经是静态 HTML，本脚本只负责：筛选、检索、目录折叠、滚动定位、
   深色模式与移动端抽屉。脚本不生成任何正文内容。
   ========================================================================== */
(function () {
  'use strict';

  var CARDS = Array.prototype.slice.call(document.querySelectorAll('#list .card'));
  if (!CARDS.length) return;

  var BLOCKS = Array.prototype.slice.call(document.querySelectorAll('#list .sec-block'));
  var PARTS = Array.prototype.slice.call(document.querySelectorAll('#list .part'));
  var TOC = {};
  Array.prototype.forEach.call(document.querySelectorAll('.toc-sub a[data-go]'), function (a) {
    TOC[a.dataset.go] = a;
  });
  var SUBS = {};
  Array.prototype.forEach.call(document.querySelectorAll('.toc-sub'), function (s) {
    SUBS[s.dataset.for] = s;
  });

  // 每张卡的可检索文本只算一次；正文是静态的，算完就不再变
  var HAY = CARDS.map(function (el) {
    return ((el.dataset.search || '') + ' ' + el.textContent).toLowerCase().replace(/\s+/g, ' ');
  });

  var DIMS = ['part', 'kind', 'mat', 'len'];
  var state = { q: '', ch: '', part: [], kind: [], mat: [], len: [], minsheng: false, table: false };

  /* ---------- 地址栏 ---------- */
  function readUrl() {
    try {
      var p = new URLSearchParams(location.search);
      state.q = p.get('q') || '';
      state.ch = p.get('ch') || '';
      DIMS.forEach(function (d) { state[d] = (p.get(d) || '').split(',').filter(Boolean); });
      state.minsheng = p.get('minsheng') === '1';
      state.table = p.get('table') === '1';
    } catch (e) { /* file:// 或无 query 时按默认筛选 */ }
  }
  function writeUrl() {
    try {
      var p = new URLSearchParams();
      if (state.q) p.set('q', state.q);
      if (state.ch) p.set('ch', state.ch);
      DIMS.forEach(function (d) { if (state[d].length) p.set(d, state[d].join(',')); });
      if (state.minsheng) p.set('minsheng', '1');
      if (state.table) p.set('table', '1');
      var qs = p.toString();
      history.replaceState(null, '', (qs ? '?' + qs : location.pathname) + location.hash);
    } catch (e) { /* 本地 file:// 打开时不允许改地址栏，忽略 */ }
  }

  /* ---------- 控件同步 ---------- */
  function syncControls() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-dim] [data-v]'), function (b) {
      var dim = b.parentElement.dataset.dim;
      var on = dim === 'ch' ? state.ch === b.dataset.v : state[dim].indexOf(b.dataset.v) >= 0;
      b.setAttribute('aria-pressed', String(on));
    });
    var q = document.getElementById('q');
    if (q.value !== state.q) q.value = state.q;
    document.getElementById('f-minsheng').checked = state.minsheng;
    document.getElementById('f-table').checked = state.table;
  }

  /* ---------- 检索词高亮 ---------- */
  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function highlight(el, terms) {
    var raw = el.dataset.raw;
    if (raw === undefined) { raw = el.textContent; el.dataset.raw = raw; }
    if (!terms.length) { el.textContent = raw; return; }
    var re = new RegExp('(' + terms.map(function (t) {
      return t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }).join('|') + ')', 'gi');
    el.innerHTML = esc(raw).replace(re, '<mark>$1</mark>');
  }

  /* ---------- 筛选 ---------- */
  function apply() {
    var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
    var shown = 0, perBlock = {}, perPart = {};
    CARDS.forEach(function (el, i) {
      var d = el.dataset, ok = true;
      if (ok && state.part.length && state.part.indexOf(d.part) < 0) ok = false;
      if (ok && state.kind.length && state.kind.indexOf(d.kind) < 0) ok = false;
      if (ok && state.len.length && state.len.indexOf(d.len) < 0) ok = false;
      if (ok && state.mat.length) {
        var mats = d.mats ? d.mats.split('|') : [];
        ok = state.mat.some(function (m) { return mats.indexOf(m) >= 0; });
      }
      if (ok && state.minsheng && d.minsheng !== '1') ok = false;
      if (ok && state.table && d.table !== '1') ok = false;
      if (ok && terms.length) {
        var hay = HAY[i];
        ok = terms.every(function (t) { return hay.indexOf(t) >= 0; });
      }
      if (ok && state.ch && d.ch !== state.ch) ok = false;
      if (el.hidden === ok) el.hidden = !ok;
      if (ok) {
        shown++;
        perBlock[d.ch] = (perBlock[d.ch] || 0) + 1;
        perPart[d.part] = (perPart[d.part] || 0) + 1;
        var a = TOC[el.id];
        if (a && a.hidden) a.hidden = false;
      } else {
        var a2 = TOC[el.id];
        if (a2 && !a2.hidden) a2.hidden = true;
      }
      if (ok) {
        highlight(el.querySelector('h3'), terms);
        highlight(el.querySelector('.human'), terms);
      }
    });
    BLOCKS.forEach(function (b) {
      var n = perBlock[b.dataset.ch] || 0;
      var k = b.querySelector('.shown .k');
      if (k && k.textContent !== String(n)) k.textContent = n;
      if (b.hidden !== (n === 0)) b.hidden = n === 0;
    });
    PARTS.forEach(function (p) {
      var n = perPart[p.dataset.part] || 0;
      if (p.hidden !== (n === 0)) p.hidden = n === 0;
    });
    Object.keys(SUBS).forEach(function (key) {
      var sub = SUBS[key];
      var none = sub.querySelector('.toc-none');
      var any = Array.prototype.some.call(sub.querySelectorAll('a[data-go]'), function (a) { return !a.hidden; });
      if (none) none.hidden = any;
    });
    document.getElementById('cnt').textContent = shown;
    document.getElementById('empty').hidden = shown !== 0;
    syncControls();
    writeUrl();
  }

  /* ---------- 目录面板 ---------- */
  function fold(key, want) {
    var sub = SUBS[key];
    if (!sub) return;
    sub.hidden = !want;
    var btn = document.querySelector('#f-ch [data-v="' + key + '"]');
    if (btn) btn.classList.toggle('open', want);
  }

  // 侧栏一次只展开一个章节的目录：同时摊开好几份会把后面的章节挤到看不见，
  // 也容易让人以为「这一节的条目跑到了列表末尾」
  function openOnly(key, want, reveal) {
    if (!want) { fold(key, false); return; }
    Object.keys(SUBS).forEach(function (k) { if (k !== key) fold(k, false); });
    fold(key, true);
    if (reveal) {
      var btn = document.querySelector('#f-ch [data-v="' + key + '"]');
      if (btn) btn.scrollIntoView({ block: 'nearest' });
    }
  }

  /* ---------- 跳到某个单元 ---------- */
  function goto(id) {
    var el = document.getElementById(id);
    if (!el) return;
    if (el.hidden) { reset(); }
    var block = el.closest('.sec-block');
    var land = block ? block.querySelector('.sec-h') : el;
    land.scrollIntoView({ behavior: 'smooth', block: 'start' });
    el.classList.remove('flash');
    void el.offsetWidth;
    el.classList.add('flash');
    setTimeout(function () { el.classList.remove('flash'); }, 2000);
  }

  function reset() {
    state.q = ''; state.ch = '';
    DIMS.forEach(function (d) { state[d] = []; });
    state.minsheng = false; state.table = false;
    apply();
  }

  /* ---------- 事件 ---------- */
  function wire() {
    var sb = document.getElementById('sidebar');
    var bd = document.getElementById('backdrop');
    var mb = document.getElementById('menu');
    function setMenu(on) {
      sb.classList.toggle('open', on);
      bd.classList.toggle('on', on);
      mb.setAttribute('aria-expanded', String(on));
    }

    document.querySelectorAll('[data-dim]').forEach(function (g) {
      g.addEventListener('click', function (ev) {
        var b = ev.target.closest('[data-v]');
        if (!b) return;
        var dim = g.dataset.dim, v = b.dataset.v;
        if (dim === 'ch') {
          // 点折叠箭头，或再点一次已选中的章：只收起或展开目录，筛选不动
          if (ev.target.closest('.fold') || state.ch === v) {
            openOnly(v, !!(SUBS[v] && SUBS[v].hidden), true);
            return;
          }
          state.ch = v;
          if (v) openOnly(v, true, true);
        } else if (dim === 'part' && v === '') {
          state.part = [];
        } else {
          var i = state[dim].indexOf(v);
          if (i >= 0) state[dim].splice(i, 1); else state[dim].push(v);
        }
        apply();
        setMenu(false);
        scrollTo({ top: 0 });
      });
    });

    document.getElementById('f-ch').addEventListener('click', function (ev) {
      var a = ev.target.closest('a[data-go]');
      if (!a) return;
      ev.preventDefault();
      setMenu(false);
      goto(a.dataset.go);
    });

    document.getElementById('f-minsheng').addEventListener('change', function (e) {
      state.minsheng = e.target.checked; apply();
    });
    document.getElementById('f-table').addEventListener('change', function (e) {
      state.table = e.target.checked; apply();
    });

    var tm, q = document.getElementById('q');
    q.addEventListener('input', function () {
      clearTimeout(tm);
      tm = setTimeout(function () { state.q = q.value.trim(); apply(); }, 120);
    });

    document.getElementById('reset').addEventListener('click', reset);
    document.getElementById('reset2').addEventListener('click', reset);

    document.getElementById('theme').addEventListener('click', function () {
      var dark = !document.documentElement.classList.contains('dark');
      document.documentElement.classList.toggle('dark', dark);
      try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch (e) {}
    });

    mb.addEventListener('click', function () { setMenu(!sb.classList.contains('open')); });
    bd.addEventListener('click', function () { setMenu(false); });

    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
        e.preventDefault(); q.focus();
      }
      if (e.key === 'Escape') {
        if (document.activeElement === q) document.activeElement.blur();
        setMenu(false);
      }
    });

    // 目录跟随阅读位置：取视口偏上三成那条线以上的最后一张卡
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var a = TOC[en.target.id];
          if (!a) return;
          Object.keys(TOC).forEach(function (k) { TOC[k].classList.remove('on'); });
          a.classList.add('on');
          var key = a.closest('.toc-sub').dataset.for;
          // 只展开、不滚动侧栏：跟着阅读位置自动滚会一直和读者抢滚动条
          if (SUBS[key] && SUBS[key].hidden) openOnly(key, true, false);
        });
      }, { rootMargin: '-30% 0px -60% 0px' });
      CARDS.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------- 启动 ---------- */
  readUrl();
  wire();
  apply();
  // 就绪标记：正文是一个 600 多 KB 的 HTML，首屏卡片出现得比样式表和脚本早得多，
  // 外部核对（以及任何等待「页面可用」的地方）应该等这个属性，而不是等 load
  document.documentElement.setAttribute('data-ready', '1');
  if (location.hash) {
    var target = document.getElementById(location.hash.slice(1));
    if (target && target.hidden) {
      state.q = ''; state.ch = '';
      DIMS.forEach(function (d) { state[d] = []; });
      state.minsheng = false; state.table = false;
      apply();
    }
    if (target) {
      var head = target.closest('.sec-block');
      (head ? head.querySelector('.sec-h') : target).scrollIntoView();
    }
  }
})();
