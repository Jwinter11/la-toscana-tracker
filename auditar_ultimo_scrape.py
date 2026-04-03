from __future__ import annotations

import argparse
import contextlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import pandas as pd

import scraper
import scraper_aceitunas
from tracker_copy_helpers import (
    clean_olive_brand,
    is_olive_oil_product,
    is_olive_product,
    normalize_text,
    oil_brand,
    oil_ml,
    olive_brand,
    olive_grams,
)
from tracker_paths import precios_db_path


ROOT = Path(__file__).parent
DEFAULT_OUTPUT = ROOT / "auditoria_ultimo_scrape.xlsx"


def _split_csv(raw: str) -> list[str]:
    return [part.strip() for part in (raw or "").split(",") if part.strip()]


def _ensure_stdio() -> None:
    if getattr(sys.stdout, "closed", False):
        sys.stdout = sys.__stdout__
    if getattr(sys.stderr, "closed", False):
        sys.stderr = sys.__stderr__


def _console(text: str) -> None:
    os.write(1, f"{text}\n".encode("utf-8", errors="replace"))


def _canon_chain(chain: str) -> str:
    normalized = normalize_text(chain)
    mapping = {
        "carrefour": "Carrefour",
        "dia": "Dia",
        "jumbo": "Jumbo",
        "disco": "Disco",
        "vea": "Vea",
        "chango mas": "Chango Mas",
        "coto": "Coto",
        "la anonima": "La Anonima",
    }
    return mapping.get(normalized, chain.strip())


def _canon_brand(brand: str) -> str:
    return " ".join((brand or "").strip().split())


def _canon_product_id(raw: str | None) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        return parsed.path.rstrip("/") or parsed.path
    return value.rstrip("/")


def _fallback_key(name: str, size_value: int | None) -> str:
    name_key = normalize_text(name)
    size_key = str(size_value or "")
    return f"{name_key}::{size_key}"


def _oil_snapshot_from_db(conn: sqlite3.Connection, fecha: str) -> pd.DataFrame:
    rows = conn.execute(
        """
        SELECT fecha, supermercado, nombre, marca, ml, precio, precio_sin_dto, en_oferta, producto_id
        FROM precios
        WHERE fecha = ?
        """,
        (fecha,),
    ).fetchall()
    data = []
    for fecha_row, chain, name, brand, ml, precio, precio_sin, en_oferta, product_id in rows:
        if not is_olive_oil_product(name):
            continue
        brand_norm = _canon_brand(brand if brand and brand not in ("", "Otra") else oil_brand(name))
        ml_norm = ml or oil_ml(name)
        product_key = _canon_product_id(product_id) or _fallback_key(name, ml_norm)
        data.append(
            {
                "categoria": "aceite",
                "fecha": fecha_row,
                "cadena": _canon_chain(chain),
                "marca": brand_norm,
                "producto": name,
                "tamano": ml_norm,
                "precio": float(precio or 0),
                "precio_base": float(precio_sin or precio or 0),
                "en_oferta": bool(en_oferta),
                "producto_id": product_key,
                "match_key": f"{_canon_chain(chain)}::{product_key}",
            }
        )
    return pd.DataFrame(data)


def _olive_snapshot_from_db(conn: sqlite3.Connection, fecha: str) -> pd.DataFrame:
    rows = conn.execute(
        """
        SELECT fecha, supermercado, nombre, marca, gramos_sin_escurrir, precio, precio_sin_dto, en_oferta, producto_id, url
        FROM aceitunas
        WHERE fecha = ?
        """,
        (fecha,),
    ).fetchall()
    data = []
    for fecha_row, chain, name, brand, grams, precio, precio_sin, en_oferta, product_id, url in rows:
        if not is_olive_product(name):
            continue
        brand_norm = _canon_brand(clean_olive_brand(brand if brand else olive_brand(name), chain))
        grams_norm = grams or olive_grams(name, chain, precio).get("gramos_sin_escurrir")
        product_key = _canon_product_id(url or product_id) or _fallback_key(name, grams_norm)
        data.append(
            {
                "categoria": "aceitunas",
                "fecha": fecha_row,
                "cadena": _canon_chain(chain),
                "marca": brand_norm,
                "producto": name,
                "tamano": grams_norm,
                "precio": float(precio or 0),
                "precio_base": float(precio_sin or precio or 0),
                "en_oferta": bool(en_oferta),
                "producto_id": product_key,
                "match_key": f"{_canon_chain(chain)}::{product_key}",
            }
        )
    return pd.DataFrame(data)


def _latest_date(conn: sqlite3.Connection, table: str) -> str | None:
    row = conn.execute(f"SELECT MAX(fecha) FROM {table}").fetchone()
    return row[0] if row and row[0] else None


def _filter_frame(df: pd.DataFrame, brands: list[str], chains: list[str]) -> pd.DataFrame:
    out = df.copy()
    if brands:
        brand_set = {_canon_brand(x) for x in brands}
        out = out[out["marca"].isin(brand_set)]
    if chains:
        chain_set = {_canon_chain(x) for x in chains}
        out = out[out["cadena"].isin(chain_set)]
    return out.reset_index(drop=True)


def _filter_compare_frame(df: pd.DataFrame, brands: list[str]) -> pd.DataFrame:
    if df.empty or not brands:
        return df.copy()
    brand_set = {_canon_brand(x) for x in brands}
    brand_cols = [col for col in df.columns if col == "marca" or col.startswith("marca_")]
    if not brand_cols:
        return df.copy()
    mask = pd.Series(False, index=df.index)
    for col in brand_cols:
        mask = mask | df[col].fillna("").isin(brand_set)
    return df[mask].copy().reset_index(drop=True)


def _aggregate(df: pd.DataFrame, side: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "match_key",
                f"cadena_{side}",
                f"marca_{side}",
                f"producto_{side}",
                f"tamano_{side}",
                f"precio_{side}",
                f"precio_base_{side}",
                f"en_oferta_{side}",
                f"producto_id_{side}",
            ]
        )
    grouped = (
        df.sort_values(["cadena", "marca", "producto"])
        .groupby("match_key", as_index=False)
        .agg(
            cadena=("cadena", "first"),
            marca=("marca", "first"),
            producto=("producto", "first"),
            tamano=("tamano", "first"),
            precio=("precio", "min"),
            precio_base=("precio_base", "max"),
            en_oferta=("en_oferta", "max"),
            producto_id=("producto_id", "first"),
        )
    )
    return grouped.rename(columns={col: f"{col}_{side}" for col in grouped.columns if col != "match_key"})


def _build_compare(db_df: pd.DataFrame, live_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    db_agg = _aggregate(db_df, "db")
    live_agg = _aggregate(live_df, "live")
    merged = db_agg.merge(live_agg, on="match_key", how="outer", indicator=True)

    missing_in_db = merged[merged["_merge"] == "right_only"].copy()
    missing_in_live = merged[merged["_merge"] == "left_only"].copy()

    overlap = merged[merged["_merge"] == "both"].copy()
    if not overlap.empty:
        overlap["delta_precio"] = overlap["precio_live"] - overlap["precio_db"]
        overlap["delta_precio_pct"] = overlap.apply(
            lambda r: ((r["precio_live"] - r["precio_db"]) / r["precio_db"] * 100) if r["precio_db"] else 0,
            axis=1,
        )
        overlap["oferta_distinta"] = overlap["en_oferta_db"] != overlap["en_oferta_live"]
        price_diff = overlap[
            (overlap["delta_precio"].abs() >= 1) | overlap["oferta_distinta"]
        ].copy()
    else:
        price_diff = pd.DataFrame()

    return missing_in_db, missing_in_live, price_diff


def _run_scraper(name: str, fn: Callable[[], list[dict]], errors: list[dict]) -> list[dict]:
    try:
        with open(os.devnull, "w", encoding="utf-8") as sink:
            with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                items = fn() or []
        _console(f"[audit] {name}: {len(items)} productos")
        return items
    except Exception as exc:  # pragma: no cover - defensive
        errors.append({"fuente": name, "error": str(exc)})
        _console(f"[audit] {name}: ERROR {exc}")
        return []


def _run_scraper_subprocess(
    name: str,
    module_name: str,
    function_name: str,
    kwargs: dict,
    errors: list[dict],
) -> list[dict]:
    runner_code = "\n".join(
        [
            "import contextlib",
            "import importlib",
            "import json",
            "import os",
            "import sys",
            "payload = json.loads(sys.argv[1])",
            "module = importlib.import_module(payload['module'])",
            "fn = getattr(module, payload['function'])",
            "with open(os.devnull, 'w', encoding='utf-8') as sink:",
            "    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):",
            "        items = fn(**payload['kwargs']) or []",
            "sys.stdout.write(json.dumps(items, ensure_ascii=False))",
        ]
    )
    payload = json.dumps(
        {
            "module": module_name,
            "function": function_name,
            "kwargs": kwargs,
        },
        ensure_ascii=False,
    )
    try:
        completed = subprocess.run(
            [sys.executable, "-c", runner_code, payload],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive
        errors.append({"fuente": name, "error": str(exc)})
        _console(f"[audit] {name}: ERROR {exc}")
        return []

    if completed.returncode != 0:
        error_text = (completed.stderr or completed.stdout or "").strip() or f"subprocess rc={completed.returncode}"
        errors.append({"fuente": name, "error": error_text})
        _console(f"[audit] {name}: ERROR {error_text}")
        return []

    raw = (completed.stdout or "").strip()
    if not raw:
        items: list[dict] = []
    else:
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append({"fuente": name, "error": f"JSON decode error: {exc}"})
            _console(f"[audit] {name}: ERROR JSON decode error: {exc}")
            return []

    _console(f"[audit] {name}: {len(items)} productos")
    return items


def _oil_live_snapshot(headless: bool, allowed_chains: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict] = []
    errors: list[dict] = []
    chain_filter = {_canon_chain(x) for x in allowed_chains} if allowed_chains else None

    for chain, base_url in scraper.VTEX_SUPERS.items():
        if chain_filter and _canon_chain(chain) not in chain_filter:
            continue
        for item in _run_scraper(chain, lambda c=chain, u=base_url: scraper.scrape_vtex(c, u), errors):
            name = item.get("nombre", "")
            if not is_olive_oil_product(name):
                continue
            brand_norm = _canon_brand(item.get("marca") or oil_brand(name))
            ml_norm = item.get("ml") or oil_ml(name)
            product_key = _canon_product_id(item.get("producto_id")) or _fallback_key(name, ml_norm)
            chain_norm = _canon_chain(item.get("supermercado", chain))
            rows.append(
                {
                    "categoria": "aceite",
                    "cadena": chain_norm,
                    "marca": brand_norm,
                    "producto": name,
                    "tamano": ml_norm,
                    "precio": float(item.get("precio") or 0),
                    "precio_base": float(item.get("precio_sin_dto") or item.get("precio") or 0),
                    "en_oferta": bool(item.get("en_oferta")),
                    "producto_id": product_key,
                    "match_key": f"{chain_norm}::{product_key}",
                }
            )

    for chain, base_url in scraper.CENCOSUD_SUPERS.items():
        if chain_filter and _canon_chain(chain) not in chain_filter:
            continue
        for item in _run_scraper(
            chain,
            lambda c=chain, u=base_url: scraper.scrape_cencosud_playwright(c, u, headless=headless),
            errors,
        ):
            name = item.get("nombre", "")
            if not is_olive_oil_product(name):
                continue
            brand_norm = _canon_brand(item.get("marca") or oil_brand(name))
            ml_norm = item.get("ml") or oil_ml(name)
            product_key = _canon_product_id(item.get("producto_id")) or _fallback_key(name, ml_norm)
            chain_norm = _canon_chain(item.get("supermercado", chain))
            rows.append(
                {
                    "categoria": "aceite",
                    "cadena": chain_norm,
                    "marca": brand_norm,
                    "producto": name,
                    "tamano": ml_norm,
                    "precio": float(item.get("precio") or 0),
                    "precio_base": float(item.get("precio_sin_dto") or item.get("precio") or 0),
                    "en_oferta": bool(item.get("en_oferta")),
                    "producto_id": product_key,
                    "match_key": f"{chain_norm}::{product_key}",
                }
            )

    extra_oil_sources: list[tuple[str, Callable[[], list[dict]]]] = [
        ("Chango Mas", scraper.scrape_changomas),
        ("Coto", lambda: scraper.scrape_coto(headless=headless)),
        ("La Anonima", lambda: scraper.scrape_anonima(headless=headless)),
    ]
    for chain, fn in extra_oil_sources:
        if chain_filter and _canon_chain(chain) not in chain_filter:
            continue
        if chain == "La Anonima":
            items = _run_scraper_subprocess(chain, "scraper", "scrape_anonima", {"headless": headless}, errors)
        else:
            items = _run_scraper(chain, fn, errors)
        for item in items:
            name = item.get("nombre", "")
            if not is_olive_oil_product(name):
                continue
            brand_norm = _canon_brand(item.get("marca") or oil_brand(name))
            ml_norm = item.get("ml") or oil_ml(name)
            product_key = _canon_product_id(item.get("producto_id")) or _fallback_key(name, ml_norm)
            chain_norm = _canon_chain(item.get("supermercado", chain))
            rows.append(
                {
                    "categoria": "aceite",
                    "cadena": chain_norm,
                    "marca": brand_norm,
                    "producto": name,
                    "tamano": ml_norm,
                    "precio": float(item.get("precio") or 0),
                    "precio_base": float(item.get("precio_sin_dto") or item.get("precio") or 0),
                    "en_oferta": bool(item.get("en_oferta")),
                    "producto_id": product_key,
                    "match_key": f"{chain_norm}::{product_key}",
                }
            )

    return pd.DataFrame(rows), pd.DataFrame(errors)


def _olive_live_snapshot(headless: bool, allowed_chains: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict] = []
    errors: list[dict] = []
    chain_filter = {_canon_chain(x) for x in allowed_chains} if allowed_chains else None

    for chain, base_url in scraper_aceitunas.VTEX_SUPERS.items():
        if chain_filter and _canon_chain(chain) not in chain_filter:
            continue
        for item in _run_scraper(chain, lambda c=chain, u=base_url: scraper_aceitunas.scrape_vtex_aceitunas(c, u), errors):
            name = item.get("nombre", "")
            if not is_olive_product(name):
                continue
            brand_norm = _canon_brand(clean_olive_brand(item.get("marca") or olive_brand(name), chain))
            grams_norm = item.get("gramos_sin_escurrir") or olive_grams(name, chain, item.get("precio") or 0).get("gramos_sin_escurrir")
            product_key = _canon_product_id(item.get("url") or item.get("producto_id")) or _fallback_key(name, grams_norm)
            chain_norm = _canon_chain(item.get("supermercado", chain))
            rows.append(
                {
                    "categoria": "aceitunas",
                    "cadena": chain_norm,
                    "marca": brand_norm,
                    "producto": name,
                    "tamano": grams_norm,
                    "precio": float(item.get("precio") or 0),
                    "precio_base": float(item.get("precio_sin_dto") or item.get("precio") or 0),
                    "en_oferta": bool(item.get("en_oferta")),
                    "producto_id": product_key,
                    "match_key": f"{chain_norm}::{product_key}",
                }
            )

    for chain, base_url in scraper_aceitunas.CENCOSUD_SUPERS.items():
        if chain_filter and _canon_chain(chain) not in chain_filter:
            continue
        for item in _run_scraper(
            chain,
            lambda c=chain, u=base_url: scraper_aceitunas.scrape_cencosud_aceitunas(c, u, headless=headless),
            errors,
        ):
            name = item.get("nombre", "")
            if not is_olive_product(name):
                continue
            brand_norm = _canon_brand(clean_olive_brand(item.get("marca") or olive_brand(name), chain))
            grams_norm = item.get("gramos_sin_escurrir") or olive_grams(name, chain, item.get("precio") or 0).get("gramos_sin_escurrir")
            product_key = _canon_product_id(item.get("url") or item.get("producto_id")) or _fallback_key(name, grams_norm)
            chain_norm = _canon_chain(item.get("supermercado", chain))
            rows.append(
                {
                    "categoria": "aceitunas",
                    "cadena": chain_norm,
                    "marca": brand_norm,
                    "producto": name,
                    "tamano": grams_norm,
                    "precio": float(item.get("precio") or 0),
                    "precio_base": float(item.get("precio_sin_dto") or item.get("precio") or 0),
                    "en_oferta": bool(item.get("en_oferta")),
                    "producto_id": product_key,
                    "match_key": f"{chain_norm}::{product_key}",
                }
            )

    extra_olive_sources: list[tuple[str, Callable[[], list[dict]]]] = [
        ("Chango Mas", scraper_aceitunas.scrape_changomas_aceitunas),
        ("Coto", lambda: scraper_aceitunas.scrape_coto_aceitunas(headless=headless)),
        ("La Anonima", lambda: scraper_aceitunas.scrape_anonima_aceitunas(headless=headless)),
    ]
    for chain, fn in extra_olive_sources:
        if chain_filter and _canon_chain(chain) not in chain_filter:
            continue
        if chain == "La Anonima":
            items = _run_scraper_subprocess(
                chain,
                "scraper_aceitunas",
                "scrape_anonima_aceitunas",
                {"headless": headless},
                errors,
            )
        else:
            items = _run_scraper(chain, fn, errors)
        for item in items:
            name = item.get("nombre", "")
            if not is_olive_product(name):
                continue
            brand_norm = _canon_brand(clean_olive_brand(item.get("marca") or olive_brand(name), chain))
            grams_norm = item.get("gramos_sin_escurrir") or olive_grams(name, chain, item.get("precio") or 0).get("gramos_sin_escurrir")
            product_key = _canon_product_id(item.get("url") or item.get("producto_id")) or _fallback_key(name, grams_norm)
            chain_norm = _canon_chain(item.get("supermercado", chain))
            rows.append(
                {
                    "categoria": "aceitunas",
                    "cadena": chain_norm,
                    "marca": brand_norm,
                    "producto": name,
                    "tamano": grams_norm,
                    "precio": float(item.get("precio") or 0),
                    "precio_base": float(item.get("precio_sin_dto") or item.get("precio") or 0),
                    "en_oferta": bool(item.get("en_oferta")),
                    "producto_id": product_key,
                    "match_key": f"{chain_norm}::{product_key}",
                }
            )

    return pd.DataFrame(rows), pd.DataFrame(errors)


def _summary_rows(
    categoria: str,
    fecha_db: str,
    db_df: pd.DataFrame,
    live_df: pd.DataFrame,
    missing_in_db: pd.DataFrame,
    missing_in_live: pd.DataFrame,
    price_diff: pd.DataFrame,
    errors: pd.DataFrame,
) -> list[dict]:
    return [
        {
            "categoria": categoria,
            "fecha_db": fecha_db,
            "filas_db": len(db_df),
            "filas_live": len(live_df),
            "marcas": db_df["marca"].nunique() if not db_df.empty else 0,
            "cadenas": db_df["cadena"].nunique() if not db_df.empty else 0,
            "faltan_en_db": len(missing_in_db),
            "faltan_en_live": len(missing_in_live),
            "diferencias_precio_oferta": len(price_diff),
            "errores_fuente": len(errors),
        }
    ]


def _write_sheet(writer: pd.ExcelWriter, name: str, df: pd.DataFrame) -> None:
    safe_name = name[:31]
    if df.empty:
        pd.DataFrame([{"sin_datos": "sin filas"}]).to_excel(writer, index=False, sheet_name=safe_name)
    else:
        df.to_excel(writer, index=False, sheet_name=safe_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audita la ultima foto scrapeada contra una reconsulta en vivo.")
    parser.add_argument("--categoria", choices=["aceite", "aceitunas", "ambas"], default="ambas")
    parser.add_argument("--brands", default="", help="Marcas separadas por coma. Si se omite, audita todas.")
    parser.add_argument("--chains", default="", help="Cadenas separadas por coma para acotar la auditoria.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Ruta del Excel de salida.")
    parser.add_argument("--focus-brands", default="", help="Marcas clave separadas por coma para exportar un segundo Excel filtrado.")
    parser.add_argument("--focus-output", default="", help="Ruta opcional para el Excel filtrado de marcas clave.")
    parser.add_argument("--headless", action="store_true", help="Usa navegador headless para las reconsultas Playwright.")
    args = parser.parse_args()

    brands = _split_csv(args.brands)
    chains = _split_csv(args.chains)
    focus_brands = _split_csv(args.focus_brands)
    output_path = Path(args.output).expanduser()
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    focus_output_path = None
    if args.focus_output:
        focus_output_path = Path(args.focus_output).expanduser()
        if not focus_output_path.is_absolute():
            focus_output_path = ROOT / focus_output_path

    conn = sqlite3.connect(precios_db_path())
    resumen_rows: list[dict] = []
    sheets: dict[str, pd.DataFrame] = {}
    focus_summary_rows: list[dict] = []
    focus_sheets: dict[str, pd.DataFrame] = {}

    if args.categoria in ("aceite", "ambas"):
        fecha = _latest_date(conn, "precios")
        if fecha:
            db_df = _filter_frame(_oil_snapshot_from_db(conn, fecha), brands, chains)
            live_df, errors_df = _oil_live_snapshot(headless=args.headless, allowed_chains=chains)
            live_df = _filter_frame(live_df, brands, chains)
            missing_in_db, missing_in_live, price_diff = _build_compare(db_df, live_df)
            resumen_rows.extend(_summary_rows("aceite", fecha, db_df, live_df, missing_in_db, missing_in_live, price_diff, errors_df))
            sheets["aceite_resumen"] = pd.DataFrame(resumen_rows[-1:])
            sheets["aceite_db"] = db_df
            sheets["aceite_live"] = live_df
            sheets["aceite_faltan_db"] = missing_in_db
            sheets["aceite_faltan_live"] = missing_in_live
            sheets["aceite_diff"] = price_diff
            sheets["aceite_errors"] = errors_df
            if focus_brands:
                db_focus = _filter_frame(db_df, focus_brands, [])
                live_focus = _filter_frame(live_df, focus_brands, [])
                miss_db_focus = _filter_compare_frame(missing_in_db, focus_brands)
                miss_live_focus = _filter_compare_frame(missing_in_live, focus_brands)
                diff_focus = _filter_compare_frame(price_diff, focus_brands)
                focus_summary_rows.extend(
                    _summary_rows("aceite", fecha, db_focus, live_focus, miss_db_focus, miss_live_focus, diff_focus, errors_df)
                )
                focus_sheets["aceite_resumen"] = pd.DataFrame(focus_summary_rows[-1:])
                focus_sheets["aceite_db"] = db_focus
                focus_sheets["aceite_live"] = live_focus
                focus_sheets["aceite_faltan_db"] = miss_db_focus
                focus_sheets["aceite_faltan_live"] = miss_live_focus
                focus_sheets["aceite_diff"] = diff_focus
                focus_sheets["aceite_errors"] = errors_df

    if args.categoria in ("aceitunas", "ambas"):
        fecha = _latest_date(conn, "aceitunas")
        if fecha:
            db_df = _filter_frame(_olive_snapshot_from_db(conn, fecha), brands, chains)
            live_df, errors_df = _olive_live_snapshot(headless=args.headless, allowed_chains=chains)
            live_df = _filter_frame(live_df, brands, chains)
            missing_in_db, missing_in_live, price_diff = _build_compare(db_df, live_df)
            resumen_rows.extend(_summary_rows("aceitunas", fecha, db_df, live_df, missing_in_db, missing_in_live, price_diff, errors_df))
            sheets["aceitunas_resumen"] = pd.DataFrame(resumen_rows[-1:])
            sheets["aceitunas_db"] = db_df
            sheets["aceitunas_live"] = live_df
            sheets["aceitunas_faltan_db"] = missing_in_db
            sheets["aceitunas_faltan_live"] = missing_in_live
            sheets["aceitunas_diff"] = price_diff
            sheets["aceitunas_errors"] = errors_df
            if focus_brands:
                db_focus = _filter_frame(db_df, focus_brands, [])
                live_focus = _filter_frame(live_df, focus_brands, [])
                miss_db_focus = _filter_compare_frame(missing_in_db, focus_brands)
                miss_live_focus = _filter_compare_frame(missing_in_live, focus_brands)
                diff_focus = _filter_compare_frame(price_diff, focus_brands)
                focus_summary_rows.extend(
                    _summary_rows("aceitunas", fecha, db_focus, live_focus, miss_db_focus, miss_live_focus, diff_focus, errors_df)
                )
                focus_sheets["aceitunas_resumen"] = pd.DataFrame(focus_summary_rows[-1:])
                focus_sheets["aceitunas_db"] = db_focus
                focus_sheets["aceitunas_live"] = live_focus
                focus_sheets["aceitunas_faltan_db"] = miss_db_focus
                focus_sheets["aceitunas_faltan_live"] = miss_live_focus
                focus_sheets["aceitunas_diff"] = diff_focus
                focus_sheets["aceitunas_errors"] = errors_df

    conn.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        _write_sheet(writer, "resumen", pd.DataFrame(resumen_rows))
        for sheet_name, frame in sheets.items():
            _write_sheet(writer, sheet_name, frame)

    if focus_output_path and focus_summary_rows:
        focus_output_path.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(focus_output_path, engine="openpyxl") as writer:
            _write_sheet(writer, "resumen", pd.DataFrame(focus_summary_rows))
            for sheet_name, frame in focus_sheets.items():
                _write_sheet(writer, sheet_name, frame)

    _console(f"Auditoria guardada en: {output_path}")
    if resumen_rows:
        _console(pd.DataFrame(resumen_rows).to_string(index=False))
    if focus_output_path and focus_summary_rows:
        _console(f"Auditoria marcas clave guardada en: {focus_output_path}")
        _console(pd.DataFrame(focus_summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()
