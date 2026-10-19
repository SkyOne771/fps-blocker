@echo off
setlocal
cd /d "%~dp0"
set "FPS_ARGS=-m fps_blocker"
if /i "%~1"=="--restore-freesync" set "FPS_ARGS=tools\amd_freesync.py --restore"
if /i "%~1"=="--disable-freesync" set "FPS_ARGS=tools\amd_freesync.py --disable"
where py.exe >nul 2>&1
if errorlevel 1 goto find_python
py -3 %FPS_ARGS%
goto done

:find_python
set "FPS_PYTHON="
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set "FPS_PYTHON=%%D\python.exe"
if defined FPS_PYTHON goto run_python
python %FPS_ARGS%
goto done

:run_python
"%FPS_PYTHON%" %FPS_ARGS%

:done
if errorlevel 1 pause
