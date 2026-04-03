from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd

DIRECTORIO = Path(__file__).parent
ARCHIVO_UNIFICACIONES = DIRECTORIO / "unificaciones_gramaje.xlsx"
ARCHIVO_ENVASE = DIRECTORIO / "envase_aceitunas.xlsx"
ARCHIVO_REVISION_ENVASE = DIRECTORIO / "revision_envase.xlsx"

GRAMAJE_GRUPOS_LABELS = {
    "1) hasta 140g": "hasta 140g",
    "2) 141-230g": "141-230g",
    "3) 231-330g": "231-330g",
    "4) 331-400g": "331-400g",
    "5) 401-600g": "401-600g",
    "6) 601g+": "601g+",
}

ENVASES_VALIDOS = {
    "Doypack",
    "Frasco",
    "Frasco Premium",
    "Lata",
    "Bandeja",
}


def _slug(texto: str) -> str:
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", (texto or "").strip().lower())
        if not unicodedata.combining(c)
    )
    texto = re.sub(r"\s+", " ", texto)
    return texto


def _safe_int(valor) -> int | None:
    if pd.isna(valor):
        return None
    try:
        return int(round(float(valor)))
    except Exception:
        return None


def gramaje_a_grupo_aceituna(g) -> str | None:
    if not g:
        return None
    if g <= 140:
        return "1) hasta 140g"
    if g <= 230:
        return "2) 141-230g"
    if g <= 330:
        return "3) 231-330g"
    if g <= 400:
        return "4) 331-400g"
    if g <= 600:
        return "5) 401-600g"
    return "6) 601g+"


def gramaje_grupo_label_aceituna(grupo: str | None) -> str:
    return GRAMAJE_GRUPOS_LABELS.get(grupo or "", grupo or "Sin gramaje")


def _normalizar_envase(valor: str | None) -> str | None:
    key = _slug(valor or "")
    if not key:
        return None
    alias = {
        "doypack": "Doypack",
        "doy pack": "Doypack",
        "pouch": "Doypack",
        "bolsa": "Doypack",
        "sachet": "Doypack",
        "sobre": "Doypack",
        "frasco": "Frasco",
        "fco": "Frasco",
        "vidrio": "Frasco",
        "pote": "Frasco",
        "frasco premium": "Frasco Premium",
        "lata": "Lata",
        "tarro": "Lata",
        "bandeja": "Bandeja",
    }
    return alias.get(key)


@lru_cache(maxsize=1)
def _cargar_unificaciones_gramaje():
    by_pid: dict[str, int] = {}
    by_name: dict[tuple[str, str], int] = {}
    by_producto: dict[str, int] = {}
    by_mvg: dict[tuple[str, str, int], int] = {}

    if not ARCHIVO_UNIFICACIONES.exists():
        return by_pid, by_name, by_producto, by_mvg

    df = pd.read_excel(ARCHIVO_UNIFICACIONES, sheet_name="Unificaciones")
    for _, row in df.iterrows():
        unified = _safe_int(row.get("Gramaje Unificado (g)"))
        original = _safe_int(row.get("Gramaje Original (g)"))
        if unified is None:
            continue

        pid = str(row.get("producto_id") or "").strip()
        cadena = _slug(str(row.get("Supermercado") or ""))
        nombre = _slug(str(row.get("Nombre") or ""))
        marca = _slug(str(row.get("Marca") or ""))
        variedad = _slug(str(row.get("Variedad") or ""))

        if pid:
            by_pid[pid] = unified
        if cadena and nombre:
            by_name[(cadena, nombre)] = unified
        if nombre:
            by_producto[nombre] = unified
        if marca and variedad and original is not None:
            by_mvg[(marca, variedad, original)] = unified

    return by_pid, by_name, by_producto, by_mvg


def buscar_gramaje_unificado_catalogo(
    supermercado: str,
    nombre: str,
    producto_id,
    marca: str,
    variedad: str,
    gramos,
) -> int | None:
    by_pid, by_name, by_producto, by_mvg = _cargar_unificaciones_gramaje()

    pid = str(producto_id or "").strip()
    if pid and pid in by_pid:
        return by_pid[pid]

    key_name = (_slug(supermercado), _slug(nombre))
    if all(key_name) and key_name in by_name:
        return by_name[key_name]

    producto = _slug(nombre)
    if producto and producto in by_producto:
        return by_producto[producto]

    gramos_int = _safe_int(gramos)
    key_mvg = (_slug(marca), _slug(variedad), gramos_int)
    if all(key_mvg[:2]) and gramos_int is not None and key_mvg in by_mvg:
        return by_mvg[key_mvg]

    return gramos_int


def _resolver_envase_desde_conteo(conteo: dict[str, int]) -> str | None:
    if not conteo:
        return None
    ordenados = sorted(conteo.items(), key=lambda item: (-item[1], item[0]))
    if len(ordenados) == 1:
        return ordenados[0][0]
    if ordenados[0][1] >= ordenados[1][1] * 2:
        return ordenados[0][0]
    return None


@lru_cache(maxsize=1)
def _cargar_envases_catalogo():
    exactos: dict[tuple[str, str], dict[str, int]] = {}
    por_nombre: dict[str, dict[str, int]] = {}
    por_familia: dict[tuple[str, str, int], dict[str, int]] = {}

    archivos = [ARCHIVO_REVISION_ENVASE, ARCHIVO_ENVASE]
    for archivo in archivos:
        if not archivo.exists():
            continue
        xls = pd.ExcelFile(archivo)
        for sheet in xls.sheet_names:
            df = pd.read_excel(archivo, sheet_name=sheet)
            if "Cadena" not in df.columns or "Producto" not in df.columns:
                continue
            corr_col = next((c for c in df.columns if _slug(str(c)) == "correccion_manual"), None)
            for _, row in df.iterrows():
                manual = _normalizar_envase(str(row.get(corr_col) or "").strip()) if corr_col else None
                detectado = _normalizar_envase(str(row.get("Tipo_envase") or "").strip())
                envase = manual or detectado
                if envase not in ENVASES_VALIDOS:
                    continue

                peso = 3 if manual else 1
                cadena = _slug(str(row.get("Cadena") or ""))
                producto = _slug(str(row.get("Producto") or ""))
                marca = _slug(str(row.get("Marca_raw") or row.get("Marca") or ""))
                variedad = _slug(str(row.get("Variedad_raw") or row.get("Variedad") or ""))
                gramos = _safe_int(row.get("Gramos"))

                if cadena and producto:
                    exactos.setdefault((cadena, producto), {})
                    exactos[(cadena, producto)][envase] = exactos[(cadena, producto)].get(envase, 0) + peso
                if producto:
                    por_nombre.setdefault(producto, {})
                    por_nombre[producto][envase] = por_nombre[producto].get(envase, 0) + peso
                if marca and variedad and gramos is not None:
                    key = (marca, variedad, gramos)
                    por_familia.setdefault(key, {})
                    por_familia[key][envase] = por_familia[key].get(envase, 0) + peso

    exactos_resueltos = {
        key: _resolver_envase_desde_conteo(conteo)
        for key, conteo in exactos.items()
    }
    por_nombre_resueltos = {
        key: _resolver_envase_desde_conteo(conteo)
        for key, conteo in por_nombre.items()
    }
    por_familia_resueltos = {
        key: _resolver_envase_desde_conteo(conteo)
        for key, conteo in por_familia.items()
    }
    return exactos_resueltos, por_nombre_resueltos, por_familia_resueltos


def resolver_envase_catalogo(
    supermercado: str,
    nombre: str,
    marca: str,
    variedad: str,
    gramos,
    envase_detectado: str,
) -> str:
    envase_norm = _normalizar_envase(envase_detectado)
    envase_detectado = envase_norm or (envase_detectado if envase_detectado in ENVASES_VALIDOS else "Sin detectar")
    exactos, por_nombre, por_familia = _cargar_envases_catalogo()
    key_exacto = (_slug(supermercado), _slug(nombre))
    envase_catalogo = (
        exactos.get(key_exacto)
        or por_nombre.get(_slug(nombre))
        or por_familia.get((_slug(marca), _slug(variedad), _safe_int(gramos)))
    )
    if envase_catalogo:
        envase_detectado = envase_catalogo

    marca_slug = _slug(marca)
    variedad_slug = _slug(variedad)
    nombre_slug = _slug(nombre)
    gramos_int = _safe_int(gramos)

    # Correcciones manuales validadas sobre familias unificadas.
    # La Toscana verde con carozo 300g (Disco/Jumbo/Vea) corresponde a frasco.
    if (
        marca_slug in {"la toscana", "toscana"}
        and gramos_int == 300
        and (
            variedad_slug in {"verde", "verde con carozo"}
            or "verdes con carozo 300 gr" in nombre_slug
        )
    ):
        return "Frasco"

    if envase_detectado in ENVASES_VALIDOS:
        return envase_detectado

    if _slug(marca) != "castell":
        return envase_detectado

    n = _slug(nombre)

    if "premium" in n or " prem " in f" {n} " or n.endswith(" prem"):
        return "Frasco Premium"
    if any(tok in n for tok in ("doypack", "doy pack", " dp ", " pouch", " pou", " xl ")):
        return "Doypack"
    if any(tok in n for tok in ("ahumad", "picante", " ajo")):
        return "Doypack"
    if gramos_int and gramos_int <= 330:
        return "Doypack"
    if gramos_int and gramos_int > 330:
        return "Frasco Premium"
    return envase_detectado
