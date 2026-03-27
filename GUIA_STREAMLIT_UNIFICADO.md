# La Toscana Tracker en Streamlit

## Qué quedó preparado

- `dashboard_unificado.py`: nueva app principal con acceso a Aceite y Aceitunas.
- `abrir_dashboard_unificado.bat`: levanta la suite local.
- `actualizar_todo_diario.bat`: corre ambos scrapers, deja `last_update.txt` nuevo y hace `git push`.
- `instalar_tarea_diaria.bat`: crea una tarea diaria en Windows a las `08:00`.

## Paso a paso para publicar La Toscana Tracker

1. Subí este repo a GitHub con el dashboard unificado.
2. Entrá a Streamlit Community Cloud.
3. Elegí `Create app`.
4. Seleccioná:
   - repositorio: este repo
   - branch: `main`
   - main file path: `dashboard_unificado.py`
5. En `Advanced settings` copiá el secreto:

```toml
PASSWORD = "tu_password"
```

6. Confirmá el deploy.

## Cómo queda la actualización diaria

1. `actualizar_todo_diario.bat` corre `scraper.py --auto`.
2. Después corre `scraper_aceitunas.py --auto`.
3. Ambos usan `ACEITE_TRACKER_HEADLESS=1`, así que Playwright ya puede correr sin navegador visible.
4. Si hay cambios, el script hace `git add`, `git commit` y `git push origin main`.
5. Streamlit detecta el push y redeploya la app unificada.

## Cómo instalar la tarea diaria

1. Ejecutá `instalar_tarea_diaria.bat`.
2. La tarea se crea con el nombre `La Toscana Tracker Diario`.
3. Hora configurada por defecto: `08:00`.
4. Si querés quitarla después, ejecutá `desinstalar_tarea_diaria.bat`.

## Cómo probar localmente

1. `abrir_dashboard_unificado.bat`
2. Abrí `http://localhost:8513`

## Cómo probar sobre la copia reparada

1. `abrir_dashboard_unificado_copia.bat`
2. Abrí `http://localhost:8513`

## Nota

Para que la tarea diaria funcione sola, la PC tiene que estar prendida y con conexión. Si más adelante querés que esto corra aunque la PC esté apagada, el siguiente paso natural es mover la automatización a una VM o a GitHub Actions.
