@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%CD%"
set "LOG=%ROOT%\logs_automatizacion_diaria.txt"
set "POWERSHELL_EXE=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
set "LAST_UPDATE_FILE=%ROOT%\last_update.txt"

"%POWERSHELL_EXE%" -NoProfile -Command "$today = (Get-Date).Date; if (Test-Path '%LAST_UPDATE_FILE%') { $last = (Get-Item '%LAST_UPDATE_FILE%').LastWriteTime.Date; if ($last -eq $today) { exit 0 } }; exit 1" >> "%LOG%" 2>&1
if not errorlevel 1 (
    echo [%date% %time%] Verificacion diaria: scrape omitido, la base ya tiene datos de hoy >> "%LOG%"
    exit /b 0
)

echo [%date% %time%] Verificacion diaria: no hay datos completos de hoy, ejecutando actualizacion diaria >> "%LOG%"
call "%ROOT%\actualizar_todo_diario.bat"
exit /b %errorlevel%
