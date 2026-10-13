(function () {
  let activeMode = "ORIGINAL";
  let showEdges = true;
  let isFrozen = false;
  let cursorXRatio = 0.51;
  let cursorYRatio = 0.65;
  let lastTelemetry = null;

  function initClock() {
    const clockEl = document.getElementById("digital-clock");
    function tick() {
      const d = new Date();
      const hh = String(d.getHours()).padStart(2, "0");
      const mm = String(d.getMinutes()).padStart(2, "0");
      const ss = String(d.getSeconds()).padStart(2, "0");
      if (clockEl) {
        clockEl.textContent = `${hh}:${mm}:${ss}`;
      }
    }
    tick();
    setInterval(tick, 1000);
  }

  function initLedBar() {
    const bar = document.getElementById("led-confidence-bar");
    if (!bar) return;
    bar.innerHTML = "";
    for (let i = 0; i < 24; i++) {
      const seg = document.createElement("div");
      seg.className = "led-seg lit";
      seg.dataset.index = i;
      bar.appendChild(seg);
    }
  }

  function setConfidencePct(pct) {
    const bar = document.getElementById("led-confidence-bar");
    const label = document.getElementById("conf-pct");
    if (label) {
      label.textContent = `${Math.round(pct)}% GOOD`;
    }
    if (!bar) return;
    const segs = bar.querySelectorAll(".led-seg");
    const litCount = Math.round((pct / 100) * segs.length);
    segs.forEach((seg, idx) => {
      if (idx < litCount) {
        seg.classList.add("lit");
      } else {
        seg.classList.remove("lit");
      }
    });
  }

  function initTabs() {
    const tabBtns = document.querySelectorAll(".mode-tab");
    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        tabBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeMode = btn.dataset.mode;
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_view_mode) {
          window.pywebview.api.set_view_mode(activeMode);
        }
      });
    });

    const btnEdges = document.getElementById("btn-toggle-edges");
    if (btnEdges) {
      btnEdges.addEventListener("click", () => {
        showEdges = !showEdges;
        btnEdges.classList.toggle("active", showEdges);
        if (window.pywebview && window.pywebview.api && window.pywebview.api.toggle_edges) {
          window.pywebview.api.toggle_edges(showEdges);
        }
      });
    }

    const btnFreeze = document.getElementById("btn-toggle-freeze");
    if (btnFreeze) {
      btnFreeze.addEventListener("click", () => {
        isFrozen = !isFrozen;
        btnFreeze.classList.toggle("active", isFrozen);
        if (window.pywebview && window.pywebview.api && window.pywebview.api.toggle_freeze) {
          window.pywebview.api.toggle_freeze(isFrozen);
        }
      });
    }

    const btnFullscreen = document.getElementById("btn-toggle-fullscreen");
    if (btnFullscreen) {
      btnFullscreen.addEventListener("click", () => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.toggle_fullscreen) {
          window.pywebview.api.toggle_fullscreen();
        }
      });
    }
  }

  function initMouseInspection() {
    const wrapper = document.getElementById("video-wrapper");
    const tooltip = document.getElementById("caliper-tooltip");

    if (!wrapper) return;

    wrapper.addEventListener("mousemove", (e) => {
      const rect = wrapper.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      cursorXRatio = Math.max(0, Math.min(1, x / rect.width));
      cursorYRatio = Math.max(0, Math.min(1, y / rect.height));

      if (tooltip) {
        tooltip.style.display = "block";
        const maxTipX = rect.width - 220;
        const tipX = Math.min(maxTipX, Math.max(10, x + 14));
        const tipY = Math.min(rect.height - 80, Math.max(30, y));
        tooltip.style.left = `${tipX}px`;
        tooltip.style.top = `${tipY}px`;
      }

      updateCaliperOverlay();
      renderProfileChart(lastTelemetry);

      const pxX = Math.round(cursorXRatio * 1920);
      const pxY = Math.round(cursorYRatio * 1080);
      const label = document.getElementById("cursor-pos-label");
      if (label) label.textContent = `CURSOR X: ${pxX} px`;

      if (window.pywebview && window.pywebview.api && window.pywebview.api.set_cursor) {
        window.pywebview.api.set_cursor(pxX, pxY);
      }
    });

    wrapper.addEventListener("mouseleave", () => {
      if (tooltip) tooltip.style.display = "none";
    });
  }

  function updateCaliperOverlay() {
    const svg = document.getElementById("caliper-overlay");
    const wrapper = document.getElementById("video-wrapper");
    if (!svg || !wrapper) return;

    const w = wrapper.clientWidth;
    const h = wrapper.clientHeight;
    const cx = cursorXRatio * w;

    const topRatio = 0.50;
    const botRatio = 0.79;
    const topY = topRatio * h;
    const botY = botRatio * h;

    svg.innerHTML = `
      <rect x="${w * 0.08}" y="${h * 0.04}" width="${w * 0.81}" height="${h * 0.81}" fill="none" stroke="#00d7ff" stroke-width="1.5" stroke-dasharray="6 4"/>
      <line x1="${cx}" y1="${h * 0.04}" x2="${cx}" y2="${h * 0.85}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4 4"/>
      <line x1="${cx}" y1="${topY}" x2="${cx}" y2="${botY}" stroke="#eab308" stroke-width="2.5"/>
      <circle cx="${cx}" cy="${topY}" r="4" fill="#00d7ff"/>
      <circle cx="${cx}" cy="${botY}" r="4" fill="#00d7ff"/>
    `;

    const ttX = document.getElementById("tt-x");
    const ttY = document.getElementById("tt-y");
    if (ttX) ttX.textContent = Math.round(cursorXRatio * 1920);
    if (ttY) ttY.textContent = Math.round(cursorYRatio * 1080);
  }

  function renderProfileChart(data) {
    const canvas = document.getElementById("profile-chart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    const padLeft = 40;
    const padRight = 20;
    const padTop = 15;
    const padBottom = 25;
    const plotW = w - padLeft - padRight;
    const plotH = h - padTop - padBottom;

    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 3; i++) {
      const y = padTop + (plotH / 3) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(w - padRight, y);
      ctx.stroke();

      const val = 300 - i * 100;
      ctx.fillStyle = "#94a3b8";
      ctx.font = "10px sans-serif";
      ctx.fillText(`${val}`, 12, y + 3);
    }

    const targetY = padTop + plotH * (1.0 - 108.6 / 300);
    ctx.strokeStyle = "#94a3b8";
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(padLeft, targetY);
    ctx.lineTo(w - padRight, targetY);
    ctx.stroke();

    const upperY = padTop + plotH * (1.0 - 145 / 300);
    const lowerY = padTop + plotH * (1.0 - 80 / 300);
    ctx.strokeStyle = "#ef4444";
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(padLeft, upperY);
    ctx.lineTo(w - padRight, upperY);
    ctx.moveTo(padLeft, lowerY);
    ctx.lineTo(w - padRight, lowerY);
    ctx.stroke();
    ctx.setLineDash([]);

    const profile = (data && data.profile && data.profile.length > 0) ? data.profile : null;
    ctx.strokeStyle = "#0f4c81";
    ctx.lineWidth = 2.5;
    ctx.beginPath();

    const steps = 120;
    for (let i = 0; i <= steps; i++) {
      const r = i / steps;
      const px = padLeft + r * plotW;
      let valMm = 108.6;
      if (profile) {
        const pIdx = Math.floor(r * (profile.length - 1));
        valMm = profile[pIdx];
      } else {
        valMm = 108.6 + Math.sin(r * Math.PI * 4) * 2.5;
      }
      const py = padTop + plotH * Math.max(0, Math.min(1, 1.0 - valMm / 300));
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    const curPx = padLeft + cursorXRatio * plotW;
    let curMm = 108.6;
    if (profile) {
      const pIdx = Math.floor(cursorXRatio * (profile.length - 1));
      curMm = profile[pIdx];
    }
    const curPy = padTop + plotH * (1.0 - curMm / 300);
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(curPx, curPy, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#0f4c81";
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  window.updateTelemetry = function (payload) {
    if (!payload) return;
    lastTelemetry = payload;

    if (payload.frame_b64) {
      const img = document.getElementById("video-stream");
      if (img) {
        img.src = `data:image/jpeg;base64,${payload.frame_b64}`;
      }
    }

    if (payload.thickness_mm !== undefined) {
      const el = document.getElementById("readout-mm");
      if (el) el.textContent = payload.thickness_mm.toFixed(1);
      const ttMm = document.getElementById("tt-mm");
      if (ttMm) ttMm.textContent = payload.thickness_mm.toFixed(1);
      const pCur = document.getElementById("prof-cur");
      if (pCur) pCur.textContent = `${payload.thickness_mm.toFixed(1)} mm`;
    }

    if (payload.thickness_px !== undefined) {
      const el = document.getElementById("readout-px");
      if (el) el.textContent = `${payload.thickness_px.toFixed(1)} px`;
      const ttPx = document.getElementById("tt-px");
      if (ttPx) ttPx.textContent = payload.thickness_px.toFixed(1);
    }

    if (payload.min_mm !== undefined) {
      const el = document.getElementById("stat-min");
      if (el) el.textContent = `${payload.min_mm.toFixed(1)} mm`;
      const pMin = document.getElementById("prof-min");
      if (pMin) pMin.textContent = payload.min_mm.toFixed(1);
    }

    if (payload.max_mm !== undefined) {
      const el = document.getElementById("stat-max");
      if (el) el.textContent = `${payload.max_mm.toFixed(1)} mm`;
      const pMax = document.getElementById("prof-max");
      if (pMax) pMax.textContent = payload.max_mm.toFixed(1);
    }

    if (payload.avg_mm !== undefined) {
      const el = document.getElementById("stat-avg");
      if (el) el.textContent = `${payload.avg_mm.toFixed(1)} mm`;
      const pAvg = document.getElementById("prof-avg");
      if (pAvg) pAvg.textContent = payload.avg_mm.toFixed(1);
    }

    if (payload.std_dev_mm !== undefined) {
      const el = document.getElementById("stat-std");
      if (el) el.textContent = `${payload.std_dev_mm.toFixed(2)} mm`;
      const pStd = document.getElementById("prof-std");
      if (pStd) pStd.textContent = payload.std_dev_mm.toFixed(2);
    }

    if (payload.is_normal !== undefined) {
      const banner = document.getElementById("spec-status-banner");
      const badge = document.getElementById("badge-status");
      if (banner) {
        banner.className = payload.is_normal ? "status-banner banner-normal" : "status-banner banner-alert";
        banner.textContent = payload.is_normal ? "\u2022 NORMAL" : "\u2022 OUT OF SPEC";
      }
      if (badge) {
        badge.textContent = payload.is_normal ? "\u2022 NORMAL" : "\u2022 OUT OF SPEC";
        badge.className = payload.is_normal ? "pill-badge pill-status" : "pill-badge pill-alert";
      }
    }

    if (payload.confidence_pct !== undefined) {
      setConfidencePct(payload.confidence_pct);
    }

    if (payload.fps !== undefined) {
      const el = document.getElementById("status-fps");
      if (el) el.textContent = payload.fps.toFixed(1);
    }

    if (payload.processing_ms !== undefined) {
      const el = document.getElementById("status-proc");
      if (el) el.textContent = `${Math.round(payload.processing_ms)} ms`;
    }

    if (payload.calibration !== undefined) {
      const el = document.getElementById("calib-mm-px");
      if (el) el.textContent = `${payload.calibration.toFixed(5)} mm/px`;
      const elStat = document.getElementById("status-calib");
      if (elStat) elStat.textContent = `${payload.calibration.toFixed(5)} mm/px`;
    }

    renderProfileChart(payload);
  };

  function startPolling() {
    async function poll() {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.get_telemetry) {
        try {
          const data = await window.pywebview.api.get_telemetry();
          if (data) {
            window.updateTelemetry(data);
          }
        } catch (e) {}
      }
      setTimeout(poll, 30);
    }
    poll();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initClock();
    initLedBar();
    initTabs();
    initMouseInspection();
    updateCaliperOverlay();
    renderProfileChart(null);
    window.addEventListener("pywebviewready", startPolling);
    if (window.pywebview && window.pywebview.api) {
      startPolling();
    } else {
      setTimeout(startPolling, 500);
    }
  });
})();
