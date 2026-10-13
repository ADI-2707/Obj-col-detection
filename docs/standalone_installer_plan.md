# Orbix Standalone Windows Executable & Installer — Implementation Plan

## 1. Executive Summary

The objective of this initiative is to package **Orbix** into an enterprise-grade Windows desktop application:
- **Zero Prerequisites**: Target machines do not require Python, Git, C++ build tools, or pip. All Python binaries, PyTorch runtimes, OpenCV codecs, and YOLO model weights are self-contained.
- **Professional Windows Setup Wizard**: Users install the software via a standard `Orbix-Setup-v1.4.0.exe` installer with customary steps (install location, desktop icon, start menu folder, and clean uninstaller).
- **Instant Cold Start**: Utilizes a dual-stage architecture (**PyInstaller `--onedir` + Inno Setup compression**) so execution starts within 1–2 seconds, avoiding the 15–30 second extraction delay typical of naive `--onefile` packaging with PyTorch.

---

## 2. Packaging Architecture

```
+---------------------------------------------------------------------------------------+
|                                    SOURCE CODE                                         |
|  - orbix/ package (capture, pipeline, visualizer, detector, motion, tracker)           |
|  - Assets & weights (yolov8n.pt, icons, default configs)                              |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                             STAGE 1: PYINSTALLER COMPILATION                          |
|  - Tool: PyInstaller with custom orbix.spec                                           |
|  - Mode: --onedir (Standalone folder containing Python runtime, DLLs, and frozen app) |
|  - Binary hooks: PyTorch C++ bindings, OpenCV video I/O codecs, NumPy/Torch tensors   |
|  - Output: dist/Orbix/ (Contains Orbix.exe + frozen runtime bundle)                   |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                             STAGE 2: WINDOWS INSTALLER CREATION                       |
|  - Tool: Inno Setup 6 (ISCC.exe)                                                      |
|  - Script: installer/OrbixSetup.iss                                                   |
|  - Features:                                                                          |
|    * Program Files installation (or %LOCALAPPDATA% for non-admin mode)                |
|    * Desktop shortcut & Start Menu group with high-res icon (.ico)                    |
|    * Windows "Installed Apps" registration with clean unins000.exe                    |
|    * LZMA2 high-ratio solid compression                                               |
|  - Output: dist/Orbix-Setup-v1.4.0.exe (Single distributable setup file)              |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                                 END USER EXPERIENCE                                   |
|  1. Download Orbix-Setup-v1.4.0.exe                                                   |
|  2. Double-click setup -> Next -> Install -> Finish                                    |
|  3. Double-click desktop icon "Orbix" -> App launches immediately                     |
+---------------------------------------------------------------------------------------+
```

---

## 3. Key Technical Challenges & Architectural Solutions

### A. Read-Only Program Files vs. Writable Application Data
- **Problem**: When installed to `C:\Program Files\Orbix`, standard Windows users do not have write access to that folder. Any attempt to write CSV logs (`data/logs/*.csv`) or save screenshots to the installation directory will fail with `PermissionError`.
- **Solution**: Implement a dynamic filesystem helper `orbix/paths.py`:
  - **Read-Only Resource Path (`get_bundle_path`)**: Resolves bundled static files (like `yolov8n.pt`, icons) from `sys._MEIPASS` when frozen, or repo root when running in development.
  - **Writable Data Path (`get_user_data_path`)**: Automatically creates and uses `%LOCALAPPDATA%\Orbix\` (or `%APPDATA%\Orbix\`) for CSV logs, user calibration parameters, and exported captures.

### B. Startup Latency (`--onedir` vs `--onefile`)
- **Problem**: PyTorch + Ultralytics + OpenCV libraries exceed 500 MB uncompressed. A `--onefile` executable must extract all 500 MB to a temporary directory in `%TEMP%` on **every single application launch**, causing unbearable 15–25s delays.
- **Solution**: Build a frozen directory via `--onedir`, then wrap the entire folder inside an Inno Setup installer. The files are unpacked once during installation, enabling instantaneous (< 2 second) startup times.

### C. Dynamic PyTorch & OpenCV Hidden Imports
- **Problem**: PyTorch and Ultralytics dynamically load C++ DLLs (`torch_python.dll`, `c10.dll`, `fbgemm.dll`, `opencv_videoio_ffmpeg*.dll`) and meta-packages that standard static analysis fails to trace.
- **Solution**: Author an explicit `orbix.spec` defining:
  - Hidden imports for `ultralytics`, `torch`, `supervision`, `cv2`, `PIL`.
  - Proper exclusion of unnecessary packages (e.g., `matplotlib` if unused, `tkinter`, `IPython`, `tests`, `cuda` if CPU-only) to trim installer size by ~30–40%.

### D. Windows High-DPI & Console Window Management
- **Problem**: In manufacturing plant environments, 4K monitors and high scaling (150%–200%) are standard. Also, an open CMD console window looks unpolished for commercial software.
- **Solution**:
  - Configure `--windowed` / `--noconsole` mode in PyInstaller.
  - Embed Windows DPI awareness manifests so fonts and video viewports scale crisply without Windows blur.

---

## 4. Implementation Work Breakdown

### Phase 1: Codebase Runtime Hardening for Frozen Binaries
1. **Create `orbix/paths.py`**:
   - `get_resource_path(relative_path: str) -> Path`: Handles `sys._MEIPASS` detection.
   - `get_data_dir() -> Path`: Provides `%LOCALAPPDATA%\Orbix` for logs and configurations.
2. **Refactor Resource & Log References**:
   - Update `Config.model_path` to resolve default `yolov8n.pt` through `get_resource_path()`.
   - Update `Config.output_dir` in `orbix/config.py` to default to `get_data_dir() / "logs"`.
3. **Verify Dev/Test Compatibility**:
   - Ensure all 95 tests continue passing under both development and simulated frozen environments.

### Phase 2: PyInstaller Spec File & Local Compilation
1. **Create `packaging/orbix.spec`**:
   - Entry point: `orbix/__main__.py`.
   - Include datas: `yolov8n.pt`, assets, branding icons.
   - Exclude bloat: test suites, unnecessary PyTorch test modules.
2. **Create Icon Assets**:
   - Generate multi-resolution Windows icon `assets/orbix.ico` (16x16, 32x32, 48x48, 64x64, 128x128, 256x256).
3. **Automate Freeze Build**:
   - Script `scripts/build_exe.bat` to install build requirements (`pyinstaller>=6.5`), compile the bundle, and verify `dist/Orbix/Orbix.exe`.

### Phase 3: Inno Setup Windows Installer Script
1. **Create `installer/OrbixSetup.iss`**:
   - Application metadata: Name, Version (`1.4.0`), Publisher (`Orbix Vision`).
   - Dual installation architecture: Supports standard System install (`{autopf}\Orbix`) with fallback to User install (`{localappdata}\Programs\Orbix`) without UAC elevation prompts if user is not admin.
   - Shortcut targets: Desktop Icon and Start Menu group.
   - Registry and uninstaller registration.
   - Visual styling: Clean modern Inno Setup wizard with branded banner graphics.
2. **Build Automation**:
   - Add ISCC invocation to `scripts/build_installer.bat`.
   - Detect system Inno Setup compiler (`C:\Program Files (x86)\Inno Setup 6\ISCC.exe`) or automatically fetch via `winget`.

### Phase 4: Automated Testing & Validation
1. **Clean Virtual Machine / Non-Python Host Validation**:
   - Test installation on a machine without Python installed.
   - Verify camera feed acquisition, YOLO inference, tracking, and CSV log writes.
   - Verify uninstallation leaves no orphan files in `Program Files`.
2. **Automated Packaging Test in `tests/`**:
   - Add unit test verifying `get_resource_path` and `get_data_dir` logic.

### Phase 5: CI/CD Integration (GitHub Actions)
1. **Add `installer.yml` Workflow**:
   - Triggered on Git tags (`v*`) or manual dispatch.
   - Sets up Python on `windows-latest`.
   - Installs Inno Setup via `chocolatey` / `winget` in CI.
   - Compiles `Orbix-Setup-vX.X.X.exe`.
   - Uploads installer as an artifact and attaches it to the GitHub Release.

---

## 5. Deliverables & File Layout

```
Orbix/
├── assets/
│   └── orbix.ico                 # High-resolution application icon
├── packaging/
│   ├── orbix.spec                # PyInstaller bundling definition
│   └── app_manifest.xml          # Windows DPI and UAC manifest
├── installer/
│   ├── OrbixSetup.iss            # Inno Setup installation script
│   └── wizard_banner.bmp         # Installer wizard graphics
├── orbix/
│   ├── paths.py                  # Frozen vs. local path resolver
│   └── ...
├── scripts/
│   ├── build_exe.bat             # Compiles PyInstaller --onedir bundle
│   └── build_installer.bat       # Full pipeline: freeze + Inno Setup build
└── .github/workflows/
    └── release_installer.yml     # GitHub Actions automated release builder
```

---

## 6. Success & Acceptance Criteria

| Requirement | Acceptance Threshold |
| :--- | :--- |
| **Zero Python Dependency** | App runs on a vanilla Windows 10/11 system without Python or C++ runtimes installed. |
| **Startup Speed** | Desktop shortcut click to live camera window < **2.5 seconds**. |
| **Installation Flow** | Standard wizard installs to `Program Files` or `%LocalAppData%` in < **30 seconds**. |
| **Permissions** | Logs successfully save to `%LocalAppData%\Orbix\logs` without admin/UAC elevation. |
| **Uninstallation** | Uninstaller cleanly removes binary files and Start Menu shortcuts. |
| **Test Integrity** | Full test suite maintains 100% pass rate. |
