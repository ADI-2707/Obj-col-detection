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
  let isCalibrating = false;
  let calibPoints = [];
  let activeProfileTab = "profile";

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
        showHelpModal();
      });
    }

    const itemAbout = document.getElementById("item-about");
    if (itemAbout) {
      itemAbout.addEventListener("click", () => {
        dropdown.classList.remove("show");
        showAboutModal();
      });
    }
  }

  function showScadaModal(title, html) {
    const backdrop = document.getElementById("scada-modal-backdrop");
    const titleEl = document.getElementById("scada-modal-title");
    const bodyEl = document.getElementById("scada-modal-body");
    if (titleEl) titleEl.textContent = title;
    if (bodyEl) bodyEl.innerHTML = html;
    if (backdrop) backdrop.style.display = "flex";
  }

  function closeScadaModal() {
    const backdrop = document.getElementById("scada-modal-backdrop");
    if (backdrop) backdrop.style.display = "none";
  }

  function showHelpModal() {
    showScadaModal("ORBIX \u2014 SYSTEM HELP & DOCUMENTATION", `
      <h4>1. SYSTEM OVERVIEW</h4>
      <p>The Orbix Hot Metal Slab Thickness Vision System performs non-contact real-time optical thickness gauging of red-hot cast steel slabs at 1920\u00d71080 resolution.</p>
      <h4>2. EDGE DETECTION &amp; COLOR SPACES</h4>
      <p>The vision engine computes vertical Sobel intensity gradients combined with Otsu, Adaptive Gaussian, or Manual thresholding to lock onto boundary edges.</p>
      <ul>
        <li><strong>Grayscale:</strong> Standard luminance intensity calculation.</li>
        <li><strong>HSV (V):</strong> High dynamic range value channel for glowing hot steel.</li>
        <li><strong>CIELAB (L):</strong> Perceptually uniform lightness channel.</li>
      </ul>
      <h4>3. CALIBRATION PROCEDURE</h4>
      <p>Click <strong>CALIBRATE</strong> on the right panel, then click Point 1 (top edge) and Point 2 (bottom edge) on the live video. Enter the known reference distance in millimeters to synchronize scale.</p>
      <h4>4. REGION OF INTEREST (ROI)</h4>
      <p>Click <strong>SELECT ROI</strong> and drag across the slab area to constrain edge tracking and improve noise immunity.</p>
      <h4>5. KEYBOARD SHORTCUTS</h4>
      <ul>
        <li><strong>ESC:</strong> Cancel ROI selection, Calibration mode, or close modal dialogs.</li>
        <li><strong>F11:</strong> Toggle Fullscreen display mode.</li>
      </ul>
    `);
  }

  function showAboutModal() {
    showScadaModal("ABOUT \u2014 ORBIX VISION SYSTEM", `
      <h4>ORBIX HOT METAL SLAB THICKNESS VISION SYSTEM</h4>
      <p><strong>Version:</strong> 1.5.0 Production Build</p>
      <p><strong>Architecture:</strong> Hybrid Python 3.14 Vision Core + Accelerated Webview SCADA</p>
      <p><strong>Mill Subsystem:</strong> Continuous Casting / Roughing Mill In-line Gauging</p>
      <h4>SPECIFICATIONS</h4>
      <ul>
        <li><strong>Resolution:</strong> 1920 \u00d7 1080 @ 30 FPS Industrial GigE / RTSP</li>
        <li><strong>Accuracy:</strong> \u00b10.2 mm calibrated measurement tolerance</li>
        <li><strong>Measurement Rate:</strong> Sub-15 ms edge processing pipeline</li>
        <li><strong>Sensor Interface:</strong> RTSP / GigE Vision / Direct V4L2-DirectShow</li>
      </ul>
      <p style="margin-top:14px; border-top:1px solid var(--border-sub); padding-top:8px; font-size:10px; color:var(--text-muted);">
        \u00a9 2026 Systrol Industrial Automation. All rights reserved.
      </p>
    `);
  }

  function showSourceConfigModal() {
    showScadaModal("SOURCE CONFIGURATION", `
      <h4>CAMERA STREAM &amp; SOURCE PRESETS</h4>
      <p>Configure the optical sensor ingestion parameters:</p>
      <ul>
        <li><strong>RTSP Stream:</strong> <code>rtsp://192.168.1.250:554/live/ch0</code></li>
        <li><strong>Local Webcam / USB Sensor:</strong> <code>0</code> or <code>1</code></li>
        <li><strong>Recorded Test Reel:</strong> Sample MP4 slab rolling archive</li>
      </ul>
      <p>Enter connection string in the Image Source input box and click <strong>CONNECT CAMERA</strong>.</p>
    `);
  }

  function initModalSystem() {
    const backdrop = document.getElementById("scada-modal-backdrop");
    const closeBtn = document.getElementById("scada-modal-close");
    const okBtn = document.getElementById("scada-modal-ok");
    const win = document.getElementById("scada-modal-window");

    if (closeBtn) closeBtn.addEventListener("click", closeScadaModal);
    if (okBtn) okBtn.addEventListener("click", closeScadaModal);

    if (backdrop && win) {
      backdrop.addEventListener("click", (e) => {
        if (!win.contains(e.target)) closeScadaModal();
      });
    }

    const btnHelp = document.getElementById("btn-help");
    if (btnHelp) btnHelp.addEventListener("click", showHelpModal);

    const btnSourceCfg = document.getElementById("btn-source-config");
    if (btnSourceCfg) btnSourceCfg.addEventListener("click", showSourceConfigModal);

    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeScadaModal();
    });
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

    const profTabs = document.querySelectorAll(".prof-tab");
    const chartCanvas = document.getElementById("profile-chart");
    const tableWrapper = document.getElementById("points-table-wrapper");
    const legend = document.querySelector(".profile-legend");

    profTabs.forEach((tab, idx) => {
      tab.addEventListener("click", () => {
        profTabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        if (idx === 0) {
          activeProfileTab = "profile";
          if (chartCanvas) chartCanvas.style.display = "block";
          if (tableWrapper) tableWrapper.style.display = "none";
          if (legend) legend.style.display = "flex";
          renderProfileChart(lastTelemetry);
        } else {
          activeProfileTab = "points";
          if (chartCanvas) chartCanvas.style.display = "none";
          if (tableWrapper) tableWrapper.style.display = "block";
          if (legend) legend.style.display = "none";
          renderPointsTable(lastTelemetry);
        }
      });
    });

    const btnEdges = document.getElementById("btn-toggle-edges");
    if (btnEdges) {
      btnEdges.addEventListener("click", () => {
        showEdges = !showEdges;
        btnEdges.classList.toggle("active", showEdges);
        updateCaliperOverlay();
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

    const badgeRec = document.getElementById("badge-rec");
    if (badgeRec) {
      badgeRec.addEventListener("click", () => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.toggle_recording) {
          window.pywebview.api.toggle_recording().then((res) => {
            if (res && res.recording !== undefined) {
              badgeRec.textContent = res.recording ? "\u25cf REC ON" : "RECORDING OFF";
              badgeRec.classList.toggle("recording-active", res.recording);
            }
          });
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

  function initDetectionControls() {
    const selColor = document.getElementById("select-colour-space");
    const selThresh = document.getElementById("select-thresh-mode");

    if (selColor) {
      selColor.addEventListener("change", (e) => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_colour_space) {
          window.pywebview.api.set_colour_space(e.target.value);
        }
      });
    }

    if (selThresh) {
      selThresh.addEventListener("change", (e) => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_threshold_mode) {
          window.pywebview.api.set_threshold_mode(e.target.value);
        }
      });
    }
  }

  function initCalibrationControls() {
    const btnCalib = document.getElementById("btn-calibrate");
    const wrapper = document.getElementById("video-wrapper");

    function resetCalibrationState() {
      isCalibrating = false;
      calibPoints = [];
      if (btnCalib) {
        btnCalib.textContent = "CALIBRATE";
        btnCalib.classList.remove("active-calibrating");
      }
      if (wrapper) wrapper.classList.remove("calibrating-mode");
      updateCaliperOverlay();
    }

    if (btnCalib) {
      btnCalib.addEventListener("click", () => {
        if (isCalibrating) {
          resetCalibrationState();
        } else {
          isCalibrating = true;
          calibPoints = [];
          btnCalib.textContent = "POINT 1: CLICK TOP";
          btnCalib.classList.add("active-calibrating");
          if (wrapper) wrapper.classList.add("calibrating-mode");
          const tooltip = document.getElementById("caliper-tooltip");
          if (tooltip) tooltip.style.display = "none";
        }
      });
    }

    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && isCalibrating) {
        resetCalibrationState();
      }
    });
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

    wrapper.addEventListener("click", (e) => {
      if (!isCalibrating) return;
      const rect = wrapper.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const fx = Math.round((x / rect.width) * 1920);
      const fy = Math.round((y / rect.height) * 1080);

      calibPoints.push({ x: fx, y: fy });

      const btnCalib = document.getElementById("btn-calibrate");
      if (calibPoints.length === 1) {
        if (btnCalib) btnCalib.textContent = "POINT 2: CLICK BOTTOM";
        updateCaliperOverlay();
      } else if (calibPoints.length >= 2) {
        const pt1 = calibPoints[0];
        const pt2 = calibPoints[1];
        const distPx = Math.hypot(pt2.x - pt1.x, pt2.y - pt1.y);
        const input = window.prompt("Enter known reference distance in millimeters (mm):", "174.0");
        if (input !== null) {
          const knownMm = parseFloat(input);
          if (knownMm > 0 && distPx > 0) {
            const newScale = knownMm / distPx;
            if (window.pywebview && window.pywebview.api && window.pywebview.api.set_calibration) {
              window.pywebview.api.set_calibration(newScale);
            }
            const elVal = document.getElementById("calib-mm-px");
            const elDer = document.getElementById("calib-px-mm");
            const elDate = document.getElementById("calib-date");
            if (elVal) elVal.textContent = `${newScale.toFixed(5)} mm/px`;
            if (elDer) elDer.textContent = `= ${(1 / newScale).toFixed(5)} px/mm (derived)`;
            if (elDate) {
              const d = new Date();
              elDate.textContent = `${String(d.getDate()).padStart(2, "0")}-${String(d.getMonth() + 1).padStart(2, "0")}-${d.getFullYear()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}`;
            }
          }
        }
        isCalibrating = false;
        calibPoints = [];
        if (btnCalib) {
          btnCalib.textContent = "CALIBRATE";
          btnCalib.classList.remove("active-calibrating");
        }
        if (wrapper) wrapper.classList.remove("calibrating-mode");
        updateCaliperOverlay();
      }
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

    let edgeGraphic = "";
    if (showEdges) {
      edgeGraphic = `
        <line x1="${cx}" y1="${ry}" x2="${cx}" y2="${ry + rh}" stroke="#555555" stroke-width="1" stroke-dasharray="3 3"/>
        <line x1="${cx}" y1="${topY}" x2="${cx}" y2="${botY}" stroke="#ffb703" stroke-width="2.5"/>
        <circle cx="${cx}" cy="${topY}" r="4.5" fill="#00e5ff" stroke="#000000" stroke-width="1.5"/>
        <circle cx="${cx}" cy="${botY}" r="4.5" fill="#00e5ff" stroke="#000000" stroke-width="1.5"/>
      `;
    }

    svg.innerHTML = `
      <rect x="${rx}" y="${ry}" width="${rw}" height="${rh}" fill="rgba(0, 229, 255, 0.04)" stroke="#00e5ff" stroke-width="1.4" stroke-dasharray="6 4" opacity="0.85"/>
      <rect x="${rx - 3}" y="${ry - 3}" width="6" height="6" fill="#00e5ff"/>
      <rect x="${rx + rw - 3}" y="${ry - 3}" width="6" height="6" fill="#00e5ff"/>
      <rect x="${rx - 3}" y="${ry + rh - 3}" width="6" height="6" fill="#00e5ff"/>
      <rect x="${rx + rw - 3}" y="${ry + rh - 3}" width="6" height="6" fill="#00e5ff"/>
      ${edgeGraphic}
    `;

    if (isCalibrating && calibPoints.length > 0) {
      calibPoints.forEach((pt, idx) => {
        const sx = (pt.x / 1920) * w;
        const sy = (pt.y / 1080) * h;
        svg.innerHTML += `
          <circle cx="${sx}" cy="${sy}" r="6" fill="#ffb703" stroke="#000000" stroke-width="2"/>
          <line x1="${sx - 12}" y1="${sy}" x2="${sx + 12}" y2="${sy}" stroke="#ffb703" stroke-width="1.5"/>
          <line x1="${sx}" y1="${sy - 12}" x2="${sx}" y2="${sy + 12}" stroke="#ffb703" stroke-width="1.5"/>
          <text x="${sx + 10}" y="${sy - 8}" fill="#ffb703" font-size="11" font-weight="bold">PT ${idx + 1}</text>
        `;
      });
    }

    const topLabel = document.getElementById("label-top-edge");
    const botLabel = document.getElementById("label-bot-edge");
    if (topLabel) {
      if (showEdges && !isCalibrating && !isSelectingRoi) {
        topLabel.style.display = "block";
        topLabel.style.left = `${Math.max(8, rx + 16)}px`;
        topLabel.style.top = `${Math.max(8, topY - 14)}px`;
      } else {
        topLabel.style.display = "none";
      }
    }
    if (botLabel) {
      if (showEdges && !isCalibrating && !isSelectingRoi) {
        botLabel.style.display = "block";
        botLabel.style.left = `${Math.max(8, rx + 16)}px`;
        botLabel.style.top = `${Math.min(h - 22, botY + 4)}px`;
      } else {
        botLabel.style.display = "none";
      }
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

  function renderPointsTable(data) {
    const tbody = document.getElementById("points-table-body");
    if (!tbody) return;
    if (!data || !data.profile || data.profile.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:12px; color:var(--text-muted);">NO MEASUREMENT DATA AVAILABLE</td></tr>';
      return;
    }

    const prof = data.profile;
    const len = prof.length;
    const count = Math.min(25, len);
    const step = Math.max(1, Math.floor(len / count));
    const calib = data.calibration || 0.34757;
    const roi = data.roi || [150, 39, 1549, 870];
    const topAvg = data.avg_top_y || (roi[1] + roi[3] * 0.33);
    const lowerIn = document.getElementById("lim-lower-input");
    const upperIn = document.getElementById("lim-upper-input");
    const lower = parseFloat(lowerIn ? lowerIn.value : 10.0) || 10.0;
    const upper = parseFloat(upperIn ? upperIn.value : 300.0) || 300.0;

    let html = "";
    let ptIndex = 1;
    for (let i = 0; i < len; i += step) {
      const thickMm = prof[i];
      const thickPx = Math.round(thickMm / calib);
      const posX = Math.round(roi[0] + (i / len) * roi[2]);
      const topY = Math.round(topAvg);
      const botY = Math.round(topAvg + thickPx);
      const isOk = thickMm >= lower && thickMm <= upper;
      const statusClass = isOk ? "status-cell-ok" : "status-cell-bad";
      const statusText = isOk ? "NORMAL" : "OUT OF SPEC";

      html += `<tr>
        <td>#${String(ptIndex).padStart(2, "0")}</td>
        <td>${posX}</td>
        <td>${topY}</td>
        <td>${botY}</td>
        <td>${thickPx}</td>
        <td>${thickMm.toFixed(1)}</td>
        <td class="${statusClass}">${statusText}</td>
      </tr>`;
      ptIndex++;
    }
    tbody.innerHTML = html;
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
    if (statusThresh) statusThresh.textContent = `${(payload.threshold_mode || "otsu").toUpperCase()} ${payload.otsu_threshold}`;

    const hudStatus = document.getElementById("hud-status-text");
    if (hudStatus) hudStatus.textContent = isFrozen ? "PAUSED / FROZEN" : (payload.is_valid ? "VIDEO PLAYING" : "LOW CONFIDENCE");

    const hudFps = document.getElementById("hud-fps-text");
    if (hudFps) hudFps.textContent = `FPS ${payload.fps.toFixed(1)} in / ${payload.processing_ms}ms proc \u2022 1920\u00d71080`;

    const hudMode = document.getElementById("hud-mode-text");
    if (hudMode) hudMode.textContent = `VIEW ${activeMode} \u2022 THRESHOLD ${(payload.threshold_mode || "otsu").toUpperCase()} ${payload.otsu_threshold} \u2022 ${(payload.colour_space || "grayscale").toUpperCase()}`;

    const hudThick = document.getElementById("hud-thick-text");
    if (hudThick) hudThick.textContent = `THICKNESS ${payload.thickness_mm.toFixed(1)} mm`;

    const selColor = document.getElementById("select-colour-space");
    if (selColor && document.activeElement !== selColor && payload.colour_space) {
      selColor.value = payload.colour_space;
    }
    const selThresh = document.getElementById("select-thresh-mode");
    if (selThresh && document.activeElement !== selThresh && payload.threshold_mode) {
      selThresh.value = payload.threshold_mode;
    }

    if (payload.source_name) {
      updateSourceDisplay(payload.source_name);
    }

    if (payload.roi && !isSelectingRoi && !roiDragStart) {
      if (activeRoi.x !== payload.roi[0] || activeRoi.y !== payload.roi[1] || activeRoi.w !== payload.roi[2] || activeRoi.h !== payload.roi[3]) {
        activeRoi = { x: payload.roi[0], y: payload.roi[1], w: payload.roi[2], h: payload.roi[3] };
        updateRoiDisplay(activeRoi);
      }
    }

    const elVal = document.getElementById("calib-mm-px");
    const elDer = document.getElementById("calib-px-mm");
    if (elVal && !isCalibrating && payload.calibration) {
      elVal.textContent = `${payload.calibration.toFixed(5)} mm/px`;
    }
    if (elDer && !isCalibrating && payload.calibration > 0) {
      elDer.textContent = `= ${(1 / payload.calibration).toFixed(5)} px/mm (derived)`;
    }

    const badgeRec = document.getElementById("badge-rec");
    if (badgeRec && payload.is_recording !== undefined) {
      badgeRec.textContent = payload.is_recording ? "\u25cf REC ON" : "RECORDING OFF";
      badgeRec.classList.toggle("recording-active", !!payload.is_recording);
    }

    if (payload.show_edges !== undefined && payload.show_edges !== showEdges) {
      showEdges = payload.show_edges;
      const btnEdges = document.getElementById("btn-toggle-edges");
      if (btnEdges) btnEdges.classList.toggle("active", showEdges);
    }

    updateCaliperOverlay();
    if (activeProfileTab === "points") {
      renderPointsTable(payload);
    } else {
      renderProfileChart(payload);
    }
  };

  document.addEventListener("DOMContentLoaded", () => {
    initClock();
    initThemeSystem();
    initSettingsDropdown();
    initModalSystem();
    initLedBar();
    initTabs();
    initRoiControls();
    initDetectionControls();
    initCalibrationControls();
    initMouseInspection();
    updateRoiDisplay(activeRoi);
    renderProfileChart(null);
  });
})();

