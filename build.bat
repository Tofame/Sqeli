@echo off
:: Sqeli build wrapper — delegates all logic to build.py (no quoting issues)
cd /d "%~dp0"
python build.py
pause
