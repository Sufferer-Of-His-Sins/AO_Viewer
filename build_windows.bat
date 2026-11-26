@echo off
if /i "%~1"=="run" goto start
rem Relaunch in a window that stays open, so any error stays visible
cmd /k call "%~f0" run
exit /b

:start
setlocal
cd /d "%~dp0"
title Avalon Map Viewer - build

set "TESS_DIR=C:\Program Files\Tesseract-OCR"
set "TESS_USER=%LOCALAPPDATA%\Programs\Tesseract-OCR"
set "APP=dist\AvalonMapViewer"
set "ICON=assets\icon.ico"

echo Working folder: %CD%
echo.

rem ---------- sanity checks ----------
if exist "%ICON%" goto icon_ok
echo ERROR: icon not found: %CD%\%ICON%
goto fail
:icon_ok

if exist "main.py" goto main_ok
echo ERROR: main.py not found in %CD%
goto fail
:main_ok

if exist "build\installer.iss" goto iss_ok
echo ERROR: build\installer.iss not found
goto fail
:iss_ok

set "PY=python"
python --version >nul 2>nul
if not errorlevel 1 goto py_ok
set "PY=py -3"
py -3 --version >nul 2>nul
if not errorlevel 1 goto py_ok
echo ERROR: Python was not found. Install it from https://www.python.org/downloads/
echo        and tick "Add python.exe to PATH" in the installer.
goto fail
:py_ok

rem ---------- 1. python packages ----------
echo [1/5] Installing Python packages...
%PY% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto fail

rem ---------- 2. tesseract (build machine only) ----------
echo [2/5] Checking Tesseract...
if exist "%TESS_DIR%\tesseract.exe" goto tess_ok
if exist "%TESS_USER%\tesseract.exe" set "TESS_DIR=%TESS_USER%"
if exist "%TESS_DIR%\tesseract.exe" goto tess_ok
echo Tesseract not found, installing with winget...
winget install -e --id UB-Mannheim.TesseractOCR --silent --accept-package-agreements --accept-source-agreements
if exist "%TESS_DIR%\tesseract.exe" goto tess_ok
if exist "%TESS_USER%\tesseract.exe" set "TESS_DIR=%TESS_USER%"
if exist "%TESS_DIR%\tesseract.exe" goto tess_ok
echo ERROR: could not install Tesseract automatically.
echo        Download it from https://github.com/UB-Mannheim/tesseract/wiki
echo        install it and run this file again.
goto fail
:tess_ok
if exist "%TESS_DIR%\tessdata\eng.traineddata" goto tessdata_ok
echo ERROR: %TESS_DIR%\tessdata\eng.traineddata not found.
goto fail
:tessdata_ok
echo Tesseract: %TESS_DIR%

rem ---------- 3. inno setup ----------
echo [3/5] Checking Inno Setup...
call :find_iscc
if defined ISCC goto iscc_ok
echo Inno Setup not found, installing with winget...
winget install -e --id JRSoftware.InnoSetup --silent --accept-package-agreements --accept-source-agreements
call :find_iscc
if defined ISCC goto iscc_ok
echo ERROR: could not install Inno Setup automatically.
echo        Download it from https://jrsoftware.org/isdl.php
echo        install it and run this file again.
goto fail
:iscc_ok
echo Inno Setup: %ISCC%

rem ---------- 4. exe ----------
echo [4/5] Building EXE...
if exist dist rmdir /s /q dist
%PY% -m PyInstaller --noconfirm --clean --windowed --name AvalonMapViewer ^
  --icon "%CD%\%ICON%" ^
  --collect-all customtkinter ^
  --hidden-import avalon.snip ^
  --exclude-module cv2 --exclude-module numpy ^
  --distpath dist --workpath build\work --specpath build\work ^
  "%CD%\main.py"
if errorlevel 1 goto fail

xcopy /E /I /Y data "%APP%\data" >nul
if errorlevel 1 goto copy_fail
xcopy /E /I /Y locales "%APP%\locales" >nul
if errorlevel 1 goto copy_fail
xcopy /E /I /Y assets "%APP%\assets" >nul
if errorlevel 1 goto copy_fail

if exist maps goto copy_maps
mkdir "%APP%\maps"
goto maps_done
:copy_maps
xcopy /E /I /Y maps "%APP%\maps" >nul
if errorlevel 1 goto copy_fail
:maps_done

mkdir "%APP%\tesseract\tessdata"
copy /Y "%TESS_DIR%\tesseract.exe" "%APP%\tesseract\" >nul
if errorlevel 1 goto copy_fail
copy /Y "%TESS_DIR%\*.dll" "%APP%\tesseract\" >nul
copy /Y "%TESS_DIR%\tessdata\eng.traineddata" "%APP%\tesseract\tessdata\" >nul
if errorlevel 1 goto copy_fail

rem ---------- 5. installer ----------
echo [5/5] Building installer...
"%ISCC%" build\installer.iss
if errorlevel 1 goto fail

echo.
echo DONE: %CD%\installer\AvalonMapViewer_Setup.exe
goto end

:copy_fail
echo ERROR: copying files into %APP% failed. Check that the folders data, locales and assets exist.
goto fail

:end
echo.
echo You can close this window.
exit /b 0

:fail
echo.
echo BUILD FAILED - read the messages above.
exit /b 1

:find_iscc
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
exit /b 0
