@echo off
cd /d %~dp0
chcp 65001 >nul
echo.
echo ============================================
echo   Starting RAG System (Docker Backend + Local Frontend)...
echo ============================================
echo.

REM 1. 检查 Docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker 未启动，请先打开 Docker Desktop
    pause
    exit /b 1
)

REM 2. 启动 Docker 后端
echo Starting Docker backend...
docker compose up -d

REM 3. 启动本地前端（关键！）
echo Starting local frontend...
start "RAG-Frontend" cmd /k "cd rag-frontend && npm run dev"

REM 4. 等后端就绪
echo.
echo Waiting for backend to be ready...
set /a count=0
:wait_loop
timeout /t 3 /nobreak >nul
set /a count+=1

curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel%==0 goto ready
if %count% lss 60 goto wait_loop

echo.
echo [WARNING] Backend not responding after 180s.
goto open_browser

:ready
echo.
echo [OK] Backend is ready! (waited %count% x 3 seconds)
echo.

:open_browser
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo ============================================
echo   All services started!
echo   Frontend:  http://localhost:5173
echo   API Docs:  http://localhost:8000/docs
echo ============================================
echo.
pause