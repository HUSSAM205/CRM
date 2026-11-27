@echo off
REM Create .venv with Python 3.12 and install the pinned dependencies.
py -3.12 scripts\setup_environment.py
if errorlevel 1 (echo Setup failed. Is Python 3.12 installed? See docs\installation_guide.md & exit /b 1)
