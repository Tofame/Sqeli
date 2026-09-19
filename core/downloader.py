"""
core/downloader.py — Downloads and installs Apache + MariaDB for Sqeli.

Uses urllib (stdlib only, no extra deps). Runs in a QThread so the UI stays
responsive. Emits granular signals for progress bars and status labels.
"""

from __future__ import annotations

import os
import re
import json
import shutil
import zipfile
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from html.parser import HTMLParser

from PyQt6.QtCore import QThread, pyqtSignal
from core.config import get_app_root

# ── Installation root ─────────────────────────────────────────────────────────

BIN_ROOT = get_app_root() / "bin"
HTDOCS_ROOT = get_app_root() / "htdocs"

# ── URL discovery ─────────────────────────────────────────────────────────────

APACHE_LOUNGE_URL = "https://www.apachelounge.com/download/"
MARIADB_API_URL = "https://downloads.mariadb.org/rest-api/mariadb/"

_UA = "Mozilla/5.0 (compatible; Sqeli/1.0)"


def _get(url: str, timeout: int = 15) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


class _ApacheLinkParser(HTMLParser):
    """Extracts the first Win64 VS17 ZIP download link from apachelounge.com."""

    def __init__(self):
        super().__init__()
        self.found: str | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "a" and not self.found:
            href = dict(attrs).get("href", "")
            if re.search(r"httpd-[\d.]+-\d+-win64-VS\d+\.zip", href, re.I):
                if href.startswith("http"):
                    self.found = href
                else:
                    self.found = "https://www.apachelounge.com" + href


def find_apache_url() -> str:
    """Scrape Apache Lounge to find the latest Win64 VS17 httpd ZIP URL."""
    html = _get(APACHE_LOUNGE_URL).decode("utf-8", errors="replace")
    parser = _ApacheLinkParser()
    parser.feed(html)
    if not parser.found:
        raise RuntimeError(
            "Could not locate Apache download link on apachelounge.com.\n"
            "The site may have changed layout. Please download manually."
        )
    return parser.found


def find_mariadb_url() -> tuple[str, str]:
    """
    Query the MariaDB REST API for the latest stable LTS Win64 ZIP.
    Returns (download_url, version_string).

    API note:
    - Top-level field is 'major_releases'.
    - Each release's files use 'file_name', not 'package_name'.
    - 'file_download_url' points back to the REST API; we build a real
      mirror URL from the filename instead.
    """
    raw = _get(MARIADB_API_URL).decode("utf-8")
    data = json.loads(raw)

    releases = data.get("major_releases", [])

    # Prefer LTS Stable, fall back to any Stable
    target_release = None
    for prefer_lts in (True, False):
        for rel in releases:
            status = rel.get("release_status", "")
            support = rel.get("release_support_type", "")
            is_stable = "Stable" in status
            is_lts = "Long Term" in support
            if is_stable and (not prefer_lts or is_lts):
                target_release = rel["release_id"]
                break
        if target_release:
            break

    if not target_release:
        raise RuntimeError("Could not find a stable MariaDB release via REST API.")

    # Fetch files for that major release branch
    files_url = f"{MARIADB_API_URL}{target_release}/"
    raw2 = _get(files_url).decode("utf-8")
    data2 = json.loads(raw2)

    # releases is a dict keyed by patch version; take the first (latest)
    for patch_version, release in data2.get("releases", {}).items():
        for f in release.get("files", []):
            # API uses 'file_name', not 'package_name'
            fname = f.get("file_name", "")
            if (
                "winx64" in fname.lower()
                and fname.endswith(".zip")
                and "debug" not in fname.lower()
            ):
                # archive.mariadb.org serves the real file directly
                dl_url = (
                    f"https://archive.mariadb.org/mariadb-{patch_version}"
                    f"/winx64-packages/{fname}"
                )
                return dl_url, patch_version

    raise RuntimeError(
        f"Could not find a Win64 ZIP for MariaDB {target_release}. "
        "Check https://mariadb.org/download/"
    )


def find_php_url() -> str:
	"""Find the latest PHP 8.4.x / 8.x Win64 Thread Safe ZIP for Apache."""
	archives_url = "https://windows.php.net/downloads/releases/archives/"
	html = _get(archives_url).decode("utf-8", errors="replace")
	matches = re.findall(
		r'href=[\"\'](php-(\d+)\.(\d+)\.(\d+)-Win32-(?:vs16|vs17)-x64\.zip)[\"\']',
		html,
		re.I,
	)
	if not matches:
		raise RuntimeError("Could not find suitable PHP 8.x Thread-Safe download.")
	# Target PHP <= 8.4 for broad phpMyAdmin compatibility
	filtered = [
		(int(m[1]), int(m[2]), int(m[3]), m[0])
		for m in matches
		if int(m[1]) == 8 and int(m[2]) <= 4
	]
	if not filtered:
		filtered = [(int(m[1]), int(m[2]), int(m[3]), m[0]) for m in matches if int(m[1]) == 8]
	sorted_pkgs = sorted(filtered)
	latest_zip = sorted_pkgs[-1][3]
	return f"{archives_url}{latest_zip}"


def find_phpmyadmin_url() -> str:
	"""Return the download URL for phpMyAdmin."""
	return "https://files.phpmyadmin.net/phpMyAdmin/5.2.2/phpMyAdmin-5.2.2-all-languages.zip"


def patch_apache_for_php(apache_root: Path, php_root: Path, pma_root: Path | None = None):
	"""Configures Apache httpd.conf to load PHP and alias /phpmyadmin."""
	conf = apache_root / "conf" / "httpd.conf"
	if not conf.exists():
		return
	text = conf.read_text(encoding="utf-8", errors="replace")
	php_fwd = str(php_root).replace("\\", "/")

	# Find php8apache2_4.dll
	dll_candidates = list(php_root.glob("php8apache2_4.dll"))
	if not dll_candidates:
		dll_candidates = list(php_root.glob("php*apache*.dll"))
	php_dll = str(dll_candidates[0]).replace("\\", "/") if dll_candidates else f"{php_fwd}/php8apache2_4.dll"

	# Enable DirectoryIndex index.php
	if re.search(r'DirectoryIndex\s+index\.html', text):
		text = re.sub(
			r'DirectoryIndex\s+index\.html',
			'DirectoryIndex index.php index.html',
			text,
			count=1,
		)

	# Remove any existing Sqeli PHP & phpMyAdmin blocks
	text = re.sub(
		r'# ─── Sqeli PHP & phpMyAdmin ───.*?# ─── End Sqeli PHP ───\n?',
		'',
		text,
		flags=re.DOTALL,
	)

	extra_block = f"""
# ─── Sqeli PHP & phpMyAdmin ───
LoadModule php_module "{php_dll}"
PHPIniDir "{php_fwd}"
AddType application/x-httpd-php .php
"""
	if pma_root and pma_root.exists():
		pma_fwd = str(pma_root).replace("\\", "/")
		extra_block += f"""
Alias /phpmyadmin "{pma_fwd}"
<Directory "{pma_fwd}">
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>
"""
	extra_block += "# ─── End Sqeli PHP ───\n"

	text = text.strip() + "\n" + extra_block
	conf.write_text(text, encoding="utf-8")


def patch_apache_document_root(apache_root: Path, htdocs_path: Path):
	"""Updates DocumentRoot and <Directory> in httpd.conf to point to htdocs_path."""
	conf = apache_root / "conf" / "httpd.conf"
	if not conf.exists():
		return
	text = conf.read_text(encoding="utf-8", errors="replace")
	htdocs_path.mkdir(parents=True, exist_ok=True)
	htdocs_fwd = str(htdocs_path.resolve()).replace("\\", "/")

	# Patch DocumentRoot
	text = re.sub(
		r'^DocumentRoot\s+"[^"]*"',
		f'DocumentRoot "{htdocs_fwd}"',
		text,
		flags=re.MULTILINE,
	)
	# Replace DocumentRoot Directory block with Options, AllowOverride All, and disabled OS caching
	if re.search(r'<Directory\s+"[^"]*(?:htdocs|www|public|html)[^"]*">.*?</Directory>', text, re.DOTALL):
		text = re.sub(
			r'<Directory\s+"[^"]*(?:htdocs|www|public|html)[^"]*">.*?</Directory>',
			f'<Directory "{htdocs_fwd}">\n    Options Indexes FollowSymLinks\n    AllowOverride All\n    Require all granted\n    EnableMMAP Off\n    EnableSendfile Off\n</Directory>',
			text,
			count=1,
			flags=re.DOTALL,
		)
	conf.write_text(text, encoding="utf-8")


def ensure_ssl_certificate(apache_root: Path) -> tuple[Path, Path]:
	"""Generates a SAN self-signed SSL certificate for localhost, 127.0.0.1, ::1 if not present."""
	ssl_dir = apache_root / "conf" / "ssl"
	ssl_dir.mkdir(parents=True, exist_ok=True)
	key_file = ssl_dir / "server.key"
	cert_file = ssl_dir / "server.crt"

	if key_file.exists() and cert_file.exists():
		return key_file, cert_file

	openssl_bin = apache_root / "bin" / "openssl.exe"
	if not openssl_bin.exists():
		return key_file, cert_file

	cnf_text = """
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = localhost
O = Sqeli Local Development

[v3_req]
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
"""
	tmp_cnf = ssl_dir / "sqeli_ssl.cnf"
	tmp_cnf.write_text(cnf_text, encoding="utf-8")

	import subprocess
	cmd = [
		str(openssl_bin),
		"req", "-x509", "-nodes", "-days", "3650",
		"-newkey", "rsa:2048",
		"-keyout", str(key_file),
		"-out", str(cert_file),
		"-config", str(tmp_cnf),
	]
	subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
	tmp_cnf.unlink(missing_ok=True)
	return key_file, cert_file


def patch_apache_ssl(apache_root: Path, htdocs_path: Path):
	"""Enables mod_ssl, mod_socache_shmcb, Listen 443, and an SSL VirtualHost."""
	conf = apache_root / "conf" / "httpd.conf"
	if not conf.exists():
		return
	text = conf.read_text(encoding="utf-8", errors="replace")

	# Enable mod_ssl and mod_socache_shmcb
	text = re.sub(
		r'^\s*#\s*LoadModule\s+ssl_module\s+modules/mod_ssl\.so',
		'LoadModule ssl_module modules/mod_ssl.so',
		text,
		flags=re.MULTILINE,
	)
	text = re.sub(
		r'^\s*#\s*LoadModule\s+socache_shmcb_module\s+modules/mod_socache_shmcb\.so',
		'LoadModule socache_shmcb_module modules/mod_socache_shmcb.so',
		text,
		flags=re.MULTILINE,
	)

	key_file, cert_file = ensure_ssl_certificate(apache_root)
	key_fwd = str(key_file.resolve()).replace("\\", "/")
	cert_fwd = str(cert_file.resolve()).replace("\\", "/")
	htdocs_fwd = str(htdocs_path.resolve()).replace("\\", "/")

	# Remove any existing Sqeli SSL block
	text = re.sub(
		r'# ─── Sqeli SSL ───.*?# ─── End Sqeli SSL ───\n?',
		'',
		text,
		flags=re.DOTALL,
	)

	ssl_block = f"""
# ─── Sqeli SSL ───
<IfModule ssl_module>
    Listen 443
    SSLCipherSuite HIGH:MEDIUM:!MD5:!RC4:!3DES
    SSLProxyCipherSuite HIGH:MEDIUM:!MD5:!RC4:!3DES
    SSLHonorCipherOrder on
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLProxyProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLPassPhraseDialog  builtin
    SSLSessionCache "shmcb:logs/ssl_scache(512000)"
    SSLSessionCacheTimeout 300

    <VirtualHost _default_:443>
        DocumentRoot "{htdocs_fwd}"
        ServerName localhost:443
        ServerAdmin admin@localhost
        ErrorLog "logs/ssl_error.log"
        TransferLog "logs/ssl_access.log"

        SSLEngine on
        SSLCertificateFile "{cert_fwd}"
        SSLCertificateKeyFile "{key_fwd}"

        <Directory "{htdocs_fwd}">
            Options Indexes FollowSymLinks
            AllowOverride All
            Require all granted
        </Directory>
    </VirtualHost>
</IfModule>
# ─── End Sqeli SSL ───
"""
	text = text.strip() + "\n" + ssl_block
	conf.write_text(text, encoding="utf-8")

class InstallWorker(QThread):
	"""
	QThread that downloads, extracts, and configures one service.

	Signals
	-------
	progress(int)   0-100 percentage
	status(str)     human-readable current step
	done(str)       absolute path to installed binary (e.g. httpd.exe)
	error(str)      error message if something went wrong
	"""

	progress = pyqtSignal(int)
	status   = pyqtSignal(str)
	done     = pyqtSignal(str)   # binary path
	error    = pyqtSignal(str)

	def __init__(self, service: str, parent=None):
		"""service must be 'apache', 'mysql', or 'phpmyadmin'."""
		super().__init__(parent)
		self._service = service

	# ── Thread entry ──────────────────────────────────────────────────────────

	def run(self):
		try:
			if self._service == "apache":
				self._install_apache()
			elif self._service == "mysql":
				self._install_mysql()
			elif self._service == "phpmyadmin":
				self._install_phpmyadmin()
		except Exception as exc:
			self.error.emit(str(exc))

	# ── Apache ────────────────────────────────────────────────────────────────

	def _install_apache(self):
		self.status.emit("Finding latest Apache version…")
		url = find_apache_url()
		zip_name = url.split("/")[-1].split("?")[0]
		self.status.emit(f"Downloading {zip_name}…")

		dest_dir = BIN_ROOT / "apache"
		dest_dir.mkdir(parents=True, exist_ok=True)

		zip_path = self._download(url, zip_name)

		self.status.emit("Extracting…")
		self._extract(zip_path, dest_dir)
		zip_path.unlink(missing_ok=True)

		# Apache Lounge ZIPs have a top-level folder named 'Apache24' or similar
		candidates = list(dest_dir.glob("*/bin/httpd.exe"))
		if not candidates:
			raise RuntimeError(
				f"Could not find httpd.exe after extraction in {dest_dir}"
			)
		httpd_path = candidates[0]
		apache_root = httpd_path.parent.parent  # e.g. .../bin/apache/Apache24

		self.status.emit("Patching httpd.conf…")
		self._patch_httpd_conf(apache_root)

		# If PHP is already installed, wire it into Apache
		php_dir = BIN_ROOT / "php"
		pma_dir = BIN_ROOT / "phpmyadmin"
		if php_dir.exists():
			patch_apache_for_php(apache_root, php_dir, pma_dir if pma_dir.exists() else None)

		self.status.emit("Done!")
		self.progress.emit(100)
		self.done.emit(str(httpd_path).replace("\\", "/"))

	def _patch_httpd_conf(self, apache_root: Path):
		conf = apache_root / "conf" / "httpd.conf"
		if not conf.exists():
			return
		text = conf.read_text(encoding="utf-8", errors="replace")
		root_fwd = str(apache_root).replace("\\", "/")

		# Patch ServerRoot
		text = re.sub(
			r'^ServerRoot\s+"[^"]*"',
			f'ServerRoot "{root_fwd}"',
			text,
			flags=re.MULTILINE,
		)
		# Suppress the FQDN warning
		if re.search(r'^\s*#?\s*ServerName\b', text, re.MULTILINE):
			text = re.sub(
				r'^\s*#?\s*ServerName\b.*$',
				'ServerName localhost:80',
				text,
				count=1,
				flags=re.MULTILINE,
			)
		else:
			text = text + "\n# Added by Sqeli\nServerName localhost:80\n"

		# Enable mod_rewrite for frameworks/clean URLs
		text = re.sub(
			r'^\s*#\s*LoadModule\s+rewrite_module\s+modules/mod_rewrite\.so',
			'LoadModule rewrite_module modules/mod_rewrite.so',
			text,
			flags=re.MULTILINE,
		)

		# Ensure project root htdocs/ exists with welcome page
		HTDOCS_ROOT.mkdir(parents=True, exist_ok=True)
		welcome_index = HTDOCS_ROOT / "index.php"
		if not any(HTDOCS_ROOT.iterdir()):
			welcome_index.write_text(
				"<!DOCTYPE html>\n<html>\n<head>\n"
				"    <title>Welcome to Sqeli</title>\n"
				"    <style>body{font-family:'Segoe UI',sans-serif;background:#12141f;color:#e2e4f0;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;} .box{text-align:center;padding:40px;background:#1a1d2e;border-radius:12px;border:1px solid #2e3352;} h1{color:#00d4aa;margin:0 0 10px;} p{color:#9ca3af;margin:0 0 20px;} a{color:#a78bfa;text-decoration:none;font-weight:bold;} a:hover{text-decoration:underline;}</style>\n"
				"</head>\n<body>\n"
				"    <div class='box'>\n"
				"        <h1>Sqeli Local Server is Running!</h1>\n"
				"        <p>Drop your website files into the <code>htdocs/</code> folder.</p>\n"
				"        <p><a href='/phpmyadmin/'>Open phpMyAdmin &rarr;</a></p>\n"
				"    </div>\n"
				"</body>\n</html>\n",
				encoding="utf-8",
			)

		# Patch DocumentRoot and Directory to point to project root htdocs/
		htdocs_fwd = HTDOCS_ROOT.as_posix()
		text = re.sub(
			r'^DocumentRoot\s+"[^"]*"',
			f'DocumentRoot "{htdocs_fwd}"',
			text,
			flags=re.MULTILINE,
		)
		# Replace <Directory "..."> block for old htdocs with new HTDOCS_ROOT and AllowOverride All
		text = re.sub(
			r'<Directory\s+"[^"]*htdocs[^"]*">.*?</Directory>',
			f'<Directory "{htdocs_fwd}">\n    Options Indexes FollowSymLinks\n    AllowOverride All\n    Require all granted\n</Directory>',
			text,
			count=1,
			flags=re.DOTALL,
		)
		conf.write_text(text, encoding="utf-8")

	# ── PHP & phpMyAdmin ──────────────────────────────────────────────────────

	def _install_phpmyadmin(self):
		import secrets
		php_dir = BIN_ROOT / "php"
		pma_dir = BIN_ROOT / "phpmyadmin"

		# If Apache is currently running, stop it so DLL files (like php8apache2_4.dll) are unlocked
		apache_candidates = list(BIN_ROOT.glob("apache/*/bin/httpd.exe"))
		if apache_candidates:
			try:
				import subprocess
				subprocess.run(
					["taskkill", "/F", "/IM", "httpd.exe"],
					capture_output=True,
					creationflags=subprocess.CREATE_NO_WINDOW,
				)
			except Exception:
				pass

		# Step 1: Download & extract PHP
		self.status.emit("Finding PHP package (Thread-Safe x64)…")
		php_url = find_php_url()
		php_zip_name = php_url.split("/")[-1].split("?")[0]
		self.status.emit(f"Downloading {php_zip_name}…")
		php_zip = self._download(php_url, php_zip_name)

		self.status.emit("Extracting PHP…")
		php_dir.mkdir(parents=True, exist_ok=True)
		self._extract(php_zip, php_dir)
		php_zip.unlink(missing_ok=True)

		# Configure php.ini
		self.status.emit("Configuring php.ini…")
		php_ini = php_dir / "php.ini"
		php_ini_dev = php_dir / "php.ini-development"
		if not php_ini.exists() and php_ini_dev.exists():
			shutil.copy(php_ini_dev, php_ini)

		if php_ini.exists():
			ini_text = php_ini.read_text(encoding="utf-8", errors="replace")
			# Set absolute extension_dir so Apache mod_php locates extensions correctly
			ext_dir_fwd = (php_dir / "ext").as_posix()
			ini_text = re.sub(
				r'^\s*;?\s*extension_dir\s*=.*$',
				f'extension_dir = "{ext_dir_fwd}"',
				ini_text,
				flags=re.MULTILINE,
			)
			# Suppress deprecation warnings on newer PHP versions
			ini_text = re.sub(r'^\s*error_reporting\s*=.*$', 'error_reporting = E_ALL & ~E_DEPRECATED & ~E_USER_DEPRECATED', ini_text, flags=re.MULTILINE)
			# Enable essential extensions for MySQL & phpMyAdmin
			exts = ["curl", "fileinfo", "mbstring", "mysqli", "openssl", "pdo_mysql"]
			for ext in exts:
				ini_text = re.sub(
					rf'^\s*;\s*extension\s*=\s*{ext}\b',
					f'extension={ext}',
					ini_text,
					flags=re.MULTILINE,
				)
			php_ini.write_text(ini_text, encoding="utf-8")

		# Step 2: Download & extract phpMyAdmin
		self.status.emit("Finding phpMyAdmin package…")
		pma_url = find_phpmyadmin_url()
		pma_zip_name = pma_url.split("/")[-1].split("?")[0]
		self.status.emit(f"Downloading {pma_zip_name}…")
		pma_zip = self._download(pma_url, pma_zip_name)

		self.status.emit("Extracting phpMyAdmin…")
		tmp_pma_dest = BIN_ROOT / "_pma_tmp"
		if tmp_pma_dest.exists():
			shutil.rmtree(tmp_pma_dest, ignore_errors=True)
		tmp_pma_dest.mkdir(parents=True, exist_ok=True)
		self._extract(pma_zip, tmp_pma_dest)
		pma_zip.unlink(missing_ok=True)

		# phpMyAdmin ZIPs contain a root folder e.g. phpMyAdmin-5.2.2-all-languages
		extracted_dirs = [d for d in tmp_pma_dest.iterdir() if d.is_dir()]
		if not extracted_dirs:
			raise RuntimeError("Could not extract phpMyAdmin contents.")

		if pma_dir.exists():
			shutil.rmtree(pma_dir, ignore_errors=True)
		shutil.move(str(extracted_dirs[0]), str(pma_dir))
		shutil.rmtree(tmp_pma_dest, ignore_errors=True)

		# Configure config.inc.php
		self.status.emit("Configuring phpMyAdmin…")
		pma_sample = pma_dir / "config.sample.inc.php"
		pma_conf = pma_dir / "config.inc.php"
		if pma_sample.exists() and not pma_conf.exists():
			shutil.copy(pma_sample, pma_conf)

		if pma_conf.exists():
			pma_text = pma_conf.read_text(encoding="utf-8", errors="replace")
			secret = secrets.token_hex(16)  # 32 chars blowfish secret
			pma_text = re.sub(
				r"\$cfg\['blowfish_secret'\]\s*=\s*'[^']*';",
				f"$cfg['blowfish_secret'] = '{secret}';",
				pma_text,
			)
			# Allow empty password & set host to 127.0.0.1
			pma_text = re.sub(
				r"\$cfg\['Servers'\]\[\$i\]\['host'\]\s*=\s*'[^']*';",
				"$cfg['Servers'][$i]['host'] = '127.0.0.1';",
				pma_text,
			)
			if "AllowNoPassword" not in pma_text:
				pma_text += "\n$cfg['Servers'][$i]['AllowNoPassword'] = true;\n"
			else:
				pma_text = re.sub(
					r"\$cfg\['Servers'\]\[\$i\]\['AllowNoPassword'\]\s*=\s*(?:false|true);",
					"$cfg['Servers'][$i]['AllowNoPassword'] = true;",
					pma_text,
				)
			pma_conf.write_text(pma_text, encoding="utf-8")

		# Step 3: Wire into Apache if Apache is present
		apache_candidates = list(BIN_ROOT.glob("apache/*/bin/httpd.exe"))
		if apache_candidates:
			self.status.emit("Configuring Apache with PHP & phpMyAdmin…")
			apache_root = apache_candidates[0].parent.parent
			patch_apache_for_php(apache_root, php_dir, pma_dir)

		self.status.emit("Done!")
		self.progress.emit(100)
		self.done.emit(str(pma_dir).replace("\\", "/"))

	# ── MySQL / MariaDB ───────────────────────────────────────────────────────

	def _install_mysql(self):
		self.status.emit("Finding latest MariaDB version…")
		url, version = find_mariadb_url()
		zip_name = url.split("/")[-1].split("?")[0]
		self.status.emit(f"Downloading MariaDB {version}…")

		dest_dir = BIN_ROOT / "mysql"
		dest_dir.mkdir(parents=True, exist_ok=True)

		zip_path = self._download(url, zip_name)

		self.status.emit("Extracting…")
		self._extract(zip_path, dest_dir)
		zip_path.unlink(missing_ok=True)

		candidates = list(dest_dir.glob("*/bin/mysqld.exe"))
		if not candidates:
			raise RuntimeError(
				f"Could not find mysqld.exe after extraction in {dest_dir}"
			)
		mysqld_path = candidates[0]
		mysql_root = mysqld_path.parent.parent

		data_dir = mysql_root / "data"
		if not data_dir.exists() or not any(data_dir.iterdir()):
			self.status.emit("Initializing database (first-time setup)…")
			self._init_mysql(mysqld_path, data_dir)

		self.status.emit("Done!")
		self.progress.emit(100)
		# Return "bin_path|datadir" so the caller can split
		self.done.emit(
			f"{str(mysqld_path).replace(chr(92), '/')}|"
			f"{str(data_dir).replace(chr(92), '/')}"
		)

	def _init_mysql(self, mysqld: Path, datadir: Path):
		import subprocess
		datadir.mkdir(parents=True, exist_ok=True)
		bin_dir = mysqld.parent
		install_db = bin_dir / "mariadb-install-db.exe"
		if not install_db.exists():
			install_db = bin_dir / "mysql_install_db.exe"

		if install_db.exists():
			cmd = [str(install_db), f"--datadir={datadir}", "--default-user"]
		else:
			cmd = [str(mysqld), "--initialize-insecure", f"--datadir={datadir}"]

		result = subprocess.run(
			cmd,
			capture_output=True,
			timeout=120,
			creationflags=subprocess.CREATE_NO_WINDOW,
		)
		if result.returncode not in (0, 1):
			stderr = result.stderr.decode("utf-8", errors="replace")
			if "error" in stderr.lower() and "already" not in stderr.lower():
				raise RuntimeError(f"MySQL init failed:\n{stderr[:400]}")

	# ── Download helper ───────────────────────────────────────────────────────

	def _download(self, url: str, filename: str) -> Path:
		clean_name = filename.split("?")[0]   # strip any query string
		tmp = Path(tempfile.gettempdir()) / f"sqeli_{clean_name}"
		req = urllib.request.Request(url, headers={"User-Agent": _UA})
		with urllib.request.urlopen(req, timeout=120) as resp:
			total = int(resp.headers.get("Content-Length", 0))
			downloaded = 0
			chunk = 65536
			with open(tmp, "wb") as f:
				while True:
					data = resp.read(chunk)
					if not data:
						break
					f.write(data)
					downloaded += len(data)
					if total:
						pct = min(int(downloaded / total * 90), 90)
						self.progress.emit(pct)
		self.progress.emit(92)
		return tmp

	def _extract(self, zip_path: Path, dest: Path):
		with zipfile.ZipFile(zip_path, "r") as zf:
			zf.extractall(dest)
		self.progress.emit(98)
