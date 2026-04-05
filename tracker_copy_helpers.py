from __future__ import annotations

import re
import unicodedata


OIL_EXCLUDE = [
    "mayonesa", "hummus", "vinagre", "aderezo", "salsa", "pesto",
    "aceituna", "girasol", "maiz", "maíz", "soja", "canola", "spray",
    "atun", "atún", "papa", "papas",
]

OIL_BRAND_ALIAS = {
    "familia zuccardi": "Familia Zuccardi",
    "filippo berio": "Filippo Berio",
    "ciudad del lago": "Ciudad Del Lago",
    "pietro coricelli": "Pietro Coricelli",
    "cuisine & co": "Cousine & Co",
    "cousine & co": "Cousine & Co",
    "dv catena": "DV Catena",
    "la toscana": "La Toscana",
    "la española": "La Española",
    "la riojana": "La Riojana",
    "del monte": "Del Monte",
    "de cecco": "De Cecco",
    "zuccardi": "Familia Zuccardi",
    "filippo": "Filippo Berio",
    "cuisine": "Cousine & Co",
    "cousine": "Cousine & Co",
    "costaflores": "Costaflores",
    "yancanello": "Yancanello",
    "carbonell": "Carbonell",
    "colavita": "Colavita",
    "fritolim": "Fritolim",
    "rastrilla": "Rastrilla",
    "cocinero": "Cocinero",
    "oliovita": "Oliovita",
    "kirkland": "Kirkland",
    "olitalia": "Olitalia",
    "cañuelas": "Cañuelas",
    "casalta": "Casalta",
    "monini": "Monini",
    "morixe": "Morixe",
    "nucete": "Nucete",
    "cortijo": "Cortijo",
    "castell": "Castell",
    "borges": "Borges",
    "ybarra": "Ybarra",
    "natura": "Natura",
    "cecco": "De Cecco",
    "vigil": "Vigil",
    "zuelo": "Zuelo",
    "laur": "Laur",
    "zucco": "Zucco",
    "lopez": "Lopez",
    "pisi": "Pisi",
    "lira": "Lira",
    "carrefour": "Carrefour",
    "jumbo": "Jumbo",
    "disco": "Disco",
    "vea": "Vea",
    "día": "Día",
    "dia": "Día",
}
OIL_BRAND_ALIAS_SORTED = sorted(OIL_BRAND_ALIAS.items(), key=lambda x: -len(x[0]))
OIL_NO_BRAND = {
    "ml", "cc", "lt", "lts", "ltr", "gr", "grm", "kg", "g", "l",
    "aceite", "oliva", "extra", "virgen", "virgen-extra", "extra-virgen", "extravirgen",
    "organico", "clasico", "clásico", "suave", "intenso", "blend", "picual", "arbequina",
    "botella", "lata", "envase", "pet", "vidrio", "aerosol", "de", "en", "con", "sin",
    "el", "la", "bot", "x", "y", "e", "o", "a", "premium", "seleccion", "selección",
    "natural", "tradicional", "especial", "tacc", "bío", "bio", "puro", "pura",
}

OLIVE_EXCLUDE = [
    "empanada", "pizza", "relleno para",
    "pasta de aceituna", "pasta aceitunas", "pasta de aceitunas",
    "tapenade", "paté de", "pate de", "pasta para untar",
    "aceite de oliva", "aceite oliva",
    "sandwich", "sandwiche", "sándwich",
    "ciabata", "ciabatta",
]

OLIVE_VAR_PATTERNS = [
    (re.compile(r"negra[s]?\s+des?carozada[s]?", re.IGNORECASE), "Negra Descarozada", "alta"),
    (re.compile(r"negra[s]?\s+(?:en\s+)?rodaja[ds]?a?[s]?", re.IGNORECASE), "Negra Rodajada", "alta"),
    (re.compile(r"negra[s]?\s+rellena[s]?", re.IGNORECASE), "Negra Rellena", "alta"),
    (re.compile(r"kalamata", re.IGNORECASE), "Kalamata", "alta"),
    (re.compile(r"negra[s]?", re.IGNORECASE), "Negra", "alta"),
    (re.compile(r"rellena[s]?\s+(?:con\s+)?queso", re.IGNORECASE), "Verde Rellena Queso", "alta"),
    (re.compile(r"rellena[s]?\s+(?:con\s+)?salmon", re.IGNORECASE), "Verde Rellena Salmon", "alta"),
    (re.compile(r"rellena[s]?\s+(?:con\s+)?anchoa[s]?", re.IGNORECASE), "Verde Rellena Anchoas", "alta"),
    (re.compile(r"rellena[s]?\s+(?:con\s+)?morron[es]?", re.IGNORECASE), "Verde Rellena Morron", "alta"),
    (re.compile(r"rellena[s]?", re.IGNORECASE), "Verde Rellena Morron", "media"),
    (re.compile(r"(?:con\s+)?ajo\b", re.IGNORECASE), "Verde con Ajo", "alta"),
    (re.compile(r"picante[s]?", re.IGNORECASE), "Verde Picante", "alta"),
    (re.compile(r"ahumada[s]?", re.IGNORECASE), "Verde Ahumada", "alta"),
    (re.compile(r"(?:en\s+)?rodaja[ds]?a?[s]?", re.IGNORECASE), "Verde Rodajada", "alta"),
    (re.compile(r"des?carozada[s]?", re.IGNORECASE), "Verde Descarozada", "alta"),
    (re.compile(r"saborizada[s]?", re.IGNORECASE), "Verde Saborizada", "alta"),
    (re.compile(r"mix\b|mixta[s]?\b|combinad[ao]|surtid[ao]|variedad", re.IGNORECASE), "Mix", "alta"),
    (re.compile(r"verde[s]?", re.IGNORECASE), "Verde", "alta"),
]

OLIVE_BRAND_ALIAS = {
    "del fuerte": "Del Fuerte",
    "la sevillana": "La Sevillana",
    "cuisine & co": "Cousine & Co",
    "cousine & co": "Cousine & Co",
    "aceitunera": "Aceitunera",
    "qualita": "Qualita",
    "famiglia gullo": "Famiglia Gullo",
    "famiglia": "Famiglia Gullo",
    "goya": "Goya",
    "nucete": "Nucete",
    "castell": "Castell",
    "ybarra": "Ybarra",
    "carrefour": "Carrefour",
    "morixe": "Morixe",
    "oliovita": "Oliovita",
    "great value": "Great Value",
    "la malagueña": "La Malagueña",
    "la malaguena": "La Malagueña",
    "malagueña": "La Malagueña",
    "malaguena": "La Malagueña",
    "la toscana": "La Toscana",
    "marvavic": "Marvavic",
    "vanoli": "Vanoli",
    "olymp": "Olymp",
    "meridiano": "Meridiano",
}
OLIVE_BRAND_ALIAS_SORTED = sorted(OLIVE_BRAND_ALIAS.items(), key=lambda x: -len(x[0]))
OLIVE_NO_BRAND = {
    "ml", "cc", "lt", "lts", "gr", "grm", "grms", "kg", "g", "l",
    "aceituna", "aceitunas", "verde", "verdes", "negra", "negras",
    "rellena", "rellenas", "descarozada", "descarozadas", "rodajada",
    "rodajas", "rodaja", "kalamata", "mix", "mixta", "surtido",
    "de", "en", "con", "sin", "el", "la", "los", "las", "un", "una", "por",
    "x", "y", "e", "o", "u", "a", "al", "frasco", "lata", "envase",
    "tarro", "pouch", "doypack", "sachet", "pou", "sabor", "saborizada",
    "saborizadas", "picante", "ahumada", "ahumado", "clasica", "clásica",
    "premium", "extra", "light", "xl", "classic", "morron", "morrón",
    "morrones", "ajo", "limon", "limón",
}
OLIVE_BRAND_CORRECTIONS = {
    "Toscana": "La Toscana",
    "Trozos": "Marvavic",
    "Gordal": "Ybarra",
    "Premium": "Castell",
    "La Malaguena": "La Malagueña",
    "Malagueña": "La Malagueña",
    "Malaguena": "La Malagueña",
}
OLIVE_NON_BRAND_WORDS = {
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

PAT_SIN_ESCURRIR = re.compile(
    r"(?:peso\s+(?:sin\s+esc[u]?rrir|neto)|contenido\s+neto|neto|s\.?\s*e\.?)\s*[:\-]?\s*(\d{2,4})\s*(?:gr?|grs?|grm[s]?|g(?=\b))",
    re.IGNORECASE,
)
PAT_ESCURRIDO = re.compile(
    r"(?:peso\s+esc[u]?rrido|contenido\s+esc[u]?rrido|esc[u]?rrido|p\.?\s*e\.?)\s*[:\-]?\s*(\d{2,4})\s*(?:gr?|grs?|grm[s]?|g(?=\b))",
    re.IGNORECASE,
)
PAT_PESO_SOLO = re.compile(r"\b(\d{2,4})\s*(?:gr?s?|grm[s]?|g(?=\b))", re.IGNORECASE)
PAT_X_GRAMAJE = re.compile(
    r"\bx\s*(\d{2,4})(?=\s*(?:gr?s?|grm[s]?|g\b|doy\s*pack\b|doypack\b|dp\b|sachet\b|fras(?:co)?\b|fco\b|pote\b|tarro\b|lata\b|bolsa\b|$))",
    re.IGNORECASE,
)
PAT_ENVASE_GRAMAJE = re.compile(
    r"(?:fras(?:co)?|fco|pote|tarro|doy\s*pack|doypack|dp|sachet|pouch|bolsa|lata)\s*x?\s*(\d{2,4})\b",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


OLIVE_BRAND_CORRECTIONS_NORM = {normalize_text(k): v for k, v in OLIVE_BRAND_CORRECTIONS.items()}
OLIVE_NON_BRAND_WORDS_NORM = {normalize_text(p) for p in OLIVE_NON_BRAND_WORDS}


def is_olive_oil_product(name: str) -> bool:
    n = (name or "").lower()
    if "oliva" not in n or "aceite" not in n:
        return False
    if any(p in n for p in OIL_EXCLUDE):
        return False
    return True


def oil_brand(name: str) -> str:
    n = (name or "").lower()
    for alias, canonical in OIL_BRAND_ALIAS_SORTED:
        if alias in n:
            return canonical
    for word in (name or "").split():
        p = word.lower().strip(".,()-/&°")
        if len(p) >= 3 and p not in OIL_NO_BRAND and not re.search(r"\d", p):
            return word.strip(".,()-/&°")
    return "Otra"


def _search_ml(text: str) -> int | None:
    t = (text or "").lower()
    m = re.search(r"(?:grm[s]?|gr[s]?|gramo[s]?)\s*[.\-]+\s*(\d+)", t)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+[\.,]?\d*)\s*(grm[s]?|gramo[s]?|gr[s]?|g(?=\b)|cmq|ml|cc)\b", t)
    if m:
        return int(float(m.group(1).replace(",", ".")))
    m = re.search(r"(\d+[\.,]?\d*)\s*(kg[s]?|kilogramo[s]?|litro[s]?|ltr[s]?|lt[s]?|l(?![a-z]))\b", t)
    if m:
        return int(float(m.group(1).replace(",", ".")) * 1000)
    m = re.search(r"\bx\s*(\d+)\b(?!\s*(?:ml|cc|gr?|l\b|lt|litro|unid|pack|u\b))", t)
    if m:
        n = int(m.group(1))
        if n == 50:
            return 500
        if 100 <= n <= 5000:
            return n
    return None


def oil_ml(name: str) -> int | None:
    return _search_ml(name)


def price_per_liter(price: float, ml: int | None) -> int | None:
    if ml and ml > 0:
        return round(price / ml * 1000)
    return None


def is_olive_product(name: str) -> bool:
    n = normalize_text(name)
    m_olive = re.search(r"aceitun[ao]", n)
    if not m_olive:
        return False
    m_cheese = re.search(r"\bqueso\b", n)
    if m_cheese and m_cheese.start() < m_olive.start():
        return False
    if re.match(r"pasta\b", n):
        return False
    if any(normalize_text(excl) in n for excl in OLIVE_EXCLUDE):
        return False
    return True


def olive_variety(name: str) -> tuple[str, str]:
    for pat, variety, confidence in OLIVE_VAR_PATTERNS:
        if pat.search(normalize_text(name)):
            return variety, confidence
    return "Verde", "baja"


def _valid_grams(value: int | None) -> bool:
    return value is not None and 50 <= value <= 3000


def _labeled_grams(text: str) -> tuple[int | None, int | None]:
    t = normalize_text(text)
    s = PAT_SIN_ESCURRIR.search(t)
    e = PAT_ESCURRIDO.search(t)
    g_s = int(s.group(1)) if s else None
    g_e = int(e.group(1)) if e else None
    return (g_s if _valid_grams(g_s) else None, g_e if _valid_grams(g_e) else None)


def _grams_from_context(text: str) -> int | None:
    t = normalize_text(text)
    for pat in (PAT_X_GRAMAJE, PAT_ENVASE_GRAMAJE, PAT_PESO_SOLO):
        m = pat.search(t)
        if not m:
            continue
        value = int(m.group(1))
        if _valid_grams(value):
            return value
    return None


def olive_grams(name: str, supermarket: str, price: float = 0.0) -> dict:
    sin_esc, esc = _labeled_grams(name)
    source, confidence = "unknown", "baja"
    if sin_esc is not None or esc is not None:
        source, confidence = "nombre", "alta"
    if sin_esc is None and esc is None:
        candidate = _grams_from_context(name)
        if candidate is not None:
            if supermarket == "Chango Mas":
                esc = candidate
            else:
                sin_esc = candidate
            source, confidence = "nombre", "media"
    if sin_esc is None and esc is not None and _valid_grams(esc):
        derived = round(esc / 0.65)
        if _valid_grams(derived):
            sin_esc = derived
            if confidence == "alta":
                confidence = "media"
    if not _valid_grams(sin_esc):
        sin_esc = None
    if not _valid_grams(esc):
        esc = None
    if sin_esc is None and esc is None:
        source, confidence = "unknown", "baja"
    return {
        "gramos_sin_escurrir": sin_esc,
        "gramos_escurrido": esc,
        "fuente": source,
        "confianza": confidence,
    }


def olive_brand(name: str) -> str:
    n = normalize_text(name)
    for alias, canonical in OLIVE_BRAND_ALIAS_SORTED:
        if normalize_text(alias) in n:
            return canonical
    for word in (name or "").split():
        p = word.lower().strip(".,()-/&")
        if len(p) > 2 and p not in OLIVE_NO_BRAND and not re.search(r"\d", p):
            return word.strip(".,()-/&").capitalize()
    return "Otra"


def clean_olive_brand(brand: str, chain: str, name: str = "") -> str:
    brand = (brand or "").strip()
    brand_norm = normalize_text(brand)
    if not brand:
        inferred = olive_brand(name) if name else ""
        inferred_norm = normalize_text(inferred)
        return OLIVE_BRAND_CORRECTIONS_NORM.get(inferred_norm, inferred) if inferred and inferred_norm not in OLIVE_NON_BRAND_WORDS_NORM else "Otra"
    if brand_norm in OLIVE_BRAND_CORRECTIONS_NORM:
        return OLIVE_BRAND_CORRECTIONS_NORM[brand_norm]
    if brand_norm in OLIVE_NON_BRAND_WORDS_NORM:
        inferred = olive_brand(name) if name else ""
        inferred_norm = normalize_text(inferred)
        if inferred and inferred_norm not in OLIVE_NON_BRAND_WORDS_NORM and inferred_norm != brand_norm:
            return OLIVE_BRAND_CORRECTIONS_NORM.get(inferred_norm, inferred)
        return chain
    return OLIVE_BRAND_CORRECTIONS_NORM.get(brand_norm, brand)


def price_per_100g(price: float, grams: int | None) -> int | None:
    if grams and grams > 0:
        return round(price / grams * 100)
    return None


def olive_bucket(grams) -> str | None:
    if not grams:
        return None
    if grams <= 140:
        return "1) hasta 140g"
    if grams <= 230:
        return "2) 141-230g"
    if grams <= 330:
        return "3) 231-330g"
    if grams <= 400:
        return "4) 331-400g"
    if grams <= 600:
        return "5) 401-600g"
    return "6) 601g+"
