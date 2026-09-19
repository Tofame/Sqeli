"""
gui/settings_dialog.py — Settings modal for Sqeli.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QFileDialog, QGroupBox, QCheckBox,
    QFrame, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core import autostart


class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self._cfg = cfg
        self.setWindowTitle("Sqeli — Settings")
        self.setObjectName("SettingsDialog")
        self.setMinimumWidth(460)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint
        )
        self._build_ui()
        self._load_values()

    def showEvent(self, event):
        super().showEvent(event)
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.left() + (screen.width() - self.width()) // 2,
            screen.top() + (screen.height() - self.height()) // 2,
        )

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── Title ─────────────────────────────────────────────
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #00d4aa; margin-bottom: 4px;")
        root.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # ── Apache ────────────────────────────────────────────
        apache_box = QGroupBox("Apache")
        apache_lay = QVBoxLayout(apache_box)
        apache_lay.setSpacing(8)

        apache_lay.addWidget(QLabel("Binary path  (httpd.exe)"))
        self._apache_bin = QLineEdit()
        self._apache_bin.setPlaceholderText("C:/laragon/bin/apache/bin/httpd.exe")
        apache_lay.addLayout(self._path_row(self._apache_bin))

        apache_lay.addWidget(QLabel("Web root directory  (htdocs)"))
        self._apache_htdocs = QLineEdit()
        self._apache_htdocs.setPlaceholderText("Default: <app_folder>/htdocs")
        apache_lay.addLayout(self._path_row(self._apache_htdocs, dir_mode=True))

        apache_lay.addWidget(QLabel("Port"))
        self._apache_port = QSpinBox()
        self._apache_port.setRange(1, 65535)
        apache_lay.addWidget(self._apache_port)

        root.addWidget(apache_box)

        # ── MySQL ─────────────────────────────────────────────
        mysql_box = QGroupBox("MySQL")
        mysql_lay = QVBoxLayout(mysql_box)
        mysql_lay.setSpacing(8)

        mysql_lay.addWidget(QLabel("Binary path  (mysqld.exe)"))
        self._mysql_bin = QLineEdit()
        self._mysql_bin.setPlaceholderText("C:/laragon/bin/mysql/bin/mysqld.exe")
        mysql_lay.addLayout(self._path_row(self._mysql_bin))

        mysql_lay.addWidget(QLabel("Data directory  (optional)"))
        self._mysql_data = QLineEdit()
        self._mysql_data.setPlaceholderText("C:/laragon/data")
        mysql_lay.addLayout(self._path_row(self._mysql_data, dir_mode=True))

        mysql_lay.addWidget(QLabel("Port"))
        self._mysql_port = QSpinBox()
        self._mysql_port.setRange(1, 65535)
        mysql_lay.addWidget(self._mysql_port)

        root.addWidget(mysql_box)

        # ── General ───────────────────────────────────────────
        general_box = QGroupBox("General")
        general_lay = QVBoxLayout(general_box)

        self._autostart_cb = QCheckBox("Launch Sqeli on Windows startup")
        general_lay.addWidget(self._autostart_cb)

        self._autostart_svc_cb = QCheckBox("Auto-start Apache && MySQL when Sqeli launches")
        general_lay.addWidget(self._autostart_svc_cb)

        root.addWidget(general_box)

        # ── Buttons ───────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep2)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        save_btn = btns.button(QDialogButtonBox.StandardButton.Save)
        save_btn.setObjectName("BtnStart")
        root.addWidget(btns)

    def _path_row(self, line_edit: QLineEdit, dir_mode: bool = False) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(line_edit)
        browse = QPushButton("Browse…")
        browse.setFixedWidth(80)
        browse.clicked.connect(lambda: self._browse(line_edit, dir_mode))
        row.addWidget(browse)
        return row

    # ── Data ─────────────────────────────────────────────────────────────────

    def _load_values(self):
        self._apache_bin.setText(self._cfg.get("apache", {}).get("bin", ""))
        self._apache_htdocs.setText(self._cfg.get("apache", {}).get("htdocs", ""))
        self._apache_port.setValue(self._cfg.get("apache", {}).get("port", 80))
        self._mysql_bin.setText(self._cfg.get("mysql", {}).get("bin", ""))
        self._mysql_data.setText(self._cfg.get("mysql", {}).get("datadir", ""))
        self._mysql_port.setValue(self._cfg.get("mysql", {}).get("port", 3306))
        self._autostart_cb.setChecked(autostart.is_enabled())
        self._autostart_svc_cb.setChecked(self._cfg.get("autostart_services", False))

    def _save(self):
        self._cfg.setdefault("apache", {})
        self._cfg.setdefault("mysql", {})
        self._cfg["apache"]["bin"] = self._apache_bin.text().strip()
        self._cfg["apache"]["htdocs"] = self._apache_htdocs.text().strip()
        self._cfg["apache"]["port"] = self._apache_port.value()
        self._cfg["mysql"]["bin"] = self._mysql_bin.text().strip()
        self._cfg["mysql"]["datadir"] = self._mysql_data.text().strip()
        self._cfg["mysql"]["port"] = self._mysql_port.value()

        want_autostart = self._autostart_cb.isChecked()
        autostart.set_enabled(want_autostart)
        self._cfg["autostart"] = want_autostart
        self._cfg["autostart_services"] = self._autostart_svc_cb.isChecked()

        self.accept()

    def _browse(self, field: QLineEdit, dir_mode: bool):
        start = os.path.dirname(field.text()) if field.text() else "C:/"
        if dir_mode:
            path = QFileDialog.getExistingDirectory(self, "Select directory", start)
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select executable", start, "Executables (*.exe)"
            )
        if path:
            field.setText(path.replace("/", "/"))

    def get_config(self) -> dict:
        return self._cfg
