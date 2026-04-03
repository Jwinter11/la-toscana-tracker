@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%CD%"
set "PYTHON_EXE=C:\Users\Julian\AppData\Local\Python\pythoncore-3.14-64\python.exe"
set "LOG=%ROOT%\logs_automatizacion_diaria.txt"
set "AUDIT_ALL=%ROOT%\auditoria_ultimo_scrape.xlsx"
set "AUDIT_KEY=%ROOT%\auditoria_marcas_clave.xlsx"
set "KEY_BRANDS=La Toscana,Castell,Nucete,Zuelo,Oliovita"

echo [%date% %time%] Inicio de auditoria automatica >> "%LOG%"

"%PYTHON_EXE%" auditar_ultimo_scrape.py --categoria ambas --output "%AUDIT_ALL%" --focus-brands "%KEY_BRANDS%" --focus-output "%AUDIT_KEY%" --headless >> "%LOG%" 2>&1
if errorlevel 1 goto :error

echo [%date% %time%] Auditoria automatica OK >> "%LOG%"
exit /b 0

:error
echo [%date% %time%] AVISO: fallo la auditoria automatica >> "%LOG%"
exit /b 1
