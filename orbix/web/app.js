(function () {
  let activeMode = "ORIGINAL";
  let showEdges = true;
  let isFrozen = false;
  let cursorXRatio = 0.47;
  let cursorYRatio = 0.55;
  let lastTelemetry = null;
  let activeRoi = { x: 150, y: 39, w: 1549, h: 870 };
  let isSelectingRoi = false;
  let roiDragStart = null;
  let tempRoi = null;

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

  function initThemeSystem() {
    const savedTheme = localStorage.getItem("orbix_theme") || "dark";
    applyTheme(savedTheme);

    const toggleChk = document.getElementById("theme-toggle-chk");
    if (toggleChk) {
      toggleChk.checked = (savedTheme === "dark");
      toggleChk.addEventListener("change", (e) => {
        const nextTheme = e.target.checked ? "dark" : "light";
        applyTheme(nextTheme);
        localStorage.setItem("orbix_theme", nextTheme);
      });
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    const statusText = document.getElementById("theme-status-text");
    if (statusText) {
      statusText.textContent = (theme === "dark") ? "Dark" : "Light";
    }
    const toggleChk = document.getElementById("theme-toggle-chk");
    if (toggleChk) {
      toggleChk.checked = (theme === "dark");
    }
    renderProfileChart(lastTelemetry);
  }

  function initSettingsDropdown() {
    const btnSettings = document.getElementById("btn-settings");
    const dropdown = document.getElementById("settings-dropdown");
    if (!btnSettings || !dropdown) return;

    btnSettings.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdown.classList.toggle("show");
    });

    document.addEventListener("click", (e) => {
      if (!dropdown.contains(e.target) && e.target !== btnSettings) {
        dropdown.classList.remove("show");
      }
    });

    const itemHelp = document.getElementById("item-help");
    if (itemHelp) {
      itemHelp.addEventListener("click", () => {
        dropdown.classList.remove("show");
      });
    }

    const itemAbout = document.getElementById("item-about");
    if (itemAbout) {
      itemAbout.addEventListener("click", () => {
        dropdown.classList.remove("show");
      });
    }
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

  function setConfidencePct(pct, isValid) {
    const bar = document.getElementById("led-confidence-bar");
    const label = document.getElementById("conf-pct");
    const rounded = Math.round(pct);
    if (label) {
      if (!isValid || rounded < 40) {
        label.textContent = `${rounded}% LOW`;
        label.style.color = "var(--red-alert)";
      } else if (rounded < 75) {
        label.textContent = `${rounded}% FAIR`;
        label.style.color = "var(--amber-warn)";
      } else {
        label.textContent = `${rounded}% GOOD`;
        label.style.color = "var(--green-success)";
      }
    }
    if (!bar) return;
    const segs = bar.querySelectorAll(".led-seg");
    const litCount = Math.round((pct / 100) * segs.length);
    segs.forEach((seg, idx) => {
      seg.className = "led-seg";
      if (idx < litCount) {
        if (!isValid || pct < 40) {
          seg.classList.add("lit-danger");
        } else if (pct < 75) {
          seg.classList.add("lit-warn");
        } else {
          seg.classList.add("lit");
        }
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

    initSourceButtons();
    initOperationButtons();
    initLimitsSync();
  }

  function initSourceButtons() {
    const btnOpenVid = document.getElementById("btn-open-video");
    if (btnOpenVid) {
      btnOpenVid.addEventListener("click", () => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.open_video_dialog) {
          window.pywebview.api.open_video_dialog().then((res) => {
            if (res && res.filename) {
              updateSourceDisplay(res.filename);
            }
          });
        }
      });
    }

    const btnOpenImg = document.getElementById("btn-open-image");
    if (btnOpenImg) {
      btnOpenImg.addEventListener("click", () => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.open_image_dialog) {
          window.pywebview.api.open_image_dialog().then((res) => {
            if (res && res.filename) {
              updateSourceDisplay(res.filename);
            }
          });
        }
      });
    }

    const btnSampleVid = document.getElementById("btn-sample-video");
    if (btnSampleVid) {
      btnSampleVid.addEventListener("click", () => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.load_sample_video) {
          window.pywebview.api.load_sample_video().then((res) => {
            if (res && res.filename) {
              updateSourceDisplay(res.filename);
            }
          });
        }
      });
    }

    const btnSampleImg = document.getElementById("btn-sample-image");
    if (btnSampleImg) {
      btnSampleImg.addEventListener("click", () => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.load_sample_image) {
          window.pywebview.api.load_sample_image().then((res) => {
            if (res && res.filename) {
              updateSourceDisplay(res.filename);
            }
          });
        }
      });
    }

    const btnConnect = document.getElementById("btn-connect");
    const inputRtsp = document.getElementById("rtsp-input");
    if (btnConnect && inputRtsp) {
      btnConnect.addEventListener("click", () => {
        const val = inputRtsp.value.trim();
        if (val && window.pywebview && window.pywebview.api && window.pywebview.api.connect_camera) {
          window.pywebview.api.connect_camera(val).then((res) => {
            if (res && res.source) {
              updateSourceDisplay(res.source);
            }
          });
        }
      });
    }
  }

  function updateSourceDisplay(name) {
    const fn = document.getElementById("source-filename");
    if (fn) fn.textContent = name;
    const sfn = document.getElementById("status-source-name");
    if (sfn) sfn.textContent = `Playing ${name}`;
  }

  function initLimitsSync() {
    const targetIn = document.getElementById("lim-target-input");
    const lowerIn = document.getElementById("lim-lower-input");
    const upperIn = document.getElementById("lim-upper-input");

    function pushLimits() {
      const t = parseFloat(targetIn ? targetIn.value : 174.0) || 174.0;
      const l = parseFloat(lowerIn ? lowerIn.value : 10.0) || 10.0;
      const u = parseFloat(upperIn ? upperIn.value : 300.0) || 300.0;
      if (window.pywebview && window.pywebview.api && window.pywebview.api.set_limits) {
        window.pywebview.api.set_limits(t, l, u);
      }
    }

    if (targetIn) targetIn.addEventListener("change", pushLimits);
    if (lowerIn) lowerIn.addEventListener("change", pushLimits);
    if (upperIn) upperIn.addEventListener("change", pushLimits);
  }

  function initOperationButtons() {
    const btnStart = document.getElementById("btn-start-meas");
    if (btnStart) {
      let measuring = true;
      btnStart.addEventListener("click", () => {
        measuring = !measuring;
        btnStart.textContent = measuring ? "\u25b6 START MEASUREMENT" : "\u25a0 STOP MEASUREMENT";
        btnStart.className = measuring ? "btn btn-success btn-block" : "btn btn-outline btn-block";
        if (window.pywebview && window.pywebview.api && window.pywebview.api.start_measurement) {
          window.pywebview.api.start_measurement();
        }
      });
    }

    const btnCap = document.getElementById("btn-capture");
    if (btnCap) {
      btnCap.addEventListener("click", () => {
        const origText = btnCap.textContent;
        btnCap.textContent = "\u2714 CAPTURED!";
        setTimeout(() => { btnCap.textContent = origText; }, 1200);
        if (window.pywebview && window.pywebview.api && window.pywebview.api.capture_image) {
          window.pywebview.api.capture_image();
        }
      });
    }

    const btnRep = document.getElementById("btn-report");
    if (btnRep) {
      btnRep.addEventListener("click", () => {
        const origText = btnRep.textContent;
        btnRep.textContent = "\u2714 EXPORTED!";
        setTimeout(() => { btnRep.textContent = origText; }, 1200);
        if (window.pywebview && window.pywebview.api && window.pywebview.api.generate_report) {
          window.pywebview.api.generate_report();
        }
      });
    }
  }

  function updateRoiDisplay(roi) {
    if (!roi) return;
    const elX = document.getElementById("roi-x-val");
    const elY = document.getElementById("roi-y-val");
    const elW = document.getElementById("roi-w-val");
    const elH = document.getElementById("roi-h-val");
    const elArea = document.getElementById("roi-area-val");
    const elChip = document.getElementById("roi-chip-label");

    if (elX) elX.textContent = `${roi.x} px`;
    if (elY) elY.textContent = `${roi.y} px`;
    if (elW) elW.textContent = `${roi.w} px`;
    if (elH) elH.textContent = `${roi.h} px`;
    if (elArea) elArea.innerHTML = `${(roi.w * roi.h).toLocaleString()} px&sup2;`;
    if (elChip) elChip.innerHTML = `ROI 1: ${roi.w} &times; ${roi.h} @ (${roi.x}, ${roi.y})`;
  }

  function initRoiControls() {
    const btnSelect = document.getElementById("btn-select-roi");
    const btnConfirm = document.getElementById("btn-confirm-roi");
    const btnFull = document.getElementById("btn-roi-full");
    const btnDel = document.getElementById("btn-roi-del");
    const btnAdd = document.getElementById("btn-roi-add");
    const wrapper = document.getElementById("video-wrapper");

    if (btnSelect) {
      btnSelect.addEventListener("click", () => {
        isSelectingRoi = !isSelectingRoi;
        btnSelect.classList.toggle("active-selecting", isSelectingRoi);
        if (wrapper) wrapper.classList.toggle("selecting-roi", isSelectingRoi);
        if (isSelectingRoi) {
          const tooltip = document.getElementById("caliper-tooltip");
          if (tooltip) tooltip.style.display = "none";
        }
      });
    }

    if (btnConfirm) {
      btnConfirm.addEventListener("click", () => {
        isSelectingRoi = false;
        if (btnSelect) btnSelect.classList.remove("active-selecting");
        if (wrapper) wrapper.classList.remove("selecting-roi");
        if (tempRoi) {
          activeRoi = { ...tempRoi };
          tempRoi = null;
        }
        updateRoiDisplay(activeRoi);
        updateCaliperOverlay();
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_roi) {
          window.pywebview.api.set_roi(activeRoi.x, activeRoi.y, activeRoi.w, activeRoi.h);
        }
        const orig = btnConfirm.innerHTML;
        btnConfirm.innerHTML = "&#10004; CONFIRMED!";
        setTimeout(() => { btnConfirm.innerHTML = orig; }, 1200);
      });
    }

    if (btnFull) {
      btnFull.addEventListener("click", () => {
        activeRoi = { x: 0, y: 0, w: 1920, h: 1080 };
        tempRoi = null;
        updateRoiDisplay(activeRoi);
        updateCaliperOverlay();
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_roi) {
          window.pywebview.api.set_roi(0, 0, 1920, 1080);
        }
      });
    }

    if (btnDel) {
      btnDel.addEventListener("click", () => {
        activeRoi = { x: 0, y: 0, w: 1920, h: 1080 };
        tempRoi = null;
        updateRoiDisplay(activeRoi);
        updateCaliperOverlay();
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_roi) {
          window.pywebview.api.set_roi(0, 0, 1920, 1080);
        }
      });
    }

    if (btnAdd) {
      btnAdd.addEventListener("click", () => {
        activeRoi = { x: 240, y: 135, w: 1440, h: 810 };
        tempRoi = null;
        updateRoiDisplay(activeRoi);
        updateCaliperOverlay();
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_roi) {
          window.pywebview.api.set_roi(activeRoi.x, activeRoi.y, activeRoi.w, activeRoi.h);
        }
      });
    }
  }

  function initMouseInspection() {
    const wrapper = document.getElementById("video-wrapper");
    const tooltip = document.getElementById("caliper-tooltip");

    if (!wrapper) return;

    wrapper.addEventListener("mousedown", (e) => {
      if (!isSelectingRoi) return;
      const rect = wrapper.getBoundingClientRect();
      roiDragStart = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      tempRoi = null;
    });

    wrapper.addEventListener("mousemove", (e) => {
      const rect = wrapper.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      if (isSelectingRoi && roiDragStart) {
        const rx = Math.min(roiDragStart.x, x);
        const ry = Math.min(roiDragStart.y, y);
        const rw = Math.max(10, Math.abs(x - roiDragStart.x));
        const rh = Math.max(10, Math.abs(y - roiDragStart.y));

        const frameX = Math.round(Math.max(0, Math.min(1910, (rx / rect.width) * 1920)));
        const frameY = Math.round(Math.max(0, Math.min(1070, (ry / rect.height) * 1080)));
        const frameW = Math.round(Math.max(10, Math.min(1920 - frameX, (rw / rect.width) * 1920)));
        const frameH = Math.round(Math.max(10, Math.min(1080 - frameY, (rh / rect.height) * 1080)));

        tempRoi = { x: frameX, y: frameY, w: frameW, h: frameH };
        updateRoiDisplay(tempRoi);
        updateCaliperOverlay();
        return;
      }

      cursorXRatio = Math.max(0, Math.min(1, x / rect.width));
      cursorYRatio = Math.max(0, Math.min(1, y / rect.height));

      if (tooltip && !isSelectingRoi) {
        tooltip.style.display = "block";
        const maxTipX = rect.width - 230;
        const tipX = Math.min(maxTipX, Math.max(10, x + 16));
        const tipY = Math.min(rect.height - 90, Math.max(20, y - 20));
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

    window.addEventListener("mouseup", () => {
      if (isSelectingRoi && roiDragStart) {
        if (tempRoi) {
          activeRoi = { ...tempRoi };
          tempRoi = null;
        }
        roiDragStart = null;
        updateRoiDisplay(activeRoi);
        updateCaliperOverlay();
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_roi) {
          window.pywebview.api.set_roi(activeRoi.x, activeRoi.y, activeRoi.w, activeRoi.h);
        }
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

    const r = tempRoi || activeRoi;
    const rx = (r.x / 1920) * w;
    const ry = (r.y / 1080) * h;
    const rw = (r.w / 1920) * w;
    const rh = (r.h / 1080) * h;

    let topRatio = 0.33;
    let botRatio = 0.78;

    if (lastTelemetry && lastTelemetry.top_y !== undefined) {
      topRatio = Math.max(0, Math.min(1, lastTelemetry.top_y / 1080));
      botRatio = Math.max(0, Math.min(1, lastTelemetry.bottom_y / 1080));
    }

    const topY = topRatio * h;
    const botY = botRatio * h;

    svg.innerHTML = `
      <rect x="${rx}" y="${ry}" width="${rw}" height="${rh}" fill="rgba(0, 229, 255, 0.04)" stroke="#00e5ff" stroke-width="1.4" stroke-dasharray="6 4" opacity="0.85"/>
      <rect x="${rx - 3}" y="${ry - 3}" width="6" height="6" fill="#00e5ff"/>
      <rect x="${rx + rw - 3}" y="${ry - 3}" width="6" height="6" fill="#00e5ff"/>
      <rect x="${rx - 3}" y="${ry + rh - 3}" width="6" height="6" fill="#00e5ff"/>
      <rect x="${rx + rw - 3}" y="${ry + rh - 3}" width="6" height="6" fill="#00e5ff"/>
      <line x1="${cx}" y1="${ry}" x2="${cx}" y2="${ry + rh}" stroke="#555555" stroke-width="1" stroke-dasharray="3 3"/>
      <line x1="${cx}" y1="${topY}" x2="${cx}" y2="${botY}" stroke="#ffb703" stroke-width="2.5"/>
      <circle cx="${cx}" cy="${topY}" r="4.5" fill="#00e5ff" stroke="#000000" stroke-width="1.5"/>
      <circle cx="${cx}" cy="${botY}" r="4.5" fill="#00e5ff" stroke="#000000" stroke-width="1.5"/>
    `;

    const topLabel = document.getElementById("label-top-edge");
    const botLabel = document.getElementById("label-bot-edge");
    if (topLabel) {
      topLabel.style.left = `${Math.max(8, rx + 16)}px`;
      topLabel.style.top = `${Math.max(8, topY - 14)}px`;
    }
    if (botLabel) {
      botLabel.style.left = `${Math.max(8, rx + 16)}px`;
      botLabel.style.top = `${Math.min(h - 22, botY + 4)}px`;
    }
  }

  function renderProfileChart(data) {
    const canvas = document.getElementById("profile-chart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (canvas.clientWidth && (canvas.width !== canvas.clientWidth || canvas.height !== canvas.clientHeight)) {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    }

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    const bgFill = isLight ? "#ffffff" : "#020202";
    const gridStroke = isLight ? "#cbd5e1" : "#1e1e1e";
    const textFill = isLight ? "#0f172a" : "#94a3b8";
    const curveStroke = isLight ? "#0284c7" : "#00e5ff";
    const targetStroke = isLight ? "#16a34a" : "#00e676";
    const limitStroke = isLight ? "#dc2626" : "#ff334b";
    const scrubberStroke = isLight ? "#0f172a" : "#ffffff";

    ctx.fillStyle = bgFill;
    ctx.fillRect(0, 0, w, h);

    const padLeft = 46;
    const padRight = 20;
    const padTop = 14;
    const padBottom = 22;
    const plotW = w - padLeft - padRight;
    const plotH = h - padTop - padBottom;

    ctx.strokeStyle = gridStroke;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padTop + (plotH / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(w - padRight, y);
      ctx.stroke();

      ctx.fillStyle = textFill;
      ctx.font = "bold 10px 'Segoe UI Mono', monospace";
      const val = Math.round(300 - (300 / 5) * i);
      ctx.fillText(String(val), 8, y + 4);
    }

    for (let i = 0; i <= 6; i++) {
      const x = padLeft + (plotW / 6) * i;
      ctx.beginPath();
      ctx.moveTo(x, padTop);
      ctx.lineTo(x, h - padBottom);
      ctx.stroke();

      ctx.fillStyle = textFill;
      ctx.font = "bold 10px 'Segoe UI Mono', monospace";
      const dist = Math.round(i * 100);
      ctx.fillText(String(dist), x - 8, h - 6);
    }

    const targetY = padTop + plotH * (1.0 - 174.0 / 300.0);
    ctx.strokeStyle = targetStroke;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(padLeft, targetY);
    ctx.lineTo(w - padRight, targetY);
    ctx.stroke();

    const lowerY = padTop + plotH * (1.0 - 10.0 / 300.0);
    const upperY = padTop + plotH * (1.0 - 300.0 / 300.0);
    ctx.strokeStyle = limitStroke;
    ctx.lineWidth = 1.2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padLeft, lowerY);
    ctx.lineTo(w - padRight, lowerY);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(padLeft, upperY);
    ctx.lineTo(w - padRight, upperY);
    ctx.stroke();
    ctx.setLineDash([]);

    const points = (data && data.profile && data.profile.length > 1) ? data.profile : [];
    if (points.length > 1) {
      ctx.strokeStyle = curveStroke;
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i < points.length; i++) {
        const x = padLeft + (plotW / (points.length - 1)) * i;
        const normY = Math.max(0, Math.min(300, points[i])) / 300.0;
        const y = padTop + plotH * (1.0 - normY);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    } else {
      ctx.strokeStyle = curveStroke;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(padLeft, targetY);
      ctx.lineTo(w - padRight, targetY);
      ctx.stroke();
    }

    const scrubberX = padLeft + plotW * cursorXRatio;
    ctx.strokeStyle = scrubberStroke;
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(scrubberX, padTop);
    ctx.lineTo(scrubberX, h - padBottom);
    ctx.stroke();
    ctx.setLineDash([]);

    let curThick = (data && data.thickness_mm) ? data.thickness_mm : 174.2;
    const scrubberY = padTop + plotH * (1.0 - Math.min(300, curThick) / 300.0);
    ctx.fillStyle = scrubberStroke;
    ctx.beginPath();
    ctx.arc(scrubberX, scrubberY, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = curveStroke;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  window.updateTelemetry = function (payload) {
    if (!payload) return;
    lastTelemetry = payload;

    const stream = document.getElementById("video-stream");
    if (stream && payload.frame_b64) {
      stream.src = "data:image/jpeg;base64," + payload.frame_b64;
    }

    const readoutMm = document.getElementById("readout-mm");
    if (readoutMm) readoutMm.textContent = payload.thickness_mm.toFixed(1);

    const readoutPx = document.getElementById("readout-px");
    if (readoutPx) readoutPx.textContent = `${payload.thickness_px.toFixed(1)} px`;

    const statMin = document.getElementById("stat-min");
    if (statMin) statMin.textContent = `${payload.min_mm.toFixed(1)} mm`;

    const statMax = document.getElementById("stat-max");
    if (statMax) statMax.textContent = `${payload.max_mm.toFixed(1)} mm`;

    const statAvg = document.getElementById("stat-avg");
    if (statAvg) statAvg.textContent = `${payload.avg_mm.toFixed(1)} mm`;

    const statStd = document.getElementById("stat-std");
    if (statStd) statStd.textContent = `${payload.std_dev_mm.toFixed(2)} mm`;

    const hudFps = document.getElementById("hud-fps-text");
    if (hudFps) hudFps.textContent = `FPS ${payload.fps.toFixed(1)} in / ${(payload.processing_ms / 100).toFixed(1)} proc \u2022 1920\u00d71080`;

    const hudMode = document.getElementById("hud-mode-text");
    if (hudMode) hudMode.textContent = `VIEW ${activeMode} \u2022 THRESHOLD OTSU ${payload.otsu_threshold}`;

    const hudThick = document.getElementById("hud-thick-text");
    if (hudThick) hudThick.textContent = `THICKNESS ${payload.thickness_mm.toFixed(1)} mm`;

    const ttX = document.getElementById("tt-x");
    const ttY = document.getElementById("tt-y");
    const ttTop = document.getElementById("tt-top");
    const ttBot = document.getElementById("tt-bot");
    const ttPx = document.getElementById("tt-px");
    const ttMm = document.getElementById("tt-mm");

    if (ttX) ttX.textContent = Math.round(payload.cursor_x);
    if (ttY) ttY.textContent = Math.round(payload.cursor_y);
    if (ttTop) ttTop.textContent = payload.top_y.toFixed(1);
    if (ttBot) ttBot.textContent = payload.bottom_y.toFixed(1);
    if (ttPx) ttPx.textContent = payload.thickness_px.toFixed(1);
    if (ttMm) ttMm.textContent = payload.thickness_mm.toFixed(1);

    const profMin = document.getElementById("prof-min");
    const profMax = document.getElementById("prof-max");
    const profAvg = document.getElementById("prof-avg");
    const profStd = document.getElementById("prof-std");
    const profCur = document.getElementById("prof-cur");

    if (profMin) profMin.textContent = payload.min_mm.toFixed(1);
    if (profMax) profMax.textContent = payload.max_mm.toFixed(1);
    if (profAvg) profAvg.textContent = payload.avg_mm.toFixed(1);
    if (profStd) profStd.textContent = payload.std_dev_mm.toFixed(2);
    if (profCur) profCur.textContent = `${payload.thickness_mm.toFixed(1)} mm`;

    const banner = document.getElementById("spec-status-banner");
    const bannerTitle = document.getElementById("banner-title-text");
    const bannerSub = document.getElementById("banner-sub-text");
    const badgeStatus = document.getElementById("badge-status");

    if (payload.is_valid === false) {
      if (banner) {
        banner.className = "status-banner banner-warning";
      }
      if (bannerTitle) bannerTitle.textContent = "\u25b2 LOW CONFIDENCE \u2014 MEASUREMENT NOT VALID";
      if (bannerSub) {
        bannerSub.textContent = "\u25b2 " + (payload.warning_text || "Detected boundaries are weak - check threshold settings");
        bannerSub.style.display = "block";
      }
      if (badgeStatus) {
        badgeStatus.textContent = "\u2022 LOW CONFIDENCE";
        badgeStatus.className = "pill-badge pill-status out-of-spec";
      }
    } else if (payload.is_normal) {
      if (banner) banner.className = "status-banner banner-normal";
      if (bannerTitle) bannerTitle.textContent = "\u2022 NORMAL";
      if (bannerSub) bannerSub.style.display = "none";
      if (badgeStatus) {
        badgeStatus.textContent = "\u2022 NORMAL";
        badgeStatus.className = "pill-badge pill-status";
      }
    } else {
      if (banner) banner.className = "status-banner banner-warning";
      if (bannerTitle) bannerTitle.textContent = "\u25b2 OUT OF SPEC";
      if (bannerSub) {
        bannerSub.textContent = "\u25b2 " + (payload.warning_text || "Thickness outside target tolerance");
        bannerSub.style.display = "block";
      }
      if (badgeStatus) {
        badgeStatus.textContent = "\u2022 OUT OF SPEC";
        badgeStatus.className = "pill-badge pill-status out-of-spec";
      }
    }

    setConfidencePct(payload.confidence_pct, payload.is_valid !== false);

    const statusFps = document.getElementById("status-fps");
    if (statusFps) statusFps.textContent = payload.fps.toFixed(1);

    const statusProc = document.getElementById("status-proc");
    if (statusProc) statusProc.textContent = `${payload.processing_ms} ms`;

    const statusThresh = document.getElementById("status-thresh");
    if (statusThresh) statusThresh.textContent = `OTSU ${payload.otsu_threshold}`;

    if (payload.source_name) {
      updateSourceDisplay(payload.source_name);
    }

    if (payload.roi && !isSelectingRoi && !roiDragStart) {
      if (activeRoi.x !== payload.roi[0] || activeRoi.y !== payload.roi[1] || activeRoi.w !== payload.roi[2] || activeRoi.h !== payload.roi[3]) {
        activeRoi = { x: payload.roi[0], y: payload.roi[1], w: payload.roi[2], h: payload.roi[3] };
        updateRoiDisplay(activeRoi);
      }
    }

    updateCaliperOverlay();
    renderProfileChart(payload);
  };

  document.addEventListener("DOMContentLoaded", () => {
    initClock();
    initThemeSystem();
    initSettingsDropdown();
    initLedBar();
    initTabs();
    initRoiControls();
    initMouseInspection();
    updateRoiDisplay(activeRoi);
    renderProfileChart(null);
  });
})();

