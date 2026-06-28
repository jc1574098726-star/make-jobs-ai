@echo off
chcp 65001 >nul
title make-jobs-ai 停止

echo 正在关闭后端和前端服务...

taskkill /FI "WINDOWTITLE eq make-jobs-backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq make-jobs-frontend*" /F >nul 2>&1

REM 关闭占用 8000 和 5173 端口的进程
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo 已关闭所有服务。
timeout /t 2 /nobreak >nul
