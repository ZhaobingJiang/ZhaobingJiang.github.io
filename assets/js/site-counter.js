/* 全站访问量统计（site-wide page views）
 *
 * 用途：站点每个页面加载时都以“本页 URL”为 Referer 向不蒜子（busuanzi）
 * 上报一次 PV；首页页脚把全站累计访问量（site_pv，含论文/项目/诗词等
 * 所有页面）写入 #visit-counter。
 *
 * 设计要点：
 * - 静态站（GitHub Pages）没有后端，采用不蒜子的 site_pv 做全站累计；
 *   只要本脚本在每个页面加载一次，任意页面的访问都会计入同一个总数。
 * - 不蒜子脚本通过隐藏的 #busuanzi_value_* 节点回填数据，本脚本轮询读取。
 * - 统计服务不可达时：首页回退显示本机上次记录值（title 注明），
 *   避免把旧值或 0 当作实时数据展示。
 */
(function () {
  "use strict";

  if (window.__jzbSiteCounter) return;
  window.__jzbSiteCounter = true;

  var BUSUANZI_SRC = "https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";
  var SINK_PREFIX = "busuanzi_value_";
  var CACHE_KEY = "jzb-site-pv-cache";
  var POLL_MS = 200;
  var TIMEOUT_MS = 8000;
  var isZh = /\/zh\//.test(location.pathname);

  var labels = isZh
    ? {
        total: "全站累计访问量（PV，含所有页面）",
        uvPrefix: "；全站访客数（UV）：",
        stale: "统计服务暂不可达，显示本机上次记录值",
        unavailable: "统计服务暂不可达"
      }
    : {
        total: "Total site visits (PV, all pages)",
        uvPrefix: "; unique visitors (UV): ",
        stale: "Counter service unreachable; showing the last value recorded on this device",
        unavailable: "Counter service unreachable"
      };

  /* 供不蒜子脚本回填的隐藏节点（其脚本按固定 id 查找）。 */
  function ensureSinks() {
    if (document.getElementById(SINK_PREFIX + "site_pv")) return;
    var box = document.createElement("div");
    box.style.display = "none";
    box.setAttribute("aria-hidden", "true");
    ["site_pv", "site_uv", "page_pv"].forEach(function (key) {
      var span = document.createElement("span");
      span.id = SINK_PREFIX + key;
      box.appendChild(span);
    });
    (document.body || document.documentElement).appendChild(box);
  }

  function readInt(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    var digits = (el.textContent || "").replace(/[^\d]/g, "");
    if (!digits) return null;
    var n = parseInt(digits, 10);
    return isNaN(n) ? null : n;
  }

  function format(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function setCounter(text, title) {
    var el = document.getElementById("visit-counter");
    if (!el) return;
    el.textContent = text;
    if (title) el.title = title;
  }

  function readCache() {
    try {
      var obj = JSON.parse(localStorage.getItem(CACHE_KEY) || "null");
      if (obj && typeof obj.n === "number" && obj.n >= 0) return obj.n;
    } catch (e) {}
    return null;
  }

  function writeCache(n) {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ n: n, at: Date.now() }));
    } catch (e) {}
  }

  function showStale() {
    var cached = readCache();
    if (cached === null) {
      setCounter("—", labels.unavailable);
    } else {
      setCounter(format(cached), labels.stale);
    }
  }

  function showFresh() {
    var pv = readInt(SINK_PREFIX + "site_pv");
    if (pv === null) return false;
    var uv = readInt(SINK_PREFIX + "site_uv");
    var title = labels.total;
    if (uv !== null) title += labels.uvPrefix + format(uv);
    setCounter(format(pv), title);
    writeCache(pv);
    return true;
  }

  function loadCounter() {
    var scripts = document.getElementsByTagName("script");
    for (var i = 0; i < scripts.length; i++) {
      if (scripts[i].src && scripts[i].src.indexOf("busuanzi") !== -1) return;
    }
    var s = document.createElement("script");
    s.src = BUSUANZI_SRC;
    s.async = true;
    s.referrerPolicy = "no-referrer-when-downgrade";
    s.onerror = function () {
      if (document.getElementById("visit-counter")) showStale();
    };
    (document.head || document.documentElement).appendChild(s);
  }

  function init() {
    ensureSinks();
    loadCounter();
    if (!document.getElementById("visit-counter")) return;

    setCounter("…", labels.total);
    var waited = 0;
    var timer = setInterval(function () {
      if (showFresh()) {
        clearInterval(timer);
        return;
      }
      waited += POLL_MS;
      if (waited >= TIMEOUT_MS) {
        clearInterval(timer);
        if (!showFresh()) showStale();
      }
    }, POLL_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
