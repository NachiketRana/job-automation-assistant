@echo off
chcp 65001 > nul
title Job Copilot Web Dashboard
pushd "%~dp0"
echo ============================================================
echo      🚀 Starting Job Copilot Automation Dashboard...
echo      👉 Opening http://localhost:8000 in your browser
echo ============================================================
set PYTHONIOENCODING=utf-8

start "" "http://localhost:8000"
python dashboard_server.py
popd
pause
