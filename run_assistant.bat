@echo off
chcp 65001 > nul
title 150-Job Application Automation Assistant
pushd "%~dp0"
echo ============================================================
echo      🎯 Starting 150-Job Application Assistant...
echo ============================================================
set PYTHONIOENCODING=utf-8
python main.py
popd
pause
