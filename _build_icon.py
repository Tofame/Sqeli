# _build_icon.py — converts assets/icon_dark.png to assets/icon.ico for PyInstaller
import sys
from pathlib import Path

try:
    from PIL import Image
    src = Path(__file__).parent / "assets" / "icon_dark.png"
    dst = Path(__file__).parent / "assets" / "icon.ico"
    img = Image.open(src).convert("RGBA")
    img.save(dst, format="ICO", sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])
    print(f"Icon saved: {dst}")
except Exception as e:
    print(f"WARNING: Icon conversion failed: {e}", file=sys.stderr)
    sys.exit(1)
