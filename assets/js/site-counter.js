/* 全站访问量统计（site-wide page views）
 *
 * 口径：首页页脚显示 = 历史基数 BASELINE（2026-10-21 前的累计访问量）
 *       + 全站 PV（site_pv，含所有页面的访问）。
 *
 * 每个页面加载本脚本时都会向统计服务上报一次本页 PV，因此访问任何页面
 * （首页、论文、项目、诗词详情等）都会累加进同一个全站总数。
 *
 * 数据来源：Vercount（不蒜子的替代服务，https://github.com/evannotfound/vercount）
 *   POST https://events.vercount.one/api/v2/log
 *   body: {"url": location.href, "isNewUv": 是否本站新访客}
 *   返回: {"status":"success","data":{"site_pv":N,"page_pv":N,"site_uv":N}}
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

  var ENDPOINT = "https://events.vercount.one/api/v2/log";
  var UV_COOKIE_PREFIX = "vercount_uv_";
  var CACHE_KEY = "jzb-site-pv-cache-v2";
  var REQUEST_TIMEOUT_MS = 6000;
  var isZh = /\/zh\//.test(location.pathname);

  var labels = isZh
    ? {
        total: "全站累计访问量：",
        breakdown: function (base, pv) {
          return "（历史 " + format(base) + " + 全站 PV " + format(pv) + "）";
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

  function format(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function setCounter(text, title) {
    var el = document.getElementById("visit-counter");
    if (!el) return false;
    el.textContent = text;
    if (title) el.title = title;
    return true;
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
      if (obj && typeof obj.pv === "number" && obj.pv >= 0) return obj;
    } catch (e) {}
    return null;
  }

  function writeCache(pv, uv) {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({ pv: pv, uv: uv, at: Date.now() }));
    } catch (e) {}
  }

  function readCount(payload, key) {
    if (!payload) return null;
    var box = payload.data && typeof payload.data === "object" ? payload.data : payload;
    var n = Number(box[key]);
    return isFinite(n) && n >= 0 ? n : null;
  }

  function showStale() {
    var base = baseline();
    var cached = readCache();
    if (cached === null) {
      setCounter(format(base), labels.unavailable);
    } else {
      setCounter(format(base + cached.pv), labels.stale);
    }
  }

  function uvCookieName() {
    var host = location.host || "unknown-host";
    return UV_COOKIE_PREFIX + host.replace(/[^a-zA-Z0-9_-]/g, "_");
  }

  function isNewVisitor() {
    var name = uvCookieName() + "=";
    var parts = document.cookie ? document.cookie.split("; ") : [];
    for (var i = 0; i < parts.length; i++) {
      if (parts[i].indexOf(name) === 0) return false;
    }
    return true;
  }

  function markVisitor() {
    document.cookie = uvCookieName() + "=1; path=/; max-age=31536000; samesite=lax";
  }

  function reportVisit() {
    if (location.protocol.indexOf("http") !== 0 || !window.fetch) {
      showStale();
      return;
    }
    var isNewUv = isNewVisitor();
    if (isNewUv) markVisitor();
    var controller = typeof AbortController === "function" ? new AbortController() : null;
    var timer = controller
      ? setTimeout(function () {
          controller.abort();
        }, REQUEST_TIMEOUT_MS)
      : null;
    var options = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: location.href, isNewUv: isNewUv }),
      keepalive: true
    };
    if (controller) options.signal = controller.signal;
    fetch(ENDPOINT, options)
      .then(function (resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      })
      .then(function (payload) {
        if (timer) clearTimeout(timer);
        var pv = readCount(payload, "site_pv");
        if (pv === null) throw new Error("bad payload");
        var uv = readCount(payload, "site_uv");
        writeCache(pv, uv);
        if (!document.getElementById("visit-counter")) return;
        var base = baseline();
        var title = labels.total + format(base + pv) + labels.breakdown(base, pv);
        if (uv !== null) title += labels.uv + format(uv);
        setCounter(format(base + pv), title);
      })
      .catch(function () {
        if (timer) clearTimeout(timer);
        showStale();
      });
  }

  function init() {
    var cached = readCache();
    if (cached !== null && document.getElementById("visit-counter")) {
      var base = baseline();
      setCounter(format(base + cached.pv), labels.stale);
    }
    reportVisit();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
