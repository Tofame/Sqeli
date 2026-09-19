"""
gui/setup_dialog.py — Built-in setup wizard to download Apache + MariaDB.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QWidget,
    QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from core.downloader import InstallWorker


# ── Single service install card ───────────────────────────────────────────────

class ServiceInstallCard(QWidget):
    def __init__(self, service: str, display_name: str, subtitle: str, parent=None):
        super().__init__(parent)
        self._service = service
        self._worker: InstallWorker | None = None
        self.installed_payload: str | None = None   # binary path (or "bin|data")

        self.setObjectName("ServiceCard")
        self._build(display_name, subtitle)

    def _build(self, name: str, subtitle: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(6)

        # Header row
        header = QHBoxLayout()
        name_lbl = QLabel(name)
        name_lbl.setObjectName("ServiceName")
        header.addWidget(name_lbl)
        header.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding))

        self._state_lbl = QLabel("Not installed")
        self._state_lbl.setStyleSheet("font-size: 11px; color: #4a4f6a;")
        header.addWidget(self._state_lbl)
        outer.addLayout(header)

        sub = QLabel(subtitle)
        sub.setObjectName("AppSubtitle")
        sub.setWordWrap(True)
        outer.addWidget(sub)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedHeight(6)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(
            """
            QProgressBar {
                background: #1e2130; border-radius: 3px; border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00d4aa, stop:1 #7c3aed);
                border-radius: 3px;
            }
            """
        )
        self._bar.hide()
        outer.addWidget(self._bar)

        # Status text
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("font-size: 11px; color: #6b7280;")
        self._status_lbl.hide()
        outer.addWidget(self._status_lbl)

        # Button
        self._btn = QPushButton(f"⬇  Install {name}")
        self._btn.setObjectName("BtnStart")
        self._btn.clicked.connect(self._start_install)
        outer.addWidget(self._btn)

    # ── Install ───────────────────────────────────────────────────────────────

    def _start_install(self):
        # Disconnect old worker signals if retrying
        if self._worker is not None:
            try:
                self._worker.progress.disconnect()
                self._worker.status.disconnect()
                self._worker.done.disconnect()
                self._worker.error.disconnect()
            except RuntimeError:
                pass

        self._btn.setEnabled(False)
        self._btn.setText("Installing…")
        self._bar.show()
        self._bar.setValue(0)
        self._status_lbl.show()
        self._state_lbl.setText("Downloading…")

        self._worker = InstallWorker(self._service)
        self._worker.progress.connect(self._on_progress)
        self._worker.status.connect(self._on_status)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    @pyqtSlot(int)
    def _on_progress(self, pct: int):
        self._bar.setValue(pct)

    @pyqtSlot(str)
    def _on_status(self, msg: str):
        self._status_lbl.setText(msg)

    @pyqtSlot(str)
    def _on_done(self, payload: str):
        self.installed_payload = payload
        self._bar.setValue(100)
        self._btn.setText("✓  Installed")
        self._btn.setObjectName("BtnStart")
        self._btn.setEnabled(False)
        self._state_lbl.setText("✓ Ready")
        self._state_lbl.setStyleSheet("font-size: 11px; color: #22c55e;")
        self._status_lbl.setText("Installation complete.")
        # Notify parent dialog
        parent = self.parent()
        while parent and not isinstance(parent, SetupDialog):
            parent = parent.parent()
        if parent:
            parent.on_card_done()

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        self._bar.hide()
        self._btn.setText("⚠  Retry")
        self._btn.setEnabled(True)
        self._state_lbl.setText("Failed")
        self._state_lbl.setStyleSheet("font-size: 11px; color: #ef4444;")
        self._status_lbl.setText(f"Error: {msg[:120]}")
        self._status_lbl.setStyleSheet("font-size: 11px; color: #ef4444;")


# ── Setup Dialog ──────────────────────────────────────────────────────────────

class SetupDialog(QDialog):
    """
    Modal wizard that downloads, extracts, and configures Apache + MariaDB.
    After both are installed it updates cfg in-place and calls accept().
    """

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self.setWindowTitle("Sqeli — Auto Setup")
        self.setMinimumWidth(480)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint
        )
        self._build_ui()

    def showEvent(self, event):
        super().showEvent(event)
        # Center on screen
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.left() + (screen.width() - self.width()) // 2,
            screen.top() + (screen.height() - self.height()) // 2,
        )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Title
        title = QLabel("Auto Setup")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #00d4aa;")
        root.addWidget(title)

        desc = QLabel(
            "Sqeli will download, extract and configure Apache and MariaDB "
            "automatically into the <code>bin/</code> folder next to this app. "
            "No installer, no admin rights required."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px; color: #9ca3af; line-height: 1.5;")
        root.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # Apache card
        self._apache_card = ServiceInstallCard(
            "apache",
            "Apache HTTP Server",
            "Latest stable from Apache Lounge (Win64 VS17) — no VC++ runtimes needed.",
            self,
        )
        root.addWidget(self._apache_card)

        # MySQL card
        self._mysql_card = ServiceInstallCard(
            "mysql",
            "MariaDB (MySQL-compatible)",
            "Latest stable MariaDB Win64 ZIP — drop-in MySQL replacement, smaller download.",
            self,
        )
        root.addWidget(self._mysql_card)

        # phpMyAdmin card
        self._pma_card = ServiceInstallCard(
            "phpmyadmin",
            "phpMyAdmin + PHP 8",
            "Installs PHP 8 (Thread-Safe) & phpMyAdmin, automatically integrated into Apache.",
            self,
        )
        root.addWidget(self._pma_card)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep2)

        # Bottom row
        bottom = QHBoxLayout()
        note = QLabel("⚡  Packages can be installed in any order.")
        note.setStyleSheet("font-size: 11px; color: #4a4f6a;")
        bottom.addWidget(note)
        bottom.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding))

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.reject)
        bottom.addWidget(self._close_btn)

        self._apply_btn = QPushButton("✓  Apply & Close")
        self._apply_btn.setObjectName("BtnStart")
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self._apply)
        bottom.addWidget(self._apply_btn)

        root.addLayout(bottom)

    # ── Callbacks from cards ──────────────────────────────────────────────────

    def on_card_done(self):
        """Called by each card when its install finishes."""
        all_done = (
            self._apache_card.installed_payload is not None
            and self._mysql_card.installed_payload is not None
        )
        if all_done:
            self._apply_btn.setEnabled(True)
            self._apply_btn.setText("✓  Apply & Close  (all ready)")
        elif (
            self._apache_card.installed_payload is not None
            or self._mysql_card.installed_payload is not None
            or self._pma_card.installed_payload is not None
        ):
            self._apply_btn.setEnabled(True)

    def _apply(self):
        """Write discovered paths into cfg."""
        if self._apache_card.installed_payload:
            self._cfg.setdefault("apache", {})
            self._cfg["apache"]["bin"] = self._apache_card.installed_payload

        if self._mysql_card.installed_payload:
            # payload is "bin_path|data_dir"
            parts = self._mysql_card.installed_payload.split("|", 1)
            self._cfg.setdefault("mysql", {})
            self._cfg["mysql"]["bin"] = parts[0]
            if len(parts) > 1:
                self._cfg["mysql"]["datadir"] = parts[1]

        self.accept()
