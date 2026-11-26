@echo off
setlocal
cd /d "%~dp0"
set "VOCALSPLIT_OFFLINE="
set "PYTHON=.venv\Scripts\python.exe"
set "TEMP=%~dp0cache\temp"
set "TMP=%TEMP%"
set "PIP_CACHE_DIR=%~dp0cache\pip"
set "TORCH_HOME=%~dp0cache\torch"
if not exist "%TEMP%" mkdir "%TEMP%"
if exist ".venv\ready" if exist "%PYTHON%" goto run

echo Installing VocalSplit dependencies. Keep this window open.
if exist "%PYTHON%" goto install
where py >nul 2>&1
if not errorlevel 1 py -3.11 -m venv .venv
if exist "%PYTHON%" goto install
python -c "import sys,struct; sys.exit(sys.version_info[:2] != (3, 11) or struct.calcsize('P') != 8)"
if errorlevel 1 goto failed
python -m venv .venv
if errorlevel 1 goto failed

:install
"%PYTHON%" -m pip install --index-url https://pypi.org/simple --upgrade "pip>=25.3"
if errorlevel 1 goto failed
"%PYTHON%" -m pip install --index-url https://pypi.org/simple ^
  "https://download-r2.pytorch.org/whl/cpu/torch-2.5.1%%2Bcpu-cp311-cp311-win_amd64.whl" ^
  "https://download-r2.pytorch.org/whl/cpu/torchaudio-2.5.1%%2Bcpu-cp311-cp311-win_amd64.whl" ^
  -r requirements.txt
if errorlevel 1 goto failed
"%PYTHON%" -m pip check
if errorlevel 1 goto failed
echo ready>".venv\ready"

:run
"%PYTHON%" app.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo VocalSplit setup or launch failed. See the first error above.
if not "%VOCALSPLIT_NO_PAUSE%"=="1" pause
exit /b 1

