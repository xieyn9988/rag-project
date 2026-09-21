@echo off
cd /d %~dp0
chcp 65001 >nul
echo.
echo ============================================
echo   Starting RAG System...
echo ============================================
echo.

REM 1. 启动后端（新窗口）
start "RAG-Backend" cmd /k "call D:\miniconda3\condabin\conda.bat activate chroma_env && python apps\fastapi_app.py"

REM 2. 启动前端（新窗口）
start "RAG-Frontend" cmd /k "cd rag-frontend && npm run dev"

REM 3. 等待后端就绪（轮询 /health 接口，最多等 180 秒）
echo Waiting for backend to be ready...
set /a count=0
:wait_loop
timeout /t 3 /nobreak >nul
set /a count+=1

REM 用 curl 探测后端健康检查接口
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel%==0 goto ready
if %count% lss 60 goto wait_loop

echo.
echo [WARNING] Backend not responding after 180s. Opening browser anyway...
goto open_browser

:ready
echo.
echo [OK] Backend is ready! (waited %count% x 3 seconds)
echo.

:open_browser
REM 4. 等待前端 Vite 就绪
timeout /t 3 /nobreak >nul

REM 5. 打开浏览器
start http://localhost:5173

echo ============================================
echo   All services started!
echo   Frontend:  http://localhost:5173
echo   API Docs:  http://localhost:8000/docs
echo ============================================
echo.
echo You can close this window. Services keep running.
pause