"""Guide HTML serve-time hardening and URL sanitization (AUDIT-009 F2/F10)."""

from __future__ import annotations

import re

_MOBILE_CSS_PATCH = """
<style id="aulos-mobile-harden">
img{max-width:100%;height:auto}
.portrait{width:100%}
.portrait img{width:100%;height:auto;display:block;background:#1a1510}
@media(max-width:719px){
  .wrap{padding:1.35rem 1rem 3.25rem!important}
  .portrait{max-width:17rem;margin:0 auto}
  .portrait img{max-height:min(68vh,26rem);object-fit:contain;object-position:top center}
  h1{font-size:clamp(1.75rem,7vw,2.4rem)!important}
}
</style>
"""

# Serve-time only: public share pages stay clean without recompose.
_SHARE_CHROME_PATCH = """
<style id="aulos-share-chrome">
#aulos-owner-bar{display:none!important}
body.has-owner-bar{padding-top:0!important}
.wrap{padding-bottom:7.5rem!important}
.ambient{position:fixed!important;z-index:60!important;right:0.75rem!important;bottom:0.75rem!important;left:auto!important;width:min(22.5rem,calc(100vw - 1.5rem))!important;margin:0!important;padding:0.35rem 0.5rem!important;border:1px solid rgba(232,239,233,0.11)!important;background:rgba(16,22,27,0.92)!important;backdrop-filter:blur(12px);box-shadow:0 12px 36px rgba(0,0,0,0.45);max-height:min(72vh,30rem)!important;display:flex!important;flex-direction:column!important}
.ambient .ambient-mini{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:0.4rem;align-items:center;flex:0 0 auto}
.ambient.is-collapsed .ambient-details,
.ambient.is-collapsed .ambient-credit,
.ambient.is-collapsed .ambient-hint,
.ambient.is-collapsed .ambient-kicker{display:none!important}
.ambient .ambient-toggle{width:1.7rem!important;height:1.7rem!important;border-radius:999px;padding:0!important;min-height:0!important;display:inline-flex;align-items:center;justify-content:center;font-size:0!important}
.ambient .ambient-title{margin:0!important;font-size:0.72rem!important;line-height:1.25!important;font-weight:500!important;color:#9aafa3!important;font-family:Manrope,system-ui,sans-serif!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ambient:not(.is-collapsed) .ambient-title{white-space:normal;color:#e8efe9!important;font-size:0.88rem!important;font-family:Fraunces,"Noto Serif SC",serif!important}
.ambient .ambient-expand{appearance:none;border:0;background:transparent;color:#9aafa3;font:inherit;font-size:0.62rem!important;cursor:pointer;text-decoration:underline;text-underline-offset:0.12em;white-space:nowrap;opacity:0.85;padding:0.1rem 0!important}
.ambient .ambient-expand:hover{color:#c9a66b;opacity:1}
.ambient .ambient-details{padding:0.1rem 0;border-top:1px solid rgba(232,239,233,0.11);margin-top:0.4rem;overflow:auto;flex:1 1 auto;min-height:0}
.ambient .ambient-credit,.ambient .ambient-hint{margin:0.4rem 0 0!important;font-size:0.72rem!important}
.ambient audio{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none;overflow:hidden;clip:rect(0 0 0 0)}
.lang-switch{display:inline-flex!important;gap:0.15rem!important;margin:0 0 0.85rem!important;padding:0.12rem!important;border:1px solid rgba(232,239,233,0.11)!important;background:rgba(21,28,34,0.7)!important}
.lang-switch button{font-size:0.68rem!important;font-weight:600!important;padding:0.22rem 0.5rem!important;min-height:0!important;line-height:1.2!important;letter-spacing:0.02em!important}
@media (max-width:719px){.ambient{right:0.5rem!important;left:0.5rem!important;bottom:0.5rem!important;width:auto!important;max-height:min(60vh,24rem)!important}.wrap{padding-bottom:6.5rem!important}}
</style>
<script id="aulos-share-chrome-js">
(function () {
  function wipeOwnerChrome() {
    var bar = document.getElementById("aulos-owner-bar");
    if (bar) bar.remove();
    document.body.classList.remove("has-owner-bar");
    document.querySelectorAll("script").forEach(function (s) {
      var t = s.textContent || "";
      if (t.indexOf("aulos-owner-bar") >= 0 && s.id !== "aulos-share-chrome-js") s.remove();
    });
  }
  function compactAmbient() {
    var amb = document.querySelector(".ambient");
    if (!amb) return;
    wipeOwnerChrome();
    if (amb.querySelector(".ambient-mini")) {
      amb.classList.add("is-collapsed");
      return;
    }
    var title = amb.querySelector(".ambient-title");
    var kicker = amb.querySelector(".ambient-kicker");
    var credit = amb.querySelector(".ambient-credit");
    var hint = amb.querySelector(".ambient-hint");
    var toggle = amb.querySelector(".ambient-toggle");
    var audio = amb.querySelector("audio");
    var langAttr = document.documentElement.getAttribute("lang") || "";
    var isHant = langAttr === "zh-Hant";
    var lang = langAttr.indexOf("zh") === 0 ? "zh" : "en";
    var expandLabel = lang === "zh" ? (isHant ? "說明" : "说明") : "Info";
    var collapseLabel = lang === "zh" ? "收起" : "Hide";
    var mini = document.createElement("div");
    mini.className = "ambient-mini";
    var text = document.createElement("div");
    text.className = "ambient-mini-text";
    if (kicker) text.appendChild(kicker);
    if (title) text.appendChild(title);
    var expand = document.createElement("button");
    expand.type = "button";
    expand.className = "ambient-expand";
    expand.setAttribute("aria-expanded", "false");
    expand.textContent = expandLabel;
    if (toggle) mini.appendChild(toggle);
    mini.appendChild(text);
    mini.appendChild(expand);
    var details = document.createElement("div");
    details.className = "ambient-details";
    details.hidden = true;
    if (credit) details.appendChild(credit);
    if (hint) details.appendChild(hint);
    amb.innerHTML = "";
    amb.appendChild(mini);
    amb.appendChild(details);
    if (audio) amb.appendChild(audio);
    amb.classList.add("is-collapsed");
    expand.addEventListener("click", function () {
      var open = amb.classList.toggle("is-collapsed") === false;
      open = !amb.classList.contains("is-collapsed");
      details.hidden = !open;
      expand.setAttribute("aria-expanded", open ? "true" : "false");
      expand.textContent = open ? collapseLabel : expandLabel;
    });
  }
  wipeOwnerChrome();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", compactAmbient);
  } else {
    compactAmbient();
  }
  // Owner script may race-create the bar later
  setTimeout(wipeOwnerChrome, 0);
  setTimeout(wipeOwnerChrome, 400);
})();
</script>
<script id="aulos-ambient-failover">
(function () {
  function encodeSrc(u) {
    try { return encodeURIComponent(u); } catch (e) { return ""; }
  }
  function resolveUrl(u) {
    if (!u) return u;
    if (/^(https?:|blob:|data:)/i.test(u)) return u;
    try { return new URL(u, document.baseURI || window.location.href).href; } catch (e) { return u; }
  }
  function wire(ambient) {
    if (!ambient || ambient.getAttribute("data-failover-wired") === "1") return;
    if (ambient.getAttribute("data-ambient-player") === "v2") return;
    var audio = ambient.querySelector("audio") || document.getElementById("aulos-ambient");
    if (!audio) return;
    var origin = ambient.getAttribute("data-origin-src") || "";
    if (!origin) {
      var s = audio.querySelector("source");
      origin = (s && s.getAttribute("src")) || audio.getAttribute("src") || "";
    }
    if (!origin || origin.indexOf("/v1/media/") === 0) return;
    if (origin.indexOf("http") !== 0) return;
    ambient.setAttribute("data-failover-wired", "1");
    if (!ambient.getAttribute("data-origin-src")) ambient.setAttribute("data-origin-src", origin);
    if (!ambient.getAttribute("data-cache-src")) {
      ambient.setAttribute("data-cache-src", "/v1/media/audio?src=" + encodeSrc(origin) + "&mode=cache");
    }
    if (!ambient.getAttribute("data-proxy-src")) {
      ambient.setAttribute("data-proxy-src", "/v1/media/audio?src=" + encodeSrc(origin) + "&mode=proxy");
    }
    if (ambient.getAttribute("data-ambient-failover-ready") === "1") return;
    // If the page already ships the new player script, skip duplicate wiring.
    if (audio.getAttribute("data-active-tier")) {
      ambient.setAttribute("data-ambient-failover-ready", "1");
      return;
    }
    var originSrc = ambient.getAttribute("data-origin-src");
    var cacheSrc = ambient.getAttribute("data-cache-src");
    var proxySrc = ambient.getAttribute("data-proxy-src");
    var tiers = ["cache", "proxy", "origin"];
    var idx = 0;
    var key = "aulos_ambient_tier:" + originSrc;
    try {
      var saved = localStorage.getItem(key);
      if (saved === "proxy") idx = 1;
      else if (saved === "origin") idx = 2;
      else idx = 0;
    } catch (e) {}
    var stallTimer = null;
    var busy = false;
    function urlFor(i) {
      if (tiers[i] === "cache") return cacheSrc;
      if (tiers[i] === "proxy") return proxySrc;
      return originSrc;
    }
    function apply(i) {
      idx = i;
      var src = resolveUrl(urlFor(idx));
      if (!src) return;
      while (audio.firstChild) audio.removeChild(audio.firstChild);
      audio.removeAttribute("src");
      audio.src = src;
      audio.setAttribute("data-active-tier", tiers[idx]);
      try { audio.load(); } catch (e) {}
    }
    function remember() {
      try { localStorage.setItem(key, tiers[idx]); } catch (e) {}
    }
    function clearStall() {
      if (stallTimer) { clearTimeout(stallTimer); stallTimer = null; }
    }
    function watch() {
      clearStall();
      var last = audio.currentTime || 0;
      stallTimer = setTimeout(function () {
        if (!audio.paused && (audio.currentTime || 0) <= last + 0.05 && !audio.ended) failover("stall");
      }, 4500);
    }
    function failover(reason) {
      if (busy || idx >= tiers.length - 1) return;
      busy = true;
      clearStall();
      var playing = !audio.paused;
      var t = audio.currentTime || 0;
      apply(idx + 1);
      remember();
      audio.addEventListener("loadedmetadata", function onMeta() {
        audio.removeEventListener("loadedmetadata", onMeta);
        try { if (t > 0 && isFinite(t)) audio.currentTime = t; } catch (e) {}
        busy = false;
        if (playing) {
          var p = audio.play();
          if (p && p.catch) p.catch(function () {});
        }
      });
      setTimeout(function () { busy = false; }, 1200);
    }
    apply(idx);
    audio.addEventListener("error", function () { failover("error"); });
    audio.addEventListener("stalled", function () { failover("stalled"); });
    audio.addEventListener("waiting", watch);
    audio.addEventListener("playing", function () { remember(); clearStall(); watch(); });
    audio.addEventListener("play", watch);
    audio.addEventListener("pause", clearStall);
    ambient.setAttribute("data-ambient-failover-ready", "1");
  }
  function boot() {
    document.querySelectorAll(".ambient").forEach(wire);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
  setTimeout(boot, 300);
})();
</script>
"""


def harden_public_guide_html(html: str) -> str:
    """Patch stored public guides at serve time — no recompose needed for chrome/style."""
    out = html.replace('loading="lazy"', 'loading="eager"')
    if "referrerpolicy=" not in out and "<img " in out:
        out = out.replace(
            "<img ",
            '<img decoding="async" fetchpriority="high" referrerpolicy="no-referrer" ',
            1,
        )
    if "aulos-mobile-harden" not in out and "</head>" in out:
        out = out.replace("</head>", _MOBILE_CSS_PATCH + "</head>", 1)
    if "aulos-share-chrome" not in out and "</body>" in out:
        out = out.replace("</body>", _SHARE_CHROME_PATCH + "</body>", 1)
    elif "aulos-share-chrome" not in out and "</html>" in out:
        out = out.replace("</html>", _SHARE_CHROME_PATCH + "</html>", 1)
    # Float + prefer-cache patch can land on guides that already have an older share-chrome block.
    if "aulos-ambient-float-live" not in out:
        float_patch = (
            '<style id="aulos-ambient-float-live">'
            ".wrap{padding-bottom:7.5rem!important}"
            ".ambient{position:fixed!important;z-index:60!important;right:0.75rem!important;"
            "bottom:0.75rem!important;left:auto!important;"
            "width:min(22.5rem,calc(100vw - 1.5rem))!important;margin:0!important;"
            "max-height:min(72vh,30rem)!important;display:flex!important;flex-direction:column!important;"
            "background:rgba(16,22,27,0.92)!important;backdrop-filter:blur(12px);"
            "box-shadow:0 12px 36px rgba(0,0,0,0.45)}"
            ".ambient .ambient-details{overflow:auto;flex:1 1 auto;min-height:0}"
            "@media (max-width:719px){.ambient{right:0.5rem!important;left:0.5rem!important;"
            "bottom:0.5rem!important;width:auto!important;max-height:min(60vh,24rem)!important}"
            ".wrap{padding-bottom:6.5rem!important}}"
            "</style>"
            '<script id="aulos-prefer-cache-live">'
            "(function(){function nudge(){document.querySelectorAll('.ambient[data-cache-src]').forEach(function(amb){"
            "var cache=amb.getAttribute('data-cache-src');var origin=amb.getAttribute('data-origin-src')||'';"
            "if(!cache)return;try{localStorage.setItem('aulos_ambient_tier:'+origin,'cache');}catch(e){}"
            "var audio=amb.querySelector('audio');if(!audio||!audio.paused)return;"
            "var tier=audio.getAttribute('data-active-tier');if(tier==='cache'||tier==='proxy')return;"
            "try{audio.src=new URL(cache,location.href).href;audio.setAttribute('data-active-tier','cache');audio.load();}catch(e){}"
            "});}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(nudge,50);});"
            "else setTimeout(nudge,50);setTimeout(nudge,400);})();"
            "</script>"
        )
        if "</body>" in out:
            out = out.replace("</body>", float_patch + "</body>", 1)
        elif "</html>" in out:
            out = out.replace("</html>", float_patch + "</html>", 1)
    return out


def harden_guide_html(html: str) -> str:
    """Backward-compatible alias."""
    return harden_public_guide_html(html)


_DANGEROUS_SCHEME = re.compile(
    r"""(?ix)
    (\b(?:href|src|action|formaction|xlink:href)\s*=\s*)
    (['"])\s*(?:javascript|vbscript|data\s*:\s*text\s*/\s*html)[^'"]*\2
    """
)

_EVENT_HANDLER = re.compile(
    r"""(?ix)\s+on[a-z]+\s*=\s*(?:'[^']*'|"[^"]*"|[^\s>]+)"""
)


def sanitize_guide_html(html: str) -> str:
    """Neutralize dangerous URL schemes and inline event handlers in guide HTML.

    Intentional ambient/share scripts injected by harden_public_guide_html remain;
    dossier-sourced javascript: links and on* handlers are stripped.
    """
    out = html or ""
    out = _DANGEROUS_SCHEME.sub(r"\1\2#\2", out)
    out = _EVENT_HANDLER.sub("", out)
    return out


def prepare_public_guide_html(html: str) -> str:
    """Sanitize then apply public share chrome patches."""
    return harden_public_guide_html(sanitize_guide_html(html))
