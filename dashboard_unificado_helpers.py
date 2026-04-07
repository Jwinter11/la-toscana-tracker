from __future__ import annotations

import os

import streamlit as st

UNIFIED_MODE_ENV = "ACEITE_TRACKER_UNIFIED_MODE"
SECTION_KEY = "suite_section"
SESSION_SCHEMA_KEY = "_session_schema_version"
SESSION_SCHEMA_VERSION = "2026-04-06-v1"
_PRESERVE_KEYS = {SECTION_KEY, "_pwd_ok", "_intentos", SESSION_SCHEMA_KEY}
COMMON_DASHBOARD_SECTIONS = [
    "📊  Resumen",
    "🏪  Por Cadena",
    "🏷️  Por Marca",
    "📈  Evolución",
    "🔖  Ofertas",
    "⚖️  Comparativa",
    "🎯  Mi Marca",
    "📦  Quiebres",
    "🔢  Tabla dinámica",
]
PLOTLY_FONT_FAMILY = "Montserrat"
NAV_WIDGET_VERSION = "v3"


def unified_mode_enabled() -> bool:
    return os.environ.get(UNIFIED_MODE_ENV) == "1"


def current_section(default: str = "inicio") -> str:
    return st.session_state.get(SECTION_KEY, default)


def ensure_session_schema(default_section: str = "inicio") -> None:
    if st.session_state.get(SESSION_SCHEMA_KEY) == SESSION_SCHEMA_VERSION:
        return

    preserved = {
        key: st.session_state[key]
        for key in (SECTION_KEY, "_pwd_ok", "_intentos")
        if key in st.session_state
    }
    valid_sections = {"inicio", "aceite", "aceitunas"}
    if preserved.get(SECTION_KEY) not in valid_sections:
        preserved[SECTION_KEY] = default_section

    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.session_state.update(preserved)
    st.session_state[SESSION_SCHEMA_KEY] = SESSION_SCHEMA_VERSION
    st.rerun()


def switch_section(section: str) -> None:
    preserved = {key: st.session_state[key] for key in _PRESERVE_KEYS if key in st.session_state}
    for key in list(st.session_state.keys()):
        if key not in _PRESERVE_KEYS:
            del st.session_state[key]
    st.session_state.update(preserved)
    st.session_state[SECTION_KEY] = section
    st.rerun()


def render_sidebar_section_switcher(current: str, key_prefix: str = "suite_switcher") -> None:
    col_aceite, col_aceitunas = st.columns(2)
    with col_aceite:
        if st.button(
            "Aceite",
            key=f"{key_prefix}_aceite",
            use_container_width=True,
            disabled=current == "aceite",
        ):
            switch_section("aceite")
    with col_aceitunas:
        if st.button(
            "Aceitunas",
            key=f"{key_prefix}_aceitunas",
            use_container_width=True,
            disabled=current == "aceitunas",
        ):
            switch_section("aceitunas")
