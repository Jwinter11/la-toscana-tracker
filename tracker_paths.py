from __future__ import annotations

import os
from pathlib import Path


DIRECTORIO = Path(__file__).parent

PRECIOS_DB_ENV = "ACEITE_TRACKER_DB_PATH"
HISTORIAL_ENV = "ACEITE_TRACKER_HISTORIAL_PATH"


def _resolver_path(env_name: str, default_name: str) -> Path:
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        return DIRECTORIO / default_name

    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = DIRECTORIO / path
    return path


def precios_db_path() -> Path:
    return _resolver_path(PRECIOS_DB_ENV, "precios.db")


def historial_path() -> Path:
    return _resolver_path(HISTORIAL_ENV, "historial_precios.json")
