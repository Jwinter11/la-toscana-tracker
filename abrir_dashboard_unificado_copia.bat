@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=C:\Users\Julian\AppData\Local\Python\pythoncore-3.14-64\python.exe"
set "ACEITE_TRACKER_DB_PATH=%CD%\precios_fix.db"
set "ACEITE_TRACKER_HISTORIAL_PATH=%CD%\historial_precios_fix.json"

"%PYTHON_EXE%" -m streamlit run dashboard_unificado.py --server.port 8513 --browser.gatherUsageStats false
