"""
build.py — Builds Sqeli release executable into build/ directory.

Usage:
    python build.py
    (or double-click build.bat which calls this)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
ASSETS = ROOT / "assets"
BUILD_DIR = ROOT / "build"
BUILD_TMP = ROOT / "build_tmp"
ICON_ICO = ASSETS / "icon.ico"
ICON_SRC = ASSETS / "icon_dark.png"
OUT_DIR = BUILD_DIR / "Sqeli"
OUT_EXE = OUT_DIR / "Sqeli.exe"

SEPARATOR = "=" * 50


def step(n, msg):
    print(f"\n[{n}/3] {msg}")


def run(cmd, **kwargs):
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"\nERROR: command failed: {' '.join(str(c) for c in cmd)}")
        sys.exit(1)


# ── 1. Ensure PyInstaller ─────────────────────────────────────────────────────
print(f"\n Sqeli Build\n {SEPARATOR}")
print(f" Output: {OUT_EXE}")

step(1, "Checking PyInstaller...")
try:
    import PyInstaller
    print(f"     PyInstaller {PyInstaller.__version__} ready.")
except ImportError:
    print("     Installing PyInstaller...")
    run([sys.executable, "-m", "pip", "install", "pyinstaller==6.22.3"])

# ── 2. Convert icon if needed ─────────────────────────────────────────────────
step(2, "Checking application icon...")
use_icon = False
if not ICON_ICO.exists() or (ICON_SRC.exists() and ICON_SRC.stat().st_mtime > ICON_ICO.stat().st_mtime):
    try:
        from PIL import Image
        img = Image.open(ICON_SRC).convert("RGBA")
        img.save(ICON_ICO, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print(f"     Generated: {ICON_ICO}")
        use_icon = True
    except Exception as e:
        print(f"     WARNING: {e} — building without icon.")
elif ICON_ICO.exists():
    use_icon = True
    print(f"     Using cached: {ICON_ICO}")

# ── 3. Run PyInstaller (onedir mode with persistent build cache) ───────────────
step(3, "Running PyInstaller (incremental fast build)...")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onedir",
    "--windowed",
    "--noconfirm",
    "--name", "Sqeli",
    "--distpath", str(BUILD_DIR),
    "--workpath", str(BUILD_TMP),
    "--specpath", str(BUILD_TMP),
    "--add-data", f"{ASSETS}{chr(59)}assets",
    "--hidden-import", "winreg",
]

if use_icon and ICON_ICO.exists():
    cmd += ["--icon", str(ICON_ICO)]

cmd.append(str(ROOT / "main.py"))

run(cmd)

print(f"\n Done! Release ready -> {OUT_EXE}\n")

