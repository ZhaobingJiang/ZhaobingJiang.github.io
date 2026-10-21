/* 全站访问量统计（site-wide page views）
 *
 * 口径：首页页脚显示 = 历史基数 BASELINE（2026-10-21 前的累计访问量）
 *       + 不蒜子全站 PV（site_pv，含所有页面的访问）。
 *
 * 每个页面加载本脚本时都会向不蒜子上报一次本页 PV，因此访问任何页面
 * （首页、论文、项目、诗词详情等）都会累加进同一个全站总数。
 *
 * 维护约束（由 scripts/verify_visit_counter.py 与
 * .github/workflows/visit-counter-guard.yml 自动校验）：
 * 1. BASELINE 只能调大，不能删除或调小；首页 span 的 data-base 必须与之一致。
 * 2. 所有 HTML 页面都必须引入本脚本，且引用中的 ?v=N 版本号保持一致。
 * 3. 修改本脚本后，把各页面引用里的 ?v= 版本号加一，确保浏览器取到新脚本。
 *
 * 统计服务不可达时：显示「历史基数 + 本机上次记录值」；无缓存则只显示历史基数。
 */
(function () {
  "use strict";

  if (window.__jzbSiteCounter) return;
  window.__jzbSiteCounter = true;

  /* 历史累计访问量（2026-10-21 之前）。只能调大，不能删除或调小。 */
  var BASELINE = 2189;

  var BUSUANZI_SRC = "https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";
  var SINK_PREFIX = "busuanzi_value_";
  var CACHE_KEY = "jzb-site-pv-cache";
  var POLL_MS = 200;
  var TIMEOUT_MS = 8000;
  var isZh = /\/zh\//.test(location.pathname);

  var labels = isZh
    ? {
        total: "全站累计访问量：",
        breakdown: function (base, pv) {
          return "（历史 " + format(base) + " + 实时 PV " + format(pv) + "）";
        },
        uv: "；全站访客数（UV）：",
        stale: "统计服务暂不可达，显示本机上次记录值",
        unavailable: "统计服务暂不可达，仅显示历史累计"
      }
    : {
        total: "Total site visits: ",
        breakdown: function (base, pv) {
          return " (baseline " + format(base) + " + live PV " + format(pv) + ")";
        },
        uv: "; unique visitors (UV): ",
        stale: "Counter service unreachable; showing the last value recorded on this device",
        unavailable: "Counter service unreachable; showing the historical total only"
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

  /* 历史基数：脚本常量与页面 data-base 取较大者，任一份保留即可不丢历史数据。 */
  function baseline() {
    var el = document.getElementById("visit-counter");
    var fromDom = el ? parseInt(el.getAttribute("data-base"), 10) : 0;
    if (isNaN(fromDom)) fromDom = 0;
    return Math.max(BASELINE, fromDom);
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

  function showFresh() {
    var pv = readInt(SINK_PREFIX + "site_pv");
    if (pv === null) return false;
    var base = baseline();
    var title = labels.total + format(base + pv) + labels.breakdown(base, pv);
    var uv = readInt(SINK_PREFIX + "site_uv");
    if (uv !== null) title += labels.uv + format(uv);
    setCounter(format(base + pv), title);
    writeCache(pv);
    return true;
  }

  function showStale() {
    var base = baseline();
    var cached = readCache();
    if (cached === null) {
      setCounter(format(base), labels.unavailable);
    } else {
      setCounter(format(base + cached), labels.stale);
    }
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
