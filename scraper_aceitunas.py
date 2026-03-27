"""
Scraper de precios de aceitunas - Supermercados Argentina
Uso: python scraper_aceitunas.py
"""

import io
import os
import re
import sqlite3
import sys
import time
import unicodedata
import webbrowser
from datetime import date
from pathlib import Path

# Forzar UTF-8 en la consola (Windows cp1252 no soporta algunos caracteres)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup

from aceitunas_catalogo_manual import (
    buscar_gramaje_unificado_catalogo,
    gramaje_a_grupo_aceituna,
)
from tracker_paths import precios_db_path

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

DIRECTORIO = Path(__file__).parent
DB_PATH    = precios_db_path()
ARCHIVO_ANALISIS_AC = DIRECTORIO / "analisis_calidad_aceitunas.txt"

PRECIO_MIN_AC = 500
PRECIO_MAX_AC = 50_000

GRAMOS_MIN_AC = 50
GRAMOS_MAX_AC = 3_000

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

TERMINOS_BUSQUEDA_AC = [
    "aceitunas",
    "aceituna",
    "aceitunas verdes",
    "aceitunas negras",
]

PALABRAS_EXCLUIR_AC = [
    "empanada", "pizza", "relleno para",
    "pasta de aceituna", "pasta aceitunas", "pasta de aceitunas",
    "tapenade", "paté de", "pasta para untar",
    "aceite de oliva", "aceite oliva",
    "sandwich", "sandwiche", "sándwich",
    "ciabata", "ciabatta",
]

_HEADLESS_FALSE_VALUES = {"0", "false", "no", "off"}


def _resolver_headless(auto_mode: bool) -> bool:
    valor = os.environ.get("ACEITE_TRACKER_HEADLESS")
    if valor is None:
        return auto_mode
    return valor.strip().lower() not in _HEADLESS_FALSE_VALUES

VTEX_SUPERS = {
    "Carrefour": "https://www.carrefour.com.ar",
    "Día":       "https://diaonline.supermercadosdia.com.ar",
}

CENCOSUD_SUPERS = {
    "Jumbo": "https://www.jumbo.com.ar",
    "Disco": "https://www.disco.com.ar",
    "Vea":   "https://www.vea.com.ar",
}

# ---------------------------------------------------------------------------
# Normalización de texto
# ---------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    """Lowercase + quitar tildes."""
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ---------------------------------------------------------------------------
# Filtro de producto
# ---------------------------------------------------------------------------

def es_aceituna(nombre: str) -> bool:
    n = _normalizar(nombre)
    m_ac = re.search(r"aceitun[ao]", n)
    if not m_ac:
        return False
    # Excluir si "queso" aparece ANTES de "aceituna" → es producto de queso con aceitunas
    m_q = re.search(r"\bqueso\b", n)
    if m_q and m_q.start() < m_ac.start():
        return False
    # Excluir si la primera palabra es "pasta" → es untable de aceitunas, no aceitunas
    if re.match(r"pasta\b", n):
        return False
    if any(_normalizar(excl) in n for excl in PALABRAS_EXCLUIR_AC):
        return False
    return True


def precio_ac_valido(precio: float) -> bool:
    return PRECIO_MIN_AC <= precio <= PRECIO_MAX_AC


# ---------------------------------------------------------------------------
# Clasificación de variedad
# ---------------------------------------------------------------------------

_VARIEDADES_PATS_RAW: list[tuple[str, str, str]] = [
    # (pattern, variedad_canonical, confianza)
    # Negras primero
    (r"negra[s]?\s+des?carozada[s]?|negra[s]?\s+descor\b", "Negra Descarozada", "alta"),
    (r"negra[s]?\s+(?:en\s+)?rodaja[ds]?a?[s]?", "Negra Rodajada",       "alta"),
    (r"negra[s]?\s+rellena[s]?",                "Negra Rellena",        "alta"),
    (r"kalamata",                                "Kalamata",             "alta"),
    (r"negra[s]?",                               "Negra",                "alta"),
    # Verdes rellenas (específico antes que genérico)
    (r"rellena[s]?\s+(?:con\s+)?queso",         "Verde Rellena Queso",  "alta"),
    (r"rellena[s]?\s+(?:con\s+)?salmon",        "Verde Rellena Salmón", "alta"),
    (r"rellena[s]?\s+(?:con\s+)?anchoa[s]?",    "Verde Rellena Anchoas","alta"),
    (r"rellena[s]?\s+(?:con\s+)?morron[es]?",   "Verde Rellena Morrón", "alta"),
    (r"rellena[s]?",                             "Verde Rellena Morrón", "media"),  # default = morrón
    # Verdes con características
    (r"(?:con\s+)?ajo\b",                        "Verde con Ajo",        "alta"),
    (r"picante[s]?",                             "Verde Picante",        "alta"),
    (r"ahumad[ao]s?",                            "Verde Ahumada",        "alta"),
    (r"(?:en\s+)?rodaja[ds]?a?[s]?",             "Verde Rodajada",       "alta"),
    (r"des?carozada[s]?|descor\b",               "Verde Descarozada",    "alta"),
    (r"saborizada[s]?",                          "Verde Saborizada",     "alta"),
    # Mix
    (r"mix\b|mixta[s]?\b|combinad[ao]|surtid[ao]|variedad", "Mix",      "alta"),
    # Verde genérica (fallback)
    (r"verde[s]?",                               "Verde",                "alta"),
]
_VARIEDADES_PATS = [
    (re.compile(p, re.IGNORECASE), v, c)
    for p, v, c in _VARIEDADES_PATS_RAW
]


def clasificar_variedad(nombre: str) -> tuple[str, str]:
    """Retorna (variedad_canonical, confianza: 'alta'|'media'|'baja')."""
    n = _normalizar(nombre)
    for pat, variedad, conf in _VARIEDADES_PATS:
        if pat.search(n):
            return (variedad, conf)
    return ("Verde", "baja")


# ---------------------------------------------------------------------------
# Extracción de gramaje
# ---------------------------------------------------------------------------

_PAT_SIN_ESCURRIR = re.compile(
    r"(?:peso\s+(?:sin\s+esc[u]?rrir|neto)|contenido\s+neto|neto|s\.?\s*e\.?)\s*"
    r"[:\-]?\s*(\d{2,4})\s*(?:gr?|grs?|grm[s]?|g(?=\b))",
    re.IGNORECASE,
)
_PAT_ESCURRIDO = re.compile(
    r"(?:peso\s+esc[u]?rrido|contenido\s+esc[u]?rrido|esc[u]?rrido|p\.?\s*e\.?)\s*"
    r"[:\-]?\s*(\d{2,4})\s*(?:gr?|grs?|grm[s]?|g(?=\b))",
    re.IGNORECASE,
)
_PAT_PESO_SOLO = re.compile(
    r"(?:^|(?<=[\s\-,.(X x]))(\d{2,4})\s*(?:gr?s?|grm[s]?|g(?=\b))",
    re.IGNORECASE,
)
_PAT_X_GRAMAJE = re.compile(
    r"\bx\s*(\d{2,4})(?=\s*(?:gr?s?|grm[s]?|g\b|doy\s*pack\b|doypack\b|dp\b|"
    r"sachet\b|fras(?:co)?\b|fco\b|pote\b|tarro\b|lata\b|bolsa\b|$))",
    re.IGNORECASE,
)
_PAT_ENVASE_GRAMAJE = re.compile(
    r"(?:fras(?:co)?|fco|pote|tarro|doy\s*pack|doypack|dp|sachet|pouch|bolsa|lata)\s*x?\s*(\d{2,4})\b",
    re.IGNORECASE,
)

_SPECS_SIN_ESCURRIR = {
    "peso neto", "contenido neto", "peso sin escurrir",
    "peso bruto", "gramaje", "contenido",
    # NOTA: "gramaje de unidad de consumo" de Carrefour es tamaño de porción, NO total → no incluir
}
_SPECS_ESCURRIDO = {
    "peso escurrido", "contenido escurrido", "peso drenado",
    "peso escur", "escurrido",
}

# Cadenas que siempre expresan gramaje en "sin escurrir" (peso neto del frasco)
_CADENAS_SIN_ESCURRIR = {
    "Carrefour", "Día", "Coto",
    "Jumbo", "Disco", "Vea",
}


def _gramos_valido(g: int | None) -> bool:
    if g is None:
        return False
    return GRAMOS_MIN_AC <= g <= GRAMOS_MAX_AC


def _buscar_gramos_etiquetado(texto: str) -> tuple[int | None, int | None]:
    """Busca pesos con etiqueta. Retorna (sin_escurrir, escurrido)."""
    t = _normalizar(texto)
    sin_esc, esc = None, None
    m = _PAT_SIN_ESCURRIR.search(t)
    if m:
        try:
            sin_esc = int(m.group(1))
        except ValueError:
            pass
    m = _PAT_ESCURRIDO.search(t)
    if m:
        try:
            esc = int(m.group(1))
        except ValueError:
            pass
    return sin_esc, esc


def _parsear_gramos_spec(valor: str) -> int | None:
    """Parsea un valor de spec que puede ser '330.00' o '330 grm' o '330g'."""
    # Primero intenta con sufijo de unidad
    v = _buscar_gramos_solo(valor)
    if v is not None:
        return v
    # Luego intenta número puro (sin unidad, como "330.00")
    m = re.match(r"^\s*(\d{2,4})(?:[.,]\d+)?\s*$", valor.strip())
    if m:
        try:
            g = int(m.group(1))
            if _gramos_valido(g):
                return g
        except ValueError:
            pass
    return None


def _buscar_gramos_solo(texto: str) -> int | None:
    """Primer número de gramos sin etiqueta que sea válido."""
    for m in _PAT_PESO_SOLO.finditer(_normalizar(texto)):
        try:
            v = int(m.group(1))
            if _gramos_valido(v):
                return v
        except ValueError:
            pass
    return None


def _buscar_gramos_contexto_libre(texto: str) -> int | None:
    """
    Captura formatos comunes de catálogo como "X140 Doy Pack", "X240gr"
    o "Frasco 320" cuando el sitio no muestra la unidad completa.
    """
    t = _normalizar(texto)
    for pat in (_PAT_X_GRAMAJE, _PAT_ENVASE_GRAMAJE):
        m = pat.search(t)
        if not m:
            continue
        try:
            v = int(m.group(1))
        except ValueError:
            continue
        if _gramos_valido(v):
            return v
    return None


def _backsolve(precio: float, ppk: float | None) -> int | None:
    if not ppk or ppk <= 0 or precio <= 0 or ppk <= precio:
        return None
    return round(precio / (ppk / 1000))


def _match_cerca(calculado: int | None, candidatos: list[int | None], tol: float = 0.15) -> int | None:
    if calculado is None:
        return None
    mejor, mejor_dif = None, float("inf")
    for c in candidatos:
        if c is None:
            continue
        dif = abs(calculado - c) / max(calculado, 1)
        if dif <= tol and dif < mejor_dif:
            mejor, mejor_dif = c, dif
    return mejor


def extraer_gramaje_aceituna(
    nombre: str,
    supermercado: str,
    measure_unit: str = "",
    unit_mult: float = 0.0,
    textos_extra: list[str] | None = None,
    specs: dict[str, str] | None = None,
    precio: float = 0.0,
    precio_por_kilo: float | None = None,
) -> dict:
    """
    Extrae gramaje en base sin_escurrir.
    Retorna dict con gramos_sin_escurrir, gramos_escurrido, fuente, confianza.
    """
    sin_esc: int | None = None
    esc:     int | None = None
    fuente    = "unknown"
    confianza = "baja"

    # 1. measurementUnit / unitMultiplier VTEX
    if measure_unit and unit_mult and unit_mult > 0:
        um = measure_unit.lower().strip()
        if um in ("g", "gr", "grs", "grm", "grms", "gramo", "gramos"):
            raw = int(float(unit_mult))
            if _gramos_valido(raw):
                if supermercado == "Chango Mas" and precio_por_kilo:
                    esc = raw
                else:
                    sin_esc = raw
                fuente, confianza = "vtex", "media"
        elif um in ("kg", "kgs", "kilogramo", "kilogramos"):
            raw = int(float(unit_mult) * 1000)
            if _gramos_valido(raw):
                sin_esc = raw
                fuente, confianza = "vtex", "media"

    # 2. Especificaciones VTEX etiquetadas
    if specs:
        for sk, sv in specs.items():
            k = _normalizar(sk)
            if k in _SPECS_SIN_ESCURRIR:
                v = _parsear_gramos_spec(sv)
                if v is not None:
                    sin_esc = v
                    fuente, confianza = "spec", "alta"
            elif k in _SPECS_ESCURRIDO:
                v = _parsear_gramos_spec(sv)
                if v is not None:
                    esc = v
                    if fuente != "spec":
                        fuente, confianza = "spec", "alta"

    # 3. Regex etiquetado en nombre + textos extra
    for texto in [nombre] + (textos_extra or []):
        if not texto:
            continue
        s, e = _buscar_gramos_etiquetado(texto)
        if s is not None and sin_esc is None:
            sin_esc = s
            if fuente == "unknown":
                fuente, confianza = "nombre", "alta"
        if e is not None and esc is None:
            esc = e
            if fuente == "unknown":
                fuente, confianza = "nombre", "alta"
        if sin_esc is not None and esc is not None:
            break

    # 4. Back-calculation desde precio_por_kilo
    impl = _backsolve(precio, precio_por_kilo)
    if impl is not None:
        if supermercado == "Chango Mas":
            # Chango con ppk → base escurrido
            matched = _match_cerca(impl, [esc, sin_esc])
            if matched is not None:
                esc = matched
                fuente, confianza = "backsolve", "media"
            elif _gramos_valido(impl):
                esc = impl
                fuente, confianza = "backsolve", "media"
        else:
            matched = _match_cerca(impl, [sin_esc, esc])
            if matched is not None and sin_esc is None:
                sin_esc = matched
                if confianza != "alta":
                    fuente, confianza = "backsolve", "media"
            elif sin_esc is None and _gramos_valido(impl):
                sin_esc = impl
                fuente, confianza = "backsolve", "media"

    # 5. Fallback: número suelto según regla de cadena
    if sin_esc is None and esc is None:
        for texto in [nombre] + (textos_extra or []):
            v = _buscar_gramos_contexto_libre(texto)
            if v is not None:
                if supermercado == "Chango Mas" and precio_por_kilo:
                    esc = v
                else:
                    sin_esc = v
                fuente, confianza = "nombre", "media"
                break

        for texto in [nombre] + (textos_extra or []):
            v = _buscar_gramos_solo(texto)
            if v is not None:
                if supermercado == "Chango Mas" and precio_por_kilo:
                    esc = v
                else:
                    sin_esc = v
                # Cadenas con regla de base conocida → "media"; resto → "baja"
                if supermercado in _CADENAS_SIN_ESCURRIR or (
                    supermercado == "Chango Mas" and precio_por_kilo
                ):
                    fuente, confianza = "nombre", "media"
                else:
                    fuente, confianza = "nombre", "baja"
                break

    # 6. Derivar sin_escurrir desde escurrido (Chango Más con ppk)
    RATIO = 0.65
    if sin_esc is None and esc is not None and _gramos_valido(esc):
        derived = round(esc / RATIO)
        if _gramos_valido(derived):
            sin_esc = derived
            if confianza == "alta":
                confianza = "media"

    # 7. Validación final
    if not _gramos_valido(sin_esc):
        sin_esc = None
    if not _gramos_valido(esc):
        esc = None
    if sin_esc is None and esc is None:
        fuente, confianza = "unknown", "baja"

    return {
        "gramos_sin_escurrir": sin_esc,
        "gramos_escurrido":    esc,
        "fuente":              fuente,
        "confianza":           confianza,
    }


# ---------------------------------------------------------------------------
# Precio por 100g
# ---------------------------------------------------------------------------

def precio_por_100g(precio: float, gramos: int | None) -> int | None:
    if gramos and gramos > 0:
        return round(precio / gramos * 100)
    return None


def aplicar_catalogo_gramajes(productos: list[dict]) -> list[dict]:
    ajustados: list[dict] = []
    for p in productos:
        g_actual = p.get("gramos_sin_escurrir")
        g_unificado = buscar_gramaje_unificado_catalogo(
            p.get("supermercado", ""),
            p.get("nombre", ""),
            p.get("producto_id"),
            p.get("marca", ""),
            p.get("variedad", ""),
            g_actual,
        )
        if not g_unificado or g_unificado == g_actual:
            ajustados.append(p)
            continue

        nuevo = dict(p)
        nuevo["gramos_sin_escurrir"] = g_unificado
        nuevo["gramaje_fuente"] = "catalogo"
        nuevo["gramaje_confianza"] = "alta"
        nuevo["precio_100g"] = precio_por_100g(nuevo["precio"], g_unificado)
        if nuevo.get("precio_sin_dto"):
            nuevo["precio_sin_dto_100g"] = precio_por_100g(nuevo["precio_sin_dto"], g_unificado)
        nuevo["gramaje_grupo"] = gramaje_a_grupo_aceituna(g_unificado)
        ajustados.append(nuevo)
    return ajustados


# ---------------------------------------------------------------------------
# Marca
# ---------------------------------------------------------------------------

_MARCAS_ALIAS_AC: dict[str, str] = {
    "del fuerte":   "Del Fuerte",
    "la sevillana": "La Sevillana",
    "cuisine & co": "Cousine & Co",
    "cousine & co": "Cousine & Co",
    "aceitunera":   "Aceitunera",
    "qualita":      "Qualitá",
    "qualitá":      "Qualitá",
    "sevillana":    "La Sevillana",
    "crespi":       "Crespi",
    "olimega":      "Olimega",
    "arcor":        "Arcor",
    "bells":        "Bell's",
    "facundo":      "Facundo",
    "nucete":       "Nucete",
    "castell":      "Castell",
    "yovinessa":    "Yovinessa",
    "cuisine":      "Cousine & Co",
    "cousine":      "Cousine & Co",
    "carrefour":    "Carrefour",
    "jumbo":        "Jumbo",
    "disco":        "Disco",
    "vea":          "Vea",
    "coto":         "Coto",
    "dia":          "Día",
    "día":          "Día",
}
_MARCAS_AC_SORTED = sorted(_MARCAS_ALIAS_AC.items(), key=lambda x: -len(x[0]))

_NO_MARCA_AC = {
    "ml", "cc", "lt", "lts", "gr", "grm", "grms", "kg", "g", "l",
    "aceituna", "aceitunas", "verde", "verdes", "negra", "negras",
    "rellena", "rellenas", "descarozada", "descarozadas", "rodajada",
    "rodajas", "rodaja",
    "kalamata", "mix", "mixta", "surtido",
    "de", "en", "con", "sin", "el", "la", "los", "las", "un", "una", "por",
    "x", "y", "e", "o", "u", "a", "al",
    "frasco", "lata", "envase", "tarro", "pouch", "doypack", "sachet", "pou",
    "sabor", "saborizad", "saborizada", "saborizadas", "picante", "ahumada", "ahumado",
    "clasica", "clásica", "premium", "extra", "light", "xl", "classic",
    "morron", "morrón", "morrones", "ajo", "limon", "limón",
    "rellenas", "rellena",
}

_MARCA_CORRECCIONES_AC = {
    "Toscana":      "La Toscana",
    "Trozos":       "Marvavic",
    "Gordal":       "Ybarra",
    "Premium":      "Castell",
    "La Malaguena": "La Malagueña",
    "Malagueña":    "La Malagueña",
    "Malaguena":    "La Malagueña",
}

_PALABRAS_NO_MARCA_AC = {
    "Manzanilla", "Enteras", "Entera", "Descarozada", "Descarozadas",
    "Descarozado", "Carozo", "Rodajas", "Rodaja", "Trozos", "Picadas",
    "Rellenas", "Rellena", "Rell.con", "Ajo", "Anchoas", "Jalapeños",
    "Jalapeño", "Pimiento", "Pimientos", "Morrones", "Morron", "Morrón",
    "C/morrón", "Salmon", "Salmón", "Salm", "Queso", "Parmesano",
    "Jamón", "Jamon", "Pasta", "Picantes", "Picante", "Ahumado",
    "Ahumada", "Doy", "Check", "Clásica", "Clásicas", "Clasica",
    "Clasicas", "Orgánicas", "Organicas", "Naturales", "Españolas",
    "Espanolas", "Ver", "Verdes", "Verde", "Negr", "Negras", "Negra",
    "Aceitunas", "Aceituna", "Aceitunas.verdes", "Rodajadas",
}


def extraer_marca_aceituna(nombre: str) -> str:
    n = nombre.lower()
    for alias, canonical in _MARCAS_AC_SORTED:
        if alias in n:
            return canonical
    for palabra in nombre.split():
        p = palabra.lower().strip(".,()-/&")
        if len(p) > 2 and p not in _NO_MARCA_AC and not re.search(r"\d", p):
            return palabra.strip(".,()-/&").capitalize()
    return "Otra"


def limpiar_marca_aceituna(marca: str, cadena: str) -> str:
    """Normaliza marcas antes de agrupar y guardar en la base."""
    marca = (marca or "").strip()
    if not marca:
        return "Otra"
    if marca in _MARCA_CORRECCIONES_AC:
        return _MARCA_CORRECCIONES_AC[marca]
    if marca in _PALABRAS_NO_MARCA_AC:
        return cadena
    return marca


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------

def _init_db_aceitunas(cur: sqlite3.Cursor) -> None:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS aceitunas (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha               TEXT    NOT NULL,
            supermercado        TEXT    NOT NULL,
            nombre              TEXT    NOT NULL,
            variedad            TEXT,
            variedad_confianza  TEXT,
            gramos_sin_escurrir INTEGER,
            gramos_escurrido    INTEGER,
            gramaje_fuente      TEXT,
            gramaje_confianza   TEXT,
            precio              REAL    NOT NULL,
            precio_sin_dto      REAL,
            en_oferta           INTEGER NOT NULL DEFAULT 0,
            precio_100g         INTEGER,
            precio_sin_dto_100g INTEGER,
            gramaje_grupo       TEXT,
            marca               TEXT,
            producto_id         TEXT,
            url                 TEXT,
            UNIQUE(fecha, supermercado, nombre)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ac_fecha    ON aceitunas(fecha)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ac_variedad ON aceitunas(variedad)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gramaje_overrides (
            producto_id         TEXT    PRIMARY KEY,
            supermercado        TEXT    NOT NULL,
            nombre              TEXT    NOT NULL,
            url                 TEXT,
            gramos_sin_escurrir INTEGER NOT NULL,
            gramos_escurrido    INTEGER,
            notas               TEXT,
            verificado_en       TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS marca_overrides (
            producto_id    TEXT NOT NULL,
            supermercado   TEXT NOT NULL,
            nombre         TEXT,
            marca_correcta TEXT NOT NULL,
            notas          TEXT,
            verificado_en  TEXT,
            PRIMARY KEY (producto_id, supermercado)
        )
    """)


def buscar_override(cur: sqlite3.Cursor, producto_id: str | None) -> dict | None:
    if not producto_id:
        return None
    row = cur.execute(
        "SELECT gramos_sin_escurrir, gramos_escurrido FROM gramaje_overrides WHERE producto_id = ?",
        (str(producto_id),),
    ).fetchone()
    if row:
        return {"gramos_sin_escurrir": row[0], "gramos_escurrido": row[1]}
    return None


def buscar_marca_override(cur: sqlite3.Cursor, producto_id: str | None, supermercado: str) -> str | None:
    """Devuelve la marca corregida si existe en marca_overrides, o None."""
    if not producto_id:
        return None
    row = cur.execute(
        "SELECT marca_correcta FROM marca_overrides WHERE producto_id = ? AND supermercado = ?",
        (str(producto_id), supermercado),
    ).fetchone()
    return row[0] if row else None


def guardar_override(
    cur: sqlite3.Cursor,
    producto_id: str,
    supermercado: str,
    nombre: str,
    url: str | None,
    gramos_sin_escurrir: int,
    gramos_escurrido: int | None = None,
    notas: str | None = None,
) -> None:
    cur.execute("""
        INSERT OR REPLACE INTO gramaje_overrides
          (producto_id, supermercado, nombre, url, gramos_sin_escurrir,
           gramos_escurrido, notas, verificado_en)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(producto_id), supermercado, nombre, url,
        gramos_sin_escurrir, gramos_escurrido, notas,
        str(date.today()),
    ))
    cur.connection.commit()  # Commit inmediato — no se pierde si se interrumpe


def gramaje_a_grupo(g) -> str | None:
    """Clasifica gramos_sin_escurrir en grupos de comparacion."""
    if not g:
        return None
    if g <= 140:  return "1) hasta 140g"
    if g <= 230:  return "2) 141-230g"
    if g <= 330:  return "3) 231-330g"
    if g <= 400:  return "4) 331-400g"
    if g <= 600:  return "5) 401-600g"
    return "6) 601g+"


def guardar_en_sqlite_aceitunas(productos: list[dict], fecha: str) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    _init_db_aceitunas(cur)
    cur.execute("DELETE FROM aceitunas WHERE fecha = ?", (fecha,))

    filas = []
    for p in productos:
        g  = p.get("gramos_sin_escurrir")
        gs = p.get("precio_sin_dto")
        filas.append({
            "fecha":               fecha,
            "supermercado":        p.get("supermercado", ""),
            "nombre":              p.get("nombre", ""),
            "variedad":            p.get("variedad"),
            "variedad_confianza":  p.get("variedad_confianza"),
            "gramos_sin_escurrir": g,
            "gramos_escurrido":    p.get("gramos_escurrido"),
            "gramaje_fuente":      p.get("gramaje_fuente"),
            "gramaje_confianza":   p.get("gramaje_confianza"),
            "precio":              p.get("precio", 0),
            "precio_sin_dto":      gs,
            "en_oferta":           1 if p.get("en_oferta") else 0,
            "precio_100g":         precio_por_100g(p.get("precio", 0), g),
            "precio_sin_dto_100g": precio_por_100g(gs, g) if gs else None,
            "gramaje_grupo":       gramaje_a_grupo(g),
            "marca":               p.get("marca"),
            "producto_id":         p.get("producto_id"),
            "url":                 p.get("url"),
        })

    cur.executemany("""
        INSERT OR IGNORE INTO aceitunas
          (fecha, supermercado, nombre, variedad, variedad_confianza,
           gramos_sin_escurrir, gramos_escurrido, gramaje_fuente, gramaje_confianza,
           precio, precio_sin_dto, en_oferta, precio_100g, precio_sin_dto_100g,
           gramaje_grupo, marca, producto_id, url)
        VALUES (:fecha, :supermercado, :nombre, :variedad, :variedad_confianza,
                :gramos_sin_escurrir, :gramos_escurrido, :gramaje_fuente, :gramaje_confianza,
                :precio, :precio_sin_dto, :en_oferta, :precio_100g, :precio_sin_dto_100g,
                :gramaje_grupo, :marca, :producto_id, :url)
    """, filas)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Helpers para scrapers VTEX
# ---------------------------------------------------------------------------

def _extraer_specs_vtex(item: dict, sku: dict) -> dict[str, str]:
    specs = {}
    for spec_name in item.get("allSpecifications", []):
        vals = item.get(spec_name, [])
        if isinstance(vals, list) and vals:
            specs[spec_name] = str(vals[0])
        elif isinstance(vals, str):
            specs[spec_name] = vals
    return specs


def _extraer_textos_vtex(item: dict, sku: dict) -> list[str]:
    textos = [
        sku.get("name", ""),
        item.get("description", ""),
        item.get("complementName", ""),
        item.get("metaTagDescription", ""),
    ]
    for spec_name in item.get("allSpecifications", []):
        vals = item.get(spec_name, [])
        if isinstance(vals, list):
            textos.extend(str(v) for v in vals)
        elif isinstance(vals, str):
            textos.append(vals)
    return [t for t in textos if t]


def _ppk_desde_specs(specs: dict[str, str]) -> float | None:
    for sk, sv in specs.items():
        sk_n = _normalizar(sk)
        # Carrefour: "pricePerUnit" = "29696.97"
        if sk_n == "priceperunit":
            try:
                v = float(sv.strip())
                if v > 0:
                    return v
            except ValueError:
                pass
        # Genérico: "precio x kg", "precio por kilo", etc.
        if re.search(r"precio.*kg|precio.*kilo", sk, re.IGNORECASE):
            # Carrefour "Precio x unidad": "($29,696.97 x 1 K.)"
            limpio = re.sub(r"[()$a-zA-Z\s]", "", sv).replace(".", "").split("x")[0]
            limpio = limpio.replace(",", ".")
            try:
                v = float(limpio.strip())
                if v > 0:
                    return v
            except ValueError:
                pass
    return None


def _construir_producto_ac(
    supermercado: str,
    nombre: str,
    price: float,
    precio_sin: float | None,
    en_oferta: bool,
    gramaje: dict,
    prod_id: str,
    url: str,
) -> dict:
    variedad, var_conf = clasificar_variedad(nombre)
    marca_raw = extraer_marca_aceituna(nombre)
    return {
        "supermercado":        supermercado,
        "nombre":              nombre,
        "variedad":            variedad,
        "variedad_confianza":  var_conf,
        "gramos_sin_escurrir": gramaje["gramos_sin_escurrir"],
        "gramos_escurrido":    gramaje["gramos_escurrido"],
        "gramaje_fuente":      gramaje["fuente"],
        "gramaje_confianza":   gramaje["confianza"],
        "precio":              round(price, 2),
        "precio_sin_dto":      round(precio_sin, 2) if precio_sin else None,
        "en_oferta":           en_oferta,
        "marca":               limpiar_marca_aceituna(marca_raw, supermercado),
        "producto_id":         prod_id,
        "url":                 url,
    }


# ---------------------------------------------------------------------------
# Scraper VTEX estándar (Carrefour, Día)
# ---------------------------------------------------------------------------

def scrape_vtex_aceitunas(supermercado: str, base_url: str) -> list[dict]:
    productos = []
    vistos: set[str] = set()

    for termino in TERMINOS_BUSQUEDA_AC:
        url = (
            f"{base_url}/api/catalog_system/pub/products/search/"
            f"{requests.utils.quote(termino)}"
            f"?O=OrderByPriceDESC&_from=0&_to=47"
        )
        try:
            resp = requests.get(url, headers=HEADERS_HTTP, timeout=20)
            if resp.status_code not in (200, 206):
                continue
            data = resp.json()
            if not data:
                continue

            nuevos = 0
            for item in data:
                nombre = item.get("productName", "")
                if not es_aceituna(nombre):
                    continue
                prod_id = str(item.get("productId", nombre))
                if prod_id in vistos:
                    continue
                vistos.add(prod_id)

                skus = item.get("items", [])
                if not skus:
                    continue
                sku   = skus[0]
                offer = sku.get("sellers", [{}])[0].get("commertialOffer", {})

                price      = float(offer.get("Price", 0) or 0)
                list_price = float(offer.get("ListPrice", 0) or 0)
                spot_price = float(offer.get("spotPrice", 0) or 0)
                disponible = int(offer.get("AvailableQuantity", 0) or 0)

                if price <= 0 or not precio_ac_valido(price) or disponible <= 0:
                    continue

                if spot_price > 0 and spot_price < price * 0.99 and precio_ac_valido(spot_price):
                    en_oferta, precio_sin, price = True, round(price, 2), spot_price
                else:
                    en_oferta  = (list_price > price * 1.01
                                  and list_price <= price * 1.35
                                  and precio_ac_valido(list_price))
                    precio_sin = round(list_price, 2) if en_oferta else None

                measure_unit = sku.get("measurementUnit", "")
                unit_mult    = float(sku.get("unitMultiplier", 0) or 0)
                specs        = _extraer_specs_vtex(item, sku)
                textos       = _extraer_textos_vtex(item, sku)
                ppk          = _ppk_desde_specs(specs)

                gramaje = extraer_gramaje_aceituna(
                    nombre, supermercado, measure_unit, unit_mult,
                    textos, specs, price, ppk,
                )

                link = item.get("link") or ""
                if link and not link.startswith("http"):
                    link = base_url.rstrip("/") + link

                productos.append(_construir_producto_ac(
                    supermercado, nombre, price, precio_sin, en_oferta,
                    gramaje, prod_id, link,
                ))
                nuevos += 1

            print(f"  [{supermercado}] '{termino}' → {nuevos} aceitunas")

        except Exception as e:
            print(f"  [{supermercado}] Error con '{termino}': {e}")

    return productos


# ---------------------------------------------------------------------------
# Chango Más (VTEX IO Intelligent Search)
# ---------------------------------------------------------------------------

def scrape_changomas_aceitunas() -> list[dict]:
    BASE = "https://www.masonline.com.ar/api/io/_v/api/intelligent-search/product_search/"
    productos = []
    vistos: set[str] = set()
    desde = 0
    paso  = 50

    while True:
        url = f"{BASE}?query=aceitunas&count={paso}&from={desde}&to={desde + paso - 1}"
        try:
            resp = requests.get(url, headers=HEADERS_HTTP, timeout=20)
            if resp.status_code not in (200, 206):
                break
            data = resp.json()
        except Exception as e:
            print(f"  [Chango Mas] Error en offset {desde}: {e}")
            break

        items_pagina = data.get("products", [])
        if not items_pagina:
            break

        nuevos = 0
        for item in items_pagina:
            nombre = item.get("productName", "")
            if not es_aceituna(nombre):
                continue
            prod_id = str(item.get("productId", nombre))
            if prod_id in vistos:
                continue
            vistos.add(prod_id)

            skus  = item.get("items", [])
            if not skus:
                continue
            sku   = skus[0]
            offer = sku.get("sellers", [{}])[0].get("commertialOffer", {})

            price      = float(offer.get("Price", 0) or 0)
            list_price = float(offer.get("ListPrice", 0) or 0)

            if price <= 0 or not precio_ac_valido(price):
                continue

            en_oferta  = list_price > price * 1.01 and precio_ac_valido(list_price)
            precio_sin = round(list_price, 2) if en_oferta else None

            measure_unit = sku.get("measurementUnit", "")
            unit_mult    = float(sku.get("unitMultiplier", 0) or 0)
            specs        = _extraer_specs_vtex(item, sku)
            textos       = _extraer_textos_vtex(item, sku)

            # Precio por kilo: desde offer.pricePerUnit o measurementUnit=kg
            ppk = float(offer.get("pricePerUnit", 0) or 0)
            if ppk > 0 and ppk <= price:
                ppk = None   # sanity: ppk debe ser mayor que precio por frasco
            elif ppk <= 0:
                ppk = None
            if ppk is None and unit_mult > 0 and measure_unit.lower() in ("kg", "kgs"):
                ppk = price / unit_mult

            gramaje = extraer_gramaje_aceituna(
                nombre, "Chango Mas", measure_unit, unit_mult,
                textos, specs, price, ppk,
            )

            link = item.get("link") or ""
            if link and not link.startswith("http"):
                link = "https://www.masonline.com.ar" + link

            productos.append(_construir_producto_ac(
                "Chango Mas", nombre, price, precio_sin, en_oferta,
                gramaje, link if link else prod_id, link,
            ))
            nuevos += 1

        print(f"  [Chango Mas] offset {desde}: {nuevos} aceitunas (total {len(productos)})")
        total = data.get("recordsFiltered", 0)
        desde += paso
        if desde >= total:
            break

    return productos


# ---------------------------------------------------------------------------
# Cencosud con Playwright (Jumbo, Disco, Vea)
# ---------------------------------------------------------------------------

_JS_CENCOSUD_AC = r"""() => {
    const cards = document.querySelectorAll('[class*="galleryItem"]');
    const result = [];
    for (const card of cards) {
        const nameEl = card.querySelector(
            '[class*="nameContainer"], [class*="brandName"], [class*="productName"]'
        );
        if (!nameEl) continue;
        const name = nameEl.textContent.trim();
        if (!name) continue;

        let currentPrice = null, originalPrice = null, discountPct = null;
        const allEls = card.querySelectorAll('*');

        for (const el of allEls) {
            if (el.children.length > 0) continue;
            const text = el.textContent.trim();

            if (!discountPct) {
                let clsCtx = '', node = el;
                for (let i = 0; i < 5 && node; i++) {
                    clsCtx += ' ' + (node.getAttribute('class') || '');
                    node = node.parentElement;
                }
                if (/saving|discount|badge|promo|ofert|percent|sticker|label|tag/i.test(clsCtx)) {
                    const mPct = text.match(/^-?(\d{1,2})\s*%(\s*off)?$/i);
                    if (mPct) { const p = parseInt(mPct[1]); if (p >= 5 && p <= 80) discountPct = p; }
                }
            }

            if (!text.match(/^[$][0-9][0-9.]+$/)) continue;
            const parent = el.parentElement;
            const parentText = parent ? parent.textContent : '';
            if (/lt\.|litro|impuesto/i.test(parentText)) continue;

            const deco = window.getComputedStyle(el).textDecorationLine || '';
            if (deco.includes('line-through')) { originalPrice = text; }
            else { if (!currentPrice) currentPrice = text; }
        }

        if (currentPrice && discountPct && !originalPrice) {
            const num = parseFloat(currentPrice.slice(1).replace(/[.]/g, '').replace(',', '.'));
            originalPrice = '$' + Math.round(num / (1 - discountPct / 100)).toLocaleString('es-AR');
        }

        let productHref = null;
        const cardLink = card.querySelector('a[href]');
        if (cardLink) {
            const href = cardLink.getAttribute('href');
            if (href && href.startsWith('/')) productHref = href;
        }

        if (currentPrice) result.push({ name, currentPrice, originalPrice, productHref });
    }
    return result;
}"""


def _parsear_precio_texto(texto: str, validar) -> float | None:
    if not texto:
        return None
    corte = re.search(r"sin\s+impuesto", texto, re.IGNORECASE)
    if corte:
        texto = texto[:corte.start()]
    m = re.search(r'\$([\s\d.]+)', texto)
    if not m:
        return None
    try:
        v = float(m.group(1).replace(".", "").replace(",", ".").strip())
        return v if validar(v) else None
    except ValueError:
        return None


def scrape_cencosud_aceitunas(
    supermercado: str,
    base_url: str,
    headless: bool = False,
) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(f"  [{supermercado}] Playwright no instalado. Saltando.")
        return []

    SEARCH_URL = f"{base_url}/aceitunas?_q=ACEITUNAS&map=ft"
    productos: list[dict] = []
    vistos: set[str] = set()
    items_total: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            print(f"  [{supermercado}] Iniciando sesión VTEX (home)...")
            try:
                page.goto(base_url, timeout=60_000, wait_until="domcontentloaded")
                page.wait_for_timeout(3_000)
            except Exception:
                print(f"  [{supermercado}] Home tardó mucho, continuando...")

            for pagina in range(1, 11):
                URL = SEARCH_URL if pagina == 1 else f"{SEARCH_URL}&page={pagina}"
                print(f"  [{supermercado}] Pág {pagina}: {URL}")
                page.goto(URL, timeout=30_000, wait_until="domcontentloaded")

                try:
                    page.wait_for_selector('[class*="galleryItem"]', timeout=20_000)
                except Exception:
                    print(f"  [{supermercado}] Sin products en pág {pagina}, terminando.")
                    break

                for _ in range(20):
                    page.evaluate("window.scrollBy(0, 600)")
                    page.wait_for_timeout(300)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(800)

                n_cards = page.evaluate(
                    "document.querySelectorAll('[class*=\"galleryItem\"]').length"
                )
                items_pag = page.evaluate(_JS_CENCOSUD_AC)
                items_total.extend(items_pag)
                print(f"  [{supermercado}] Pág {pagina}: {n_cards} cards, {len(items_pag)} aceitunas")

                if n_cards == 0 or not items_pag:
                    break

        except Exception as e:
            print(f"  [{supermercado}] Error Playwright: {e}")
        finally:
            browser.close()

    for item in items_total:
        nombre = (item.get("name") or "").strip()
        if not nombre or not es_aceituna(nombre):
            continue
        prod_key = item.get("productHref") or item.get("productId") or nombre
        if prod_key in vistos:
            continue
        vistos.add(prod_key)

        precio      = _parsear_precio_texto(item.get("currentPrice") or "", precio_ac_valido)
        precio_orig = _parsear_precio_texto(item.get("originalPrice") or "", precio_ac_valido)
        if not precio:
            continue

        en_oferta = bool(precio_orig and precio_orig > precio * 1.01)
        href      = item.get("productHref") or ""
        url_prod  = (base_url.rstrip("/") + href) if href else ""

        gramaje = extraer_gramaje_aceituna(nombre, supermercado, precio=precio)

        productos.append(_construir_producto_ac(
            supermercado, nombre, precio,
            round(precio_orig, 2) if en_oferta else None,
            en_oferta, gramaje, href or prod_key, url_prod,
        ))

    print(f"  [{supermercado}] {len(productos)} aceitunas total")
    return productos


# ---------------------------------------------------------------------------
# Coto (Playwright + BeautifulSoup)
# ---------------------------------------------------------------------------

def _parsear_precio_coto(texto: str) -> float | None:
    corte = re.search(r"sin\s+impuesto", texto, re.IGNORECASE)
    if corte:
        texto = texto[:corte.start()]
    for m in re.findall(r"\$[\s]*([\d.,]+)", texto):
        try:
            v = float(m.replace(".", "").replace(",", "."))
            if precio_ac_valido(v):
                return v
        except ValueError:
            pass
    return None


_COTO_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
Object.defineProperty(navigator, 'language', {get: () => 'es-AR'});
Object.defineProperty(navigator, 'languages', {get: () => ['es-AR', 'es', 'en-US', 'en']});
window.chrome = window.chrome || { runtime: {} };
"""


def _abrir_contexto_coto(pw, headless: bool):
    browser = pw.chromium.launch(headless=headless)
    context = browser.new_context(
        viewport={"width": 1400, "height": 1800},
        user_agent=HEADERS_HTTP["User-Agent"],
        locale="es-AR",
    )
    page = context.new_page()
    page.add_init_script(_COTO_STEALTH_JS)
    return browser, context, page


def _coto_bloqueado(page, html: str | None = None) -> bool:
    try:
        titulo = page.title().lower()
    except Exception:
        titulo = ""
    if "blocked" in titulo:
        return True
    contenido = (html or "").lower()
    return (
        "web page blocked" in contenido
        or "url you requested has been blocked" in contenido
    )


def scrape_coto_aceitunas(headless: bool = False) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [Coto] Playwright no instalado. Saltando.")
        return []

    productos: list[dict] = []
    vistos: set[str] = set()

    with sync_playwright() as pw:
        browser, context, page = _abrir_contexto_coto(pw, headless=headless)
        relanzado_visible = False

        pagina = 1
        while pagina < 20:
            url = "https://www.cotodigital.com.ar/sitios/cdigi/productos/aceitunas"
            if pagina > 1:
                url += f"?page={pagina}"
            print(f"  [Coto] Página {pagina}...")
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                alt_ant, sin_cambio = 0, 0
                for _ in range(60):
                    page.evaluate("window.scrollBy(0, 600)")
                    time.sleep(0.4)
                    alt_act = page.evaluate("document.body.scrollHeight")
                    if alt_act == alt_ant:
                        sin_cambio += 1
                        if sin_cambio >= 4:
                            break
                    else:
                        sin_cambio = 0
                    alt_ant = alt_act
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1.5)
                html = page.content()
                if _coto_bloqueado(page, html):
                    if headless and not relanzado_visible:
                        print("  [Coto] Bloqueo detectado en headless. Reintentando en visible...")
                        context.close()
                        browser.close()
                        browser, context, page = _abrir_contexto_coto(pw, headless=False)
                        relanzado_visible = True
                        continue
                    print("  [Coto] Bloqueo de seguridad detectado. Abortando scrape.")
                    break
            except Exception as e:
                if headless and not relanzado_visible:
                    print(f"  [Coto] Headless fallo en pagina {pagina}: {e}")
                    print("  [Coto] Reintentando en visible...")
                    context.close()
                    browser.close()
                    browser, context, page = _abrir_contexto_coto(pw, headless=False)
                    relanzado_visible = True
                    continue
                print(f"  [Coto] Error en página {pagina}: {e}")
                break

            soup   = BeautifulSoup(html, "html.parser")
            cards  = soup.select(".producto-card")
            if not cards and headless and not relanzado_visible:
                print(f"  [Coto] Página {pagina} vacía en headless. Reintentando en visible...")
                context.close()
                browser.close()
                browser, context, page = _abrir_contexto_coto(pw, headless=False)
                relanzado_visible = True
                continue
            nuevos = 0

            for card in cards:
                nombre_tag = card.select_one(".nombre-producto")
                if not nombre_tag:
                    continue
                nombre = nombre_tag.get_text(strip=True)
                if not es_aceituna(nombre):
                    continue

                href_tag = card.select_one("a[href]")
                coto_id  = href_tag["href"] if href_tag and href_tag.get("href") else nombre
                if coto_id in vistos:
                    continue
                vistos.add(coto_id)

                precio_tag = card.select_one(".card-title")
                if not precio_tag:
                    continue
                precio_real = _parsear_precio_coto(precio_tag.get_text(" ", strip=True))
                if precio_real is None:
                    continue

                precio_sin, en_oferta = None, False
                for small in card.select("small"):
                    t_s = small.get_text(" ", strip=True)
                    if re.search(r"precio\s+regular", t_s, re.IGNORECASE):
                        v = _parsear_precio_coto(t_s)
                        if v and v > precio_real * 1.01:
                            precio_sin, en_oferta = v, True
                        break

                url_prod = ("https://www.cotodigital.com.ar" + coto_id
                            if coto_id.startswith("/") else "")
                gramaje  = extraer_gramaje_aceituna(nombre, "Coto", precio=precio_real)

                productos.append(_construir_producto_ac(
                    "Coto", nombre, precio_real, precio_sin, en_oferta,
                    gramaje, coto_id, url_prod,
                ))
                nuevos += 1

            print(f"  [Coto] Página {pagina} → {nuevos} aceitunas")
            if nuevos == 0:
                break
            time.sleep(1.5)
            pagina += 1

        context.close()
        browser.close()

    return productos


# ---------------------------------------------------------------------------
# La Anónima (Playwright + BeautifulSoup)
# ---------------------------------------------------------------------------

def _parse_numero_ar(s: str) -> float:
    s = s.strip()
    if re.match(r"^\d+\.\d{2}$", s):
        return float(s)
    return float(s.replace(".", "").replace(",", "."))


def _extraer_precio_anonima(texto: str) -> float | None:
    for m in re.findall(r"\$?\s*([\d.,]+)", texto):
        try:
            v = _parse_numero_ar(m)
            if precio_ac_valido(v):
                return v
        except ValueError:
            pass
    return None


def scrape_anonima_aceitunas(headless: bool = False) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [La Anonima] Playwright no instalado. Saltando.")
        return []

    productos: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()

        # Configurar sucursal
        print("  [La Anonima] Configurando sucursal (CP 8400 - Bariloche)...")
        try:
            page.goto("https://www.laanonima.com.ar/", timeout=30000,
                      wait_until="domcontentloaded")
            time.sleep(3)
            cp_input = page.query_selector("input[placeholder='Completa tu código postal']")
            if cp_input:
                cp_input.fill("8400")
                page.keyboard.press("Enter")
                time.sleep(4)
                try:
                    page.wait_for_selector("text=Bariloche", timeout=8000)
                    page.click("text=Bariloche")
                    time.sleep(3)
                    print("  [La Anonima] Sucursal Bariloche seleccionada")
                except Exception:
                    print("  [La Anonima] No apareció modal de sucursales, continuando...")
        except Exception as e:
            print(f"  [La Anonima] Error configurando sucursal: {e}")

        # Buscar aceitunas
        print("  [La Anonima] Buscando aceitunas...")
        try:
            page.goto("https://www.laanonima.com.ar/buscar/aceitunas",
                      timeout=30000, wait_until="domcontentloaded")
            time.sleep(3)
            alt_ant, sin_cambio = 0, 0
            for _ in range(60):
                page.evaluate("window.scrollBy(0, 600)")
                time.sleep(0.4)
                alt_act = page.evaluate("document.body.scrollHeight")
                if alt_act == alt_ant:
                    sin_cambio += 1
                    if sin_cambio >= 4:
                        break
                else:
                    sin_cambio = 0
                alt_ant = alt_act
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1.5)
            html = page.content()
            print(f"  [La Anonima] Página cargada ({html.count('producto-item')} items)")
        except Exception as e:
            print(f"  [La Anonima] Error buscando productos: {e}")
            browser.close()
            return []

        soup    = BeautifulSoup(html, "html.parser")
        items   = soup.select(".producto-item")
        vistos: set[str] = set()

        for item in items:
            nombre = ""
            titulo_tag = item.select_one("h2.titulo")
            if titulo_tag:
                nombre = titulo_tag.get_text(strip=True)
            else:
                a_tag = item.select_one("a[data-nombre]")
                if a_tag:
                    nombre = a_tag.get("data-nombre", "").strip()

            if not nombre or not es_aceituna(nombre):
                continue

            a_link  = item.select_one("a[href]")
            anon_id = a_link.get("href", nombre) if a_link else nombre
            if anon_id in vistos:
                continue
            vistos.add(anon_id)

            url_prod = ("https://www.laanonima.com.ar" + anon_id
                        if anon_id.startswith("/") else "")

            precio_regular = None
            precio_div = item.select_one(".precio")
            if precio_div:
                primer_span = precio_div.select_one("span:not(.detalle-plus)")
                if primer_span:
                    precio_regular = _extraer_precio_anonima(
                        primer_span.get_text(" ", strip=True)
                    )

            precio_plus = None
            plus_tag = item.select_one(".detalle-plus")
            if plus_tag:
                txt = plus_tag.get_text(" ", strip=True)
                m   = re.search(r"pag[áa]s?\s*c/u\s*([\d.,]+)", txt, re.IGNORECASE)
                if m:
                    try:
                        v = _parse_numero_ar(m.group(1))
                        if precio_ac_valido(v):
                            precio_plus = v
                    except ValueError:
                        pass

            precio_anterior = None
            ant_tag = item.select_one(".precio-anterior")
            if ant_tag:
                precio_anterior = _extraer_precio_anonima(ant_tag.get_text(" ", strip=True))

            if precio_plus and precio_regular and precio_ac_valido(precio_plus):
                precio_real = precio_plus
                precio_sin  = (precio_anterior if precio_anterior
                               and precio_anterior > precio_plus * 1.01
                               else precio_regular)
                en_oferta   = True
            elif precio_regular and precio_ac_valido(precio_regular):
                precio_real = precio_regular
                precio_sin  = (precio_anterior if precio_anterior
                               and precio_anterior > precio_regular * 1.01
                               else None)
                en_oferta   = bool(precio_sin)
            else:
                continue

            gramaje = extraer_gramaje_aceituna(nombre, "La Anonima", precio=precio_real)
            productos.append(_construir_producto_ac(
                "La Anonima", nombre, precio_real, precio_sin, en_oferta,
                gramaje, anon_id, url_prod,
            ))

        print(f"  [La Anonima] {len(productos)} aceitunas")
        browser.close()

    return productos


# ---------------------------------------------------------------------------
# Análisis de calidad
# ---------------------------------------------------------------------------

def analizar_calidad_aceitunas(productos: list[dict]) -> list[dict]:
    print("\n[Análisis Aceitunas] Revisando calidad de datos...")

    por_cadena:    dict[str, int] = {}
    por_variedad:  dict[str, int] = {}
    por_confianza: dict[str, int] = {}
    sin_gramaje:   list[dict] = []
    baja_conf:     list[dict] = []

    todos_precios = sorted(p["precio"] for p in productos if p.get("precio"))
    mediana = todos_precios[len(todos_precios) // 2] if todos_precios else 0

    precios_anomalos: list[dict] = []

    for p in productos:
        por_cadena[p.get("supermercado", "?")] = (
            por_cadena.get(p.get("supermercado", "?"), 0) + 1
        )
        por_variedad[p.get("variedad", "?")] = (
            por_variedad.get(p.get("variedad", "?"), 0) + 1
        )
        conf = p.get("gramaje_confianza", "unknown")
        por_confianza[conf] = por_confianza.get(conf, 0) + 1

        if not p.get("gramos_sin_escurrir"):
            sin_gramaje.append(p)
        if conf == "baja":
            baja_conf.append(p)
        if mediana > 0 and (p["precio"] < mediana * 0.1 or p["precio"] > mediana * 5):
            precios_anomalos.append(p)

    lineas = [
        f"=== ANÁLISIS ACEITUNAS — {date.today()} ===",
        f"Total: {len(productos)} productos",
        "",
        "── POR CADENA ──",
    ]
    for c, n in sorted(por_cadena.items()):
        lineas.append(f"  {c}: {n}")

    lineas += ["", "── POR VARIEDAD ──"]
    for v, n in sorted(por_variedad.items(), key=lambda x: -x[1]):
        lineas.append(f"  {v}: {n}")

    lineas += ["", "── CONFIANZA GRAMAJE ──"]
    for c, n in sorted(por_confianza.items()):
        lineas.append(f"  {c}: {n}")

    lineas += [f"", f"── SIN GRAMAJE ({len(sin_gramaje)}) ──"]
    for p in sin_gramaje[:20]:
        lineas.append(f"  [{p['supermercado']}] {p['nombre']}")

    lineas += [f"", f"── CONFIANZA BAJA ({len(baja_conf)}) ──"]
    for p in baja_conf[:20]:
        lineas.append(
            f"  [{p['supermercado']}] {p['nombre']} "
            f"(auto:{p.get('gramos_sin_escurrir')}g) — {p.get('url','')}"
        )

    lineas += [f"", f"── PRECIOS ANÓMALOS ({len(precios_anomalos)}) ──"]
    for p in precios_anomalos:
        lineas.append(f"  [{p['supermercado']}] {p['nombre']} — ${p['precio']:,.0f}")

    modo = "a" if ARCHIVO_ANALISIS_AC.exists() else "w"
    with open(ARCHIVO_ANALISIS_AC, modo, encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n\n")

    pct_ok = (len(productos) - len(sin_gramaje)) / max(len(productos), 1) * 100
    print(
        f"[Análisis] {len(productos)} productos | {pct_ok:.0f}% con gramaje | "
        f"alta:{por_confianza.get('alta', 0)} "
        f"media:{por_confianza.get('media', 0)} "
        f"baja:{por_confianza.get('baja', 0)}"
    )
    return productos


# ---------------------------------------------------------------------------
# Verificación interactiva de gramaje
# ---------------------------------------------------------------------------

def verificar_gramajes_pendientes(productos: list[dict], cur: sqlite3.Cursor) -> int:
    """
    Para cada producto con gramaje incierto sin override existente:
    abre el link en el browser y pregunta al usuario el gramaje correcto.
    Retorna la cantidad de overrides guardados.
    """
    pendientes = [
        p for p in productos
        if p.get("gramaje_confianza") != "alta"
        and not buscar_override(cur, p.get("producto_id"))
    ]

    if not pendientes:
        print("\n[Verificación] Sin pendientes — todos los gramajes son confianza 'alta' "
              "o ya están verificados.")
        return 0

    print(f"\n{'='*65}")
    print(f"  {len(pendientes)} PRODUCTOS CON GRAMAJE NO CONFIRMADO")
    print(f"  Enter = aceptar auto-detectado | número = corregir | s = saltar")
    print(f"{'='*65}")

    guardados = 0
    for i, p in enumerate(pendientes, 1):
        auto = p.get("gramos_sin_escurrir")
        print(f"\n[{i}/{len(pendientes)}] {p['supermercado']}: {p['nombre']}")
        print(f"  Auto  : {auto}g sin escurrir "
              f"(conf: {p.get('gramaje_confianza')}, fuente: {p.get('gramaje_fuente')})")
        if p.get("gramos_escurrido"):
            print(f"  Escurr: {p['gramos_escurrido']}g")
        if p.get("url"):
            print(f"  URL   : {p['url']}")
            webbrowser.open(p["url"])

        try:
            entrada = input("  Gramos sin escurrir [Enter/s]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Verificación interrumpida.")
            break

        if entrada.lower() == "s":
            continue

        gramos = auto
        if entrada:
            try:
                gramos = int(entrada)
            except ValueError:
                print("  Valor inválido, saltando.")
                continue

        if gramos and GRAMOS_MIN_AC <= gramos <= GRAMOS_MAX_AC:
            guardar_override(
                cur,
                p.get("producto_id", p["nombre"]),
                p["supermercado"],
                p["nombre"],
                p.get("url"),
                gramos,
            )
            print(f"  ✓ Guardado: {gramos}g")
            guardados += 1
        elif gramos:
            print(f"  {gramos}g fuera de rango ({GRAMOS_MIN_AC}-{GRAMOS_MAX_AC}g), saltando.")

    return guardados


# ---------------------------------------------------------------------------
# Unificación de gramajes similares
# ---------------------------------------------------------------------------

def _redondez(g: int) -> int:
    """Cuán 'redondo' es un número de gramos. Más alto = más redondo."""
    for divisor, score in [(500, 5), (100, 4), (50, 3), (25, 2), (10, 1)]:
        if g % divisor == 0:
            return score
    return 0


def _mas_redondo(gramos: list[int]) -> int:
    """Del conjunto de gramos retorna el más redondo; en empate, el más frecuente."""
    return max(gramos, key=lambda g: (_redondez(g), gramos.count(g)))


def unificar_gramajes(productos: list[dict]) -> list[dict]:
    """
    Dentro de cada combinación (marca, variedad), unifica gramajes que difieren
    ≤20g al valor más redondo del cluster.
    Respeta los gramajes fijados por catÃ¡logo o verificaciÃ³n manual.
    Si quedan >4 gramajes distintos por grupo, muestra advertencia para revisar.
    Recalcula precio_100g con los gramajes unificados.
    """
    from collections import defaultdict

    # Agrupar valores de gramaje por (marca, variedad)
    grupos: dict[tuple, list[int]] = defaultdict(list)
    fijos: dict[tuple, set[int]] = defaultdict(set)
    for p in productos:
        g = p.get("gramos_sin_escurrir")
        if g:
            clave = (p.get("marca", ""), p.get("variedad", ""))
            grupos[clave].append(g)
            if p.get("gramaje_fuente") in {"manual", "catalogo"}:
                fijos[clave].add(g)

    # Para cada grupo construir mapa {gramaje_original → gramaje_unificado}
    mapas: dict[tuple, dict[int, int]] = {}
    for clave, lista_g in grupos.items():
        valores = sorted(set(lista_g))
        if len(valores) <= 1:
            mapas[clave] = {g: g for g in valores}
            continue

        # Clustering greedy: agrupa valores consecutivos con diferencia ≤20g
        anclas = sorted(fijos.get(clave, set()))
        clusters: list[list[int]] = []
        mapa: dict[int, int] = {}
        libres: list[int] = []
        for g in valores:
            if g in anclas:
                mapa[g] = g
                continue
            candidatos = [a for a in anclas if abs(a - g) <= 20]
            if candidatos:
                rep = min(candidatos, key=lambda a: (abs(a - g), -_redondez(a), a))
                mapa[g] = rep
            else:
                libres.append(g)

        if libres:
            cluster_actual = [libres[0]]
            for g in libres[1:]:
                if g - cluster_actual[-1] <= 20:
                    cluster_actual.append(g)
                else:
                    clusters.append(cluster_actual)
                    cluster_actual = [g]
            clusters.append(cluster_actual)

        for cluster in clusters:
            rep = _mas_redondo(cluster)
            for g in cluster:
                mapa[g] = rep
        mapas[clave] = mapa

        # Advertir si hay demasiados gramajes distintos (posibles errores de extracción)
        gramajes_finales = sorted(set(mapa.values()))
        if len(gramajes_finales) > 4:
            marca, variedad = clave
            print(f"\n  ⚠️  {marca} / {variedad}: {len(gramajes_finales)} gramajes distintos → VERIFICAR")
            for gf in gramajes_finales:
                originales = sorted(set(g for g, r in mapa.items() if r == gf))
                print(f"     {gf}g  (agrupó: {originales})")

    # Aplicar unificación
    result = []
    for p in productos:
        g = p.get("gramos_sin_escurrir")
        if g:
            clave = (p.get("marca", ""), p.get("variedad", ""))
            nuevo_g = mapas.get(clave, {}).get(g, g)
            if nuevo_g != g:
                p = dict(p)
                p["gramos_sin_escurrir"] = nuevo_g
        result.append(p)

    # Recalcular precio_100g y gramaje_grupo con gramaje unificado
    for p in result:
        g = p.get("gramos_sin_escurrir")
        if g:
            p["precio_100g"]          = precio_por_100g(p["precio"], g)
            if p.get("precio_sin_dto"):
                p["precio_sin_dto_100g"] = precio_por_100g(p["precio_sin_dto"], g)
            p["gramaje_grupo"] = gramaje_a_grupo(g)

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    auto_mode = "--auto" in sys.argv or not sys.stdin.isatty()
    headless = _resolver_headless(auto_mode)

    print("=" * 60)
    print("Scraper de ACEITUNAS — Supermercados Argentina")
    print(f"Fecha: {date.today()}")
    if auto_mode:
        print("Modo: automatico (sin verificacion interactiva)")
    print(f"Navegador: {'headless' if headless else 'visible'}")
    print("=" * 60)

    todos: list[dict] = []

    for nombre, base_url in VTEX_SUPERS.items():
        print(f"\n[{nombre}]")
        prods = scrape_vtex_aceitunas(nombre, base_url)
        print(f"  Total {nombre}: {len(prods)} aceitunas")
        todos.extend(prods)

    for nombre, base_url in CENCOSUD_SUPERS.items():
        print(f"\n[{nombre}]")
        prods = scrape_cencosud_aceitunas(nombre, base_url, headless=headless)
        print(f"  Total {nombre}: {len(prods)} aceitunas")
        todos.extend(prods)

    print("\n[Chango Más]")
    prods = scrape_changomas_aceitunas()
    print(f"  Total Chango Más: {len(prods)} aceitunas")
    todos.extend(prods)

    print("\n[Coto]")
    prods = scrape_coto_aceitunas(headless=headless)
    print(f"  Total Coto: {len(prods)} aceitunas")
    todos.extend(prods)

    print("\n[La Anónima]")
    prods = scrape_anonima_aceitunas(headless=headless)
    print(f"  Total La Anónima: {len(prods)} aceitunas")
    todos.extend(prods)

    print(f"\nTotal general: {len(todos)} aceitunas")
    if not todos:
        print("No se encontraron productos. Abortando.")
        return

    todos = analizar_calidad_aceitunas(todos)
    todos = aplicar_catalogo_gramajes(todos)
    todos = unificar_gramajes(todos)

    fecha_hoy = str(date.today())

    # Aplicar overrides de marca y gramaje antes de guardar
    conn_pre = sqlite3.connect(DB_PATH)
    cur_pre  = conn_pre.cursor()
    _init_db_aceitunas(cur_pre)
    todos_con_overrides = []
    for p in todos:
        pid  = p.get("producto_id")
        cad  = p.get("supermercado", "")
        marca_ovr = buscar_marca_override(cur_pre, pid, cad)
        gramaje_ovr = buscar_override(cur_pre, pid)
        cambios: dict = {}
        if marca_ovr:
            cambios["marca"] = marca_ovr
        if gramaje_ovr:
            cambios.update({
                "gramos_sin_escurrir": gramaje_ovr["gramos_sin_escurrir"],
                "gramos_escurrido":    gramaje_ovr["gramos_escurrido"],
                "gramaje_fuente":      "manual",
                "gramaje_confianza":   "alta",
            })
        todos_con_overrides.append({**p, **cambios} if cambios else p)
    conn_pre.close()
    todos = aplicar_catalogo_gramajes(todos_con_overrides)
    todos = unificar_gramajes(todos)

    guardar_en_sqlite_aceitunas(todos, fecha_hoy)
    print(f"\nGuardado: {len(todos)} registros para {fecha_hoy}")

    # Verificación interactiva de gramajes inciertos
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    _init_db_aceitunas(cur)

    if auto_mode:
        guardados = 0
        print("\n[Verificacion] Modo automatico — se omite verificacion de gramajes.")
    else:
        guardados = verificar_gramajes_pendientes(todos, cur)

    if guardados > 0:
        # Re-aplicar overrides y volver a guardar
        todos_final = []
        for p in todos:
            ovr = buscar_override(cur, p.get("producto_id"))
            marca_ovr = buscar_marca_override(cur, p.get("producto_id"), p.get("supermercado", ""))
            cambios2: dict = {}
            if marca_ovr:
                cambios2["marca"] = marca_ovr
            if ovr:
                cambios2.update({
                    "gramos_sin_escurrir": ovr["gramos_sin_escurrir"],
                    "gramos_escurrido":    ovr["gramos_escurrido"],
                    "gramaje_fuente":      "manual",
                    "gramaje_confianza":   "alta",
                })
            todos_final.append({**p, **cambios2} if cambios2 else p)
        todos_final = aplicar_catalogo_gramajes(todos_final)
        todos_final = unificar_gramajes(todos_final)
        guardar_en_sqlite_aceitunas(todos_final, fecha_hoy)
        print(f"{guardados} gramajes verificados y aplicados.")

    conn.commit()
    conn.close()
    print("\n¡Listo! Aceitunas scrapeadas correctamente.")


if __name__ == "__main__":
    main()
