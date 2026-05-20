@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%CD%"
set "TASK_NAME=La Toscana Tracker Diario"
set "TASK_TIME=08:30"

PowerShell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$root = '%ROOT%';" ^
  "$taskName = '%TASK_NAME%';" ^
  "$runnerCmd = Join-Path $root 'actualizar_si_falta_hoy.bat';" ^
  "$userId = $env:UserDomain + '\' + $env:UserName;" ^
  "$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited;" ^
  "$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 3);" ^
  "$actionDaily = New-ScheduledTaskAction -Execute $env:ComSpec -Argument ('/c \"\"' + $runnerCmd + '\"\"');" ^
  "$triggerDaily = New-ScheduledTaskTrigger -Daily -At '%TASK_TIME%';" ^
  "Unregister-ScheduledTask -TaskName 'La Toscana Tracker Al Iniciar Sesion' -Confirm:$false -ErrorAction SilentlyContinue;" ^
  "Register-ScheduledTask -TaskName $taskName -Action $actionDaily -Trigger $triggerDaily -Settings $settings -Principal $principal -Force | Out-Null"
if errorlevel 1 (
    echo No se pudieron crear las tareas programadas.
    exit /b 1
)

echo Tarea diaria instalada para las %TASK_TIME%.
echo Sin tarea al iniciar sesion. Limite maximo: 3 horas; no se superponen corridas.
echo Nota: por Coto, la sesion de Windows debe quedar abierta para que el navegador interactivo pueda ejecutarse.
exit /b 0
