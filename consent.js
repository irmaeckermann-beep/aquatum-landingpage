/* Cookie-Consent + Facebook-Pixel (Opt-in).
 * Der Pixel wird AUSSCHLIESSLICH nach aktiver Einwilligung geladen.
 * Solange PIXEL_ID leer ist, erscheint KEIN Banner und es werden KEINE
 * Cookies gesetzt – die Seite verhaelt sich wie ohne Tracking. */
(function () {
  // === Facebook-Pixel-ID hier eintragen (15–16 Ziffern). Leer = inaktiv. ===
  var PIXEL_ID = "";

  var settingsLinks = document.querySelectorAll(".js-cookie-settings");

  // Solange kein Pixel konfiguriert ist: Cookie-Einstellungen-Link ausblenden,
  // kein Banner, keine Cookies.
  if (!PIXEL_ID) {
    settingsLinks.forEach(function (a) { a.style.display = "none"; });
    return;
  }

  var STORAGE_KEY = "aquatum_consent_v1";
  var choice = null;
  try { choice = localStorage.getItem(STORAGE_KEY); } catch (e) {}

  var bannerEl = null;

  function removeBanner() {
    if (bannerEl && bannerEl.parentNode) bannerEl.parentNode.removeChild(bannerEl);
    bannerEl = null;
  }

  function loadPixel() {
    if (window._aqPixelLoaded) return;
    window._aqPixelLoaded = true;
    !function (f, b, e, v, n, t, s) {
      if (f.fbq) return; n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      }; if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = "2.0";
      n.queue = []; t = b.createElement(e); t.async = !0; t.src = v;
      s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
    }(window, document, "script", "https://connect.facebook.net/en_US/fbevents.js");
    window.fbq("init", PIXEL_ID);
    window.fbq("track", "PageView");
  }

  function grant() {
    try { localStorage.setItem(STORAGE_KEY, "granted"); } catch (e) {}
    removeBanner();
    loadPixel();
  }

  function deny() {
    try { localStorage.setItem(STORAGE_KEY, "denied"); } catch (e) {}
    removeBanner();
  }

  // Erneut-Aufrufen ermoeglichen (Footer-Link "Cookie-Einstellungen")
  window.aquatumCookieSettings = function () {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
    if (!bannerEl) showBanner();
  };
  settingsLinks.forEach(function (a) {
    a.addEventListener("click", function (ev) {
      ev.preventDefault();
      window.aquatumCookieSettings();
    });
  });

  function showBanner() {
    bannerEl = document.createElement("div");
    bannerEl.className = "cookie-banner";
    bannerEl.setAttribute("role", "dialog");
    bannerEl.setAttribute("aria-label", "Cookie-Einwilligung");
    bannerEl.innerHTML =
      '<div class="cookie-banner-inner">' +
        '<p class="cookie-banner-text">Wir verwenden Cookies und den Facebook-Pixel, um die Wirksamkeit unserer Werbung zu messen. Diese werden nur mit Ihrer Einwilligung gesetzt. Mehr dazu in der <a href="datenschutz.html">Datenschutzerklärung</a>.</p>' +
        '<div class="cookie-banner-actions">' +
          '<button type="button" class="cb-btn cb-decline" data-consent="deny">Ablehnen</button>' +
          '<button type="button" class="cb-btn cb-accept" data-consent="grant">Akzeptieren</button>' +
        '</div>' +
      "</div>";
    bannerEl.querySelector('[data-consent="grant"]').addEventListener("click", grant);
    bannerEl.querySelector('[data-consent="deny"]').addEventListener("click", deny);
    document.body.appendChild(bannerEl);
  }

  if (choice === "granted") {
    loadPixel();
  } else if (choice === "denied") {
    /* nichts laden */
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", showBanner);
  } else {
    showBanner();
  }
})();
