"""
app.py — Core application class for Sqeli.

Owns: config, ServiceManager, system tray, MainWindow.
"""

import sys
import os
import atexit
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QImage, QColor
from PyQt6.QtCore import Qt

from core import config as cfg_mod
from core.service_manager import ServiceManager, ServiceStatus
from gui.main_window import MainWindow
from gui.setup_dialog import SetupDialog
import gui.styles as styles


def _get_assets_dir() -> Path:
	if getattr(sys, "frozen", False):
		meipass = getattr(sys, "_MEIPASS", None)
		if meipass and (Path(meipass) / "assets").exists():
			return Path(meipass) / "assets"
		exe_assets = Path(sys.executable).parent / "assets"
		if exe_assets.exists():
			return exe_assets
		internal_assets = Path(sys.executable).parent / "_internal" / "assets"
		if internal_assets.exists():
			return internal_assets
	return Path(__file__).resolve().parent / "assets"


ASSETS = _get_assets_dir()


def _load_icon(name: str) -> QIcon:
    path = ASSETS / name
    if path.exists():
        return QIcon(str(path))
    # Fallback: draw a colored circle
    img = QImage(32, 32, QImage.Format.Format_ARGB32)
    img.fill(QColor("#00d4aa"))
    return QIcon(QPixmap.fromImage(img))


class SqeliApp:
    def __init__(self):
        self._cfg = cfg_mod.load()
        self._qapp = QApplication.instance() or QApplication(sys.argv)
        self._qapp.setQuitOnLastWindowClosed(False)
        self._qapp.setApplicationName("Sqeli")
        self._qapp.setApplicationVersion("1.0.0")

        self._svc = ServiceManager(self._cfg)
        self._window: MainWindow | None = None
        self._tray: QSystemTrayIcon | None = None

        # Clean shutdown hooks
        self._qapp.aboutToQuit.connect(self._svc.stop_all)
        atexit.register(self._svc.stop_all)
        self._install_os_shutdown_handlers()

        # Suppress Windows error dialog popups for helper child processes
        if sys.platform == "win32":
            try:
                import ctypes
                # SEM_FAILCRITICALERRORS (0x0001) | SEM_NOGPFAULTERRORBOX (0x0002)
                ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002)
            except Exception:
                pass

        self._current_theme = self._cfg.get("theme", "dark")
        self.apply_theme(self._current_theme)

        self._init_window()
        self._init_tray()

        # Wire tray icon to service status for visual indicator
        self._svc.apache.status_changed.connect(self._on_any_status)
        self._svc.mysql.status_changed.connect(self._on_any_status)

        # Auto-start services if the user enabled that option
        if self._cfg.get("autostart_services", False):
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(800, self._svc.start_all)

    def _install_os_shutdown_handlers(self):
        """Catches Windows system logoff/shutdown and SIGTERM/SIGINT signals."""
        import signal
        try:
            signal.signal(signal.SIGINT, lambda *_: self._quit())
            signal.signal(signal.SIGTERM, lambda *_: self._quit())
        except Exception:
            pass

        if sys.platform == "win32":
            try:
                import ctypes
                HandlerRoutine = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)

                def _console_ctrl_handler(ctrl_type):
                    # 0: CTRL_C, 1: CTRL_BREAK, 2: CTRL_CLOSE, 5: CTRL_LOGOFF, 6: CTRL_SHUTDOWN
                    self._svc.stop_all()
                    return False

                self._ctrl_handler_ref = HandlerRoutine(_console_ctrl_handler)
                ctypes.windll.kernel32.SetConsoleCtrlHandler(self._ctrl_handler_ref, True)
            except Exception:
                pass

    # ── Bootstrap ─────────────────────────────────────────────────────────────

    def _init_window(self):
        self._window = MainWindow(self._svc, self._cfg, self)

    def _init_tray(self):
        icon = _load_icon(
            "icon_dark.png" if self._current_theme == "dark" else "icon_light.png"
        )
        self._tray = QSystemTrayIcon(icon, self._qapp)
        self._tray.setToolTip("Sqeli — Local Dev Manager")

        menu = QMenu()
        menu.setStyleSheet(
            """
            QMenu {
                background: #1a1d2e; color: #e2e4f0;
                border: 1px solid #2a2d42; border-radius: 6px;
                padding: 4px;
            }
            QMenu::item { padding: 6px 18px; border-radius: 4px; }
            QMenu::item:selected { background: #252840; }
            QMenu::separator { height: 1px; background: #2a2d42; margin: 4px 0; }
            """
        )
        open_act = menu.addAction("Open Sqeli")
        open_act.triggered.connect(self._show_window)

        menu.addSeparator()

        start_act = menu.addAction("▶  Start All")
        start_act.triggered.connect(self._svc.start_all)

        stop_act = menu.addAction("■  Stop All")
        stop_act.triggered.connect(self._svc.stop_all)

        menu.addSeparator()

        quit_act = menu.addAction("Quit")
        quit_act.triggered.connect(self._quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def apply_theme(self, theme: str):
        self._current_theme = theme
        self._cfg["theme"] = theme
        self._qapp.setStyleSheet(styles.get(theme))
        if self._tray:
            icon_name = "icon_dark.png" if theme == "dark" else "icon_light.png"
            self._tray.setIcon(_load_icon(icon_name))
        self.save_config()

    # ── Tray interaction ──────────────────────────────────────────────────────

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()

    def _show_window(self):
        if self._window:
            if self._window.isVisible():
                self._window.hide()
            else:
                self._window.show_near_tray()

    def _on_any_status(self, name: str, status: str):
        """Update tray tooltip to reflect current states."""
        a = self._svc.apache.status.title()
        m = self._svc.mysql.status.title()
        self._tray.setToolTip(f"Sqeli  |  Apache: {a}  •  MySQL: {m}")

    # ── Config ────────────────────────────────────────────────────────────────

    def save_config(self):
        cfg_mod.save(self._cfg)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _quit(self):
        self._svc.stop_all()
        self._tray.hide()
        self._qapp.quit()

    def run(self) -> int:
        return self._qapp.exec()
