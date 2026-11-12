@echo off
setlocal
pushd "%~dp0" || exit /b 1

where node.exe >nul 2>&1 || (
    echo Node.js is required to start Steamgrader.
    goto :failed
)

if not exist "frontend\node_modules\.bin\craco.cmd" (
    where yarn.cmd >nul 2>&1 || (
        echo Yarn Classic is required to install frontend dependencies.
        goto :failed
    )
    call yarn.cmd --cwd frontend install
    if errorlevel 1 goto :failed
)

set "HOST=localhost"
set "PORT=3000"
set "HTTPS=false"
set "PUBLIC_BASE_URL=http://localhost:3000"
set "REACT_APP_BACKEND_URL=%PUBLIC_BASE_URL%"
set "STEAMGRADER_LOCAL_API="

call :check_port %PORT% %HOST%
if errorlevel 1 goto :failed

if exist "backend\.env" (
    call :start_api
    if errorlevel 1 goto :failed
) else (
    echo Starting the frontend. Set up backend\.env to enable the API.
)

echo Steamgrader will open at %PUBLIC_BASE_URL%
pushd frontend || goto :failed
call node_modules\.bin\craco.cmd start
if errorlevel 1 (
    popd
    goto :failed
)
popd
popd
exit /b 0

:start_api
call :check_port 8000 127.0.0.1
if errorlevel 1 exit /b 1
if not exist "backend\.venv\Scripts\python.exe" (
    echo Creating the Python environment...
    python -m venv backend\.venv || exit /b 1
)
set "API_PYTHON=%CD%\backend\.venv\Scripts\python.exe"
"%API_PYTHON%" -c "import dotenv, fastapi, httpx, jwt, motor.motor_asyncio, uvicorn" >nul 2>&1
if errorlevel 1 (
    "%API_PYTHON%" -m pip install -r backend\requirements-local.txt || exit /b 1
)
"%API_PYTHON%" -c "from dotenv import load_dotenv; from os import environ; load_dotenv('backend/.env'); missing = [key for key in ('MONGO_URL', 'DB_NAME', 'JWT_SECRET') if not environ.get(key)]; raise SystemExit('Set in backend/.env: ' + ', '.join(missing) if missing else 0)" || exit /b 1
start "Steamgrader API" /d "%CD%\backend" "%API_PYTHON%" -m uvicorn server:app --host 127.0.0.1 --port 8000
if errorlevel 1 exit /b 1
set "STEAMGRADER_LOCAL_API=http://127.0.0.1:8000"
exit /b 0

:check_port
node -e "const probe = require('node:net').createServer(); probe.once('error', () => process.exit(1)); probe.listen(Number(process.argv[1]), process.argv[2], () => probe.close());" %1 %2
if errorlevel 1 (
    echo Port %1 on %2 is unavailable.
    exit /b 1
)
exit /b 0

:failed
echo Steamgrader could not start. Check the error above.
pause
popd
exit /b 1
