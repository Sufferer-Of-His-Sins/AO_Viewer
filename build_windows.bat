@echo off
setlocal
cd /d "%~dp0"

set "TESS_DIR=C:\Program Files\Tesseract-OCR"
set "APP=dist\AvalonMapViewer"
set "ICON=%CD%\assets\icon.ico"

if not exist "%ICON%" (
  echo ERROR: Icon not found: %ICON%
  pause
  exit /b 1
)

echo [1/5] Installing Python packages...
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto error

echo [2/5] Checking Tesseract (build machine only)...
if exist "%TESS_DIR%\tesseract.exe" goto tess_ok
winget install -e --id UB-Mannheim.TesseractOCR --silent --accept-package-agreements --accept-source-agreements
if not exist "%TESS_DIR%\tesseract.exe" goto no_tess
:tess_ok

echo [3/5] Checking Inno Setup (build machine only)...
call :find_iscc
if defined ISCC goto iscc_ok
winget install -e --id JRSoftware.InnoSetup --silent --accept-package-agreements --accept-source-agreements
call :find_iscc
if not defined ISCC goto no_iscc
:iscc_ok

echo [4/5] Building EXE...
if exist dist rmdir /s /q dist
python -m PyInstaller --noconfirm --clean --windowed --name AvalonMapViewer ^
  --icon "%~dp0assets\icon.ico" ^
  --collect-all customtkinter ^
  --exclude-module cv2 --exclude-module numpy ^
  --distpath "%~dp0dist" ^
  --workpath "%~dp0build\work" ^
  --specpath "%~dp0build\work" ^
  "%~dp0main.py"
  
if errorlevel 1 goto error

xcopy /E /I /Y data "%APP%\data" >nul
xcopy /E /I /Y locales "%APP%\locales" >nul
xcopy /E /I /Y assets "%APP%\assets" >nul

if exist maps (xcopy /E /I /Y maps "%APP%\maps" >nul) else (mkdir "%APP%\maps")

mkdir "%APP%\tesseract\tessdata"
copy /Y "%TESS_DIR%\tesseract.exe" "%APP%\tesseract\" >nul
copy /Y "%TESS_DIR%\*.dll" "%APP%\tesseract\" >nul
copy /Y "%TESS_DIR%\tessdata\eng.traineddata" "%APP%\tesseract\tessdata\" >nul

echo [5/5] Building installer...
"%ISCC%" build\installer.iss
if errorlevel 1 goto error

echo.
echo DONE: installer\AvalonMapViewer_Setup.exe
pause
exit /b 0

:find_iscc
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
exit /b 0

:no_tess
echo Could not install Tesseract automatically.
echo Download it from https://github.com/UB-Mannheim/tesseract/wiki and run this file again.
pause
exit /b 1

:no_iscc
echo Could not install Inno Setup automatically.
echo Download it from https://jrsoftware.org/isdl.php and run this file again.
pause
exit /b 1

:error
echo BUILD FAILED
pause
exit /b 1