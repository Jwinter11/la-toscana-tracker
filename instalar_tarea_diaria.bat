@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%CD%"
set "TASK_NAME=La Toscana Tracker Diario"
set "TASK_TIME=08:00"
set "TASK_CMD=%ComSpec% /c \"\"%ROOT%\actualizar_todo_diario.bat\"\""

schtasks /Create /F /SC DAILY /ST %TASK_TIME% /TN "%TASK_NAME%" /TR "%TASK_CMD%"
if errorlevel 1 (
    echo No se pudo crear la tarea programada.
    exit /b 1
)

echo Tarea "%TASK_NAME%" instalada para las %TASK_TIME%.
exit /b 0
