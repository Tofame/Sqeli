# Sqeli — Local Dev Server Manager

<p align="center">
  <img src="assets/icon_dark.png" width="100" alt="Sqeli icon">
</p>

<p align="center">
  A lightweight Windows tray app to start and stop <strong>Apache</strong> and <strong>MySQL</strong> with one click.
  Dark mode by default. No bloat.
</p>

---

## Motivation

Sqeli is a lightweight alternative to **XAMPP** and **Laragon**.

The reason for creating it:
- **XAMPP** would randomly corrupt MySQL databases every few months.
- **Laragon** (unlicensed) frequently interrupts work with popups every 15–30 minutes that hijack focus and open a website in the browser.

Sqeli was built / vibed in ~1 hour to be clean, fast, reliable, and completely out of your way.

---

## Requirements

- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Internet connection** (first run only, for auto-setup)

---

## Setup

```bash
git clone https://github.com/your-username/Sqeli.git
cd Sqeli
pip install -r requirements.txt
python main.py
```

That's it. On first run the **Auto Setup wizard** opens automatically — click Install for Apache and MariaDB and Sqeli handles the rest (download, extract, configure, initialize).

> The wizard can also be reopened any time via the **⬇** button in the panel header.

---

## Troubleshooting

### Apache won't start
- Check the console log inside Sqeli for the exact error.
- Port 80 in use? Open ⚙ Settings and change the port, then edit `bin/apache/Apache24/conf/httpd.conf` → `Listen <port>` to match.
- Check the port: `netstat -ano | findstr :80`

### MySQL won't start
- Check the console log inside Sqeli for the exact error.
- Port 3306 in use? Change it in ⚙ Settings.

### Already have Laragon / XAMPP?
Skip the wizard and point Sqeli at your existing binaries via ⚙ Settings:
- Laragon Apache: `C:/laragon/bin/apache/bin/httpd.exe`
- Laragon MySQL: `C:/laragon/bin/mysql/bin/mysqld.exe`, data: `C:/laragon/data`
- XAMPP Apache: `C:/xampp/apache/bin/httpd.exe`
- XAMPP MySQL: `C:/xampp/mysql/bin/mysqld.exe`, data: `C:/xampp/mysql/data`

---

## License

MIT — do whatever you want with it.
