"""
gui/main_window.py — Main floating panel for Sqeli.

Appears when the tray icon is left-clicked. Frameless, dark-by-default,
showing service cards for Apache and MySQL.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTextEdit, QSizePolicy,
    QSpacerItem, QMenu,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtSlot, QUrl
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QDesktopServices, QAction
from pathlib import Path
import os

from core.config import get_app_root
from core.service_manager import ServiceManager, ServiceStatus
from gui.settings_dialog import SettingsDialog
from gui.setup_dialog import SetupDialog
import gui.styles as styles


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    return f


def _open_file_in_editor(file_path: Path):
    """Opens a file in the system default text editor or Notepad."""
    if not file_path.exists():
        return
    try:
        os.startfile(str(file_path))
    except Exception:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))


# ── Service Card ──────────────────────────────────────────────────────────────

class ServiceCard(QWidget):
    """One row per service showing status + control buttons."""

    _STATUS_ICONS = {
        ServiceStatus.NOT_CONFIGURED: "⚙️",
        ServiceStatus.RUNNING:        "🟢",
        ServiceStatus.STOPPED:        "⚫",
        ServiceStatus.STARTING:       "🟡",
        ServiceStatus.STOPPING:       "🟠",
        ServiceStatus.ERROR:          "🔴",
    }
    _STATUS_LABELS = {
        ServiceStatus.NOT_CONFIGURED: "Not configured",
        ServiceStatus.RUNNING:        "Running",
        ServiceStatus.STOPPED:        "Stopped",
        ServiceStatus.STARTING:       "Starting…",
        ServiceStatus.STOPPING:       "Stopping…",
        ServiceStatus.ERROR:          "Error",
    }

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.setObjectName("ServiceCard")
        self._build()
        self._refresh(service.status)
        service.status_changed.connect(self._on_status)

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(8)

        # Status dot
        self._dot = QLabel(self._STATUS_ICONS[ServiceStatus.STOPPED])
        self._dot.setObjectName("StatusDot")
        self._dot.setFont(QFont("Segoe UI Emoji", 12))
        self._dot.setFixedWidth(20)
        self._dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self._dot)

        # Name + status text
        col = QVBoxLayout()
        col.setSpacing(1)
        self._name_lbl = QLabel(self.service.name)
        self._name_lbl.setObjectName("ServiceName")
        col.addWidget(self._name_lbl)
        self._status_lbl = QLabel("Stopped")
        self._status_lbl.setObjectName("StatusLabel")
        col.addWidget(self._status_lbl)
        outer.addLayout(col)

        # Port badge
        port = self.service.cfg.get("port", "")
        self._port_lbl = QLabel(f":{port}")
        self._port_lbl.setObjectName("ServicePort")
        outer.addWidget(self._port_lbl)

        outer.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding))

        # Config dropdown button
        self._btn_conf = QPushButton("⚙️ Config ▾")
        self._btn_conf.setObjectName("BtnConfig")
        self._btn_conf.setToolTip(f"Open {self.service.name} configuration files")
        self._btn_conf.clicked.connect(self._show_config_menu)
        outer.addWidget(self._btn_conf)

        # Buttons with Messenger-style emojis
        self._btn_start = QPushButton("▶️ Start")
        self._btn_start.setObjectName("BtnStart")
        self._btn_start.clicked.connect(self.service.start)

        self._btn_stop = QPushButton("⏹️ Stop")
        self._btn_stop.setObjectName("BtnStop")
        self._btn_stop.clicked.connect(self.service.stop)

        self._btn_restart = QPushButton("🔄 Restart")
        self._btn_restart.setObjectName("BtnRestart")
        self._btn_restart.setToolTip("Restart service")
        self._btn_restart.clicked.connect(self.service.restart)

        for btn in (self._btn_start, self._btn_stop, self._btn_restart):
            outer.addWidget(btn)

    def _show_config_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(self.styleSheet())
        bin_path = self.service.cfg.get("bin", "")

        if self.service.name == "Apache":
            if bin_path:
                apache_root = Path(bin_path).resolve().parent.parent
                httpd_conf = apache_root / "conf" / "httpd.conf"
                ssl_conf = apache_root / "conf" / "extra" / "httpd-ssl.conf"
                vhosts_conf = apache_root / "conf" / "extra" / "httpd-vhosts.conf"
                
                act_httpd = menu.addAction("📄 httpd.conf")
                act_httpd.triggered.connect(lambda: _open_file_in_editor(httpd_conf))
                
                if ssl_conf.exists():
                    act_ssl = menu.addAction("🔒 httpd-ssl.conf")
                    act_ssl.triggered.connect(lambda: _open_file_in_editor(ssl_conf))
                if vhosts_conf.exists():
                    act_vhosts = menu.addAction("🌐 httpd-vhosts.conf")
                    act_vhosts.triggered.connect(lambda: _open_file_in_editor(vhosts_conf))

            # PHP configs
            php_ini = get_app_root() / "bin" / "php" / "php.ini"
            if php_ini.exists():
                menu.addSeparator()
                act_php = menu.addAction("🐘 php.ini")
                act_php.triggered.connect(lambda: _open_file_in_editor(php_ini))

        elif self.service.name == "MySQL":
            if bin_path:
                bin_p = Path(bin_path).resolve()
                mariadb_root = bin_p.parent.parent
                my_ini_data = mariadb_root / "data" / "my.ini"
                my_ini_root = mariadb_root / "my.ini"
                target_my_ini = my_ini_data if my_ini_data.exists() else my_ini_root

                act_my = menu.addAction("🐬 my.ini")
                act_my.triggered.connect(lambda: _open_file_in_editor(target_my_ini))

            # phpMyAdmin config
            pma_config = get_app_root() / "bin" / "phpmyadmin" / "config.inc.php"
            if pma_config.exists():
                menu.addSeparator()
                act_pma = menu.addAction("🗄️ config.inc.php (phpMyAdmin)")
                act_pma.triggered.connect(lambda: _open_file_in_editor(pma_config))

        menu.exec(self._btn_conf.mapToGlobal(self._btn_conf.rect().bottomLeft()))

    @pyqtSlot(str, str)
    def _on_status(self, name: str, status: str):
        if name == self.service.name:
            self._refresh(status)

    def _refresh(self, status: str):
        icon = self._STATUS_ICONS.get(status, "⚫")
        label = self._STATUS_LABELS.get(status, status.title())
        self._dot.setText(icon)
        self._dot.setProperty("status", status)
        self._status_lbl.setText(label)
        self._status_lbl.setProperty("status", status)

        not_configured = status == ServiceStatus.NOT_CONFIGURED
        running = status == ServiceStatus.RUNNING
        stopped = status == ServiceStatus.STOPPED
        busy = status in (ServiceStatus.STARTING, ServiceStatus.STOPPING)
        error = status == ServiceStatus.ERROR

        self._btn_start.setEnabled(stopped or error)
        self._btn_stop.setEnabled(running or busy)
        self._btn_restart.setEnabled(running)

        if not_configured:
            self._btn_start.setEnabled(False)
            self._btn_start.setToolTip("Use ⬇ Setup or ⚙ Settings to configure the binary path")
        else:
            self._btn_start.setToolTip("")

        # Force Qt to re-evaluate property-based stylesheet selectors
        for w in (self._dot, self._status_lbl):
            w.style().unpolish(w)
            w.style().polish(w)

    def update_port(self, port):
        self._port_lbl.setText(f":{port}")


# ── Log Panel ─────────────────────────────────────────────────────────────────

class LogPanel(QTextEdit):
    MAX_LINES = 120

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogView")
        self.setReadOnly(True)
        self.setFixedHeight(110)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    def append_log(self, service: str, line: str):
        prefix_color = "#00d4aa" if service == "Apache" else "#a78bfa"
        self.append(
            f'<span style="color:{prefix_color};">[{service}]</span> '
            f'<span style="color:#6b7280;">{line}</span>'
        )
        # Trim old lines
        doc = self.document()
        while doc.blockCount() > self.MAX_LINES:
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QWidget):
    def __init__(self, svc_manager: ServiceManager, cfg: dict, app_ref, parent=None):
        super().__init__(parent)
        self._svc = svc_manager
        self._cfg = cfg
        self._app = app_ref   # reference to SqeliApp for callbacks

        self.setObjectName("MainWindow")
        self.setWindowTitle("Sqeli")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(520)

        self._drag_pos = None
        self._build_ui()
        self._connect_signals()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QWidget()
        inner.setObjectName("MainWindow")
        root.addWidget(inner)

        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("HeaderBar")
        header.setFixedHeight(52)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(14, 0, 10, 0)
        h_lay.setSpacing(8)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title = QLabel("Sqeli")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Local Dev Server")
        subtitle.setObjectName("AppSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_lay.addLayout(title_col)

        h_lay.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding))

        # Theme toggle
        self._theme_btn = QPushButton()
        self._theme_btn.setObjectName("BtnIcon")
        self._theme_btn.setFixedSize(52, 32)
        self._theme_btn.setToolTip("Toggle theme")
        self._theme_btn.clicked.connect(self._toggle_theme)
        h_lay.addWidget(self._theme_btn)

        # Setup wizard
        setup_btn = QPushButton("⬇️ Setup")
        setup_btn.setObjectName("BtnIcon")
        setup_btn.setFixedHeight(32)
        setup_btn.setToolTip("Auto-install Apache & MySQL")
        setup_btn.clicked.connect(self._open_setup)
        h_lay.addWidget(setup_btn)

        # Settings
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setObjectName("BtnIcon")
        settings_btn.setFixedHeight(32)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._open_settings)
        h_lay.addWidget(settings_btn)

        # Close (hide to tray)
        close_btn = QPushButton("✕")
        close_btn.setObjectName("BtnIcon")
        close_btn.setFixedSize(32, 32)
        close_btn.setToolTip("Hide to tray")
        close_btn.clicked.connect(self.hide)
        h_lay.addWidget(close_btn)

        layout.addWidget(header)

        # ── Body ──────────────────────────────────────────────
        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(12, 12, 12, 8)
        body_lay.setSpacing(8)

        # Start All / Stop All row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(6)
        self._btn_start_all = QPushButton("▶️ Start All")
        self._btn_start_all.setObjectName("BtnStart")
        self._btn_start_all.clicked.connect(self._svc.start_all)
        ctrl_row.addWidget(self._btn_start_all)

        self._btn_stop_all = QPushButton("⏹️ Stop All")
        self._btn_stop_all.setObjectName("BtnStop")
        self._btn_stop_all.clicked.connect(self._svc.stop_all)
        ctrl_row.addWidget(self._btn_stop_all)

        self._btn_web = QPushButton("🌐 Web")
        self._btn_web.setObjectName("BtnWeb")
        self._btn_web.setToolTip("Open local website in browser (http://localhost)")
        self._btn_web.clicked.connect(self._open_web)
        ctrl_row.addWidget(self._btn_web)

        self._btn_htdocs = QPushButton("📁 htdocs")
        self._btn_htdocs.setObjectName("BtnHtdocs")
        self._btn_htdocs.setToolTip("Open htdocs folder in File Explorer")
        self._btn_htdocs.clicked.connect(self._open_htdocs)
        ctrl_row.addWidget(self._btn_htdocs)

        self._btn_pma = QPushButton("🗄️ phpMyAdmin")
        self._btn_pma.setObjectName("BtnPma")
        self._btn_pma.setToolTip("Open phpMyAdmin in browser (http://localhost/phpmyadmin)")
        self._btn_pma.clicked.connect(self._open_phpmyadmin)
        ctrl_row.addWidget(self._btn_pma)

        body_lay.addLayout(ctrl_row)
        body_lay.addWidget(_make_sep())

        # Service cards
        self._apache_card = ServiceCard(self._svc.apache)
        self._mysql_card = ServiceCard(self._svc.mysql)
        body_lay.addWidget(self._apache_card)
        body_lay.addWidget(self._mysql_card)

        body_lay.addWidget(_make_sep())

        # Log panel (collapsible label)
        log_toggle_row = QHBoxLayout()
        self._log_label = QLabel("Console output")
        self._log_label.setStyleSheet("font-size: 11px; color: #4a4f6a;")
        log_toggle_row.addWidget(self._log_label)
        log_toggle_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding))
        toggle_log_btn = QPushButton("v")
        toggle_log_btn.setObjectName("BtnIcon")
        toggle_log_btn.setFixedSize(24, 20)
        toggle_log_btn.setToolTip("Toggle log")
        toggle_log_btn.clicked.connect(self._toggle_log)
        log_toggle_row.addWidget(toggle_log_btn)
        body_lay.addLayout(log_toggle_row)

        self._log = LogPanel()
        body_lay.addWidget(self._log)

        layout.addWidget(body)
        self._update_theme_icon()

    def _connect_signals(self):
        self._svc.apache.log_line.connect(self._log.append_log)
        self._svc.mysql.log_line.connect(self._log.append_log)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _open_web(self):
        port = self._cfg.get("apache", {}).get("port", 80)
        port_str = "" if int(port) == 80 else f":{port}"
        url = f"http://localhost{port_str}/"
        QDesktopServices.openUrl(QUrl(url))

    def _open_htdocs(self):
        from pathlib import Path
        custom_htdocs = self._cfg.get("apache", {}).get("htdocs", "").strip()
        if custom_htdocs:
            htdocs_path = Path(custom_htdocs)
        else:
            htdocs_path = get_app_root() / "htdocs"
        htdocs_path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(htdocs_path)))

    def _open_phpmyadmin(self):
        port = self._cfg.get("apache", {}).get("port", 80)
        port_str = "" if int(port) == 80 else f":{port}"
        url = f"http://localhost{port_str}/phpmyadmin/"
        QDesktopServices.openUrl(QUrl(url))

    def _toggle_theme(self):
        new_theme = "light" if self._cfg.get("theme") == "dark" else "dark"
        self._cfg["theme"] = new_theme
        self._app.apply_theme(new_theme)
        self._update_theme_icon()

    def _update_theme_icon(self):
        icon = "Light" if self._cfg.get("theme") == "dark" else "Dark"
        self._theme_btn.setText(icon)

    def _open_setup(self):
        dlg = SetupDialog(self._cfg, self)
        dlg.setStyleSheet(self.styleSheet())
        if dlg.exec():
            self._svc.update_config(self._cfg)
            self._apache_card.update_port(self._cfg.get("apache", {}).get("port", 80))
            self._mysql_card.update_port(self._cfg.get("mysql", {}).get("port", 3306))
            self._app.save_config()

    def _open_settings(self):
        dlg = SettingsDialog(self._cfg, self)
        dlg.setStyleSheet(self.styleSheet())
        if dlg.exec():
            updated = dlg.get_config()
            old_apache_docroot = self._cfg.get("apache", {}).get("htdocs", "")
            old_apache_port = self._cfg.get("apache", {}).get("port", 80)
            
            self._cfg.update(updated)
            self._svc.update_config(updated)
            self._apache_card.update_port(updated.get("apache", {}).get("port", 80))
            self._mysql_card.update_port(updated.get("mysql", {}).get("port", 3306))
            self._app.save_config()

            # If Apache is running and docroot/port changed, restart it immediately to apply
            new_apache_docroot = updated.get("apache", {}).get("htdocs", "")
            new_apache_port = updated.get("apache", {}).get("port", 80)
            if self._svc.apache.status == ServiceStatus.RUNNING:
                if old_apache_docroot != new_apache_docroot or old_apache_port != new_apache_port:
                    self._svc.apache.restart()

    def _toggle_log(self):
        self._log.setVisible(not self._log.isVisible())
        self.adjustSize()

    # ── Drag to move (frameless window) ───────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── Position near tray ────────────────────────────────────────────────────

    def show_near_tray(self):
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        screen = QApplication.primaryScreen().availableGeometry()
        # Bottom-right corner just above taskbar — standard tray popup position
        x = screen.right() - self.width() - 12
        y = screen.bottom() - self.height() - 12
        self.move(x, y)
        self.show()
        self.raise_()
        # Delay activateWindow slightly — Windows focus-stealing prevention
        # blocks it when called synchronously right after show()
        QTimer.singleShot(50, self._force_focus)

    def _force_focus(self):
        self.setWindowState(
            (self.windowState() & ~Qt.WindowState.WindowMinimized)
            | Qt.WindowState.WindowActive
        )
        self.raise_()
        self.activateWindow()
