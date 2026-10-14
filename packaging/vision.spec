from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

repo_root = Path.cwd()

datas = [
    (str(repo_root / "yolov8n.pt"), "."),
    (str(repo_root / "packaging" / "icons" / "orbix.ico"), "packaging/icons"),
    (str(repo_root / "packaging" / "icons" / "vision.ico"), "packaging/icons"),
    (str(repo_root / "assets"), "assets"),
    (str(repo_root / "vision" / "web"), "vision/web"),
    (str(repo_root / "vision" / "web"), "orbix/web"),
]

datas += collect_data_files("ultralytics")

hiddenimports = [
    "ultralytics",
    "torch",
    "supervision",
    "cv2",
    "PIL",
    "numpy",
    "webview",
    "vision",
    "vision.paths",
    "vision.config",
    "vision.capture",
    "vision.detector",
    "vision.logger",
    "vision.motion",
    "vision.tracker",
    "vision.visualizer",
    "vision.measurement",
    "vision.bridge",
    "vision.pipeline",
]

hiddenimports += collect_submodules("ultralytics")

excludes = [
    "tkinter",
    "pytest",
    "IPython",
    "test",
    "tests",
]

a = Analysis(
    [str(repo_root / "vision" / "__main__.py")],
    pathex=[str(repo_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Orbix",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(repo_root / "packaging" / "icons" / "vision.ico") if (repo_root / "packaging" / "icons" / "vision.ico").exists() else str(repo_root / "packaging" / "icons" / "orbix.ico"),
    manifest=str(repo_root / "packaging" / "app_manifest.xml"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Orbix",
)
