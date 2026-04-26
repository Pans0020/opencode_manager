@echo off
setlocal

cd /d "%~dp0"
set "LOG_FILE=%~dp0build-portable.log"

echo ======================================== > "%LOG_FILE%"
echo Agent Model Manager build log >> "%LOG_FILE%"
echo Started at %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

echo [prep] Stopping packaged app processes...
taskkill /IM "Agent Model Manager.exe" /F >nul 2>&1
taskkill /IM "agent-model-manager-backend.exe" /F >nul 2>&1

echo [prep] Cleaning stale desktop artifacts...
if exist "dist\win-unpacked" rmdir /s /q "dist\win-unpacked"
if exist "dist\builder-debug.yml" del /f /q "dist\builder-debug.yml"
if exist "dist\agent-model-manager-0.1.0-x64.nsis.7z" del /f /q "dist\agent-model-manager-0.1.0-x64.nsis.7z"
if exist "dist\Agent-Model-Manager-*-portable.exe" del /f /q "dist\Agent-Model-Manager-*-portable.exe"

echo [prep] Checking npm dependencies...
if not exist "node_modules\electron-builder\cli.js" (
  echo [prep] Installing npm dependencies...
  call npm install >> "%LOG_FILE%" 2>&1
  if errorlevel 1 goto :fail
)

echo [prep] Checking Python packaging dependencies...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
  echo [prep] Installing Python dependencies...
  call python -m pip install -r backend\requirements.txt >> "%LOG_FILE%" 2>&1
  if errorlevel 1 goto :fail
)

echo [1/6] Running frontend tests...
call npm run test:frontend >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

echo [2/6] Running Electron tests...
call npm run test:electron >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

echo [3/6] Running backend tests...
call npm run backend:test >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

echo [4/6] Building frontend bundle...
call npm run build:frontend >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

echo [5/6] Building backend executable...
call npm run build:backend >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

echo [6/6] Building folder package...
echo [info] The last Electron packaging step can take 1-2 minutes.
call npm run build:desktop >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

echo.
echo Build finished.
echo Output: dist\win-unpacked\Agent Model Manager.exe
echo Log: %LOG_FILE%
exit /b 0

:fail
echo.
echo Build failed.
echo Check log: %LOG_FILE%
if exist "dist\builder-debug.yml" (
  echo builder-debug: dist\builder-debug.yml
)
exit /b 1
