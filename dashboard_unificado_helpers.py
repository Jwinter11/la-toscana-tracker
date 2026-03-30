from __future__ import annotations

import os

import streamlit as st

UNIFIED_MODE_ENV = "ACEITE_TRACKER_UNIFIED_MODE"
SECTION_KEY = "suite_section"
_PRESERVE_KEYS = {SECTION_KEY, "_pwd_ok", "_intentos"}
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


def unified_mode_enabled() -> bool:
    return os.environ.get(UNIFIED_MODE_ENV) == "1"


def current_section(default: str = "inicio") -> str:
    return st.session_state.get(SECTION_KEY, default)


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
