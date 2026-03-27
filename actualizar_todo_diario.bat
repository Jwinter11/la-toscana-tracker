@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%CD%"
set "PYTHON_EXE=C:\Users\Julian\AppData\Local\Python\pythoncore-3.14-64\python.exe"
set "LOG=%ROOT%\logs_automatizacion_diaria.txt"
set "ACEITE_TRACKER_HEADLESS=1"
set "GIT_REMOTE=latoscana"

echo [%date% %time%] Inicio de actualizacion diaria >> "%LOG%"

"%PYTHON_EXE%" scraper.py --auto >> "%LOG%" 2>&1
if errorlevel 1 goto :error_aceite

"%PYTHON_EXE%" scraper_aceitunas.py --auto >> "%LOG%" 2>&1
if errorlevel 1 goto :error_aceitunas

echo %date% %time% > "%ROOT%\last_update.txt"

git add precios.db historial_precios.json last_update.txt >> "%LOG%" 2>&1
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
