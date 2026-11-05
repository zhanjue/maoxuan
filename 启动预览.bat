@echo off
chcp 936 >nul
title 知行录 · 本地预览（关掉这个窗口就停止）
cd /d "%~dp0"

set "PY=C:\Users\80926\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

netstat -ano | findstr ":8801" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   服务已经在运行，直接打开浏览器。
    start "" http://127.0.0.1:8801/index.html
    goto end
)

echo.
echo   正在启动本地预览： http://127.0.0.1:8801/index.html
echo   浏览器两秒后自动打开。关闭本窗口即停止服务。
echo.

start "" /b cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8801/index.html"
"%PY%" _serve.py 8801

:end
pause
