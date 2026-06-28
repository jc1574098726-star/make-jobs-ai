@echo off
chcp 65001 >nul

echo make-jobs-ai 启动中...

REM 用独立进程启动后端（最小化窗口）
start /min "make-jobs-backend" cmd /c "cd /d F:\make_jobs\backend & .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

REM 用独立进程启动前端（最小化窗口）
start /min "make-jobs-frontend" cmd /c "cd /d F:\make_jobs\frontend & node_modules\.bin\vite.cmd --host 127.0.0.1"

echo.
echo 启动完成！
echo 后端: http://127.0.0.1:8000
echo 前端: http://127.0.0.1:5173
echo 停止服务请运行 stop.bat
echo.
timeout /t 3 /nobreak >nul
exit
