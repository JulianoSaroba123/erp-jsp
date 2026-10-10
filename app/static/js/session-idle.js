/* ERP JSP | Inatividade de sessao: apenas interacao humana renova o login. */
(() => {
  "use strict";
  const cfg = window.jspIdleConfig;
  if (!cfg || !cfg.csrf || !cfg.pingUrl || !cfg.expiresAt) return;

  const dialog = document.getElementById("jsp-idle-dialog");
  const countdown = document.getElementById("jsp-idle-countdown");
  const keepButton = document.getElementById("jsp-idle-keep");
  const idleSeconds = 1800;
  const warnSeconds = 120;
  const pingInterval = 45000;
  let expiresAt = Number(cfg.expiresAt) * 1000;
  let lastPing = Date.now();
  let busy = false;
  let ended = false;
  let channel = null;

  try {
    if (typeof BroadcastChannel !== "undefined") {
      channel = new BroadcastChannel("jsp-idle-session");
      channel.addEventListener("message", (event) => {
        if (!event.data || !event.data.action) return;
        if (event.data.action === "logout") endSession(false);
        if (event.data.action === "renewed") {
          expiresAt = Math.max(expiresAt, Number(event.data.expiresAt) || 0);
          lastPing = Date.now();
          tick();
        }
      });
    }
  } catch (_) {
    channel = null;
  }

  function endSession(broadcast = true) {
    if (ended) return;
    ended = true;
    if (broadcast && channel) channel.postMessage({ action: "logout" });
    window.location.replace(cfg.loginUrl + "?inatividade=1");
  }

  function tick() {
    if (ended) return;
    const seconds = Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000));
    if (seconds <= 0) return endSession();
    const show = seconds <= warnSeconds;
    if (dialog) dialog.hidden = !show;
    if (show && countdown) {
      const minutes = Math.floor(seconds / 60);
      countdown.textContent = String(minutes).padStart(2, "0") +
        ":" + String(seconds % 60).padStart(2, "0");
    }
  }

  async function renew() {
    if (busy || ended || Date.now() >= expiresAt) {
      tick();
      return;
    }
    busy = true;
    lastPing = Date.now();
    try {
      const response = await fetch(cfg.pingUrl, {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        headers: {
          "X-JSP-Idle-CSRF": cfg.csrf,
          "Accept": "application/json"
        }
      });
      if (response.status === 401) return endSession();
      if (!response.ok) return;
      const data = await response.json();
      if (!data.ok || !Number.isFinite(Number(data.expires_at))) {
        return endSession();
      }
      expiresAt = Number(data.expires_at) * 1000;
      if (channel) channel.postMessage({ action: "renewed", expiresAt });
      tick();
    } catch (_) {
      // Sem rede, nao prolongar o prazo artificialmente.
    } finally {
      busy = false;
    }
  }

  function userActivity(event) {
    if (ended || !event.isTrusted) return;
    if (document.visibilityState !== "visible" || !document.hasFocus()) return;
    if (Date.now() - lastPing >= pingInterval) renew();
  }

  ["pointerdown", "keydown", "input", "touchstart", "wheel", "scroll"].forEach(
    (type) => document.addEventListener(type, userActivity, { passive: true })
  );

  if (keepButton) {
    keepButton.addEventListener("click", () => renew());
  }

  // Retorno ao historico nao pode mostrar uma tela autenticada do cache.
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) window.location.reload();
  });
  document.addEventListener("visibilitychange", tick);
  window.addEventListener("focus", tick);
  setInterval(tick, 1000);
  tick();
})();
