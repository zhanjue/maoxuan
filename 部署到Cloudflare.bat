@echo off
chcp 936 >nul
title 知行录 · 发布到 Cloudflare Pages
cd /d "%~dp0"

set "PY=C:\Users\80926\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo  [1/3] 重新构建 site/
"%PY%" scripts\build.py
if errorlevel 1 goto fail

echo.
echo  [2/3] 登录 Cloudflare（第一次会开浏览器，点 Allow 即可；已登录会自动跳过）
call npx --yes wrangler@latest whoami >nul 2>&1
if errorlevel 1 call npx --yes wrangler@latest login
if errorlevel 1 goto fail

echo.
echo  [3/3] 上传 site/ 到 Pages 项目 maoxuan1
call npx --yes wrangler@latest pages deploy site --project-name=maoxuan1 --commit-dirty=true
if errorlevel 1 goto fail

echo.
echo  发布完成。地址： https://maoxuan1.pages.dev
pause
exit /b 0

:fail
echo.
echo  出错了，把上面的红字发给我。
pause
exit /b 1
