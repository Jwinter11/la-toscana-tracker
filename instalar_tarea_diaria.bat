@echo off
setlocal
cd /d "%~dp0"

set "ROOT=%CD%"
set "TASK_NAME=La Toscana Tracker Diario"
set "TASK_NAME_LOGON=La Toscana Tracker Al Iniciar Sesion"
set "TASK_TIME=08:30"

PowerShell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$root = '%ROOT%';" ^
  "$taskName = '%TASK_NAME%';" ^
  "$taskNameLogon = '%TASK_NAME_LOGON%';" ^
  "$runnerCmd = Join-Path $root 'actualizar_si_falta_hoy.bat';" ^
  "$userId = $env:UserDomain + '\' + $env:UserName;" ^
  "$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited;" ^
  "$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 72);" ^
  "$actionDaily = New-ScheduledTaskAction -Execute $env:ComSpec -Argument ('/c \"\"' + $runnerCmd + '\"\"');" ^
  "$actionLogon = New-ScheduledTaskAction -Execute $env:ComSpec -Argument ('/c \"\"' + $runnerCmd + '\"\"');" ^
  "$triggerDaily = New-ScheduledTaskTrigger -Daily -At '%TASK_TIME%';" ^
  "$triggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $userId;" ^
  "Register-ScheduledTask -TaskName $taskName -Action $actionDaily -Trigger $triggerDaily -Settings $settings -Principal $principal -Force | Out-Null;" ^
  "Register-ScheduledTask -TaskName $taskNameLogon -Action $actionLogon -Trigger $triggerLogon -Settings $settings -Principal $principal -Force | Out-Null"
if errorlevel 1 (
    echo No se pudieron crear las tareas programadas.
    exit /b 1
)

echo Tarea diaria instalada para las %TASK_TIME%.
echo Tarea de recuperacion instalada al iniciar sesion.
echo Nota: por Coto, la sesion de Windows debe quedar abierta para que el navegador interactivo pueda ejecutarse.
exit /b 0
