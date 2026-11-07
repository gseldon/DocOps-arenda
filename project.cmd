@echo off
rem Windows launcher: project.cmd [command]  (see: python run.py help)
chcp 65001 >nul
cd /d "%~dp0"
where py >/dev/null 2>nul
if %errorlevel%==0 (py -3 run.py %*) else (python run.py %*)
if errorlevel 1 pause
