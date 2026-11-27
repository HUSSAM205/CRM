@echo off
REM ======================================================================
REM  Personal Financial AI Analyzer - START HERE (double-click this file)
REM  First time: sets up Python packages (about 1-5 minutes), then starts
REM  the dashboard and opens http://localhost:8501 in your browser.
REM  Next times: starts the dashboard directly.
REM  An existing environment is reused, never deleted or overwritten.
REM ======================================================================
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
title Personal Financial AI Analyzer
set "NEED_SETUP="
if not exist ".venv\Scripts\python.exe" set NEED_SETUP=1
if not defined NEED_SETUP (
  ".venv\Scripts\python.exe" -c "import streamlit, polars, sklearn, plotly, psutil, joblib, yaml" >nul 2>&1 || set NEED_SETUP=1
)
if defined NEED_SETUP (
  echo Setting up the application for the first time. This needs an internet connection once.
  echo.
  set PFA_NO_PAUSE=1
  call setup.bat
  if errorlevel 1 (
    echo.
    echo Setup did not finish. Read the messages above, then double-click START_HERE.bat again.
    pause
    exit /b 1
  )
  set "PFA_NO_PAUSE="
)
call run.bat %*
endlocal
