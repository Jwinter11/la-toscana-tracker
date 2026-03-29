@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%CD%"
set "PYTHON_EXE=C:\Users\Julian\AppData\Local\Python\pythoncore-3.14-64\python.exe"
set "POWERSHELL_EXE=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
set "LOG=%ROOT%\logs_automatizacion_diaria.txt"
set "ACEITE_TRACKER_HEADLESS=1"
set "GIT_REMOTE=latoscana"
set "LAST_UPDATE_FILE=%ROOT%\last_update.txt"

echo [%date% %time%] Inicio de actualizacion diaria >> "%LOG%"

if not "%FORCE_DAILY_UPDATE%"=="1" (
    "%POWERSHELL_EXE%" -NoProfile -Command "$today = (Get-Date).Date; if (Test-Path '%LAST_UPDATE_FILE%') { $last = (Get-Item '%LAST_UPDATE_FILE%').LastWriteTime.Date; if ($last -eq $today) { exit 0 } }; exit 1" >> "%LOG%" 2>&1
    if not errorlevel 1 (
        echo [%date% %time%] Verificacion previa: scrape omitido, la base ya tiene datos completos de hoy >> "%LOG%"
        exit /b 0
    )
)

"%PYTHON_EXE%" scraper.py --auto >> "%LOG%" 2>&1
if errorlevel 1 goto :error_aceite

"%PYTHON_EXE%" scraper_aceitunas.py --auto >> "%LOG%" 2>&1
if errorlevel 1 goto :error_aceitunas

echo %date% %time% > "%LAST_UPDATE_FILE%"
"%POWERSHELL_EXE%" -NoProfile -Command "(Get-Date).ToString('yyyy-MM-dd')" > "%ROOT%\last_update_iso.txt"
if errorlevel 1 (
    echo [%date% %time%] AVISO: no se pudo escribir last_update_iso.txt >> "%LOG%"
)

git add precios.db historial_precios.json last_update.txt last_update_iso.txt >> "%LOG%" 2>&1
git diff --cached --quiet
if errorlevel 1 goto :commit

echo [%date% %time%] Sin cambios nuevos para pushear >> "%LOG%"
goto :ok

:commit
git commit -m "Actualizacion diaria %date% %time%" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%date% %time%] AVISO: no se pudo crear el commit >> "%LOG%"
    goto :ok
)

git push %GIT_REMOTE% main >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%date% %time%] ERROR: git push fallo >> "%LOG%"
    exit /b 1
)

echo [%date% %time%] GitHub actualizado OK >> "%LOG%"
goto :ok

:error_aceite
echo [%date% %time%] ERROR: fallo el scraper de aceite >> "%LOG%"
exit /b 1

:error_aceitunas
echo [%date% %time%] ERROR: fallo el scraper de aceitunas >> "%LOG%"
exit /b 1

:ok
echo [%date% %time%] Fin de actualizacion diaria >> "%LOG%"
exit /b 0
