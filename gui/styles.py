"""
gui/styles.py — Dark and light QSS stylesheets for Sqeli.
"""

DARK = """
/* ── Base ─────────────────────────────────────────────────── */
QWidget {
    background-color: #12141f;
    color: #e2e4f0;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Main Window ───────────────────────────────────────────── */
#MainWindow {
    background-color: #12141f;
    border: 1px solid #2a2d42;
    border-radius: 12px;
}

/* ── Header bar ────────────────────────────────────────────── */
#HeaderBar {
    background-color: #0e1019;
    border-bottom: 1px solid #1e2130;
    border-radius: 0px;
}

#AppTitle {
    font-size: 15px;
    font-weight: 700;
    color: #00d4aa;
    letter-spacing: 1px;
    background: transparent;
}

#AppSubtitle {
    font-size: 10px;
    color: #4a4f6a;
    background: transparent;
}

#HeaderIcon {
    background: transparent;
}

/* ── Service Cards ─────────────────────────────────────────── */
#ServiceCard {
    background-color: #1a1d2e;
    border: 1px solid #1e2130;
    border-radius: 10px;
    margin: 4px 0px;
}

#ServiceCard:hover {
    border: 1px solid #2e3352;
}

#ServiceName {
    font-size: 14px;
    font-weight: 600;
    color: #c8cbe0;
}

#ServicePort {
    font-size: 11px;
    color: #4a4f6a;
    background: #0e1019;
    border-radius: 4px;
    padding: 2px 6px;
}

/* ── Status indicator ──────────────────────────────────────── */
#StatusDot[status="not_configured"] {
    color: #f59e0b;
}
#StatusDot[status="running"] {
    color: #22c55e;
}
#StatusDot[status="stopped"] {
    color: #4a4f6a;
}
#StatusDot[status="starting"] {
    color: #f59e0b;
}
#StatusDot[status="stopping"] {
    color: #f59e0b;
}
#StatusDot[status="error"] {
    color: #ef4444;
}

#StatusLabel {
    font-size: 11px;
    color: #4a4f6a;
}
#StatusLabel[status="not_configured"] {
    color: #f59e0b;
}
#StatusLabel[status="running"] {
    color: #22c55e;
}
#StatusLabel[status="error"] {
    color: #ef4444;
}

/* ── Buttons ───────────────────────────────────────────────── */
QPushButton {
    background-color: #1e2130;
    color: #c8cbe0;
    border: 1px solid #2a2d42;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 11px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #252840;
    border-color: #3d4160;
    color: #e2e4f0;
}
QPushButton:pressed {
    background-color: #1a1d2e;
}
QPushButton:disabled {
    color: #2e3352;
    border-color: #1a1d2e;
}

#BtnStart {
    background-color: #0d3d2b;
    color: #22c55e;
    border-color: #145c3f;
    min-width: 58px;
}
#BtnStart:hover {
    background-color: #145c3f;
}
#BtnStart:disabled {
    background-color: #0d1f17;
    color: #1e4d33;
    border-color: #0d1f17;
}

#BtnStop {
    background-color: #3d1414;
    color: #ef4444;
    border-color: #5c1f1f;
    min-width: 58px;
}
#BtnStop:hover {
    background-color: #5c1f1f;
}
#BtnStop:disabled {
    background-color: #1f0d0d;
    color: #4d1e1e;
    border-color: #1f0d0d;
}

#BtnRestart {
    background-color: #3d2d0d;
    color: #f59e0b;
    border-color: #5c4214;
    min-width: 68px;
}
#BtnRestart:hover {
    background-color: #5c4214;
}
#BtnRestart:disabled {
    background-color: #1f1709;
    color: #4d3a10;
    border-color: #1f1709;
}

#BtnPma {
    background-color: #1e1b4b;
    color: #a78bfa;
    border-color: #3730a3;
}
#BtnPma:hover {
    background-color: #312e81;
    color: #c4b5fd;
    border-color: #4f46e5;
}
#BtnPma:disabled {
    background-color: #13112b;
    color: #3e3870;
    border-color: #13112b;
}

#BtnHtdocs {
    background-color: #112233;
    color: #38bdf8;
    border-color: #0369a1;
}
#BtnHtdocs:hover {
    background-color: #0c4a6e;
    color: #7dd3fc;
    border-color: #0284c7;
}

#BtnWeb {
    background-color: #064e3b;
    color: #34d399;
    border-color: #047857;
}
#BtnWeb:hover {
    background-color: #047857;
    color: #6ee7b7;
    border-color: #059669;
}

#BtnConfig {
    background-color: #161928;
    color: #94a3b8;
    border: 1px solid #2a2d42;
    padding: 5px 8px;
    font-size: 11px;
    min-width: 62px;
}
#BtnConfig:hover {
    background-color: #252840;
    color: #f1f5f9;
    border-color: #3d4160;
}

#BtnIcon {
    background: transparent;
    border: none;
    color: #4a4f6a;
    font-size: 13px;
    padding: 4px 8px;
    border-radius: 6px;
}
#BtnIcon:hover {
    background-color: #1e2130;
    color: #c8cbe0;
}

/* ── Menu / Popup ──────────────────────────────────────────── */
QMenu {
    background-color: #12141f;
    border: 1px solid #2a2d42;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    background-color: transparent;
    color: #c8cbe0;
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    font-size: 12px;
}
QMenu::item:selected {
    background-color: #1e2130;
    color: #00d4aa;
}
QMenu::separator {
    height: 1px;
    background-color: #1e2130;
    margin: 4px 6px;
}

/* ── Log viewer ────────────────────────────────────────────── */
#LogView {
    background-color: #0a0c14;
    color: #6b7280;
    border: 1px solid #1a1d2e;
    border-radius: 6px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11px;
    padding: 4px;
}

/* ── Separator ─────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {
    color: #1e2130;
}

/* ── Settings Dialog ───────────────────────────────────────── */
QDialog {
    background-color: #12141f;
    border: 1px solid #2a2d42;
    border-radius: 10px;
}

QLabel {
    color: #9ca3af;
    font-size: 12px;
}

QLineEdit, QSpinBox {
    background-color: #0e1019;
    color: #e2e4f0;
    border: 1px solid #2a2d42;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
    selection-background-color: #00d4aa;
    selection-color: #0e1019;
}
QLineEdit:focus, QSpinBox:focus {
    border-color: #00d4aa;
}
QSpinBox::up-button, QSpinBox::down-button {
    background: #1a1d2e;
    border: none;
    width: 18px;
}

/* ── Toggle / Checkbox ─────────────────────────────────────── */
QCheckBox {
    color: #c8cbe0;
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #2a2d42;
    background: #0e1019;
}
QCheckBox::indicator:checked {
    background: #00d4aa;
    border-color: #00d4aa;
    image: none;
}

/* ── Scrollbar ─────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0e1019;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #2a2d42;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── GroupBox ──────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #1e2130;
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 8px;
    font-size: 11px;
    font-weight: 600;
    color: #4a4f6a;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    top: 0px;
    color: #4a4f6a;
}

/* ── ToolTip ───────────────────────────────────────────────── */
QToolTip {
    background-color: #1a1d2e;
    color: #e2e4f0;
    border: 1px solid #2a2d42;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
"""

LIGHT = """
/* ── Base ─────────────────────────────────────────────────── */
QWidget {
    background-color: #f4f5f9;
    color: #1a1d2e;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Main Window ───────────────────────────────────────────── */
#MainWindow {
    background-color: #f4f5f9;
    border: 1px solid #d4d6e4;
    border-radius: 12px;
}

/* ── Header bar ────────────────────────────────────────────── */
#HeaderBar {
    background-color: #eceef5;
    border-bottom: 1px solid #d4d6e4;
    border-radius: 0px;
}

#AppTitle {
    font-size: 15px;
    font-weight: 700;
    color: #2d3561;
    letter-spacing: 1px;
    background: transparent;
}

#AppSubtitle {
    font-size: 10px;
    color: #9ca3af;
    background: transparent;
}

#HeaderIcon {
    background: transparent;
}

/* ── Service Cards ─────────────────────────────────────────── */
#ServiceCard {
    background-color: #ffffff;
    border: 1px solid #d4d6e4;
    border-radius: 10px;
    margin: 4px 0px;
}

#ServiceCard:hover {
    border: 1px solid #b0b4cc;
}

#ServiceName {
    font-size: 14px;
    font-weight: 600;
    color: #1a1d2e;
}

#ServicePort {
    font-size: 11px;
    color: #6b7280;
    background: #eceef5;
    border-radius: 4px;
    padding: 2px 6px;
}

/* ── Status indicator ──────────────────────────────────────── */
#StatusDot[status="not_configured"]  { color: #d97706; }
#StatusDot[status="running"]  { color: #16a34a; }
#StatusDot[status="stopped"]  { color: #9ca3af; }
#StatusDot[status="starting"] { color: #d97706; }
#StatusDot[status="stopping"] { color: #d97706; }
#StatusDot[status="error"]    { color: #dc2626; }

#StatusLabel                       { font-size: 11px; color: #9ca3af; }
#StatusLabel[status="not_configured"] { color: #d97706; }
#StatusLabel[status="running"]      { color: #16a34a; }
#StatusLabel[status="error"]        { color: #dc2626; }

/* ── Buttons ───────────────────────────────────────────────── */
QPushButton {
    background-color: #eceef5;
    color: #1a1d2e;
    border: 1px solid #d4d6e4;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 11px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #dfe1ef;
    border-color: #b0b4cc;
}
QPushButton:pressed { background-color: #d4d6e4; }
QPushButton:disabled { color: #c0c2ce; border-color: #e4e5ef; }

#BtnStart  { background: #dcfce7; color: #16a34a; border-color: #bbf7d0; min-width: 58px; }
#BtnStart:hover  { background: #bbf7d0; }
#BtnStart:disabled { background: #f0f0f0; color: #b0c4b8; border-color: #e0e0e0; }
#BtnStop   { background: #fee2e2; color: #dc2626; border-color: #fecaca; min-width: 58px; }
#BtnStop:hover   { background: #fecaca; }
#BtnStop:disabled { background: #f5f0f0; color: #c4b0b0; border-color: #e8e0e0; }
#BtnRestart{ background: #fef3c7; color: #d97706; border-color: #fde68a; min-width: 68px; }
#BtnRestart:hover{ background: #fde68a; }
#BtnRestart:disabled { background: #f5f2e8; color: #c4b888; border-color: #ede8d0; }
#BtnPma { background: #ede9fe; color: #7c3aed; border-color: #ddd6fe; }
#BtnPma:hover { background: #ddd6fe; color: #6d28d9; }
#BtnPma:disabled { background: #f5f3ff; color: #c4b5fd; border-color: #ede9fe; }
#BtnHtdocs { background: #e0f2fe; color: #0284c7; border-color: #bae6fd; }
#BtnHtdocs:hover { background: #bae6fd; color: #0369a1; }
#BtnWeb { background: #d1fae5; color: #059669; border-color: #a7f3d0; }
#BtnWeb:hover { background: #a7f3d0; color: #047857; }

#BtnConfig {
    background-color: #ffffff;
    color: #4b5563;
    border: 1px solid #d4d6e4;
    padding: 5px 8px;
    font-size: 11px;
    min-width: 62px;
}
#BtnConfig:hover {
    background-color: #f3f4f6;
    color: #111827;
    border-color: #b0b4cc;
}

#BtnIcon {
    background: transparent;
    border: none;
    color: #9ca3af;
    font-size: 13px;
    padding: 4px 8px;
    border-radius: 6px;
}
#BtnIcon:hover {
    background-color: #dfe1ef;
    color: #1a1d2e;
}

/* ── Menu / Popup ──────────────────────────────────────────── */
QMenu {
    background-color: #ffffff;
    border: 1px solid #d4d6e4;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    background-color: transparent;
    color: #1a1d2e;
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    font-size: 12px;
}
QMenu::item:selected {
    background-color: #eceef5;
    color: #059669;
}
QMenu::separator {
    height: 1px;
    background-color: #e5e7eb;
    margin: 4px 6px;
}

/* ── Log viewer ────────────────────────────────────────────── */
#LogView {
    background-color: #1a1d2e;
    color: #6b7280;
    border: 1px solid #d4d6e4;
    border-radius: 6px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11px;
    padding: 4px;
}

/* ── Separator ─────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] { color: #d4d6e4; }

/* ── Settings Dialog ───────────────────────────────────────── */
QDialog { background-color: #f4f5f9; border: 1px solid #d4d6e4; border-radius: 10px; }
QLabel  { color: #4b5563; font-size: 12px; }

QLineEdit, QSpinBox {
    background-color: #ffffff;
    color: #1a1d2e;
    border: 1px solid #d4d6e4;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
}
QLineEdit:focus, QSpinBox:focus { border-color: #2d3561; }
QSpinBox::up-button, QSpinBox::down-button { background: #eceef5; border: none; width: 18px; }

/* ── Toggle / Checkbox ─────────────────────────────────────── */
QCheckBox { color: #1a1d2e; spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 4px;
    border: 2px solid #d4d6e4; background: #ffffff;
}
QCheckBox::indicator:checked { background: #2d3561; border-color: #2d3561; }

/* ── Scrollbar ─────────────────────────────────────────────── */
QScrollBar:vertical { background: #eceef5; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #c0c2ce; border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

/* ── GroupBox ──────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #d4d6e4; border-radius: 8px;
    margin-top: 16px; padding-top: 8px;
    font-size: 11px; font-weight: 600; color: #9ca3af;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; top: 0px; }

/* ── ToolTip ───────────────────────────────────────────────── */
QToolTip {
    background-color: #ffffff; color: #1a1d2e;
    border: 1px solid #d4d6e4; border-radius: 4px;
    padding: 4px 8px; font-size: 11px;
}
"""


def get(theme: str) -> str:
    return DARK if theme == "dark" else LIGHT
