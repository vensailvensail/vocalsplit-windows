@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"
if exist "%PYTHON%" goto dependencies
where py >nul 2>&1
if not errorlevel 1 py -3.11 -m venv .venv
if exist "%PYTHON%" goto dependencies
python -c "import sys, struct; sys.exit(sys.version_info[:2] != (3,11) or struct.calcsize('P') != 8)"
if errorlevel 1 goto failed
python -m venv .venv
if errorlevel 1 goto failed
:dependencies
"%PYTHON%" -c "import imageio_ffmpeg" >nul 2>&1
if not errorlevel 1 goto run
"%PYTHON%" -m pip install imageio-ffmpeg==0.6.0
if errorlevel 1 goto failed
:run
set "VOCALSPLIT_OFFLINE=1"
"%PYTHON%" app.py
if not errorlevel 1 exit /b 0
:failed
echo Could not start VocalSplit. Check the first error above.
pause
exit /b 1
