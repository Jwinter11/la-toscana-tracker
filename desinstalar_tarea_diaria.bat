@echo off
setlocal

set "TASK_NAME=La Toscana Tracker Diario"

schtasks /Delete /F /TN "%TASK_NAME%"
if errorlevel 1 (
    echo No se pudo eliminar la tarea "%TASK_NAME%".
    exit /b 1
)

echo Tarea "%TASK_NAME%" eliminada.
exit /b 0
