@echo off
rem Doble clic en Windows: arranca el Pokemon REM Master Codex y abre el navegador.
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 start_codex.py %*
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python start_codex.py %*
  ) else (
    echo No se encontro Python 3. Instalalo desde https://www.python.org/downloads/
    pause
    exit /b 1
  )
)
if errorlevel 1 pause
