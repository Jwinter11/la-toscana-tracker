@echo off
setlocal

set "TASK_NAME=La Toscana Tracker Diario"
set "TASK_NAME_LOGON=La Toscana Tracker Al Iniciar Sesion"

schtasks /Delete /F /TN "%TASK_NAME%" >nul 2>&1
schtasks /Delete /F /TN "%TASK_NAME_LOGON%" >nul 2>&1

echo Tareas "%TASK_NAME%" y "%TASK_NAME_LOGON%" eliminadas.
exit /b 0
