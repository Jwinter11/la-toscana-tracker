@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%CD%"
set "TASK_NAME=La Toscana Tracker Diario"
set "TASK_TIME=08:30"

PowerShell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$taskName = '%TASK_NAME%';" ^
  "$root = '%ROOT%';" ^
  "$taskCmd = Join-Path $root 'actualizar_todo_diario.bat';" ^
  "$action = New-ScheduledTaskAction -Execute $env:ComSpec -Argument ('/c \"\"' + $taskCmd + '\"\"');" ^
  "$trigger = New-ScheduledTaskTrigger -Daily -At '%TASK_TIME%';" ^
  "$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 72);" ^
  "$principal = New-ScheduledTaskPrincipal -UserId ($env:UserDomain + '\' + $env:UserName) -LogonType Interactive -RunLevel Limited;" ^
  "Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null"
if errorlevel 1 (
    echo No se pudo crear la tarea programada.
    exit /b 1
)

echo Tarea "%TASK_NAME%" instalada para las %TASK_TIME% ^(permite bateria; requiere sesion abierta^).
exit /b 0
