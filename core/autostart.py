"""
core/autostart.py — Windows registry helpers for launch-on-login.
"""

import sys
import os
import winreg

APP_NAME = "Sqeli"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_exe_path() -> str:
    """Return the command to register: pythonw + this script, or the frozen exe."""
    if getattr(sys, "frozen", False):
        return sys.executable
    # Running as plain Python — use pythonw so no console window appears
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    main_script = os.path.abspath(sys.argv[0] if sys.argv else "main.py")
    return f'"{pythonw}" "{main_script}"'


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable() -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_exe_path())
    except OSError as e:
        print(f"[Autostart] Failed to enable: {e}")


def disable() -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"[Autostart] Failed to disable: {e}")


def set_enabled(state: bool) -> None:
    enable() if state else disable()
