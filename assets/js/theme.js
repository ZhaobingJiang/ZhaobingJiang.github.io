/* Theme switcher: minimal-light (default) <-> rich style.
 * Injects a fixed toggle button (top-right) and persists the choice.
 * Safe to load in <head>: button creation waits for DOM readiness. */
(function () {
  "use strict";

  function cssDir() {
    var ss = document.getElementsByTagName("script");
    for (var i = 0; i < ss.length; i++) {
      var m = ss[i].src.match(/(.*)assets\/js\/theme\.js/);
      if (m) return m[1] + "assets/css/";
    }
    return "assets/css/";
  }

  var KEY = "jzb-site-theme";
  var dir = cssDir();
  var rich = false;
  try {
    rich = localStorage.getItem(KEY) === "rich";
  } catch (e) {}

  var link = document.createElement("link");
  link.id = "theme-rich-style";
  link.rel = "stylesheet";
  var btn = null;

  function apply() {
    if (rich) {
      link.href = dir + "style-rich.css";
      if (!link.parentNode) document.head.appendChild(link);
    } else if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
    if (btn) {
      btn.textContent = rich ? "简约样式" : "富文本样式";
    }
    if (document.body) {
      document.body.setAttribute("data-theme", rich ? "rich" : "minimal");
    }
    try { localStorage.setItem(KEY, rich ? "rich" : "minimal"); } catch (e) {}
  }

  function init() {
    if (!document.body) return;
    btn = document.createElement("button");
    btn.type = "button";
    btn.className = "theme-toggle-btn";
    btn.setAttribute("aria-label", "Toggle theme");
    btn.addEventListener("click", function () {
      rich = !rich;
      apply();
    });
    document.body.appendChild(btn);
    apply();
  }

  // Preload rich stylesheet immediately if stored choice is rich (avoids flash)
  if (rich) {
    link.href = dir + "style-rich.css";
    document.head.appendChild(link);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
