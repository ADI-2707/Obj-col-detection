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
  let showRoiBox = true;
  let currentAppVersion = "1.6.0";

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

  function showScadaModal(title, html, isWide = false, showPdfBtn = false) {
    const backdrop = document.getElementById("scada-modal-backdrop");
    const win = document.getElementById("scada-modal-window");
    const titleEl = document.getElementById("scada-modal-title");
    const bodyEl = document.getElementById("scada-modal-body");
    const watermark = document.getElementById("modal-sticky-watermark");
    const pdfBtn = document.getElementById("btn-modal-open-pdf");

    if (titleEl) titleEl.textContent = title;
    if (bodyEl) bodyEl.innerHTML = html;
    if (win) {
      win.classList.toggle("modal-wide", !!isWide);
    }
    if (watermark) {
      watermark.style.display = showPdfBtn ? "block" : "none";
    }
    if (pdfBtn) {
      pdfBtn.style.display = showPdfBtn ? "inline-block" : "none";
    }
    if (backdrop) backdrop.style.display = "flex";
  }

  function closeScadaModal() {
    const backdrop = document.getElementById("scada-modal-backdrop");
    if (backdrop) backdrop.style.display = "none";
  }

  function showHelpModal() {
    const manualHtml = `
      <div class="manual-container">
        <div>
          <div class="manual-title">ORBIX VISION SYSTEM \u2014 FEATURES &amp; OPERATION MANUAL</div>
          <div class="manual-subtitle">
            Systrol Industrial Vision Software Suite &bull; Optical Hot Metal Slab Thickness Gauging &bull; Version ${currentAppVersion} Production Build
          </div>
          <p style="margin-bottom:12px; font-size:11px; line-height:1.5;">
            This manual details all software features mapped directly to their respective operational screen areas:
            <strong>Top Bar</strong>, <strong>Left Panel</strong>, <strong>Center Viewport</strong>, <strong>Right Panel</strong>, and <strong>Bottom Bar</strong>.
            Click the <strong>OPEN PRINTABLE MANUAL (PDF)</strong> button below to launch the formal offline ISO-compliant documentation.
          </p>
        </div>

        <div class="manual-section-card">
          <div class="manual-section-header">
            <h3 class="manual-section-title">1. TOP BAR (GLOBAL SYSTEM CONTROLS &amp; STATUS)</h3>
            <span class="manual-area-tag">TOPBAR AREA</span>
          </div>
          <table class="manual-table">
            <thead>
              <tr>
                <th style="width:28%;">FEATURE / OPERATION</th>
                <th style="width:32%;">UI LOCATION &amp; CONTROL</th>
                <th style="width:40%;">OPERATIONAL ACTION &amp; DESCRIPTION</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Settings Dropdown</strong></td>
                <td><span class="manual-location-text">Top-Right:</span> <span class="manual-ctrl-badge">&#9881; Gear Button</span></td>
                <td>Click to reveal the application menu containing Theme Switcher, Help &amp; Documentation, and About System dialogs.</td>
              </tr>
              <tr>
                <td><strong>Theme Toggle</strong></td>
                <td><span class="manual-location-text">Inside Settings:</span> <span class="manual-ctrl-badge">Switch Slider</span></td>
                <td>Toggle between Dark Industrial theme and High-Contrast Light theme. Saved in local browser storage.</td>
              </tr>
              <tr>
                <td><strong>About System</strong></td>
                <td><span class="manual-location-text">Inside Settings:</span> <span class="manual-ctrl-badge">About System</span></td>
                <td>Displays engine build specifications (v${currentAppVersion}), Python 3.14/Webview architecture, and mill operating tolerances.</td>
              </tr>
              <tr>
                <td><strong>Sensor Stream Status</strong></td>
                <td><span class="manual-location-text">Top-Right Header:</span> <span class="manual-ctrl-badge">&bull; VIDEO PLAYING</span></td>
                <td>Real-time ingestion indicator. Green dot signifies healthy video feed; amber indicates paused stream.</td>
              </tr>
              <tr>
                <td><strong>Tolerance Spec Status</strong></td>
                <td><span class="manual-location-text">Top-Right Header:</span> <span class="manual-ctrl-badge">&bull; NORMAL / &bull; OUT OF SPEC</span></td>
                <td>Instant mill quality annunciator. Green indicates thickness within bounds; red indicates tolerance deviation.</td>
              </tr>
              <tr>
                <td><strong>DVR Recording Badge</strong></td>
                <td><span class="manual-location-text">Top-Right Header:</span> <span class="manual-ctrl-badge">RECORDING OFF / &bull; REC ON</span></td>
                <td>Click directly on this badge to start or stop real-time MJPEG AVI recording to <code>data/recordings/</code>. Flashes red while active.</td>
              </tr>
              <tr>
                <td><strong>Plant Digital Clock</strong></td>
                <td><span class="manual-location-text">Top-Center Header:</span> <span class="manual-ctrl-badge">HH:MM:SS</span></td>
                <td>Displays synchronized 24-hour plant workstation time with real-time seconds ticking.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="manual-section-card">
          <div class="manual-section-header">
            <h3 class="manual-section-title">2. LEFT PANEL (INGESTION, REGION OF INTEREST &amp; FILTERING)</h3>
            <span class="manual-area-tag">LEFT PANEL</span>
          </div>
          <table class="manual-table">
            <thead>
              <tr>
                <th style="width:28%;">FEATURE / OPERATION</th>
                <th style="width:32%;">UI LOCATION &amp; CONTROL</th>
                <th style="width:40%;">OPERATIONAL ACTION &amp; DESCRIPTION</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Sensor Input String</strong></td>
                <td><span class="manual-location-text">IMAGE SOURCE:</span> <span class="manual-ctrl-badge">RTSP URL / Camera IP Input</span></td>
                <td>Enter camera index (<code>0</code> or <code>1</code>) for USB/integrated webcams, or enter network stream URI (<code>rtsp://192.168.1.250:554/live</code>).</td>
              </tr>
              <tr>
                <td><strong>Connect Camera</strong></td>
                <td><span class="manual-location-text">IMAGE SOURCE:</span> <span class="manual-ctrl-badge">[CONNECT CAMERA]</span></td>
                <td>Initiates hardware capture for the specified camera index or RTSP network stream.</td>
              </tr>
              <tr>
                <td><strong>Open File Dialogs</strong></td>
                <td><span class="manual-location-text">IMAGE SOURCE:</span> <span class="manual-ctrl-badge">[OPEN VIDEO] &amp; [OPEN IMAGE]</span></td>
                <td>Opens native Windows file dialogs to load recorded mill MP4/AVI reels or single-frame test images.</td>
              </tr>
              <tr>
                <td><strong>Sample Test Media</strong></td>
                <td><span class="manual-location-text">IMAGE SOURCE:</span> <span class="manual-ctrl-badge">[SAMPLE VIDEO] &amp; [SAMPLE IMAGE]</span></td>
                <td>Quickly reloads pre-bundled hot rolling mill slab reels without needing physical cameras.</td>
              </tr>
              <tr>
                <td><strong>Interactive Canvas ROI</strong></td>
                <td><span class="manual-location-text">REGION OF INTEREST:</span> <span class="manual-ctrl-badge">[SELECT ROI]</span></td>
                <td>Activates interactive canvas dragging. Click and drag across the slab on the video feed to define search window boundaries.</td>
              </tr>
              <tr>
                <td><strong>Confirm ROI Window</strong></td>
                <td><span class="manual-location-text">REGION OF INTEREST:</span> <span class="manual-ctrl-badge">[CONFIRM ROI]</span></td>
                <td>Locks in the drawn selection and synchronizes mathematical edge search constraints with the vision engine.</td>
              </tr>
              <tr>
                <td><strong>Full Field of View ROI</strong></td>
                <td><span class="manual-location-text">REGION OF INTEREST:</span> <span class="manual-ctrl-badge">[FULL]</span></td>
                <td>Resets search constraints to the entire 1920\u00d71080 resolution field of view.</td>
              </tr>
              <tr>
                <td><strong>ROI Presets &amp; Reset</strong></td>
                <td><span class="manual-location-text">REGION OF INTEREST:</span> <span class="manual-ctrl-badge">[+ ADD] &amp; [DELETE]</span></td>
                <td>Applies standard centered 1440\u00d7810 mill bounding box, or clears ROI back to full canvas.</td>
              </tr>
              <tr>
                <td><strong>Show/Hide ROI Overlay</strong></td>
                <td><span class="manual-location-text">REGION OF INTEREST:</span> <span class="manual-ctrl-badge">Eye Button (&#128065;)</span></td>
                <td>Toggles visibility of the slate-gray dashed search window overlay without interrupting edge tracking.</td>
              </tr>
              <tr>
                <td><strong>Colour Space Selection</strong></td>
                <td><span class="manual-location-text">THRESHOLD &amp; DETECTION:</span> <span class="manual-ctrl-badge">Colour Space Select</span></td>
                <td>Select <strong>Grayscale</strong> for cold steel, <strong>HSV Luminance</strong> for red-hot glowing metal (max dynamic range), or <strong>CIELAB</strong> for glare/water suppression.</td>
              </tr>
              <tr>
                <td><strong>Threshold Mode Selection</strong></td>
                <td><span class="manual-location-text">THRESHOLD &amp; DETECTION:</span> <span class="manual-ctrl-badge">Threshold Mode Select</span></td>
                <td>Choose between <strong>Otsu (automatic)</strong>, <strong>Adaptive Gaussian</strong> (local variations), or <strong>Manual Slider</strong>.</td>
              </tr>
              <tr>
                <td><strong>Spatial Blur Kernel</strong></td>
                <td><span class="manual-location-text">THRESHOLD &amp; DETECTION:</span> <span class="manual-ctrl-badge">Gaussian Blur (k=5)</span></td>
                <td>Applies 2D Gaussian convolution filter to suppress airborne steam, sparks, and roller surface speckle noise.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="manual-section-card">
          <div class="manual-section-header">
            <h3 class="manual-section-title">3. CENTER VIEWPORT (VIDEO FEED, VIEW MODES &amp; CALIPERS)</h3>
            <span class="manual-area-tag">CENTER VIEWPORT</span>
          </div>
          <table class="manual-table">
            <thead>
              <tr>
                <th style="width:28%;">FEATURE / OPERATION</th>
                <th style="width:32%;">UI LOCATION &amp; CONTROL</th>
                <th style="width:40%;">OPERATIONAL ACTION &amp; DESCRIPTION</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>View Mode Toolbar Tabs</strong></td>
                <td><span class="manual-location-text">Viewport Toolbar:</span> <span class="manual-ctrl-badge">[ORIGINAL] [GRAY] [THRESHOLD] [DETECTION] [THERMAL] [MEASUREMENT]</span></td>
                <td>Select between full color stream, luminance channel, segmented binary mask, Canny edge filter, false-color thermal heat map, or clean vector measurement overlay.</td>
              </tr>
              <tr>
                <td><strong>Toggle Slab Edges</strong></td>
                <td><span class="manual-location-text">Viewport Toolbar:</span> <span class="manual-ctrl-badge">[EDGES] Button</span></td>
                <td>Toggles the cyan boundary vector lines tracking the slab top and bottom surfaces on the video canvas.</td>
              </tr>
              <tr>
                <td><strong>Freeze Stream</strong></td>
                <td><span class="manual-location-text">Viewport Toolbar:</span> <span class="manual-ctrl-badge">[FREEZE] Button</span></td>
                <td>Pauses real-time video ingestion to inspect transient surface anomalies or perform stationary caliper inspection.</td>
              </tr>
              <tr>
                <td><strong>Fullscreen Toggle</strong></td>
                <td><span class="manual-location-text">Viewport Toolbar:</span> <span class="manual-ctrl-badge">[FULLSCREEN] Button</span></td>
                <td>Expands SCADA viewport to full display monitor. Press F11 or ESC to return to windowed mode.</td>
              </tr>
              <tr>
                <td><strong>Hover Caliper Tooltip</strong></td>
                <td><span class="manual-location-text">Video Canvas:</span> <span class="manual-ctrl-badge">Mouse Movement</span></td>
                <td>Hover mouse cursor anywhere over the slab to inspect localized X, Y coordinates, Top/Bottom Edge pixel positions, and thickness in px and mm.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="manual-section-card">
          <div class="manual-section-header">
            <h3 class="manual-section-title">4. RIGHT PANEL (THICKNESS GAUGING, CALIBRATION &amp; OPERATION)</h3>
            <span class="manual-area-tag">RIGHT PANEL</span>
          </div>
          <table class="manual-table">
            <thead>
              <tr>
                <th style="width:28%;">FEATURE / OPERATION</th>
                <th style="width:32%;">UI LOCATION &amp; CONTROL</th>
                <th style="width:40%;">OPERATIONAL ACTION &amp; DESCRIPTION</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Digital Thickness Readout</strong></td>
                <td><span class="manual-location-text">THICKNESS Card:</span> <span class="manual-ctrl-badge">Digital Number Hero</span></td>
                <td>Displays calibrated slab thickness in millimeters (e.g. 174.2 mm) and raw sensor pixel height (501.1 px).</td>
              </tr>
              <tr>
                <td><strong>Statistical Summary</strong></td>
                <td><span class="manual-location-text">THICKNESS Card:</span> <span class="manual-ctrl-badge">MIN / MAX / AVG / STD DEV</span></td>
                <td>Live statistical distribution computed across all horizontal cross-section measurement columns across the ROI.</td>
              </tr>
              <tr>
                <td><strong>Confidence LED Bar</strong></td>
                <td><span class="manual-location-text">THICKNESS Card:</span> <span class="manual-ctrl-badge">24-Segment LED Ladder</span></td>
                <td>Optical signal-to-noise rating. Lit green for solid edge boundaries (&gt;75%), amber for fair (40-74%), red for low confidence.</td>
              </tr>
              <tr>
                <td><strong>Target &amp; Tolerance Inputs</strong></td>
                <td><span class="manual-location-text">THICKNESS Card:</span> <span class="manual-ctrl-badge">TARGET, LOWER, UPPER Fields</span></td>
                <td>Operators configure nominal target thickness (174.0 mm) and tolerance reject thresholds (10.0 mm to 300.0 mm).</td>
              </tr>
              <tr>
                <td><strong>2-Point Calibration Wizard</strong></td>
                <td><span class="manual-location-text">CALIBRATION Card:</span> <span class="manual-ctrl-badge">[CALIBRATE] Button</span></td>
                <td>Click [CALIBRATE], then click Point 1 on the top edge and Point 2 on the bottom edge on the live video. Enter known distance in mm to synchronize scale.</td>
              </tr>
              <tr>
                <td><strong>Start / Stop Measurement</strong></td>
                <td><span class="manual-location-text">OPERATION Card:</span> <span class="manual-ctrl-badge">[START MEASUREMENT]</span></td>
                <td>Toggles active mathematical thickness gauging calculations without stopping video playback or recording.</td>
              </tr>
              <tr>
                <td><strong>Capture Image Snapshot</strong></td>
                <td><span class="manual-location-text">OPERATION Card:</span> <span class="manual-ctrl-badge">[CAPTURE IMAGE]</span></td>
                <td>Captures instantaneous full-resolution PNG image of the live inspection display saved to <code>data/captures/</code>.</td>
              </tr>
              <tr>
                <td><strong>Generate Quality Report</strong></td>
                <td><span class="manual-location-text">OPERATION Card:</span> <span class="manual-ctrl-badge">[GENERATE REPORT]</span></td>
                <td>Exports formal quality audit CSV report with timestamp, statistics, and discrete profile points to <code>data/reports/</code>.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="manual-section-card">
          <div class="manual-section-header">
            <h3 class="manual-section-title">5. BOTTOM SECTION (PROFILE CURVE, POINT TABLE &amp; TELEMETRY)</h3>
            <span class="manual-area-tag">BOTTOM BAR</span>
          </div>
          <table class="manual-table">
            <thead>
              <tr>
                <th style="width:28%;">FEATURE / OPERATION</th>
                <th style="width:32%;">UI LOCATION &amp; CONTROL</th>
                <th style="width:40%;">OPERATIONAL ACTION &amp; DESCRIPTION</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Thickness Profile Chart</strong></td>
                <td><span class="manual-location-text">Bottom Section:</span> <span class="manual-ctrl-badge">'THICKNESS PROFILE' Tab</span></td>
                <td>Plots continuous thickness curve across the slab length. Features Target reference line, Tolerance limit lines, and interactive vertical cursor scrubber.</td>
              </tr>
              <tr>
                <td><strong>Measurement Points Table</strong></td>
                <td><span class="manual-location-text">Bottom Section:</span> <span class="manual-ctrl-badge">'MEASUREMENT POINTS' Tab</span></td>
                <td>Displays discrete cross-section columns (#01 to #25) with exact X, Top Y, Bottom Y, pixel thickness, millimeter thickness, and NORMAL / OUT OF SPEC status.</td>
              </tr>
              <tr>
                <td><strong>SCADA Performance Strip</strong></td>
                <td><span class="manual-location-text">Bottom Footer:</span> <span class="manual-ctrl-badge">Left Status Bar</span></td>
                <td>Displays real-time pipeline performance: sensor FPS, processing latency in milliseconds, resolution (1920\u00d71080), Otsu threshold, and calibration ratio.</td>
              </tr>
              <tr>
                <td><strong>Active Source Indicator</strong></td>
                <td><span class="manual-location-text">Bottom Footer:</span> <span class="manual-ctrl-badge">Right Status Bar</span></td>
                <td>Displays the currently ingested file name, camera IP address, or device identifier (e.g., <code>Playing Camera 0</code>).</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    showScadaModal("ORBIX \u2014 SYSTEM FEATURES & OPERATOR MANUAL", manualHtml, true, true);
  }

  function showAboutModal() {
    showScadaModal("ABOUT \u2014 ORBIX VISION SYSTEM", `
      <h4>ORBIX HOT METAL SLAB THICKNESS VISION SYSTEM</h4>
      <p><strong>Version:</strong> ${currentAppVersion} Production Build</p>
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
    const pdfBtn = document.getElementById("btn-modal-open-pdf");

    if (closeBtn) closeBtn.addEventListener("click", closeScadaModal);
    if (okBtn) okBtn.addEventListener("click", closeScadaModal);

    if (pdfBtn) {
      pdfBtn.addEventListener("click", () => {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.open_pdf_manual) {
          const origText = pdfBtn.innerHTML;
          pdfBtn.innerHTML = "&#10004; OPENING MANUAL...";
          window.pywebview.api.open_pdf_manual().then(() => {
            setTimeout(() => { pdfBtn.innerHTML = origText; }, 2000);
          });
        }
      });
    }

    if (backdrop && win) {
      backdrop.addEventListener("click", (e) => {
        if (!win.contains(e.target)) closeScadaModal();
      });
    }

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
    const btnToggleRoi = document.getElementById("btn-toggle-roi-box");
    const wrapper = document.getElementById("video-wrapper");

    if (btnToggleRoi) {
      btnToggleRoi.addEventListener("click", () => {
        showRoiBox = !showRoiBox;
        btnToggleRoi.classList.toggle("active", showRoiBox);
        btnToggleRoi.style.opacity = showRoiBox ? "1" : "0.4";
        updateCaliperOverlay();
      });
    }

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

  function getVideoRenderRect(wrapper) {
    const w = wrapper.clientWidth;
    const h = wrapper.clientHeight;
    const targetAspect = 1920 / 1080;
    const currentAspect = w / (h || 1);
    let rw, rh, ox, oy;
    if (currentAspect > targetAspect) {
      rh = h;
      rw = h * targetAspect;
      ox = (w - rw) / 2;
      oy = 0;
    } else {
      rw = w;
      rh = w / targetAspect;
      ox = 0;
      oy = (h - rh) / 2;
    }
    return { w, h, rw, rh, ox, oy };
  }

  function initMouseInspection() {
    const wrapper = document.getElementById("video-wrapper");
    const tooltip = document.getElementById("caliper-tooltip");

    if (!wrapper) return;

    window.addEventListener("resize", () => {
      updateCaliperOverlay();
    });

    wrapper.addEventListener("mousedown", (e) => {
      if (!isSelectingRoi) return;
      const rect = wrapper.getBoundingClientRect();
      const vRect = getVideoRenderRect(wrapper);
      const rawX = Math.max(0, Math.min(vRect.rw, e.clientX - rect.left - vRect.ox));
      const rawY = Math.max(0, Math.min(vRect.rh, e.clientY - rect.top - vRect.oy));
      roiDragStart = { x: rawX, y: rawY };
      tempRoi = null;
    });

    wrapper.addEventListener("click", (e) => {
      if (!isCalibrating) return;
      const rect = wrapper.getBoundingClientRect();
      const vRect = getVideoRenderRect(wrapper);
      const rawX = Math.max(0, Math.min(vRect.rw, e.clientX - rect.left - vRect.ox));
      const rawY = Math.max(0, Math.min(vRect.rh, e.clientY - rect.top - vRect.oy));
      const fx = Math.round((rawX / vRect.rw) * 1920);
      const fy = Math.round((rawY / vRect.rh) * 1080);

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
      const vRect = getVideoRenderRect(wrapper);
      const rawX = e.clientX - rect.left - vRect.ox;
      const rawY = e.clientY - rect.top - vRect.oy;
      const clampedX = Math.max(0, Math.min(vRect.rw, rawX));
      const clampedY = Math.max(0, Math.min(vRect.rh, rawY));

      if (isSelectingRoi && roiDragStart) {
        const rx = Math.min(roiDragStart.x, clampedX);
        const ry = Math.min(roiDragStart.y, clampedY);
        const rw = Math.max(10, Math.abs(clampedX - roiDragStart.x));
        const rh = Math.max(10, Math.abs(clampedY - roiDragStart.y));

        const frameX = Math.round(Math.max(0, Math.min(1910, (rx / vRect.rw) * 1920)));
        const frameY = Math.round(Math.max(0, Math.min(1070, (ry / vRect.rh) * 1080)));
        const frameW = Math.round(Math.max(10, Math.min(1920 - frameX, (rw / vRect.rw) * 1920)));
        const frameH = Math.round(Math.max(10, Math.min(1080 - frameY, (rh / vRect.rh) * 1080)));

        tempRoi = { x: frameX, y: frameY, w: frameW, h: frameH };
        updateRoiDisplay(tempRoi);
        updateCaliperOverlay();
        return;
      }

      cursorXRatio = Math.max(0, Math.min(1, clampedX / (vRect.rw || 1)));
      cursorYRatio = Math.max(0, Math.min(1, clampedY / (vRect.rh || 1)));

      if (tooltip && !isSelectingRoi) {
        tooltip.style.display = "block";
        const maxTipX = rect.width - 230;
        const tipX = Math.min(maxTipX, Math.max(10, e.clientX - rect.left + 16));
        const tipY = Math.min(rect.height - 90, Math.max(20, e.clientY - rect.top - 20));
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

    const vRect = getVideoRenderRect(wrapper);
    const cx = vRect.ox + cursorXRatio * vRect.rw;

    const r = tempRoi || activeRoi;
    const rx = vRect.ox + (r.x / 1920) * vRect.rw;
    const ry = vRect.oy + (r.y / 1080) * vRect.rh;
    const rw = (r.w / 1920) * vRect.rw;
    const rh = (r.h / 1080) * vRect.rh;

    let topRatio = 0.33;
    let botRatio = 0.78;

    if (lastTelemetry && lastTelemetry.top_y !== undefined) {
      topRatio = Math.max(0, Math.min(1, lastTelemetry.top_y / 1080));
      botRatio = Math.max(0, Math.min(1, lastTelemetry.bottom_y / 1080));
    }

    const topY = vRect.oy + topRatio * vRect.rh;
    const botY = vRect.oy + botRatio * vRect.rh;

    let roiHtml = "";
    if (showRoiBox && (r.w < 1910 || r.h < 1070 || isSelectingRoi || roiDragStart)) {
      const isSelecting = isSelectingRoi || roiDragStart;
      const strokeColor = isSelecting ? "#ffb703" : "rgba(148, 163, 184, 0.65)";
      const handleFill = isSelecting ? "#ffb703" : "#64748b";
      const tagBg = isSelecting ? "#ffb703" : "#1e293b";
      const tagText = isSelecting ? "#000000" : "#94a3b8";
      const labelText = isSelecting ? "EDITING ROI..." : "ROI: SEARCH REGION";

      roiHtml = `
        <rect x="${rx}" y="${ry}" width="${rw}" height="${rh}" fill="rgba(100, 116, 139, 0.04)" stroke="${strokeColor}" stroke-width="${isSelecting ? 1.8 : 1.2}" stroke-dasharray="6 4"/>
        <rect x="${rx - 3}" y="${ry - 3}" width="6" height="6" fill="${handleFill}"/>
        <rect x="${rx + rw - 3}" y="${ry - 3}" width="6" height="6" fill="${handleFill}"/>
        <rect x="${rx - 3}" y="${ry + rh - 3}" width="6" height="6" fill="${handleFill}"/>
        <rect x="${rx + rw - 3}" y="${ry + rh - 3}" width="6" height="6" fill="${handleFill}"/>
        <rect x="${rx}" y="${Math.max(2, ry - 14)}" width="${isSelecting ? 90 : 116}" height="14" fill="${tagBg}" rx="2" opacity="0.9"/>
        <text x="${rx + 4}" y="${Math.max(12, ry - 3)}" fill="${tagText}" font-size="8.5" font-family="'Segoe UI Mono', monospace" font-weight="bold">${labelText}</text>
      `;
    }

    let edgeGraphic = "";
    if (showEdges) {
      edgeGraphic = `
        <line x1="${rx}" y1="${topY}" x2="${rx + rw}" y2="${topY}" stroke="#00e5ff" stroke-width="1.8" stroke-dasharray="8 4" opacity="0.85"/>
        <line x1="${rx}" y1="${botY}" x2="${rx + rw}" y2="${botY}" stroke="#00e5ff" stroke-width="1.8" stroke-dasharray="8 4" opacity="0.85"/>
        <line x1="${cx}" y1="${topY - 12}" x2="${cx}" y2="${botY + 12}" stroke="#555555" stroke-width="1" stroke-dasharray="3 3"/>
        <line x1="${cx}" y1="${topY}" x2="${cx}" y2="${botY}" stroke="#ffb703" stroke-width="2.5"/>
        <circle cx="${cx}" cy="${topY}" r="4.5" fill="#00e5ff" stroke="#000000" stroke-width="1.5"/>
        <circle cx="${cx}" cy="${botY}" r="4.5" fill="#00e5ff" stroke="#000000" stroke-width="1.5"/>
      `;
    }

    svg.innerHTML = `
      ${roiHtml}
      ${edgeGraphic}
    `;

    if (isCalibrating && calibPoints.length > 0) {
      calibPoints.forEach((pt, idx) => {
        const sx = vRect.ox + (pt.x / 1920) * vRect.rw;
        const sy = vRect.oy + (pt.y / 1080) * vRect.rh;
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
        botLabel.style.top = `${Math.min(vRect.h - 22, botY + 4)}px`;
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

    if (payload.version) {
      currentAppVersion = payload.version;
      const vBadge = document.getElementById("app-version-badge");
      if (vBadge) vBadge.textContent = `v${payload.version}`;
      const vSub = document.getElementById("app-version-subtext");
      if (vSub) vSub.textContent = `v${payload.version}`;
    }

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

