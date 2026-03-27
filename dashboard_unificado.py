#!/usr/bin/env python3
"""
Dashboard unificado de aceite y aceitunas.
Uso: streamlit run dashboard_unificado.py
"""

from __future__ import annotations

import os
import runpy
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import streamlit as st

from dashboard_unificado_helpers import (
    SECTION_KEY,
    UNIFIED_MODE_ENV,
    current_section,
    switch_section,
)
from tracker_paths import historial_path, precios_db_path

DIRECTORIO = Path(__file__).parent
DB_PATH = precios_db_path()
HISTORIAL_PATH = historial_path()
_MAX_INTENTOS = 5

st.set_page_config(
    page_title="La Toscana Tracker | Aceite + Aceitunas",
    page_icon="🫒",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _check_password() -> None:
    if st.session_state.get("_pwd_ok", False):
        return

    intentos = st.session_state.get("_intentos", 0)
    if intentos >= _MAX_INTENTOS:
        st.error("Demasiados intentos fallidos. Cerrá y volvé a abrir el navegador.")
        st.stop()

    st.markdown(
        """
        <style>
          [data-testid="stAppViewContainer"] {
            background:
              radial-gradient(circle at 12% 18%, rgba(95, 142, 78, 0.18), transparent 28%),
              radial-gradient(circle at 84% 22%, rgba(204, 153, 51, 0.18), transparent 26%),
              linear-gradient(145deg, #f6f3ea 0%, #eef5e7 48%, #f8f8f4 100%);
          }
          [data-testid="stHeader"] { background: transparent !important; }
          .suite-login {
            max-width: 420px;
            margin: 10vh auto 0;
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(79, 111, 82, 0.14);
            border-radius: 28px;
            padding: 3rem 2.6rem 2.5rem;
            box-shadow: 0 24px 80px rgba(48, 62, 41, 0.12);
            backdrop-filter: blur(10px);
            text-align: center;
          }
          .suite-login-kicker {
            display: inline-flex;
            gap: 0.5rem;
            align-items: center;
            padding: 0.45rem 0.9rem;
            border-radius: 999px;
            background: #f4efe0;
            color: #6d5a17;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
          }
          .suite-login-title {
            margin-top: 1.2rem;
            font-size: 2.1rem;
            line-height: 1.02;
            font-weight: 800;
            color: #203025;
          }
          .suite-login-copy {
            margin-top: 0.9rem;
            color: #4f5f53;
            font-size: 0.98rem;
          }
        </style>
        <div class="suite-login">
          <div class="suite-login-kicker">🫒 La Toscana Tracker</div>
          <div class="suite-login-title">Inteligencia comercial<br>en una sola vista</div>
          <div class="suite-login-copy">Ingresá la contraseña para acceder al tablero unificado.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if DB_PATH != DIRECTORIO / "precios.db" or HISTORIAL_PATH != DIRECTORIO / "historial_precios.json":
        st.caption(f"Modo copia · DB: {DB_PATH.name}")

    _, col, _ = st.columns([2, 1.4, 2])
    with col:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        pwd = st.text_input(
            "Contraseña",
            type="password",
            label_visibility="collapsed",
            placeholder="Contraseña…",
        )
        if st.button("Entrar al tracker", use_container_width=True, type="primary"):
            correct = st.secrets.get("PASSWORD", "")
            if pwd and pwd == correct:
                st.session_state["_pwd_ok"] = True
                st.session_state["_intentos"] = 0
                st.session_state.setdefault(SECTION_KEY, "inicio")
                st.rerun()
            st.session_state["_intentos"] = intentos + 1
            restantes = _MAX_INTENTOS - st.session_state["_intentos"]
            if restantes > 0:
                st.error(
                    f"Contraseña incorrecta ({restantes} intento{'s' if restantes != 1 else ''} restante{'s' if restantes != 1 else ''})"
                )
            else:
                st.rerun()
    st.stop()


@st.cache_data(ttl=300)
def cargar_resumen_suite(db_path: str) -> dict[str, dict[str, str | int]]:
    resumen: dict[str, dict[str, str | int]] = {
        "aceite": {"fecha": "Sin datos", "productos": 0, "cadenas": 0, "marcas": 0},
        "aceitunas": {"fecha": "Sin datos", "productos": 0, "cadenas": 0, "marcas": 0},
    }
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    latest_aceite = cur.execute("SELECT MAX(fecha) FROM precios").fetchone()[0]
    if latest_aceite:
        productos, cadenas, marcas = cur.execute(
            """
            SELECT COUNT(*), COUNT(DISTINCT supermercado), COUNT(DISTINCT marca)
            FROM precios
            WHERE fecha = ?
            """,
            (latest_aceite,),
        ).fetchone()
        resumen["aceite"] = {
            "fecha": latest_aceite,
            "productos": productos or 0,
            "cadenas": cadenas or 0,
            "marcas": marcas or 0,
        }

    latest_aceitunas = cur.execute("SELECT MAX(fecha) FROM aceitunas").fetchone()[0]
    if latest_aceitunas:
        productos, cadenas, marcas = cur.execute(
            """
            SELECT COUNT(*), COUNT(DISTINCT supermercado), COUNT(DISTINCT marca)
            FROM aceitunas
            WHERE fecha = ?
            """,
            (latest_aceitunas,),
        ).fetchone()
        resumen["aceitunas"] = {
            "fecha": latest_aceitunas,
            "productos": productos or 0,
            "cadenas": cadenas or 0,
            "marcas": marcas or 0,
        }

    conn.close()
    return resumen


def _render_shell_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"], .stApp { font-family: 'Manrope', sans-serif !important; }
        .stApp {
          background:
            radial-gradient(circle at 10% 18%, rgba(113, 154, 84, 0.14), transparent 28%),
            radial-gradient(circle at 88% 16%, rgba(201, 162, 74, 0.12), transparent 25%),
            linear-gradient(180deg, #f7f4eb 0%, #f4f8ef 45%, #fbfbf7 100%);
        }
        .block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1420px; }
        .suite-topbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1.1rem;
          padding: 0.95rem 1rem;
          background: rgba(255,255,255,0.72);
          border: 1px solid rgba(72, 98, 64, 0.12);
          border-radius: 22px;
          box-shadow: 0 10px 35px rgba(54, 70, 48, 0.08);
          backdrop-filter: blur(10px);
        }
        .suite-topbar-title {
          font-family: 'Fraunces', serif;
          font-size: 1.45rem;
          color: #1f3123;
          font-weight: 700;
        }
        .suite-topbar-sub {
          color: #58715a;
          font-size: 0.88rem;
          margin-top: 0.15rem;
        }
        .suite-chip {
          display: inline-flex;
          align-items: center;
          gap: 0.45rem;
          padding: 0.42rem 0.82rem;
          border-radius: 999px;
          background: #f3eddc;
          color: #725b18;
          font-size: 0.78rem;
          font-weight: 800;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }
        .suite-hero {
          position: relative;
          overflow: hidden;
          border-radius: 30px;
          padding: 2.2rem 2.2rem 2rem;
          background:
            linear-gradient(135deg, rgba(27, 50, 29, 0.96) 0%, rgba(53, 88, 48, 0.94) 48%, rgba(162, 121, 30, 0.88) 100%);
          color: #f8faf5;
          box-shadow: 0 30px 80px rgba(33, 46, 26, 0.18);
          margin-bottom: 1.2rem;
        }
        .suite-hero::after {
          content: "";
          position: absolute;
          inset: auto -40px -70px auto;
          width: 240px;
          height: 240px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(255,255,255,0.18), transparent 68%);
        }
        .suite-kicker {
          display: inline-flex;
          gap: 0.55rem;
          align-items: center;
          padding: 0.48rem 0.92rem;
          border-radius: 999px;
          background: rgba(255,255,255,0.12);
          font-size: 0.76rem;
          font-weight: 800;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }
        .suite-title {
          margin-top: 1rem;
          font-family: 'Fraunces', serif;
          font-size: clamp(2.1rem, 4.6vw, 3.8rem);
          line-height: 0.95;
          letter-spacing: -0.03em;
          max-width: 720px;
        }
        .suite-copy {
          margin-top: 1rem;
          max-width: 760px;
          color: rgba(248, 250, 245, 0.86);
          font-size: 1rem;
          line-height: 1.65;
        }
        .suite-card {
          height: 100%;
          border-radius: 24px;
          padding: 1.35rem 1.35rem 1.2rem;
          background: rgba(255,255,255,0.82);
          border: 1px solid rgba(73, 96, 67, 0.11);
          box-shadow: 0 16px 42px rgba(58, 73, 48, 0.08);
        }
        .suite-card h3 {
          margin: 0;
          font-family: 'Fraunces', serif;
          font-size: 1.7rem;
          line-height: 1;
          color: #1f3123;
        }
        .suite-card p {
          margin: 0.55rem 0 1rem;
          color: #60725d;
          font-size: 0.96rem;
          line-height: 1.55;
        }
        .suite-stat-row {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 0.75rem;
          margin-bottom: 1rem;
        }
        .suite-stat {
          border-radius: 16px;
          padding: 0.9rem 0.85rem;
          background: #f6f4ea;
          border: 1px solid rgba(114, 141, 101, 0.12);
        }
        .suite-stat-label {
          color: #6b7c68;
          font-size: 0.74rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }
        .suite-stat-value {
          margin-top: 0.3rem;
          color: #1f3123;
          font-size: 1.22rem;
          font-weight: 800;
        }
        .suite-note {
          color: #6a7a67;
          font-size: 0.86rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_topbar(section: str) -> None:
    col_title, col_inicio, col_aceite, col_aceitunas, col_badge = st.columns([3.3, 1, 1, 1.1, 1.6])
    with col_title:
        st.markdown(
            """
            <div class="suite-topbar">
              <div>
                <div class="suite-topbar-title">La Toscana Tracker</div>
                <div class="suite-topbar-sub">Lectura ejecutiva de precio, surtido, promoción y presencia en retail</div>
              </div>
              <div class="suite-chip">Tablero unificado</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_inicio:
        if st.button("Inicio", use_container_width=True, disabled=section == "inicio"):
            switch_section("inicio")
    with col_aceite:
        if st.button("Aceite", use_container_width=True, disabled=section == "aceite"):
            switch_section("aceite")
    with col_aceitunas:
        if st.button("Aceitunas", use_container_width=True, disabled=section == "aceitunas"):
            switch_section("aceitunas")
    with col_badge:
        if DB_PATH != DIRECTORIO / "precios.db" or HISTORIAL_PATH != DIRECTORIO / "historial_precios.json":
            st.caption(f"Modo copia · {DB_PATH.name}")


def _render_home(resumen: dict[str, dict[str, str | int]]) -> None:
    aceite = resumen["aceite"]
    aceitunas = resumen["aceitunas"]

    st.markdown(
        """
        <div class="suite-hero">
          <div class="suite-kicker">🫒 La Toscana Tracker</div>
          <div class="suite-title">Visión ejecutiva del mercado de aceite de oliva y aceitunas.</div>
          <div class="suite-copy">
            La suite consolida precio de góndola, presión promocional, amplitud de surtido,
            presencia por cadena, evolución temporal y benchmarks competitivos para seguir
            desempeño de marca, detectar oportunidades comerciales y monitorear la ejecución
            del portafolio en ambas categorías.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_aceite, col_aceitunas = st.columns(2)
    with col_aceite:
        st.markdown(
            f"""
            <div class="suite-card">
              <h3>Aceite</h3>
              <p>Seguimiento de pricing, mix de presentaciones, actividad promocional, posicionamiento por cadena y benchmark competitivo.</p>
              <div class="suite-stat-row">
                <div class="suite-stat">
                  <div class="suite-stat-label">Última fecha</div>
                  <div class="suite-stat-value">{aceite["fecha"]}</div>
                </div>
                <div class="suite-stat">
                  <div class="suite-stat-label">Productos</div>
                  <div class="suite-stat-value">{aceite["productos"]}</div>
                </div>
                <div class="suite-stat">
                  <div class="suite-stat-label">Cadenas</div>
                  <div class="suite-stat-value">{aceite["cadenas"]}</div>
                </div>
              </div>
              <div class="suite-note">Marcas activas: {aceite["marcas"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Abrir dashboard de aceite", key="suite_home_aceite", use_container_width=True, type="primary"):
            switch_section("aceite")

    with col_aceitunas:
        st.markdown(
            f"""
            <div class="suite-card">
              <h3>Aceitunas</h3>
              <p>Análisis de surtido por variedad, gramaje y envase, cobertura por cadena, presión promocional y quiebres de presencia.</p>
              <div class="suite-stat-row">
                <div class="suite-stat">
                  <div class="suite-stat-label">Última fecha</div>
                  <div class="suite-stat-value">{aceitunas["fecha"]}</div>
                </div>
                <div class="suite-stat">
                  <div class="suite-stat-label">Productos</div>
                  <div class="suite-stat-value">{aceitunas["productos"]}</div>
                </div>
                <div class="suite-stat">
                  <div class="suite-stat-label">Cadenas</div>
                  <div class="suite-stat-value">{aceitunas["cadenas"]}</div>
                </div>
              </div>
              <div class="suite-note">Marcas activas: {aceitunas["marcas"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Abrir dashboard de aceitunas", key="suite_home_aceitunas", use_container_width=True, type="primary"):
            switch_section("aceitunas")

    st.info(
        "La navegación entre categorías reinicia los filtros de la sección anterior para preservar una lectura limpia en cada tablero."
    )


@contextmanager
def _modo_unificado():
    anterior = os.environ.get(UNIFIED_MODE_ENV)
    os.environ[UNIFIED_MODE_ENV] = "1"
    try:
        yield
    finally:
        if anterior is None:
            os.environ.pop(UNIFIED_MODE_ENV, None)
        else:
            os.environ[UNIFIED_MODE_ENV] = anterior


def _render_dashboard(script_name: str) -> None:
    with _modo_unificado():
        runpy.run_path(str(DIRECTORIO / script_name), run_name="__main__")


_check_password()
_render_shell_css()
st.session_state.setdefault(SECTION_KEY, "inicio")
section = current_section()
resumen_suite = cargar_resumen_suite(str(DB_PATH))
_render_topbar(section)

if section == "aceite":
    _render_dashboard("dashboard.py")
elif section == "aceitunas":
    _render_dashboard("dashboard_aceitunas.py")
else:
    _render_home(resumen_suite)
