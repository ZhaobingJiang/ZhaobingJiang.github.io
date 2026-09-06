/* Theme switcher: minimal-light (default) <-> rich style.
 * Injects a fixed toggle button (top-right) and persists the choice. */
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
  var rich = localStorage.getItem(KEY) === "rich";

  var link = document.createElement("link");
  link.id = "theme-rich-style";
  link.rel = "stylesheet";

  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "theme-toggle-btn";
  btn.setAttribute("aria-label", "Toggle theme");
  document.body.appendChild(btn);

  function apply() {
    if (rich) {
      link.href = dir + "style-rich.css";
      if (!link.parentNode) document.head.appendChild(link);
    } else if (link.parentNode) {
      link.parentNode.removeChild(link);
    }
    btn.textContent = rich ? "简约样式" : "富文本样式";
    document.body.setAttribute("data-theme", rich ? "rich" : "minimal");
    try { localStorage.setItem(KEY, rich ? "rich" : "minimal"); } catch (e) {}
  }

  btn.addEventListener("click", function () {
    rich = !rich;
    apply();
  });

  apply();
})();
