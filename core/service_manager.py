"""
core/service_manager.py — Apache and MySQL process lifecycle management.

Each service runs as a QThread-monitored subprocess. Status signals are emitted
so the GUI can react without blocking the main thread.
"""

import subprocess
import os
import signal
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class ServiceStatus:
    NOT_CONFIGURED = "not_configured"
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class Service(QObject):
    status_changed = pyqtSignal(str, str)   # (name, status)
    log_line = pyqtSignal(str, str)         # (name, line)

    def __init__(self, name: str, cfg: dict, parent=None):
        super().__init__(parent)
        self.name = name
        self.cfg = cfg
        self._proc: Optional[subprocess.Popen] = None
        self._status = ServiceStatus.STOPPED

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(1500)
        self._poll_timer.timeout.connect(self._poll)

        # Reflect missing binary immediately on startup
        if not self._bin_exists():
            self._status = ServiceStatus.NOT_CONFIGURED

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def status(self) -> str:
        return self._status

    def _bin_exists(self) -> bool:
        bin_path = self.cfg.get("bin", "")
        return bool(bin_path) and Path(bin_path).exists()

    def start(self) -> None:
        if self._status in (ServiceStatus.RUNNING, ServiceStatus.STARTING):
            return
        bin_path = self.cfg.get("bin", "")
        if not bin_path or not Path(bin_path).exists():
            self._set_status(ServiceStatus.NOT_CONFIGURED)
            self.log_line.emit(
                self.name,
                f"Binary not found: {bin_path!r}. Use ⬇ Setup or ⚙ Settings.",
            )
            return

        self._set_status(ServiceStatus.STARTING)
        try:
            if self.name == "Apache":
                self._sync_apache_htdocs()
            cmd = self._build_cmd()
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._poll_timer.start()
            self.log_line.emit(self.name, f"Started (PID {self._proc.pid})")
        except OSError as e:
            self._set_status(ServiceStatus.ERROR)
            self.log_line.emit(self.name, f"Failed to start: {e}")

    def stop(self) -> None:
        if self._status == ServiceStatus.STOPPED:
            return
        self._set_status(ServiceStatus.STOPPING)
        self._poll_timer.stop()
        if self._proc:
            try:
                # If this is MySQL, perform a clean database shutdown via mariadb-admin/mysqladmin
                if self.name == "MySQL":
                    self._graceful_mysql_shutdown()
                else:
                    self._proc.terminate()

                # Wait up to 5s for clean shutdown before forceful kill
                try:
                    self._proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
            except OSError:
                pass
            self._proc = None
        self._set_status(ServiceStatus.STOPPED)
        self.log_line.emit(self.name, "Stopped.")

    def _graceful_mysql_shutdown(self) -> None:
        """Flushes InnoDB buffers and closes MariaDB tables safely via mysqladmin."""
        bin_path = self.cfg.get("bin", "")
        if not bin_path:
            self._proc.terminate()
            return
        bin_dir = Path(bin_path).parent
        admin_candidates = [
            bin_dir / "mariadb-admin.exe",
            bin_dir / "mysqladmin.exe",
        ]
        admin_bin = None
        for cand in admin_candidates:
            if cand.exists():
                admin_bin = cand
                break

        if admin_bin:
            port = str(self.cfg.get("port", 3306))
            try:
                # Include bin_dir in PATH so dependent DLLs load without issue
                env = os.environ.copy()
                env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
                
                subprocess.run(
                    [str(admin_bin), "-u", "root", f"--port={port}", "shutdown"],
                    capture_output=True,
                    timeout=5,
                    cwd=str(bin_dir),
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                return
            except Exception:
                pass
        # Fallback to terminate() if admin tool not present or timed out
        self._proc.terminate()

    def restart(self) -> None:
        self.stop()
        self.start()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _sync_apache_htdocs(self) -> None:
        """Ensures Apache httpd.conf DocumentRoot and Listen port match configuration."""
        bin_path = self.cfg.get("bin", "")
        if not bin_path:
            return
        apache_root = Path(bin_path).resolve().parent.parent
        custom_htdocs = self.cfg.get("htdocs", "").strip()
        if custom_htdocs:
            htdocs_dir = Path(custom_htdocs)
        else:
            from core.config import get_app_root
            htdocs_dir = get_app_root() / "htdocs"

        from core.downloader import patch_apache_document_root, patch_apache_ssl
        patch_apache_document_root(apache_root, htdocs_dir)
        patch_apache_ssl(apache_root, htdocs_dir)

        # Sync Listen port
        conf = apache_root / "conf" / "httpd.conf"
        if conf.exists():
            import re
            port = self.cfg.get("port", 80)
            text = conf.read_text(encoding="utf-8", errors="replace")
            # Only match top-level Listen <port>, do not touch Listen 443 inside <IfModule ssl_module>
            text = re.sub(r'^(?!\s*<)Listen\s+\d+', f'Listen {port}', text, flags=re.MULTILINE)
            conf.write_text(text, encoding="utf-8")

    def _build_cmd(self) -> list:
        bin_path = self.cfg["bin"]
        if self.name == "MySQL":
            datadir = self.cfg.get("datadir", "")
            port = self.cfg.get("port", 3306)
            cmd = [bin_path, f"--port={port}"]
            if datadir:
                cmd.append(f"--datadir={datadir}")
            return cmd
        else:  # Apache
            # -DFOREGROUND keeps httpd in the foreground as a child process.
            # Do NOT use -k start — that tries to launch a Windows Service
            # (requires admin + service registration) and exits with code 2.
            return [bin_path, "-DFOREGROUND"]

    def _set_status(self, s: str) -> None:
        if self._status != s:
            self._status = s
            self.status_changed.emit(self.name, s)

    def _poll(self) -> None:
        if self._proc is None:
            self._poll_timer.stop()
            self._set_status(ServiceStatus.STOPPED)
            return
        ret = self._proc.poll()
        if ret is None:
            # Still alive — drain stdout for log lines
            if self._proc.stdout:
                try:
                    line = self._proc.stdout.readline()
                    if line:
                        self.log_line.emit(
                            self.name, line.decode("utf-8", errors="replace").rstrip()
                        )
                except OSError:
                    pass
            if self._status == ServiceStatus.STARTING:
                self._set_status(ServiceStatus.RUNNING)
        else:
            self._poll_timer.stop()
            self._proc = None
            self._set_status(ServiceStatus.STOPPED)
            self.log_line.emit(self.name, f"Process exited (code {ret}).")


class ServiceManager(QObject):
    """Owns all services and exposes a unified interface."""

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.apache = Service("Apache", cfg.get("apache", {}), self)
        self.mysql = Service("MySQL", cfg.get("mysql", {}), self)
        self._services = [self.apache, self.mysql]

    def update_config(self, cfg: dict) -> None:
        self.apache.cfg = cfg.get("apache", {})
        self.mysql.cfg = cfg.get("mysql", {})
        # Re-evaluate NOT_CONFIGURED <-> STOPPED after paths may have changed
        for svc in self._services:
            if svc.status == ServiceStatus.NOT_CONFIGURED and svc._bin_exists():
                svc._set_status(ServiceStatus.STOPPED)
            elif svc.status == ServiceStatus.STOPPED and not svc._bin_exists():
                svc._set_status(ServiceStatus.NOT_CONFIGURED)

    def start_all(self) -> None:
        for svc in self._services:
            if svc.cfg.get("enabled", True):
                svc.start()

    def stop_all(self) -> None:
        for svc in self._services:
            svc.stop()

    def all_running(self) -> bool:
        return all(s.status == ServiceStatus.RUNNING for s in self._services)

    def any_running(self) -> bool:
        return any(s.status == ServiceStatus.RUNNING for s in self._services)
