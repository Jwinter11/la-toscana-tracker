#!/usr/bin/env python3
# última actualización: 2026-03-26b
"""
Dashboard de precios de aceitunas — Aceite Tracker
Uso: streamlit run dashboard_aceitunas.py --server.port 8502
"""

if False and active_page == "Ofertas":
    _todos_periodos_of = sorted(
        df_full["Periodo"].unique(),
        key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min(),
    )
    _periodos_of_default = [_todos_periodos_of[-1]] if _todos_periodos_of else []
    _of_f1, _of_f2, _of_f3, _of_f4 = st.columns([2.2, 1.4, 1.4, 1.3])
    with _of_f1:
        _periodos_of_sel = st.multiselect(
            "📆 Semanas / Meses",
            _todos_periodos_of,
            default=_periodos_of_default,
            key="periodos_of_aceitunas_live",
        )
    with _of_f2:
        _of_var_sel = st.selectbox("Variedad", ["Todas"] + variedades_disp, key="of_var_aceitunas_live")
    with _of_f3:
        _of_gram_sel = st.selectbox("Gramaje", ["Todos"] + grupos_labels, key="of_gram_aceitunas_live")
    with _of_f4:
        _of_envase_sel = st.selectbox("Envase", ["Todos"] + envases_disp, key="of_envase_aceitunas_live")

    _periodos_of_activos = _periodos_of_sel if _periodos_of_sel else _periodos_of_default
    _of_gram_key = None
    if _of_gram_sel != "Todos":
        _of_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _of_gram_sel), None)

    _mask_of = (
        df_full["Periodo"].isin(_periodos_of_activos)
        & df_full["Cadena"].isin(cadenas_sel)
        & df_full["Variedad"].isin(variedades_sel)
        & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
        & df_full["Envase"].isin(envases_sel)
        & df_full["En_oferta"]
    )
    if _of_var_sel != "Todas":
        _mask_of &= df_full["Variedad"].eq(_of_var_sel)
    if _of_gram_key:
        _mask_of &= df_full["Gramaje"].eq(_of_gram_key)
    if _of_envase_sel != "Todos":
        _mask_of &= df_full["Envase"].eq(_of_envase_sel)

    df_of5 = df_full[_mask_of].copy()
    _orden_per_of5 = [p for p in _todos_periodos_of if p in _periodos_of_activos]
    _fecha_hoy = df_of5["Fecha"].max() if not df_of5.empty else df_full["Fecha"].max()
    df_of5_hoy = df_of5[df_of5["Fecha"] == _fecha_hoy].copy()
    _precio_gondola_lbl = "$/kg góndola" if _met_kg else "Precio góndola ($)"
    _precio_oferta_lbl = "$/kg oferta" if _met_kg else "Precio oferta ($)"

    if df_of5.empty:
        st.info("🏷️ No hay productos en oferta con los filtros actuales.")
    else:
        with st.expander("📊 Resumen de ofertas de hoy", expanded=True):
            _src_kpi = df_of5_hoy if not df_of5_hoy.empty else df_of5
            _lbl_hoy = _fecha_hoy.strftime("%d/%m/%Y") if hasattr(_fecha_hoy, "strftime") else str(_fecha_hoy)
            _oferta_prom = _src_kpi["_met_of"].dropna().mean()
            _gondola_prom = _src_kpi["_met"].dropna().mean()
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#7C2D12,#C2410C);border-radius:14px;
                        padding:1.2rem 2rem;margin-bottom:1.2rem;display:flex;gap:3rem;align-items:center">
              <div><div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:rgba(255,255,255,0.6)">Ofertas hoy · {_lbl_hoy}</div><div style="font-size:2rem;font-weight:800;color:#fff">{len(_src_kpi):,}</div></div>
              <div><div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:rgba(255,255,255,0.6)">Descuento promedio</div><div style="font-size:2rem;font-weight:800;color:#fff">{_src_kpi["Descuento_pct"].mean():.0f}%</div></div>
              <div><div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:rgba(255,255,255,0.6)">Precio oferta prom.</div><div style="font-size:2rem;font-weight:800;color:#fff">{f"${_oferta_prom:,.0f}" if pd.notna(_oferta_prom) else "—"}</div></div>
              <div><div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:rgba(255,255,255,0.6)">Precio góndola prom.</div><div style="font-size:2rem;font-weight:800;color:rgba(255,255,255,0.7)">{f"${_gondola_prom:,.0f}" if pd.notna(_gondola_prom) else "—"}</div></div>
            </div>
            """, unsafe_allow_html=True)
            col_l, col_r = st.columns([1, 1], gap="large")
            with col_l:
                df_desc_c = (_src_kpi.groupby("Cadena")["Descuento_pct"].mean().reset_index().sort_values("Descuento_pct"))
                fig = go.Figure(go.Bar(x=df_desc_c["Descuento_pct"], y=df_desc_c["Cadena"], orientation="h",
                                       marker_color=[cc(c) for c in df_desc_c["Cadena"]],
                                       text=[f"{v:.0f}%" for v in df_desc_c["Descuento_pct"]],
                                       textposition="outside", textfont=dict(size=13, color="#111827"), cliponaxis=False))
                _vmax_d = df_desc_c["Descuento_pct"].max() if not df_desc_c.empty else 1
                fig.update_layout(**_BASE_CORE, height=320, margin=dict(l=10, r=120, t=40, b=10),
                                  xaxis=dict(title="Descuento %", ticksuffix="%",
                                             tickfont=dict(size=12, color="#111827"),
                                             range=[0, _vmax_d * 1.4 if _vmax_d else 1]),
                                  yaxis=dict(tickfont=dict(size=13, color="#111827")), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            with col_r:
                df_of_cnt = _src_kpi.groupby("Cadena").size().reset_index(name="n")
                fig = go.Figure(go.Pie(labels=df_of_cnt["Cadena"], values=df_of_cnt["n"],
                                       marker_colors=[cc(c) for c in df_of_cnt["Cadena"]],
                                       hole=0.55, textinfo="label+percent", textposition="outside",
                                       textfont=dict(size=12, color="#111827")))
                fig.update_layout(**_BASE_CORE, height=320, margin=dict(l=10, r=10, t=40, b=40), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        with st.expander("Precio góndola vs precio oferta por marca", expanded=True):
            st.markdown('<div class="chart-note">La diferencia entre las barras = ahorro de la oferta</div>', unsafe_allow_html=True)
            _gvof_gram_opts = [l for g, l in zip(grupos_disp, grupos_labels) if df_of5["Gramaje"].eq(g).any()]
            _gvof_gram_sel = st.selectbox("Gramaje", ["Todos"] + _gvof_gram_opts, key="gram_gvof_aceitunas_live")
            _df_gvof_src = df_of5.copy()
            if _gvof_gram_sel != "Todos":
                _gvof_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _gvof_gram_sel), None)
                if _gvof_gram_key:
                    _df_gvof_src = _df_gvof_src[_df_gvof_src["Gramaje"] == _gvof_gram_key]
            _df_gvof_src = _df_gvof_src[~_df_gvof_src["Marca"].isin(_MARCAS_AGREGADAS_EXCLUIDAS_AC)].copy()
            if _df_gvof_src.empty:
                st.info("Sin ofertas para la selección actual.")
            else:
                df_gvof = (_df_gvof_src.groupby("Marca").agg(gondola=("_met", "mean"), oferta=("_met_of", "mean")).reset_index())
                df_gvof = df_gvof.sort_values("Marca", key=lambda s: s.map(marca_sort_key_ac))
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Precio góndola", x=df_gvof["Marca"], y=df_gvof["gondola"], marker_color="#D1D5DB",
                                     text=[f"${v:,.0f}" for v in df_gvof["gondola"]], textposition="outside",
                                     textfont=dict(size=12, color="#374151")))
                fig.add_trace(go.Bar(name="Precio oferta", x=df_gvof["Marca"], y=df_gvof["oferta"],
                                     marker_color=[color_marca_real_ac(m) for m in df_gvof["Marca"]],
                                     text=[f"${v:,.0f}" for v in df_gvof["oferta"]], textposition="outside",
                                     textfont=dict(size=12, color="#111827")))
                _ymax = df_gvof["gondola"].max() if not df_gvof.empty else 1
                fig.update_layout(**BASE, barmode="overlay", height=420,
                                  yaxis=dict(title=_met_lbl, tickprefix="$", tickformat=",",
                                             tickfont=dict(size=12, color="#111827"),
                                             range=[0, _ymax * 1.25 if _ymax else 1]),
                                  xaxis=dict(tickfont=dict(size=13, color="#111827"), tickangle=-20))
                st.plotly_chart(fig, use_container_width=True)

        if df_of5["Periodo"].nunique() >= 2:
            with st.expander("Ofertas en el tiempo por marca & cadena", expanded=True):
                col_ol, col_or = st.columns(2, gap="large")
                _df_brand_time = df_of5[~df_of5["Marca_cat"].isin(_MARCAS_AGREGADAS_EXCLUIDAS_AC)].copy()
                if _df_brand_time.empty:
                    _df_brand_time = df_of5.copy()
                with col_ol:
                    df_of_t_m = (_df_brand_time.groupby(["Periodo", "Marca_cat"]).size().reset_index(name="n"))
                    df_of_t_m["Periodo"] = pd.Categorical(df_of_t_m["Periodo"], categories=_orden_per_of5, ordered=True)
                    fig = px.bar(df_of_t_m, x="Periodo", y="n", color="Marca_cat", barmode="stack",
                                 color_discrete_map=COLORES_MARCA_AC, labels={"n": "Cantidad de ofertas", "Periodo": ""},
                                 height=380, category_orders={"Marca_cat": ORDEN_MARCAS_AC})
                    fig.update_layout(**BASE, xaxis=dict(tickfont=dict(size=12, color="#111827"), tickangle=-20),
                                      yaxis=dict(tickfont=dict(size=12, color="#111827")))
                    st.plotly_chart(fig, use_container_width=True)
                with col_or:
                    df_of_t_c = (df_of5.groupby(["Periodo", "Cadena"]).size().reset_index(name="n"))
                    df_of_t_c["Periodo"] = pd.Categorical(df_of_t_c["Periodo"], categories=_orden_per_of5, ordered=True)
                    fig = px.bar(df_of_t_c, x="Periodo", y="n", color="Cadena", barmode="stack",
                                 color_discrete_map=COLORS_CADENAS, labels={"n": "Cantidad de ofertas", "Periodo": ""},
                                 height=380)
                    fig.update_layout(**BASE, xaxis=dict(tickfont=dict(size=12, color="#111827"), tickangle=-20),
                                      yaxis=dict(tickfont=dict(size=12, color="#111827")))
                    st.plotly_chart(fig, use_container_width=True)

        with st.expander("Top 20 · Mejores descuentos del período", expanded=True):
            df_top = (df_of5.sort_values("Descuento_pct", ascending=False)
                        .head(20)[["Cadena", "Marca", "Producto", "Variedad", "Envase", "Gramaje", "_met", "_met_of", "Descuento_pct"]]
                        .copy())
            df_top.columns = ["Cadena", "Marca", "Producto", "Variedad", "Envase", "Gramaje",
                              _precio_gondola_lbl, _precio_oferta_lbl, "Descuento %"]
            st.dataframe(df_top, height=420,
                         column_config={
                             _precio_gondola_lbl: st.column_config.NumberColumn(format="$%d"),
                             _precio_oferta_lbl: st.column_config.NumberColumn(format="$%d"),
                             "Descuento %": st.column_config.NumberColumn(format="%.0f%%"),
                         }, hide_index=True)

        with st.expander("Presencia de ofertas · marcas seleccionadas", expanded=True):
            st.markdown('<div class="chart-note">✓ = hubo oferta ese período · — = sin oferta</div>',
                        unsafe_allow_html=True)
            _marcas_of2_base = df_full[
                df_full["Periodo"].isin(_periodos_of_activos)
                & df_full["Cadena"].isin(cadenas_sel)
                & df_full["Variedad"].isin(variedades_sel)
                & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
                & df_full["Envase"].isin(envases_sel)
            ].copy()
            if _of_var_sel != "Todas":
                _marcas_of2_base = _marcas_of2_base[_marcas_of2_base["Variedad"] == _of_var_sel]
            if _of_gram_key:
                _marcas_of2_base = _marcas_of2_base[_marcas_of2_base["Gramaje"] == _of_gram_key]
            if _of_envase_sel != "Todos":
                _marcas_of2_base = _marcas_of2_base[_marcas_of2_base["Envase"] == _of_envase_sel]
            _marcas_of2_disp = sorted(_marcas_of2_base["Marca"].dropna().unique(), key=marca_sort_key_ac)
            _marcas_of2_default = [m for m in ["La Toscana", "Castell", "Nucete"] if m in _marcas_of2_disp]
            if not _marcas_of2_default:
                _marcas_of2_default = _marcas_of2_disp[:3]
            _of2_fa, _of2_fb, _of2_fc = st.columns([2.2, 1.6, 1.2])
            with _of2_fa:
                _marcas_of2_sel = st.multiselect("Marca", _marcas_of2_disp, default=_marcas_of2_default,
                                                 key="of2_marcas_aceitunas_live", placeholder="Elegí marcas")
            _cadenas_of2_disp = sorted(_marcas_of2_base["Cadena"].dropna().unique())
            with _of2_fb:
                _cadenas_of2_sel = st.multiselect("Cadena", _cadenas_of2_disp, default=_cadenas_of2_disp,
                                                  key="of2_cadenas_aceitunas_live", placeholder="Todas las cadenas")
            with _of2_fc:
                _of2_gran = st.selectbox("Temporalidad", ["Semanal", "Mensual"], key="of2_gran_aceitunas_live")
            _marcas_of2_act = _marcas_of2_sel if _marcas_of2_sel else _marcas_of2_default
            _cadenas_of2_act = _cadenas_of2_sel if _cadenas_of2_sel else _cadenas_of2_disp
            _df_dest = _marcas_of2_base[_marcas_of2_base["Marca"].isin(_marcas_of2_act) &
                                        _marcas_of2_base["Cadena"].isin(_cadenas_of2_act)].copy()
            if _df_dest.empty:
                st.info("No hay SKUs para las marcas seleccionadas con estos filtros.")
            else:
                if _of2_gran == "Mensual":
                    _df_dest["_col_per"] = pd.to_datetime(_df_dest["Fecha"]).dt.strftime("%b %Y")
                    _pers_dest_ord = [ts.strftime("%b %Y") for ts in sorted(pd.to_datetime(_df_dest["Fecha"]).dt.to_period("M").dt.to_timestamp().unique())]
                else:
                    _df_dest["_col_per"] = _df_dest["Periodo"]
                    _pers_dest_ord = [p for p in _orden_per_of5 if p in set(_df_dest["Periodo"])]
                _of_mask_dest = (
                    df_full["En_oferta"] & df_full["Marca"].isin(_marcas_of2_act)
                    & df_full["Periodo"].isin(_periodos_of_activos) & df_full["Cadena"].isin(_cadenas_of2_act)
                    & df_full["Variedad"].isin(variedades_sel)
                    & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
                    & df_full["Envase"].isin(envases_sel)
                )
                if _of_var_sel != "Todas":
                    _of_mask_dest &= df_full["Variedad"].eq(_of_var_sel)
                if _of_gram_key:
                    _of_mask_dest &= df_full["Gramaje"].eq(_of_gram_key)
                if _of_envase_sel != "Todos":
                    _of_mask_dest &= df_full["Envase"].eq(_of_envase_sel)
                _df_of_mask = df_full[_of_mask_dest].copy()
                _df_of_mask["_col_per"] = pd.to_datetime(_df_of_mask["Fecha"]).dt.strftime("%b %Y") if _of2_gran == "Mensual" else _df_of_mask["Periodo"]
                _skus_dest = sorted(_df_dest["SKU_canonico"].dropna().unique())
                _of_set = set(zip(_df_of_mask["SKU_canonico"], _df_of_mask["_col_per"]))
                _hmap_rows = []
                for _sk in _skus_dest:
                    _row = {"SKU": _sk}
                    for _pe in _pers_dest_ord:
                        _row[_pe] = "✓" if (_sk, _pe) in _of_set else "—"
                    _hmap_rows.append(_row)
                _hmap_df = pd.DataFrame(_hmap_rows).set_index("SKU")
                _hmap_num = _hmap_df.applymap(lambda x: 1.0 if x == "✓" else 0.0)
                fig_oh = go.Figure(go.Heatmap(
                    z=_hmap_num.values, x=_pers_dest_ord, y=_hmap_num.index.tolist(),
                    text=_hmap_df.values, texttemplate="%{text}",
                    colorscale=[[0, "#F1F5F9"], [1, "#15803D"]], zmin=0, zmax=1,
                    showscale=False, xgap=2, ygap=2, textfont=dict(size=11, color="#111827"),
                ))
                fig_oh.update_layout(**_BASE_CORE, height=max(120, len(_skus_dest) * 24 + 70),
                                     margin=dict(l=10, r=10, t=10, b=10),
                                     xaxis=dict(tickfont=dict(size=10, color="#374151"), tickangle=-30, side="top"),
                                     yaxis=dict(tickfont=dict(size=10, color="#374151"), autorange="reversed"))
                st.plotly_chart(fig_oh, use_container_width=True)


if False and active_page == "Comparativa":
    st.markdown('<div class="chart-note">Seleccioná dos marcas y luego un SKU de cada una para comparar su precio de góndola en el tiempo</div>',
                unsafe_allow_html=True)
    _cmp_f1, _cmp_f2, _cmp_f3, _ = st.columns([1.2, 1.2, 1.2, 2.4])
    with _cmp_f1:
        _cmp_var = st.selectbox("Variedad", ["Todas"] + variedades_disp, key="cmp_var_aceitunas_live")
    with _cmp_f2:
        _cmp_gram = st.selectbox("Gramaje", ["Todos"] + grupos_labels, key="cmp_gram_aceitunas_live")
    with _cmp_f3:
        _cmp_envase = st.selectbox("Envase", ["Todos"] + envases_disp, key="cmp_envase_aceitunas_live")
    _cmp_gram_key = None
    if _cmp_gram != "Todos":
        _cmp_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _cmp_gram), None)
    _cmp_base = dff.dropna(subset=["Marca", "SKU_canonico", "_met"]).copy()
    if _cmp_var != "Todas":
        _cmp_base = _cmp_base[_cmp_base["Variedad"] == _cmp_var]
    if _cmp_gram_key:
        _cmp_base = _cmp_base[_cmp_base["Gramaje"] == _cmp_gram_key]
    if _cmp_envase != "Todos":
        _cmp_base = _cmp_base[_cmp_base["Envase"] == _cmp_envase]
    if _cmp_base.empty:
        st.info("No hay datos comparables con los filtros actuales.")
    else:
        marcas_comp = sorted(_cmp_base["Marca"].dropna().unique(), key=marca_sort_key_ac)
        col_m1, col_m2 = st.columns(2, gap="large")
        with col_m1:
            st.markdown("**Marca 1**")
            marca_c1 = st.selectbox("Marca 1", marcas_comp, key="comp_marca1_aceitunas_live", label_visibility="collapsed")
            skus_c1 = sorted(_cmp_base[_cmp_base["Marca"] == marca_c1]["SKU_canonico"].dropna().unique())
            sku_c1 = st.selectbox("SKU 1", skus_c1, key="comp_sku1_aceitunas_live", label_visibility="collapsed")
        with col_m2:
            st.markdown("**Marca 2**")
            default_m2 = marcas_comp[1] if len(marcas_comp) > 1 else marcas_comp[0]
            idx_m2 = marcas_comp.index(default_m2)
            marca_c2 = st.selectbox("Marca 2", marcas_comp, index=idx_m2, key="comp_marca2_aceitunas_live", label_visibility="collapsed")
            skus_c2 = sorted(_cmp_base[_cmp_base["Marca"] == marca_c2]["SKU_canonico"].dropna().unique())
            sku_c2 = st.selectbox("SKU 2", skus_c2, key="comp_sku2_aceitunas_live", label_visibility="collapsed")
        orden_per8 = sorted(_cmp_base["Periodo"].unique(), key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min())

        def sku_evol(sku_name: str, label: str) -> pd.DataFrame:
            df_s = (_cmp_base[_cmp_base["SKU_canonico"] == sku_name].groupby("Periodo")["_met"].mean().reset_index())
            df_s["Periodo"] = pd.Categorical(df_s["Periodo"], categories=orden_per8, ordered=True)
            df_s["SKU"] = label
            return df_s

        lbl1, lbl2 = sku_c1, sku_c2
        df_comp = pd.concat([sku_evol(sku_c1, lbl1), sku_evol(sku_c2, lbl2)], ignore_index=True)
        of_pers1 = set(_cmp_base[(_cmp_base["SKU_canonico"] == sku_c1) & _cmp_base["En_oferta"]]["Periodo"].unique())
        of_pers2 = set(_cmp_base[(_cmp_base["SKU_canonico"] == sku_c2) & _cmp_base["En_oferta"]]["Periodo"].unique())
        if df_comp.empty:
            st.info("No hay datos de evolución para los SKUs seleccionados.")
        else:
            color1 = color_marca_real_ac(marca_c1)
            color2 = color_marca_real_ac(marca_c2) if marca_c2 != marca_c1 else "#C73E1D"
            fig = px.line(df_comp, x="Periodo", y="_met", color="SKU", markers=True,
                          color_discrete_map={lbl1: color1, lbl2: color2},
                          labels={"_met": _met_lbl, "Periodo": ""}, height=420)
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Semanas en oferta", expanded=True):
                _of_rows = []
                for _pe in orden_per8:
                    _of_rows.append({"Período": _pe, lbl1[:35]: "✓" if _pe in of_pers1 else "—",
                                     lbl2[:35]: "✓" if _pe in of_pers2 else "—"})
                st.dataframe(pd.DataFrame(_of_rows), height=min(400, len(orden_per8) * 38 + 60), hide_index=True)

if False and active_page == "Ofertas":
    _todos_periodos_of = sorted(
        df_full["Periodo"].unique(),
        key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min(),
    )
    _periodos_of_default = [_todos_periodos_of[-1]] if _todos_periodos_of else []
    _of_f1, _of_f2, _of_f3, _of_f4 = st.columns([2.2, 1.4, 1.4, 1.3])
    with _of_f1:
        _periodos_of_sel = st.multiselect(
            "📆 Semanas / Meses",
            _todos_periodos_of,
            default=_periodos_of_default,
            key="periodos_of_aceitunas",
        )
    with _of_f2:
        _of_var_sel = st.selectbox("Variedad", ["Todas"] + variedades_disp, key="of_var_aceitunas")
    with _of_f3:
        _of_gram_sel = st.selectbox("Gramaje", ["Todos"] + grupos_labels, key="of_gram_aceitunas")
    with _of_f4:
        _of_envase_sel = st.selectbox("Envase", ["Todos"] + envases_disp, key="of_envase_aceitunas")

    _periodos_of_activos = _periodos_of_sel if _periodos_of_sel else _periodos_of_default
    _of_gram_key = None
    if _of_gram_sel != "Todos":
        _of_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _of_gram_sel), None)

    _mask_of = (
        df_full["Periodo"].isin(_periodos_of_activos)
        & df_full["Cadena"].isin(cadenas_sel)
        & df_full["Variedad"].isin(variedades_sel)
        & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
        & df_full["Envase"].isin(envases_sel)
        & df_full["En_oferta"]
    )
    if _of_var_sel != "Todas":
        _mask_of &= df_full["Variedad"].eq(_of_var_sel)
    if _of_gram_key:
        _mask_of &= df_full["Gramaje"].eq(_of_gram_key)
    if _of_envase_sel != "Todos":
        _mask_of &= df_full["Envase"].eq(_of_envase_sel)

    df_of5 = df_full[_mask_of].copy()
    _orden_per_of5 = [p for p in _todos_periodos_of if p in _periodos_of_activos]
    _fecha_hoy = df_of5["Fecha"].max() if not df_of5.empty else df_full["Fecha"].max()
    df_of5_hoy = df_of5[df_of5["Fecha"] == _fecha_hoy].copy()

    _precio_gondola_lbl = "$/kg góndola" if _met_kg else "Precio góndola ($)"
    _precio_oferta_lbl = "$/kg oferta" if _met_kg else "Precio oferta ($)"
    _precio_gondola_prom_lbl = "$/kg góndola prom." if _met_kg else "Precio góndola prom."
    _precio_oferta_prom_lbl = "$/kg oferta prom." if _met_kg else "Precio oferta prom."

    if df_of5.empty:
        st.info("🏷️ No hay productos en oferta con los filtros actuales.")
    else:
        with st.expander("📊 Resumen de ofertas de hoy", expanded=True):
            _src_kpi = df_of5_hoy if not df_of5_hoy.empty else df_of5
            _lbl_hoy = _fecha_hoy.strftime("%d/%m/%Y") if hasattr(_fecha_hoy, "strftime") else str(_fecha_hoy)
            _oferta_prom = _src_kpi["_met_of"].dropna().mean()
            _gondola_prom = _src_kpi["_met"].dropna().mean()
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#7C2D12,#C2410C);border-radius:14px;
                        padding:1.2rem 2rem;margin-bottom:1.2rem;display:flex;gap:3rem;align-items:center">
              <div>
                <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:1px;color:rgba(255,255,255,0.6)">Ofertas hoy · {_lbl_hoy}</div>
                <div style="font-size:2rem;font-weight:800;color:#fff">{len(_src_kpi):,}</div>
              </div>
              <div>
                <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:1px;color:rgba(255,255,255,0.6)">Descuento promedio</div>
                <div style="font-size:2rem;font-weight:800;color:#fff">{_src_kpi["Descuento_pct"].mean():.0f}%</div>
              </div>
              <div>
                <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:1px;color:rgba(255,255,255,0.6)">{_precio_oferta_prom_lbl}</div>
                <div style="font-size:2rem;font-weight:800;color:#fff">{f"${_oferta_prom:,.0f}" if pd.notna(_oferta_prom) else "—"}</div>
              </div>
              <div>
                <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:1px;color:rgba(255,255,255,0.6)">{_precio_gondola_prom_lbl}</div>
                <div style="font-size:2rem;font-weight:800;color:rgba(255,255,255,0.7)">{f"${_gondola_prom:,.0f}" if pd.notna(_gondola_prom) else "—"}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            col_l, col_r = st.columns([1, 1], gap="large")
            with col_l:
                df_desc_c = (_src_kpi.groupby("Cadena")["Descuento_pct"].mean().reset_index().sort_values("Descuento_pct"))
                fig = go.Figure(go.Bar(
                    x=df_desc_c["Descuento_pct"], y=df_desc_c["Cadena"], orientation="h",
                    marker_color=[cc(c) for c in df_desc_c["Cadena"]],
                    text=[f"{v:.0f}%" for v in df_desc_c["Descuento_pct"]],
                    textposition="outside", textfont=dict(size=13, color="#111827"), cliponaxis=False,
                ))
                _vmax_d = df_desc_c["Descuento_pct"].max() if not df_desc_c.empty else 1
                fig.update_layout(**_BASE_CORE, height=320, margin=dict(l=10, r=120, t=40, b=10),
                                  xaxis=dict(title="Descuento %", ticksuffix="%",
                                             tickfont=dict(size=12, color="#111827"),
                                             range=[0, _vmax_d * 1.4 if _vmax_d else 1]),
                                  yaxis=dict(tickfont=dict(size=13, color="#111827")),
                                  showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col_r:
                df_of_cnt = _src_kpi.groupby("Cadena").size().reset_index(name="n")
                fig = go.Figure(go.Pie(
                    labels=df_of_cnt["Cadena"], values=df_of_cnt["n"],
                    marker_colors=[cc(c) for c in df_of_cnt["Cadena"]],
                    hole=0.55, textinfo="label+percent", textposition="outside",
                    textfont=dict(size=12, color="#111827"),
                ))
                fig.update_layout(**_BASE_CORE, height=320, margin=dict(l=10, r=10, t=40, b=40), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        with st.expander("Precio góndola vs precio oferta por marca", expanded=True):
            st.markdown('<div class="chart-note">La diferencia entre las barras = ahorro de la oferta</div>',
                        unsafe_allow_html=True)
            _gvof_gram_opts = [l for g, l in zip(grupos_disp, grupos_labels) if df_of5["Gramaje"].eq(g).any()]
            _gvof_gram_sel = st.selectbox("Gramaje", ["Todos"] + _gvof_gram_opts, key="gram_gvof_aceitunas")
            _df_gvof_src = df_of5.copy()
            if _gvof_gram_sel != "Todos":
                _gvof_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _gvof_gram_sel), None)
                if _gvof_gram_key:
                    _df_gvof_src = _df_gvof_src[_df_gvof_src["Gramaje"] == _gvof_gram_key]
            _df_gvof_src = _df_gvof_src[~_df_gvof_src["Marca"].isin(_MARCAS_AGREGADAS_EXCLUIDAS_AC)].copy()
            if _df_gvof_src.empty:
                st.info("Sin ofertas para la selección actual.")
            else:
                df_gvof = (_df_gvof_src.groupby("Marca")
                                      .agg(gondola=("_met", "mean"), oferta=("_met_of", "mean"))
                                      .reset_index())
                df_gvof = df_gvof.sort_values("Marca", key=lambda s: s.map(marca_sort_key_ac))
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Precio góndola", x=df_gvof["Marca"], y=df_gvof["gondola"],
                                     marker_color="#D1D5DB",
                                     text=[f"${v:,.0f}" for v in df_gvof["gondola"]],
                                     textposition="outside", textfont=dict(size=12, color="#374151")))
                fig.add_trace(go.Bar(name="Precio oferta", x=df_gvof["Marca"], y=df_gvof["oferta"],
                                     marker_color=[color_marca_real_ac(m) for m in df_gvof["Marca"]],
                                     text=[f"${v:,.0f}" for v in df_gvof["oferta"]],
                                     textposition="outside", textfont=dict(size=12, color="#111827")))
                _ymax = df_gvof["gondola"].max() if not df_gvof.empty else 1
                fig.update_layout(**BASE, barmode="overlay", height=420,
                                  yaxis=dict(title=_met_lbl, tickprefix="$", tickformat=",",
                                             tickfont=dict(size=12, color="#111827"),
                                             range=[0, _ymax * 1.25 if _ymax else 1]),
                                  xaxis=dict(tickfont=dict(size=13, color="#111827"), tickangle=-20))
                st.plotly_chart(fig, use_container_width=True)

        _n_per_of5 = df_of5["Periodo"].nunique()
        if _n_per_of5 >= 2:
            with st.expander("Ofertas en el tiempo por marca & cadena", expanded=True):
                col_ol, col_or = st.columns(2, gap="large")
                _df_brand_time = df_of5[~df_of5["Marca_cat"].isin(_MARCAS_AGREGADAS_EXCLUIDAS_AC)].copy()
                if _df_brand_time.empty:
                    _df_brand_time = df_of5.copy()

                with col_ol:
                    df_of_t_m = (_df_brand_time.groupby(["Periodo", "Marca_cat"]).size().reset_index(name="n"))
                    df_of_t_m["Periodo"] = pd.Categorical(df_of_t_m["Periodo"], categories=_orden_per_of5, ordered=True)
                    fig = px.bar(df_of_t_m, x="Periodo", y="n", color="Marca_cat", barmode="stack",
                                 color_discrete_map=COLORES_MARCA_AC, labels={"n": "Cantidad de ofertas", "Periodo": ""},
                                 height=380, category_orders={"Marca_cat": ORDEN_MARCAS_AC})
                    fig.update_layout(**BASE,
                                      xaxis=dict(tickfont=dict(size=12, color="#111827"), tickangle=-20),
                                      yaxis=dict(tickfont=dict(size=12, color="#111827")))
                    st.plotly_chart(fig, use_container_width=True)

                with col_or:
                    df_of_t_c = (df_of5.groupby(["Periodo", "Cadena"]).size().reset_index(name="n"))
                    df_of_t_c["Periodo"] = pd.Categorical(df_of_t_c["Periodo"], categories=_orden_per_of5, ordered=True)
                    fig = px.bar(df_of_t_c, x="Periodo", y="n", color="Cadena", barmode="stack",
                                 color_discrete_map=COLORS_CADENAS, labels={"n": "Cantidad de ofertas", "Periodo": ""},
                                 height=380)
                    fig.update_layout(**BASE,
                                      xaxis=dict(tickfont=dict(size=12, color="#111827"), tickangle=-20),
                                      yaxis=dict(tickfont=dict(size=12, color="#111827")))
                    st.plotly_chart(fig, use_container_width=True)

        with st.expander("Top 20 · Mejores descuentos del período", expanded=True):
            df_top = (
                df_of5.sort_values("Descuento_pct", ascending=False)
                .head(20)[["Cadena", "Marca", "Producto", "Variedad", "Envase", "Gramaje", "_met", "_met_of", "Descuento_pct"]]
                .copy()
            )
            df_top.columns = ["Cadena", "Marca", "Producto", "Variedad", "Envase", "Gramaje",
                              _precio_gondola_lbl, _precio_oferta_lbl, "Descuento %"]
            st.dataframe(df_top, height=420,
                         column_config={
                             _precio_gondola_lbl: st.column_config.NumberColumn(format="$%d"),
                             _precio_oferta_lbl: st.column_config.NumberColumn(format="$%d"),
                             "Descuento %": st.column_config.NumberColumn(format="%.0f%%"),
                         },
                         hide_index=True)

        with st.expander("Presencia de ofertas · marcas seleccionadas", expanded=True):
            st.markdown('<div class="chart-note">✓ = hubo oferta ese período · — = sin oferta</div>',
                        unsafe_allow_html=True)
            _marcas_of2_base = df_full[
                df_full["Periodo"].isin(_periodos_of_activos)
                & df_full["Cadena"].isin(cadenas_sel)
                & df_full["Variedad"].isin(variedades_sel)
                & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
                & df_full["Envase"].isin(envases_sel)
            ].copy()
            if _of_var_sel != "Todas":
                _marcas_of2_base = _marcas_of2_base[_marcas_of2_base["Variedad"] == _of_var_sel]
            if _of_gram_key:
                _marcas_of2_base = _marcas_of2_base[_marcas_of2_base["Gramaje"] == _of_gram_key]
            if _of_envase_sel != "Todos":
                _marcas_of2_base = _marcas_of2_base[_marcas_of2_base["Envase"] == _of_envase_sel]

            _marcas_of2_disp = sorted(_marcas_of2_base["Marca"].dropna().unique(), key=marca_sort_key_ac)
            _marcas_of2_default = [m for m in ["La Toscana", "Castell", "Nucete"] if m in _marcas_of2_disp]
            if not _marcas_of2_default:
                _marcas_of2_default = _marcas_of2_disp[:3]

            _of2_fa, _of2_fb, _of2_fc = st.columns([2.2, 1.6, 1.2])
            with _of2_fa:
                _marcas_of2_sel = st.multiselect("Marca", _marcas_of2_disp,
                                                 default=_marcas_of2_default,
                                                 key="of2_marcas_aceitunas",
                                                 placeholder="Elegí marcas")
            _cadenas_of2_disp = sorted(_marcas_of2_base["Cadena"].dropna().unique())
            with _of2_fb:
                _cadenas_of2_sel = st.multiselect("Cadena", _cadenas_of2_disp,
                                                  default=_cadenas_of2_disp,
                                                  key="of2_cadenas_aceitunas",
                                                  placeholder="Todas las cadenas")
            with _of2_fc:
                _of2_gran = st.selectbox("Temporalidad", ["Semanal", "Mensual"], key="of2_gran_aceitunas")

            _marcas_of2_act = _marcas_of2_sel if _marcas_of2_sel else _marcas_of2_default
            _cadenas_of2_act = _cadenas_of2_sel if _cadenas_of2_sel else _cadenas_of2_disp
            _df_dest = _marcas_of2_base[
                _marcas_of2_base["Marca"].isin(_marcas_of2_act)
                & _marcas_of2_base["Cadena"].isin(_cadenas_of2_act)
            ].copy()

            if _df_dest.empty:
                st.info("No hay SKUs para las marcas seleccionadas con estos filtros.")
            else:
                if _of2_gran == "Mensual":
                    _df_dest["_col_per"] = pd.to_datetime(_df_dest["Fecha"]).dt.strftime("%b %Y")
                    _pers_dest_ord = [
                        ts.strftime("%b %Y")
                        for ts in sorted(pd.to_datetime(_df_dest["Fecha"]).dt.to_period("M").dt.to_timestamp().unique())
                    ]
                else:
                    _df_dest["_col_per"] = _df_dest["Periodo"]
                    _pers_dest_ord = [p for p in _orden_per_of5 if p in set(_df_dest["Periodo"])]

                _of_mask_dest = (
                    df_full["En_oferta"]
                    & df_full["Marca"].isin(_marcas_of2_act)
                    & df_full["Periodo"].isin(_periodos_of_activos)
                    & df_full["Cadena"].isin(_cadenas_of2_act)
                    & df_full["Variedad"].isin(variedades_sel)
                    & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
                    & df_full["Envase"].isin(envases_sel)
                )
                if _of_var_sel != "Todas":
                    _of_mask_dest &= df_full["Variedad"].eq(_of_var_sel)
                if _of_gram_key:
                    _of_mask_dest &= df_full["Gramaje"].eq(_of_gram_key)
                if _of_envase_sel != "Todos":
                    _of_mask_dest &= df_full["Envase"].eq(_of_envase_sel)

                _df_of_mask = df_full[_of_mask_dest].copy()
                if _of2_gran == "Mensual":
                    _df_of_mask["_col_per"] = pd.to_datetime(_df_of_mask["Fecha"]).dt.strftime("%b %Y")
                else:
                    _df_of_mask["_col_per"] = _df_of_mask["Periodo"]

                _skus_dest = sorted(_df_dest["SKU_canonico"].dropna().unique())
                _of_set = set(zip(_df_of_mask["SKU_canonico"], _df_of_mask["_col_per"]))
                _hmap_rows = []
                for _sk in _skus_dest:
                    _row = {"SKU": _sk}
                    for _pe in _pers_dest_ord:
                        _row[_pe] = "✓" if (_sk, _pe) in _of_set else "—"
                    _hmap_rows.append(_row)
                _hmap_df = pd.DataFrame(_hmap_rows).set_index("SKU")
                _hmap_num = _hmap_df.applymap(lambda x: 1.0 if x == "✓" else 0.0)
                _cell_h = 24
                _header_h = 50
                _oh_h = max(120, len(_skus_dest) * _cell_h + _header_h + 20)
                fig_oh = go.Figure(go.Heatmap(
                    z=_hmap_num.values,
                    x=_pers_dest_ord,
                    y=_hmap_num.index.tolist(),
                    text=_hmap_df.values,
                    texttemplate="%{text}",
                    colorscale=[[0, "#F1F5F9"], [1, "#15803D"]],
                    zmin=0,
                    zmax=1,
                    showscale=False,
                    xgap=2,
                    ygap=2,
                    textfont=dict(size=11, color="#111827"),
                ))
                fig_oh.update_layout(**_BASE_CORE, height=_oh_h, margin=dict(l=10, r=10, t=10, b=10),
                                     xaxis=dict(tickfont=dict(size=10, color="#374151"), tickangle=-30, side="top"),
                                     yaxis=dict(tickfont=dict(size=10, color="#374151"), autorange="reversed"))
                st.plotly_chart(fig_oh, use_container_width=True)


if False and active_page == "Comparativa":
    st.markdown('<div class="chart-note">Seleccioná dos marcas y luego un SKU de cada una para comparar su precio de góndola en el tiempo</div>',
                unsafe_allow_html=True)
    _cmp_f1, _cmp_f2, _cmp_f3, _ = st.columns([1.2, 1.2, 1.2, 2.4])
    with _cmp_f1:
        _cmp_var = st.selectbox("Variedad", ["Todas"] + variedades_disp, key="cmp_var_aceitunas")
    with _cmp_f2:
        _cmp_gram = st.selectbox("Gramaje", ["Todos"] + grupos_labels, key="cmp_gram_aceitunas")
    with _cmp_f3:
        _cmp_envase = st.selectbox("Envase", ["Todos"] + envases_disp, key="cmp_envase_aceitunas")

    _cmp_gram_key = None
    if _cmp_gram != "Todos":
        _cmp_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _cmp_gram), None)

    _cmp_base = dff.dropna(subset=["Marca", "SKU_canonico", "_met"]).copy()
    if _cmp_var != "Todas":
        _cmp_base = _cmp_base[_cmp_base["Variedad"] == _cmp_var]
    if _cmp_gram_key:
        _cmp_base = _cmp_base[_cmp_base["Gramaje"] == _cmp_gram_key]
    if _cmp_envase != "Todos":
        _cmp_base = _cmp_base[_cmp_base["Envase"] == _cmp_envase]

    if _cmp_base.empty:
        st.info("No hay datos comparables con los filtros actuales.")
    else:
        marcas_comp = sorted(_cmp_base["Marca"].dropna().unique(), key=marca_sort_key_ac)
        col_m1, col_m2 = st.columns(2, gap="large")
        with col_m1:
            st.markdown("**Marca 1**")
            marca_c1 = st.selectbox("Marca 1", marcas_comp, key="comp_marca1_aceitunas", label_visibility="collapsed")
            skus_c1 = sorted(_cmp_base[_cmp_base["Marca"] == marca_c1]["SKU_canonico"].dropna().unique())
            sku_c1 = st.selectbox("SKU 1", skus_c1, key="comp_sku1_aceitunas", label_visibility="collapsed")
        with col_m2:
            st.markdown("**Marca 2**")
            default_m2 = marcas_comp[1] if len(marcas_comp) > 1 else marcas_comp[0]
            idx_m2 = marcas_comp.index(default_m2)
            marca_c2 = st.selectbox("Marca 2", marcas_comp, index=idx_m2, key="comp_marca2_aceitunas", label_visibility="collapsed")
            skus_c2 = sorted(_cmp_base[_cmp_base["Marca"] == marca_c2]["SKU_canonico"].dropna().unique())
            sku_c2 = st.selectbox("SKU 2", skus_c2, key="comp_sku2_aceitunas", label_visibility="collapsed")

        orden_per8 = sorted(_cmp_base["Periodo"].unique(),
                            key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min())

        def sku_evol(sku_name: str, label: str) -> pd.DataFrame:
            df_s = (_cmp_base[_cmp_base["SKU_canonico"] == sku_name]
                    .groupby("Periodo")["_met"].mean().reset_index())
            df_s["Periodo"] = pd.Categorical(df_s["Periodo"], categories=orden_per8, ordered=True)
            df_s["SKU"] = label
            return df_s

        def sku_oferta_por_periodo(sku_name: str) -> set[str]:
            return set(_cmp_base[(_cmp_base["SKU_canonico"] == sku_name) & _cmp_base["En_oferta"]]["Periodo"].unique())

        lbl1 = sku_c1
        lbl2 = sku_c2
        df_comp = pd.concat([sku_evol(sku_c1, lbl1), sku_evol(sku_c2, lbl2)], ignore_index=True)
        _of_pers1 = sku_oferta_por_periodo(sku_c1)
        _of_pers2 = sku_oferta_por_periodo(sku_c2)

        if df_comp.empty:
            st.info("No hay datos de evolución para los SKUs seleccionados.")
        else:
            color1 = color_marca_real_ac(marca_c1)
            color2 = color_marca_real_ac(marca_c2) if marca_c2 != marca_c1 else "#C73E1D"
            fig = px.line(df_comp, x="Periodo", y="_met", color="SKU", markers=True,
                          color_discrete_map={lbl1: color1, lbl2: color2},
                          labels={"_met": _met_lbl, "Periodo": ""}, height=420)
            fig.update_traces(line=dict(width=3), marker=dict(size=8))

            df_ev1 = sku_evol(sku_c1, lbl1)
            df_ev2 = sku_evol(sku_c2, lbl2)
            df_ev1_of = df_ev1[df_ev1["Periodo"].isin(_of_pers1)]
            df_ev2_of = df_ev2[df_ev2["Periodo"].isin(_of_pers2)]
            if not df_ev1_of.empty:
                fig.add_trace(go.Scatter(x=df_ev1_of["Periodo"], y=df_ev1_of["_met"], mode="markers",
                                         name=f"{lbl1} · en oferta",
                                         marker=dict(symbol="star", size=16, color=color1,
                                                     line=dict(color="#fff", width=1.5))))
            if not df_ev2_of.empty:
                fig.add_trace(go.Scatter(x=df_ev2_of["Periodo"], y=df_ev2_of["_met"], mode="markers",
                                         name=f"{lbl2} · en oferta",
                                         marker=dict(symbol="star", size=16, color=color2,
                                                     line=dict(color="#fff", width=1.5))))
            fig.update_layout(**BASE,
                              yaxis=dict(title=_met_lbl, tickprefix="$", tickformat=",",
                                         tickfont=dict(size=12, color="#111827")),
                              xaxis=dict(tickfont=dict(size=12, color="#111827")))
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Semanas en oferta", expanded=True):
                _of_rows = []
                for _pe in orden_per8:
                    _of_rows.append({"Período": _pe, lbl1[:35]: "✓" if _pe in _of_pers1 else "—",
                                     lbl2[:35]: "✓" if _pe in _of_pers2 else "—"})
                st.dataframe(pd.DataFrame(_of_rows), height=min(400, len(orden_per8) * 38 + 60), hide_index=True)

            with st.expander("Precio por cadena y período", expanded=True):
                st.markdown(f'<div class="chart-note">{_met_lbl} promedio por cadena en cada semana/mes</div>',
                            unsafe_allow_html=True)

                def _cad_per_heatmap(sku_name: str, label: str, color_hi: str) -> None:
                    _df_cp = (_cmp_base[_cmp_base["SKU_canonico"] == sku_name]
                              .groupby(["Cadena", "Periodo"])["_met"].mean().round(0).unstack("Periodo"))
                    _df_cp = _df_cp.reindex(columns=[p for p in orden_per8 if p in _df_cp.columns])
                    if _df_cp.empty:
                        st.info(f"Sin datos para {label[:40]}")
                        return
                    _txt_cp = [[f"${v:,.0f}" if not pd.isna(v) else "—" for v in row] for row in _df_cp.values]
                    _vmin = float(_df_cp.min().min()) if not _df_cp.empty else 0
                    _vmax = float(_df_cp.max().max()) if not _df_cp.empty else 1
                    _fig_cp = go.Figure(go.Heatmap(
                        z=_df_cp.values, x=_df_cp.columns.tolist(), y=_df_cp.index.tolist(),
                        colorscale=[[0, "#D1FAE5"], [0.5, "#34D399"], [1, color_hi]],
                        zmin=_vmin, zmax=_vmax, text=_txt_cp, texttemplate="%{text}",
                        textfont=dict(size=12, color="#111827"), showscale=False,
                    ))
                    _fig_cp.update_layout(**_BASE_CORE, height=max(220, len(_df_cp) * 44 + 100),
                                          margin=dict(l=10, r=10, t=50, b=10),
                                          title=dict(text=label[:50], font=dict(size=12, color="#374151"), x=0.01),
                                          xaxis=dict(tickfont=dict(size=11, color="#111827"), side="top", tickangle=-25),
                                          yaxis=dict(tickfont=dict(size=12, color="#111827")))
                    st.plotly_chart(_fig_cp, use_container_width=True)

                _col_cp1, _col_cp2 = st.columns(2, gap="large")
                with _col_cp1:
                    _cad_per_heatmap(sku_c1, lbl1, "#065F46")
                with _col_cp2:
                    _cad_per_heatmap(sku_c2, lbl2, "#7C1D2D")

            with st.expander("Precio por cadena · último período disponible", expanded=True):
                ult_per8 = orden_per8[-1] if orden_per8 else None
                if ult_per8:
                    df_cmp_tbl = _cmp_base[
                        (_cmp_base["Periodo"] == ult_per8)
                        & (_cmp_base["SKU_canonico"].isin([sku_c1, sku_c2]))
                    ][["Cadena", "SKU_canonico", "Variedad", "Envase", "Gramaje", "_met", "En_oferta"]].copy()
                    df_cmp_tbl.columns = ["Cadena", "SKU", "Variedad", "Envase", "Gramaje",
                                          "$/kg góndola" if _met_kg else "Precio góndola ($)", "En oferta"]
                    st.dataframe(
                        df_cmp_tbl.sort_values(["SKU", "Cadena"]),
                        height=320,
                        column_config={
                            "$/kg góndola" if _met_kg else "Precio góndola ($)": st.column_config.NumberColumn(format="$%d"),
                            "En oferta": st.column_config.CheckboxColumn(),
                        },
                        hide_index=True,
                    )

            if df_comp["Periodo"].nunique() > 1:
                with st.expander("Diferencia de precio entre SKUs por período", expanded=True):
                    st.markdown('<div class="chart-note">Verde = SKU 1 más barato · Rojo = SKU 2 más barato</div>',
                                unsafe_allow_html=True)
                    piv_comp = df_comp.pivot(index="Periodo", columns="SKU", values="_met")
                    if lbl1 in piv_comp.columns and lbl2 in piv_comp.columns:
                        piv_comp["Diferencia"] = piv_comp[lbl1] - piv_comp[lbl2]
                        piv_comp = piv_comp.dropna(subset=["Diferencia"]).reset_index()
                        fig = go.Figure(go.Bar(
                            x=piv_comp["Periodo"], y=piv_comp["Diferencia"],
                            marker_color=["#00B050" if v <= 0 else "#EF4444" for v in piv_comp["Diferencia"]],
                            text=[f"${v:+,.0f}" for v in piv_comp["Diferencia"]],
                            textposition="outside", textfont=dict(size=12, color="#111827"), cliponaxis=False,
                        ))
                        fig.update_layout(**_BASE_CORE, height=320, margin=dict(l=10, r=10, t=60, b=40),
                                          xaxis=dict(tickfont=dict(size=12, color="#111827"), tickangle=-20),
                                          yaxis=dict(title=f"Diferencia ({_met_lbl})", tickprefix="$",
                                                     tickformat=",", tickfont=dict(size=12, color="#111827")),
                                          showlegend=False,
                                          shapes=[dict(type="line", x0=-0.5, x1=len(piv_comp) - 0.5, y0=0, y1=0,
                                                       line=dict(color="#9CA3AF", width=1.5, dash="dot"))],
                                          title=dict(text=f"{lbl1[:30]} vs {lbl2[:30]}",
                                                     font=dict(size=12, color="#6B7280"), x=0.01))
                        st.plotly_chart(fig, use_container_width=True)

import math
import re
import sqlite3
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from aceitunas_catalogo_manual import (
    ENVASES_VALIDOS,
    buscar_gramaje_unificado_catalogo,
    gramaje_a_grupo_aceituna,
    gramaje_grupo_label_aceituna,
    resolver_envase_catalogo,
)
from dashboard_unificado_helpers import (
    COMMON_DASHBOARD_SECTIONS,
    PLOTLY_FONT_FAMILY,
    render_sidebar_section_switcher,
    unified_mode_enabled,
)
from tracker_paths import precios_db_path

DIRECTORIO = Path(__file__).parent
DB_PATH = precios_db_path()
UNIFIED_MODE = unified_mode_enabled()

_PALABRAS_EXCLUIR_DASH_AC = [
    "empanada", "pizza", "relleno para",
    "pasta de aceituna", "pasta aceitunas", "pasta de aceitunas",
    "tapenade", "paté de", "pate de", "pasta para untar",
    "aceite de oliva", "aceite oliva",
    "sandwich", "sandwiche", "sándwich",
    "ciabata", "ciabatta",
]


def _normalizar_ac(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", (texto or "").lower())
        if not unicodedata.combining(c)
    )


def es_producto_aceituna(nombre: str) -> bool:
    n = _normalizar_ac(nombre)
    m_ac = re.search(r"aceitun[ao]", n)
    if not m_ac:
        return False
    m_q = re.search(r"\bqueso\b", n)
    if m_q and m_q.start() < m_ac.start():
        return False
    if re.match(r"pasta\b", n):
        return False
    if any(_normalizar_ac(excl) in n for excl in _PALABRAS_EXCLUIR_DASH_AC):
        return False
    return True

# ---------------------------------------------------------------------------
# Marcas
# ---------------------------------------------------------------------------

MARCAS_DESTACADAS_AC = {"Castell", "Nucete", "La Toscana", "Morixe", "Oliovita", "Vanoli"}
MARCAS_SUPER_AC = {
    "Carrefour", "Jumbo", "Disco", "Vea", "Día", "Coto",
    "Chango Más", "Chango Mas", "La Anónima", "La Anonima",
    "Delicious",   # marca propia de Día
}

COLORES_MARCA_AC = {
    "Castell":     "#2E86AB",
    "Nucete":      "#3B1F2B",
    "La Toscana":  "#B45309",
    "Morixe":      "#16A34A",
    "Oliovita":    "#F18F01",
    "Vanoli":      "#A23B72",
    "Marca Propia":"#6B7280",
    "Otras":       "#9CA3AF",
}

ORDEN_MARCAS_AC = [
    "Castell", "Nucete", "La Toscana", "Morixe", "Oliovita", "Vanoli",
    "Marca Propia", "Otras",
]

_MARCAS_AGREGADAS_EXCLUIDAS_AC = {"Otras", "Marca Propia", "Desconocida", "", None}


# Correcciones directas: DB tiene un nombre incorrecto → nombre real
_MARCA_CORRECCIONES: dict[str, str] = {
    "Toscana":          "La Toscana",
    "Trozos":           "Marvavic",
    "Gordal":           "Ybarra",
    "Premium":          "Castell",
    "La Malaguena":     "La Malagueña",
    "Malagueña":        "La Malagueña",
    "Malague\xf1a":     "La Malagueña",   # encoding fix
}

# Extracciones del scraper que NO son marcas (alimentos, descriptores, preparaciones)
# → se descartan y quedan como Marca Propia de la cadena
_PALABRAS_NO_MARCA: set[str] = {
    # Variedades / preparaciones
    "Manzanilla", "Enteras", "Entera", "Descarozada", "Descarozadas",
    "Descarozado", "Carozo", "Rodajas", "Trozos", "Picadas",
    "Rellenas", "Rellena", "Rell.con",
    # Sabores / rellenos
    "Ajo", "Anchoas", "Jalapeños", "Jalapeño", "Pimiento", "Pimientos",
    "Morrones", "Morron", "Morrón", "C/morrón", "Salmon", "Salmón", "Salm",
    "Queso", "Parmesano", "Jamón", "Jamon", "Pasta", "Picantes", "Picante",
    "Ahumado", "Ahumada",
    # Tipos de envase confundidos como marca
    "Doy", "Check",
    # Calificativos / adjetivos
    "Clásica", "Clásicas", "Clasica", "Clasicas", "Orgánicas", "Organicas",
    "Naturales", "Españolas", "Espanolas", "Ver", "Negr", "Palmitos",
    "Alcaparras",
    # Palabras genéricas
    "Aceitunas", "Aceitunas.verdes",
}


def limpiar_marca_ac(marca: str, cadena: str) -> str:
    """Corrige el nombre de marca extraído por el scraper."""
    # Correcciones directas
    if marca in _MARCA_CORRECCIONES:
        return _MARCA_CORRECCIONES[marca]
    # Palabras que no son marcas (ingredientes, descriptores) → Marca Propia de la cadena
    if marca in _PALABRAS_NO_MARCA:
        return cadena
    return marca


def categorizar_marca_ac(marca: str) -> str:
    if marca in MARCAS_DESTACADAS_AC:
        return marca
    if marca in MARCAS_SUPER_AC:
        return "Marca Propia"
    return "Otras"


# ---------------------------------------------------------------------------
# Variedades unificadas
# ---------------------------------------------------------------------------

_VARIEDAD_REGLAS_DASH_AC: list[tuple[re.Pattern, str]] = [
    (re.compile(r"negra[s]?\s+descor\b|negra[s]?\s+des?carozada[s]?", re.IGNORECASE), "Negra Descarozada"),
    (re.compile(r"negra[s]?\s+(?:en\s+)?rodaj", re.IGNORECASE), "Negra Rodajada"),
    (re.compile(r"negra[s]?", re.IGNORECASE), "Negra"),
    (re.compile(r"rellena[s]?\s+(?:con\s+)?queso", re.IGNORECASE), "Verde Rellena Queso"),
    (re.compile(r"rellena[s]?\s+(?:con\s+)?salmon", re.IGNORECASE), "Verde Rellena Salmón"),
    (re.compile(r"rellena[s]?\s+(?:con\s+)?anchoa[s]?", re.IGNORECASE), "Verde Rellena Anchoas"),
    (re.compile(r"rellena[s]?\s+(?:con\s+)?morron(?:es)?", re.IGNORECASE), "Verde Rellena Morrón"),
    (re.compile(r"rellena[s]?", re.IGNORECASE), "Verde Rellena Morrón"),
    (re.compile(r"(?:con\s+)?ajo\b", re.IGNORECASE), "Verde con Ajo"),
    (re.compile(r"picante[s]?", re.IGNORECASE), "Verde Picante"),
    (re.compile(r"ahumad[ao]s?", re.IGNORECASE), "Verde Ahumada"),
    (re.compile(r"(?:en\s+)?rodaj", re.IGNORECASE), "Verde Rodajada"),
    (re.compile(r"des?carozada[s]?|descor\b", re.IGNORECASE), "Verde Descarozada"),
    (re.compile(r"saborizada[s]?", re.IGNORECASE), "Verde Saborizada"),
    (re.compile(r"kalamata", re.IGNORECASE), "Kalamata"),
    (re.compile(r"mix\b|mixta[s]?\b|combinad[ao]|surtid[ao]|variedad", re.IGNORECASE), "Mix"),
]


def ajustar_variedad_raw_ac(nombre: str, variedad_actual: str | None) -> str:
    actual = variedad_actual or "Verde"
    for patron, variedad in _VARIEDAD_REGLAS_DASH_AC:
        if patron.search(_normalizar_ac(nombre)):
            return variedad
    return actual


def unificar_variedad(v: str | None) -> str:
    if v is None:
        return "Verde con carozo"
    if "Rellena" in v:
        return "Rellenas"
    if v in ("Verde Picante", "Verde con Ajo", "Verde Ahumada", "Verde Saborizada"):
        return "Saborizadas"
    if v == "Verde":
        return "Verde con carozo"
    if v == "Negra":
        return "Negra con carozo"
    return v  # Verde Descarozada, Negra Descarozada, Kalamata, Mix, etc.


COLORES_VARIEDAD = {
    "Verde con carozo":  "#4CAF50",
    "Verde Descarozada": "#81C784",
    "Verde Rodajada":    "#66BB6A",
    "Negra con carozo":  "#212121",
    "Negra Descarozada": "#424242",
    "Negra Rodajada":    "#616161",
    "Rellenas":          "#FF7043",
    "Saborizadas":       "#795548",
    "Kalamata":          "#4A148C",
    "Mix":               "#90A4AE",
}

COLORS_CADENAS = {
    "Carrefour": "#004B9B", "Jumbo": "#E63329", "Disco": "#00A651",
    "Vea": "#F7931E", "Día": "#ED1C24", "Chango Mas": "#7B2D8B",
    "Coto": "#002D72", "La Anonima": "#C8102E",
}

GRAMAJE_GRUPOS = [
    "1) hasta 140g", "2) 141-230g", "3) 231-330g",
    "4) 331-400g",   "5) 401-600g", "6) 601g+",
]
GRAMAJE_GRUPOS_LABELS = {
    "1) hasta 140g": "hasta 140g", "2) 141-230g": "141-230g",
    "3) 231-330g":   "231-330g",   "4) 331-400g": "331-400g",
    "5) 401-600g":   "401-600g",   "6) 601g+":    "601g+",
}


def gramaje_grupo_label(g): return gramaje_grupo_label_aceituna(g)


# ---------------------------------------------------------------------------
# Detección de envase (Doypack / Frasco / Lata / Bandeja / Sin detectar)
# ---------------------------------------------------------------------------

_DOYPACK_TOKENS = {"doypack", "doy", "dp", "sachet", "pouch", "pou", "flexible", "bolsa", "sobre"}
_FRASCO_TOKENS  = {"frasco", "fco", "frco", "vidrio", "pote"}
_LATA_TOKENS    = {"lata", "bote", "tarro"}

_ENVASE_EXCEL   = DIRECTORIO / "revision_envase.xlsx"
_ENVASE_OVERRIDES: dict[str, str] = {}

def _cargar_overrides_envase():
    """Carga las correcciones manuales del Excel de revisión."""
    if not _ENVASE_EXCEL.exists():
        return
    try:
        df_sin = pd.read_excel(_ENVASE_EXCEL, sheet_name="Sin_detectar_REVISAR")
        corr_col = next((c for c in df_sin.columns if "orre" in c.lower()), None)
        if corr_col and "Producto" in df_sin.columns:
            for _, row in df_sin.iterrows():
                prod = str(row["Producto"]).strip()
                val  = str(row[corr_col]).strip() if pd.notna(row[corr_col]) else ""
                if prod and val and val not in ("", "nan"):
                    _ENVASE_OVERRIDES[prod] = val
    except Exception:
        pass

_cargar_overrides_envase()


def _tokenize_ac(text: str) -> list[str]:
    return re.findall(r"[a-záéíóúüñ0-9]+", text.lower())


def detectar_envase_nombre(nombre: str) -> str:
    nombre = (nombre or "").strip()
    # 1) Corrección manual del Excel
    if nombre in _ENVASE_OVERRIDES:
        return _ENVASE_OVERRIDES[nombre]
    # 2) Detección por keywords
    tokens = _tokenize_ac(nombre)
    tok_set = set(tokens)
    doy_hits, fra_hits, lat_hits = [], [], []
    for t in _DOYPACK_TOKENS:
        if t == "doy":
            if "doy" in tok_set:
                doy_hits.append("doy")
        elif t in tok_set:
            doy_hits.append(t)
    for t in _FRASCO_TOKENS:
        if t in tok_set:
            fra_hits.append(t)
    for t in _LATA_TOKENS:
        if t in tok_set:
            lat_hits.append(t)
    total_hits = len(doy_hits) + len(fra_hits) + len(lat_hits)
    if total_hits == 0:
        return "Sin detectar"
    if doy_hits and not fra_hits and not lat_hits:
        return "Doypack"
    if fra_hits and not doy_hits and not lat_hits:
        return "Frasco"
    if lat_hits and not doy_hits and not fra_hits:
        return "Lata"
    return "Sin detectar"


def cc(c): return COLORS_CADENAS.get(c, "#6B7280")
def cv(v): return COLORES_VARIEDAD.get(v, "#9CA3AF")
def cm(m): return COLORES_MARCA_AC.get(m, "#9CA3AF")


def sku_canonico_ac(marca: str, variedad: str, gramos, envase: str | None = None) -> str:
    if marca == "Castell":
        v = (variedad or "").strip()
        if "Ahumad" in v:
            base = "Verde Ahumada"
        elif "Picante" in v:
            base = "Verde Picante"
        elif "Ajo" in v:
            base = "Verde con Ajo"
        elif "Rellena" in v:
            base = "Verde Rellena"
        elif "Rodajada" in v:
            base = "Verde Rodajada"
        elif "Descarozada" in v:
            base = "Verde Descarozada"
        elif "Negra" in v:
            base = "Negra"
        else:
            base = "Verde con carozo"
        grupo = gramaje_grupo_label(gramaje_a_grupo_aceituna(gramos))
        marca_lbl = "Castell Premium" if envase == "Frasco Premium" else "Castell"
        partes = [marca_lbl, base]
        if grupo != "Sin gramaje":
            partes.append(grupo)
        if envase and envase != "Sin detectar":
            partes.append(envase)
        return " · ".join(partes)

    g_lbl = f"{int(gramos)}g" if gramos and not pd.isna(gramos) else "?"
    partes = [marca, variedad, g_lbl]
    if envase and envase != "Sin detectar":
        partes.append(envase)
    return " · ".join(partes)


# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------

def completar_envase_por_familia(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Envase" not in df.columns:
        return df

    base = df[
        df["Envase"].isin(ENVASES_VALIDOS)
        & df["Gramos"].notna()
        & df["Variedad_raw"].notna()
    ].copy()
    if base.empty:
        return df

    base["Gramos"] = base["Gramos"].astype(int)
    conteos = (
        base.groupby(["Marca", "Variedad_raw", "Gramos", "Envase"])
        .size()
        .reset_index(name="n")
    )

    mapa_familia: dict[tuple[str, str, int], str] = {}
    for (marca, variedad, gramos), grp in conteos.groupby(["Marca", "Variedad_raw", "Gramos"]):
        grp = grp.sort_values(["n", "Envase"], ascending=[False, True]).reset_index(drop=True)
        if len(grp) == 1 or grp.loc[0, "n"] >= grp.loc[1, "n"] * 2:
            mapa_familia[(marca, variedad, int(gramos))] = grp.loc[0, "Envase"]

    if not mapa_familia:
        return df

    df = df.copy()
    mask = (
        df["Envase"].eq("Sin detectar")
        & df["Gramos"].notna()
        & df["Variedad_raw"].notna()
    )
    if not mask.any():
        return df

    for idx in df.index[mask]:
        key = (
            df.at[idx, "Marca"],
            df.at[idx, "Variedad_raw"],
            int(df.at[idx, "Gramos"]),
        )
        envase = mapa_familia.get(key)
        if envase:
            df.at[idx, "Envase"] = envase

    return df


if not UNIFIED_MODE:
    st.set_page_config(
        page_title="Aceitunas Tracker | Monitor de Precios",
        page_icon="🫒", layout="wide", initial_sidebar_state="expanded",
    )

# ---------------------------------------------------------------------------
# Contraseña
# ---------------------------------------------------------------------------

_MAX_INTENTOS = 5


def _check_password():
    if st.session_state.get("_pwd_ok", False):
        return True
    intentos = st.session_state.get("_intentos", 0)
    if intentos >= _MAX_INTENTOS:
        st.error("Demasiados intentos fallidos. Cerrá y volvé a abrir el navegador.")
        st.stop()
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;
                justify-content:center;min-height:60vh;gap:1.2rem">
      <div style="font-size:2.5rem">🫒</div>
      <div style="font-size:1.5rem;font-weight:800;color:#0F172A">Aceitunas Tracker</div>
      <div style="font-size:0.9rem;color:#6B7280">Ingresá la contraseña para continuar</div>
    </div>
    """, unsafe_allow_html=True)
    if DB_PATH != DIRECTORIO / "precios.db":
        st.caption(f"Modo copia · DB: {DB_PATH.name}")
    _, col, _ = st.columns([2, 1.5, 2])
    with col:
        pwd = st.text_input("Contraseña", type="password",
                            label_visibility="collapsed", placeholder="Contraseña…")
        if st.button("Entrar", use_container_width=True, type="primary"):
            correct = st.secrets.get("PASSWORD", "")
            if pwd and pwd == correct:
                st.session_state["_pwd_ok"] = True
                st.session_state["_intentos"] = 0
                st.rerun()
            else:
                st.session_state["_intentos"] = intentos + 1
                restantes = _MAX_INTENTOS - st.session_state["_intentos"]
                if restantes > 0:
                    st.error(f"Contraseña incorrecta ({restantes} intento{'s' if restantes != 1 else ''} restante{'s' if restantes != 1 else ''})")
                else:
                    st.rerun()
    st.stop()


if not UNIFIED_MODE:
    _check_password()

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap');
html,body,[class*="css"],.stApp{font-family:'Montserrat',sans-serif!important}

:root{
    --green:#16A34A;--green-light:#22C55E;--green-neon:#4ADE80;
    --green-glow:rgba(22,163,74,0.4);--green-bg:#DCFCE7;
    --white:#FFFFFF;--off-white:#F8FAFC;
    --gray-50:#F9FAFB;--gray-100:#F1F5F9;--gray-200:#E2E8F0;
    --gray-400:#94A3B8;--gray-600:#475569;--gray-900:#0F172A;
    --purple:hsl(261deg 80% 48%);--sidebar-w:230px
}

.stApp{
    background:var(--off-white);
    background-image:
        radial-gradient(ellipse at var(--mx,30%) var(--my,20%),rgba(22,163,74,0.07) 0%,transparent 55%),
        radial-gradient(ellipse at 85% 85%,rgba(34,197,94,0.05) 0%,transparent 50%)
}
.block-container{padding:1.2rem 2rem 3rem;max-width:1400px}
#MainMenu,footer,header{visibility:hidden}

/* ── SIDEBAR ALWAYS OPEN ── */
[data-testid="stSidebar"]{
    background:#FFFFFF!important;
    border-right:1px solid var(--gray-200)!important;
    box-shadow:4px 0 24px rgba(0,0,0,0.06)!important;
    min-width:var(--sidebar-w)!important;
    max-width:var(--sidebar-w)!important;
    transform:translateX(0)!important
}
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"]{display:none!important;visibility:hidden!important}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p{color:#374151!important}

/* ── SIDEBAR LOGO ── */
.sidebar-logo{font-size:1.1rem;font-weight:800;color:var(--gray-900);letter-spacing:-0.5px;line-height:1.3}
.sidebar-logo .accent{color:var(--green);text-shadow:0 0 20px rgba(22,163,74,0.5)}
.sidebar-sub{font-size:0.66rem;color:var(--gray-400);margin-bottom:0.25rem}
.sidebar-sep{font-size:0.57rem;font-weight:700;text-transform:uppercase;letter-spacing:1.3px;color:var(--gray-400);margin:0.85rem 0 0.28rem;padding-bottom:0.25rem;border-bottom:1px solid var(--gray-200)}

/* ── NAV RADIO AS SIDE MENU ── */
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"]{
    padding:0.38rem 0.65rem!important;border-radius:8px!important;
    align-items:center!important;cursor:pointer!important;margin:1px 0!important;
    border-left:3px solid transparent!important;transition:all 0.2s ease!important
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"]:hover{
    background:rgba(22,163,74,0.07)!important;
    border-left:3px solid rgba(22,163,74,0.4)!important;
    transform:translateX(2px)!important
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"]{
    background:linear-gradient(135deg,#DCFCE7,#BBF7D0)!important;
    border-left:4px solid var(--green)!important;
    box-shadow:0 0 20px rgba(22,163,74,0.3),0 4px 12px rgba(22,163,74,0.2)!important;
    transform:translateX(4px)!important;
    margin-left:-1px!important;
    animation:navPressed 0.35s cubic-bezier(.36,.07,.19,.97) both!important
}
@keyframes navPressed{
    0%  {transform:translateX(0) scale(1)}
    20% {transform:translateX(8px) scale(0.96)}
    50% {transform:translateX(3px) scale(0.98)}
    75% {transform:translateX(5px) scale(1.01)}
    100%{transform:translateX(4px) scale(1)}
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] p{
    color:var(--green)!important;font-weight:800!important;
    text-shadow:0 0 12px rgba(22,163,74,0.4)!important;
    font-size:0.88rem!important
}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"] > div:first-child{display:none!important}
[data-testid="stSidebar"] [data-testid="stRadio"] p{font-size:0.82rem!important;font-weight:500!important;color:#374151!important;margin:0!important;transition:color 0.2s!important}

/* ── HEADER ── */
.main-header{
    background:linear-gradient(120deg,#064E3B 0%,#065F46 30%,#047857 60%,#059669 100%);
    background-size:300% 300%;
    animation:headerShimmer 10s ease infinite,fadeInDown 0.6s ease;
    padding:1.6rem 2.2rem;border-radius:24px;margin-bottom:1.5rem;
    display:flex;align-items:center;justify-content:space-between;
    box-shadow:0 12px 40px rgba(6,79,67,0.35),0 0 0 1px rgba(74,222,128,0.2);
    position:relative;overflow:hidden;
    transition:box-shadow 0.4s ease,transform 0.3s ease
}
.main-header:hover{
    box-shadow:0 20px 60px rgba(6,79,67,0.45),0 0 40px rgba(74,222,128,0.2);
    transform:translateY(-2px)
}
.main-header::before{
    content:'';position:absolute;top:-60%;right:-8%;width:350px;height:350px;
    background:radial-gradient(circle,rgba(74,222,128,0.2),transparent 65%);
    pointer-events:none;animation:float 6s ease-in-out infinite
}
.main-header::after{
    content:'';position:absolute;bottom:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,transparent,#4ADE80,#BBFDE8,#4ADE80,transparent);
    animation:shimmerLine 3s linear infinite
}
.header-eyebrow{font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:rgba(187,253,232,0.7);margin-bottom:0.3rem}
.header-left h1{font-size:1.6rem;font-weight:900;color:#fff;margin:0;letter-spacing:-0.8px;text-shadow:0 0 40px rgba(74,222,128,0.4)}
.header-left p{font-size:0.78rem;color:rgba(187,253,232,0.65);margin:0.25rem 0 0}
.header-right{display:flex;flex-direction:column;align-items:flex-end;gap:0.6rem}
.header-badge{
    background:rgba(74,222,128,0.15);border:1px solid rgba(74,222,128,0.4);
    border-radius:50px;padding:0.3rem 1rem;color:#fff!important;font-size:0.75rem;font-weight:700;
    animation:glowPulse 3s ease infinite;backdrop-filter:blur(8px)
}
.header-link-btn{
    background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.25);
    border-radius:50px;padding:0.32rem 1rem;color:#fff!important;font-size:0.73rem;font-weight:700;
    text-decoration:none;letter-spacing:0.5px;transition:all 0.3s ease;
    backdrop-filter:blur(8px)
}
.header-link-btn:hover{
    background:rgba(255,255,255,0.22);border-color:rgba(74,222,128,0.5);
    color:#fff!important;box-shadow:0 0 16px rgba(74,222,128,0.3);transform:scale(1.05)
}

/* ── KPI CARDS ── */
.kpi-card{
    background:#fff;border-radius:20px;padding:1.4rem 1.5rem;
    box-shadow:0 4px 20px rgba(0,0,0,0.07);border-top:4px solid var(--gray-200);
    display:flex;flex-direction:column;
    transition:all 0.35s cubic-bezier(0.34,1.56,0.64,1);
    cursor:default;transform-style:preserve-3d;position:relative;overflow:hidden;
    animation:fadeInUp 0.5s ease both
}
.kpi-card:hover{transform:translateY(-6px) scale(1.02);box-shadow:0 20px 48px rgba(0,0,0,0.12),0 0 0 1px rgba(22,163,74,0.12)}
.kpi-card.green{border-top-color:#16A34A}
.kpi-card.green:hover{box-shadow:0 20px 48px rgba(22,163,74,0.2),0 0 32px rgba(22,163,74,0.15)}
.kpi-card.orange{border-top-color:#F59E0B}
.kpi-card.orange:hover{box-shadow:0 20px 48px rgba(245,158,11,0.2),0 0 32px rgba(245,158,11,0.15)}
.kpi-card.purple{border-top-color:#7C3AED}
.kpi-card.purple:hover{box-shadow:0 20px 48px rgba(124,58,237,0.2),0 0 32px rgba(124,58,237,0.15)}
.kpi-card.red{border-top-color:#EF4444}
.kpi-card.red:hover{box-shadow:0 20px 48px rgba(239,68,68,0.2),0 0 32px rgba(239,68,68,0.15)}
.kpi-card.teal{border-top-color:#0D9488}
.kpi-card.yellow{border-top-color:#EAB308}
.kpi-label{font-size:0.59rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--gray-400);margin-bottom:0.5rem}
.kpi-value{font-size:1.8rem;font-weight:900;color:var(--gray-900);line-height:1;transition:color 0.3s}
.kpi-sub{font-size:0.68rem;color:var(--gray-600);margin-top:0.4rem}

/* ── CHART TITLES ── */
.chart-title{font-size:0.78rem;font-weight:700;color:var(--gray-900);margin-bottom:0.7rem;padding-bottom:0.4rem;border-bottom:2px solid #F0FDF4;text-transform:uppercase;letter-spacing:0.6px}
.chart-note{font-size:0.73rem;color:var(--gray-600);margin-top:-0.4rem;margin-bottom:0.75rem}

/* ── EXPANDERS ── */
[data-testid="stExpander"]{background:#fff!important;border:1px solid var(--gray-200)!important;border-radius:16px!important;margin-bottom:0.75rem!important;box-shadow:0 2px 12px rgba(0,0,0,0.05)!important;transition:all 0.3s ease!important}
[data-testid="stExpander"] summary,[data-testid="stExpander"] details > summary,.streamlit-expanderHeader{color:var(--gray-900)!important;font-weight:600!important;background:var(--gray-50)!important;border-radius:16px 16px 0 0!important}
[data-testid="stExpander"] summary *{color:var(--gray-900)!important}
[data-testid="stExpander"] summary:hover{background:#F0FDF4!important}
[data-testid="stExpander"] > div[data-testid="stExpanderDetails"],[data-testid="stExpander"] > div{background:#fff!important}
[data-testid="stExpander"] .element-container,[data-testid="stExpander"] p,[data-testid="stExpander"] span:not([data-testid="collapsedControl"] span){color:var(--gray-900)!important}

/* ── BUTTONS — Uiverse.io style ── */
.stButton > button{
    padding:10px 28px!important;border-radius:50px!important;cursor:pointer!important;
    border:0!important;background-color:white!important;
    box-shadow:rgb(0 0 0/5%) 0 0 8px!important;letter-spacing:1.5px!important;
    text-transform:uppercase!important;font-size:11px!important;
    font-family:'Montserrat',sans-serif!important;font-weight:700!important;
    color:#0F172A!important;transition:all 0.5s ease!important;
    position:relative!important;overflow:hidden!important
}
.stButton > button:hover{
    letter-spacing:3px!important;background-color:hsl(261deg 80% 48%)!important;
    color:hsl(0,0%,100%)!important;box-shadow:rgb(93 24 220) 0px 7px 29px 0px!important
}
.stButton > button:active{
    letter-spacing:3px!important;background-color:hsl(261deg 80% 48%)!important;
    color:hsl(0,0%,100%)!important;box-shadow:rgb(93 24 220) 0px 0px 0px 0px!important;
    transform:translateY(10px)!important;transition:100ms!important
}

/* ── SIDEBAR BUTTONS (compact, no uiverse) ── */
[data-testid="stSidebar"] .stButton > button{
    padding:7px 14px!important;border-radius:10px!important;letter-spacing:0.3px!important;
    text-transform:none!important;font-size:11px!important;font-weight:600!important;
    background:var(--gray-50)!important;color:var(--gray-900)!important;
    box-shadow:0 1px 4px rgba(0,0,0,0.08)!important;border:1px solid var(--gray-200)!important;
    transition:all 0.2s ease!important
}
[data-testid="stSidebar"] .stButton > button:hover{
    background:var(--green-bg)!important;color:var(--green)!important;
    border-color:rgba(22,163,74,0.3)!important;letter-spacing:0.3px!important;
    box-shadow:0 0 12px rgba(22,163,74,0.2)!important;transform:none!important
}
[data-testid="stSidebar"] .stButton > button:active{
    transform:none!important;background:var(--green-bg)!important;
    color:var(--green)!important;box-shadow:none!important
}

/* ── CATEGORY SWITCH BUTTON ── */
.cat-switch-btn{
    display:flex;align-items:center;gap:10px;
    background:linear-gradient(135deg,#064E3B,#065F46);
    border:1px solid rgba(74,222,128,0.25);border-radius:14px;
    padding:0.75rem 1rem;text-decoration:none;
    color:#fff!important;font-size:0.78rem;font-weight:700;
    letter-spacing:0.3px;transition:all 0.3s ease;
    box-shadow:0 4px 15px rgba(6,78,59,0.35);
    position:relative;overflow:hidden;
    margin-top:0.5rem;width:100%;box-sizing:border-box
}
.cat-switch-btn::before{
    content:"";position:absolute;top:-50%;left:-60%;
    width:60%;height:200%;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,0.08),transparent);
    transform:skewX(-20deg);transition:left 0.5s ease
}
.cat-switch-btn:hover::before{left:120%}
.cat-switch-btn:hover{
    background:linear-gradient(135deg,#065F46,#047857);
    box-shadow:0 6px 22px rgba(6,78,59,0.5),0 0 0 1px rgba(74,222,128,0.35);
    transform:translateY(-2px);color:#fff!important
}
.cat-switch-btn:active{transform:translateY(0);box-shadow:0 2px 8px rgba(6,78,59,0.3)}
.cat-switch-icon{font-size:1.4rem;flex-shrink:0}
.cat-switch-text{display:flex;flex-direction:column;gap:1px}
.cat-switch-label{font-size:0.6rem;font-weight:600;opacity:0.75;text-transform:uppercase;letter-spacing:1px}
.cat-switch-name{font-size:0.82rem;font-weight:800;letter-spacing:-0.2px}

/* ── DATAFRAMES ── */
.stDataFrame td,.stDataFrame th{color:var(--gray-900)!important}

/* ── FILTER LABELS ── */
div[data-testid="stSelectbox"] label,div[data-testid="stMultiSelect"] label,
div[data-testid="stRadio"] label,div[data-testid="stRadio"] p,
div[data-testid="stRadio"] div[role="radiogroup"] p{color:var(--gray-900)!important;font-weight:600!important;font-size:0.79rem!important}
div[data-baseweb="radio"] label,div[data-baseweb="radio"] span{color:var(--gray-900)!important;font-weight:600!important}

.filter-bar{display:flex;flex-wrap:wrap;gap:0.6rem;align-items:flex-end;margin-bottom:1rem;background:var(--gray-50);border-radius:12px;padding:0.65rem 0.9rem;border:1px solid var(--gray-200)}
.filter-bar label,.filter-bar p{color:var(--gray-900)!important;font-weight:600!important;font-size:0.76rem!important;margin-bottom:1px!important}

div[data-testid="stSelectbox"] > div > div,div[data-testid="stMultiSelect"] > div > div{font-size:0.82rem!important}
div[data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child{padding-top:4px!important;padding-bottom:4px!important;min-height:34px!important}
div[data-testid="stSelectbox"] [data-baseweb="select"]{border-radius:8px!important}

/* ── MULTISELECT TAGS ── */
[data-baseweb="tag"]{background:var(--green-bg)!important;border:1px solid rgba(22,163,74,0.3)!important}
[data-baseweb="tag"] span{color:var(--green)!important;font-weight:600!important}

/* ── ANIMATIONS ── */
@keyframes fadeInDown{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeInUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
@keyframes glowPulse{0%,100%{box-shadow:0 0 8px rgba(74,222,128,0.3)}50%{box-shadow:0 0 24px rgba(74,222,128,0.7),0 0 48px rgba(22,163,74,0.35)}}
@keyframes rippleAnim{to{transform:scale(4);opacity:0}}
@keyframes headerShimmer{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes float{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-15px) scale(1.05)}}
@keyframes shimmerLine{0%{background-position:-200% 0}100%{background-position:200% 0}}
@keyframes borderSpin{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}

@media(max-width:768px){
    .block-container{padding:0.6rem 0.8rem 2rem!important}
    .main-header{padding:1rem!important;flex-direction:column!important;gap:0.5rem!important}
    :root{--sidebar-w:200px}
}
</style>
""", unsafe_allow_html=True)

# ── JavaScript: parallax + 3D tilt + glow + ripple ──────────────────────
components.html("""
<script>
(function(){
  function init(){
    var doc = window.parent.document;
    if(!doc) return;

    // PARALLAX BACKGROUND on mouse move
    doc.addEventListener('mousemove', function(e){
      var x = (e.clientX / window.parent.innerWidth * 100).toFixed(1);
      var y = (e.clientY / window.parent.innerHeight * 100).toFixed(1);
      doc.documentElement.style.setProperty('--mx', x + '%');
      doc.documentElement.style.setProperty('--my', y + '%');
    });

    // 3D TILT on KPI cards
    function apply3D(){
      var cards = doc.querySelectorAll('.kpi-card');
      cards.forEach(function(card){
        if(card._3d) return; card._3d = true;
        card.addEventListener('mousemove', function(e){
          var r = card.getBoundingClientRect();
          var x = (e.clientX - r.left) / r.width - 0.5;
          var y = (e.clientY - r.top) / r.height - 0.5;
          card.style.transform = 'translateY(-6px) scale(1.02) perspective(900px) rotateX('+(-y*14)+'deg) rotateY('+(x*14)+'deg)';
          card.style.transition = 'box-shadow 0.1s, border 0.1s';
        });
        card.addEventListener('mouseleave', function(){
          card.style.transform = '';
          card.style.transition = 'all 0.35s cubic-bezier(0.34,1.56,0.64,1)';
        });
      });
    }

    // GLOW BORDER on expanders
    function applyGlow(){
      var exps = doc.querySelectorAll('[data-testid="stExpander"]');
      exps.forEach(function(exp){
        if(exp._glow) return; exp._glow = true;
        exp.addEventListener('mouseenter', function(){
          exp.style.boxShadow = '0 4px 24px rgba(22,163,74,0.14), 0 0 0 1px rgba(22,163,74,0.18)';
          exp.style.transform = 'translateY(-1px)';
        });
        exp.addEventListener('mouseleave', function(){
          exp.style.boxShadow = '0 2px 12px rgba(0,0,0,0.05)';
          exp.style.transform = '';
        });
      });
    }

    // RIPPLE EFFECT on buttons
    function applyRipple(){
      var btns = doc.querySelectorAll('.stButton > button');
      btns.forEach(function(btn){
        if(btn._ripple) return; btn._ripple = true;
        btn.addEventListener('click', function(e){
          var ripple = doc.createElement('span');
          var r = btn.getBoundingClientRect();
          var size = Math.max(r.width, r.height);
          ripple.style.cssText = 'position:absolute;border-radius:50%;pointer-events:none;'
            +'width:'+size+'px;height:'+size+'px;'
            +'left:'+(e.clientX-r.left-size/2)+'px;top:'+(e.clientY-r.top-size/2)+'px;'
            +'background:rgba(255,255,255,0.35);transform:scale(0);'
            +'animation:rippleAnim 0.6s ease;';
          btn.style.position='relative'; btn.style.overflow='hidden';
          btn.appendChild(ripple);
          setTimeout(function(){if(ripple.parentNode) ripple.parentNode.removeChild(ripple);}, 650);
        });
      });
    }

    // RUN
    apply3D(); applyGlow(); applyRipple();

    // Re-apply after Streamlit re-renders
    var observer = new MutationObserver(function(){
      apply3D(); applyGlow(); applyRipple();
    });
    observer.observe(doc.body, {childList:true, subtree:true});
  }

  if(document.readyState==='complete'){
    setTimeout(init, 400);
  } else {
    window.addEventListener('load', function(){ setTimeout(init, 400); });
  }
})();
</script>
""", height=0, scrolling=False)

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

def _db_mtime():
    return DB_PATH.stat().st_mtime if DB_PATH.exists() else 0


@st.cache_data(ttl=3600)
def cargar_datos_aceitunas(_mtime=None) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM aceitunas ORDER BY fecha")
    except Exception:
        conn.close()
        return pd.DataFrame()
    registros = cur.fetchall()
    conn.close()

    rows = []
    for r in registros:
        if not es_producto_aceituna(r["nombre"]):
            continue
        cadena  = r["supermercado"]
        marca   = limpiar_marca_ac(r["marca"] or "Desconocida", cadena)
        var_raw = ajustar_variedad_raw_ac(r["nombre"] or "", r["variedad"] or "Verde")
        g       = buscar_gramaje_unificado_catalogo(
            cadena,
            r["nombre"] or "",
            r["producto_id"],
            marca,
            var_raw,
            r["gramos_sin_escurrir"],
        )
        precio  = r["precio"]
        gondola = r["precio_sin_dto"] or precio
        desc    = round((gondola - precio) / gondola * 100) if gondola > precio else 0
        var_unif = unificar_variedad(var_raw)
        marca_cat = categorizar_marca_ac(marca)
        envase_base = detectar_envase_nombre(r["nombre"] or "")
        envase = resolver_envase_catalogo(cadena, r["nombre"] or "", marca, var_raw, g, envase_base)
        rows.append({
            "Fecha":              r["fecha"],
            "Cadena":             r["supermercado"],
            "Marca":              marca,
            "Marca_cat":          marca_cat,
            "Producto":           r["nombre"],
            "Variedad":           var_unif,
            "Variedad_raw":       var_raw,
            "Variedad_conf":      r["variedad_confianza"] or "baja",
            "Gramos":             int(g) if g else None,
            "Gramaje":            gramaje_a_grupo_aceituna(g),
            "Gramos_escurrido":   r["gramos_escurrido"],
            "Gramaje_fuente":     r["gramaje_fuente"] or "unknown",
            "Gramaje_conf":       r["gramaje_confianza"] or "baja",
            "Precio":             int(round(gondola)),
            "Precio_oferta":      int(round(precio)),
            "Precio_100g":        round(gondola / g * 100) if g else None,
            "Precio_100g_oferta": round(precio / g * 100) if g else None,
            "Descuento_pct":      desc,
            "En_oferta":          bool(r["en_oferta"]),
            "Producto_id":        r["producto_id"] or "",
            "URL":                r["url"] or "",
            "Envase":             envase,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = completar_envase_por_familia(df)
        df["SKU_canonico"] = df.apply(
            lambda row: sku_canonico_ac(
                row["Marca"],
                row["Variedad_raw"] or row["Variedad"],
                row["Gramos"],
                row["Envase"],
            ),
            axis=1,
        )
        df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.normalize()   # normalizar a medianoche
        df["Semana_num"] = df["Fecha"].dt.isocalendar().week.astype(int)
        df["Periodo"] = df["Fecha"].apply(
            lambda d: f"Sem {d.isocalendar().week} · {d.strftime('%b %Y')}"
        )
    return df


df_full = cargar_datos_aceitunas(_mtime=_db_mtime())

if df_full.empty:
    st.error("⚠️ Sin datos de aceitunas. Ejecutá primero: **python scraper_aceitunas.py**")
    st.stop()

# ---------------------------------------------------------------------------
# Helpers de layout
# ---------------------------------------------------------------------------

_BASE_CORE = dict(
    template="plotly_white",
    font=dict(family=PLOTLY_FONT_FAMILY, size=13, color="#111827"),
    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1, font=dict(size=12, color="#111827")),
)

BASE = {**_BASE_CORE, "margin": dict(l=10, r=10, t=40, b=10)}


def _kpi_mini(icon: str, titulo: str, valor: str, detalle: str = "") -> None:
    """Mini KPI card para barras de resumen (ej. barra de Ofertas)."""
    st.markdown(f"""
    <div style="background:#fff;border-radius:14px;padding:0.85rem 1rem;
                box-shadow:0 2px 10px rgba(0,0,0,0.07);border-top:3px solid #16A34A;
                text-align:center">
      <div style="font-size:1.3rem;margin-bottom:0.15rem">{icon}</div>
      <div style="font-size:0.6rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.7px;margin-bottom:0.1rem">{titulo}</div>
      <div style="font-size:1.15rem;font-weight:800;color:#111827;line-height:1.1">{valor}</div>
      <div style="font-size:0.63rem;color:#6B7280;margin-top:0.15rem">{detalle}</div>
    </div>""", unsafe_allow_html=True)


def _build_offer_card_html(r, compact: bool = False) -> str:
    """Construye el HTML de una card de oferta individual."""
    url = r.get("URL", "")
    is_url = isinstance(url, str) and url.startswith("http")
    ver = (f'<a href="{url}" target="_blank" '
           f'style="font-size:0.62rem;color:#3B82F6;font-weight:600;text-decoration:none">Ver →</a>'
           ) if is_url else ""
    sku      = str(r.get("SKU_canonico", r.get("Producto", "")))[:60]
    marca_cat = str(r.get("Marca_cat", ""))
    cadena   = str(r.get("Cadena", ""))
    def _safe(v):
        return 0 if (v is None or (isinstance(v, float) and math.isnan(v))) else v
    pof  = _safe(r.get("Precio_oferta"))
    pg   = _safe(r.get("Precio"))
    desc = _safe(r.get("Descuento_pct"))
    color = COLORES_MARCA_AC.get(marca_cat, "#3B82F6")
    pad = "0.35rem 0.6rem" if compact else "0.55rem 0.75rem"
    vs  = "0.82rem" if compact else "0.95rem"
    ss  = "0.68rem" if compact else "0.75rem"
    return (
        f'<div style="background:#fff;border-radius:8px;padding:{pad};'
        f'margin-bottom:0.3rem;border-left:3px solid {color};'
        f'box-shadow:0 1px 4px rgba(0,0,0,0.07)">'
        f'<div style="font-size:{ss};font-weight:700;color:#111827;'
        f'margin-bottom:0.2rem;line-height:1.2">{sku}</div>'
        f'<div style="display:flex;gap:0.9rem;align-items:flex-end">'
        f'<div><div style="font-size:0.52rem;color:#374151;text-transform:uppercase">Precio oferta</div>'
        f'<div style="font-size:{vs};font-weight:800;color:#16A34A">${pof:,.0f}</div></div>'
        f'<div><div style="font-size:0.52rem;color:#374151;text-transform:uppercase">Góndola</div>'
        f'<div style="font-size:{vs};font-weight:800;color:#6B7280"><s>${pg:,.0f}</s></div></div>'
        f'<div><div style="font-size:0.52rem;color:#374151;text-transform:uppercase">Dto.</div>'
        f'<div style="font-size:{vs};font-weight:800;color:#DC2626">-{desc:.0f}%</div></div>'
        f'</div><div style="font-size:0.6rem;color:#374151;margin-top:0.3rem;'
        f'display:flex;justify-content:space-between;align-items:center">'
        f'<span>🏪 {cadena}</span>{ver}</div></div>'
    )


def render_offer_cards(df: pd.DataFrame, compact: bool = False,
                       grid_cols: int = 1, max_height: int = 0) -> None:
    """Renderiza una tabla de ofertas como cards HTML con links."""
    if df.empty:
        st.markdown('<div style="color:#9CA3AF;font-size:0.8rem">Sin ofertas activas.</div>',
                    unsafe_allow_html=True)
        return
    cards = [_build_offer_card_html(r, compact) for _, r in df.iterrows()]
    if grid_cols > 1:
        col_style = f"repeat({grid_cols},1fr)"
        body = "".join(f'<div>{c}</div>' for c in cards)
        inner = (f'<div style="display:grid;grid-template-columns:{col_style};gap:0.4rem">'
                 f'{body}</div>')
    else:
        inner = "\n".join(cards)
    if max_height:
        html = (f'<div style="max-height:{max_height}px;overflow-y:auto;'
                f'padding-right:4px;scrollbar-width:thin">{inner}</div>')
    else:
        html = inner
    st.markdown(html, unsafe_allow_html=True)


def hbar(x_vals, y_vals, colores, textos, titulo_x, altura=340):
    vmax = max(x_vals) if x_vals else 1
    fig = go.Figure(go.Bar(
        x=x_vals, y=y_vals, orientation="h",
        marker_color=colores, text=textos,
        textposition="outside",
        textfont=dict(size=13, color="#111827"),
        cliponaxis=False,
    ))
    fig.update_layout(
        **_BASE_CORE, height=altura,
        margin=dict(l=10, r=220, t=40, b=10),
        xaxis=dict(title=dict(text=titulo_x, font=dict(color="#111827", size=12)),
                   tickprefix="$", tickformat=",",
                   tickfont=dict(size=12, color="#111827"),
                   range=[0, vmax * 1.4]),
        yaxis=dict(tickfont=dict(size=13, color="#111827"),
                   title=dict(font=dict(color="#111827"))),
        showlegend=False,
    )
    return fig


def color_marca_real_ac(marca: str) -> str:
    return COLORES_MARCA_AC.get(categorizar_marca_ac(marca), "#9CA3AF")


def marca_sort_key_ac(marca: str) -> tuple[int, str]:
    categoria = categorizar_marca_ac(marca)
    try:
        idx = ORDEN_MARCAS_AC.index(categoria)
    except ValueError:
        idx = len(ORDEN_MARCAS_AC)
    return idx, _normalizar_ac(str(marca))


def aplicar_filtros_mi_marca_ac(
    df: pd.DataFrame,
    variedad: str = "Todas",
    gramaje: str = "Todos",
    envase: str = "Todos",
) -> pd.DataFrame:
    df = df.copy()
    if variedad != "Todas":
        df = df[df["Variedad"] == variedad]
    if gramaje != "Todos":
        df = df[df["Gramaje"] == gramaje]
    if envase != "Todos":
        df = df[df["Envase"] == envase]
    return df


def preparar_metrica_mi_marca_ac(df: pd.DataFrame, modo: str) -> tuple[pd.DataFrame, str, str]:
    df = df.copy()
    if modo == "$/kg":
        df = df.dropna(subset=["Precio_100g"])
        df["_mm_metric"] = df["Precio_100g"] * 10
        return df, "$/kg", "$/kg promedio"
    df = df.dropna(subset=["Precio"])
    df["_mm_metric"] = df["Precio"]
    return df, "$", "Precio góndola promedio"


# ---------------------------------------------------------------------------
# Sidebar — filtros
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">🫒 <span class="accent">Aceitunas</span> Tracker</div>
    <div class="sidebar-sub">Monitor de precios · Argentina</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-sep">Navegación</div>', unsafe_allow_html=True)
    if DB_PATH != DIRECTORIO / "precios.db":
        st.caption(f"Modo copia · DB: {DB_PATH.name}")
    _page_sel = st.radio(
        "Navegación",
        COMMON_DASHBOARD_SECTIONS,
        key="nav_radio_aceitunas" if UNIFIED_MODE else "nav_radio",
        label_visibility="collapsed",
    )
    active_page = _page_sel.split("  ", 1)[1].strip() if "  " in _page_sel else _page_sel.strip()

    st.markdown('<div class="sidebar-sep">Período semanal</div>', unsafe_allow_html=True)
    periodos_disp = sorted(
        df_full["Periodo"].unique(),
        key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min(),
    )
    if len(periodos_disp) > 1:
        periodos_sel = st.multiselect("Período", periodos_disp, default=periodos_disp,
                                      label_visibility="collapsed")
    else:
        periodos_sel = periodos_disp
        st.info(f"📅 {periodos_disp[0]}")

    st.markdown("---")
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    _btn_csv = False  # CSV export removed from UI

    # ── Botón de cambio de categoría ──────────────────────────────────
    st.markdown(
        f'<div class="sidebar-sep">{"Cambiar sección" if UNIFIED_MODE else "Otras categorías"}</div>',
        unsafe_allow_html=True,
    )
    if UNIFIED_MODE:
        render_sidebar_section_switcher("aceitunas", key_prefix="suite_nav_aceitunas")
    else:
        components.html("""
<style>
  body{margin:0;padding:0;background:transparent;font-family:'Montserrat',sans-serif}
  a.csb{
    display:flex;align-items:center;gap:10px;
    background:linear-gradient(135deg,#064E3B,#065F46);
    border:1px solid rgba(74,222,128,0.25);border-radius:14px;
    padding:0.75rem 1rem;text-decoration:none;color:#fff;
    font-size:0.78rem;font-weight:700;letter-spacing:0.3px;
    transition:all 0.3s ease;box-shadow:0 4px 15px rgba(6,78,59,0.35);
    position:relative;overflow:hidden;width:100%;box-sizing:border-box
  }
  a.csb::before{
    content:"";position:absolute;top:-50%;left:-60%;width:60%;height:200%;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,0.08),transparent);
    transform:skewX(-20deg);transition:left 0.5s ease
  }
  a.csb:hover::before{left:120%}
  a.csb:hover{
    background:linear-gradient(135deg,#065F46,#047857);
    box-shadow:0 6px 22px rgba(6,78,59,0.5),0 0 0 1px rgba(74,222,128,0.35);
    transform:translateY(-2px)
  }
  a.csb:active{transform:translateY(0)}
  .icon{font-size:1.4rem;flex-shrink:0}
  .txt{display:flex;flex-direction:column;gap:1px}
  .lbl{font-size:0.6rem;font-weight:600;opacity:0.75;text-transform:uppercase;letter-spacing:1px}
  .nm{font-size:0.82rem;font-weight:800;letter-spacing:-0.2px}
  .arr{margin-left:auto;opacity:0.6;font-size:0.8rem}
</style>
<a href="https://olivapricing-argentina.streamlit.app" target="_blank" class="csb">
  <div class="icon">🫙</div>
  <div class="txt">
    <span class="lbl">Ir a</span>
    <span class="nm">Aceite de Oliva</span>
  </div>
  <span class="arr">↗</span>
</a>""", height=72, scrolling=False)

# ── Defaults para variables de filtro eliminadas del sidebar ─────────────
variedades_disp = sorted(df_full["Variedad"].dropna().unique())
variedades_sel  = list(variedades_disp)
cadenas_disp    = sorted(df_full["Cadena"].unique())
cadenas_sel     = list(cadenas_disp)
grupos_disp     = [g for g in GRAMAJE_GRUPOS if df_full["Gramaje"].eq(g).any()]
grupos_labels   = [gramaje_grupo_label(g) for g in grupos_disp]
buckets_sel     = list(grupos_disp)
_envases_orden  = ["Doypack", "Frasco Premium", "Frasco", "Lata", "Bandeja", "Sin detectar"]
envases_disp    = [e for e in _envases_orden if (df_full["Envase"] == e).any()]
envases_sel     = list(envases_disp)
metrica_sel     = "Precio góndola ($)"

# ---------------------------------------------------------------------------
# Filtro base
# ---------------------------------------------------------------------------

mask_base = (
    df_full["Periodo"].isin(periodos_sel)
    & df_full["Cadena"].isin(cadenas_sel)
    & df_full["Variedad"].isin(variedades_sel)
    & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
    & df_full["Envase"].isin(envases_sel)
)

dff   = df_full[mask_base].copy()
df_of = df_full[mask_base & df_full["En_oferta"]].copy()
df_ult = df_full[df_full["Fecha"] == df_full["Fecha"].max()].copy()

# Métrica seleccionada en sidebar
_met_kg  = metrica_sel == "$/kg"
_met_lbl = "$/kg" if _met_kg else "Precio góndola ($)"
if _met_kg:
    df_full["_met"] = df_full["Precio_100g"] * 10
    df_full["_met_of"] = df_full["Precio_100g_oferta"] * 10
    dff["_met"]    = dff["Precio_100g"] * 10
    dff["_met_of"] = dff["Precio_100g_oferta"] * 10
    df_ult["_met"] = df_ult["Precio_100g"] * 10
    df_ult["_met_of"] = df_ult["Precio_100g_oferta"] * 10
else:
    df_full["_met"] = df_full["Precio"]
    df_full["_met_of"] = df_full["Precio_oferta"]
    dff["_met"]    = dff["Precio"]
    dff["_met_of"] = dff["Precio_oferta"]
    df_ult["_met"] = df_ult["Precio"]
    df_ult["_met_of"] = df_ult["Precio_oferta"]

fecha_max_str = df_full["Fecha"].max().strftime("%d/%m/%Y")
n_sem = df_full["Periodo"].nunique()

if dff.empty:
    st.warning("Sin datos con los filtros seleccionados.")
    st.stop()

if _btn_csv:
    cols_exp = ["Periodo", "Cadena", "Marca", "Marca_cat", "Variedad", "Gramaje",
                "Gramos", "Producto", "Precio", "Precio_oferta", "Precio_100g",
                "Precio_100g_oferta", "Descuento_pct", "En_oferta", "URL"]
    with st.sidebar:
        st.download_button(
            "📥 Descargar CSV",
            dff[cols_exp].to_csv(index=False).encode("utf-8-sig"),
            "aceitunas_tracker.csv", "text/csv",
            use_container_width=True, key="dl_csv",
        )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(f"""
<div class="main-header">
  <div class="header-left">
    <div class="header-eyebrow">🫒 Monitor de Precios</div>
    <h1>Aceitunas · Tracker</h1>
    <p>{fecha_max_str} &nbsp;·&nbsp; {len(df_ult):,} productos
       &nbsp;·&nbsp; {df_ult['Cadena'].nunique()} cadenas
       &nbsp;·&nbsp; {n_sem} semana{"s" if n_sem > 1 else ""} acumulada{"s" if n_sem > 1 else ""}</p>
  </div>
  <div class="header-right">
    <div class="header-badge">🫒 Aceitunas</div>
  </div>
</div>""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------


# ── TAB 1: Resumen ────────────────────────────────────────────────────────
if active_page == "Resumen":
    # ── KPIs ─────────────────────────────────────────────────────────────
    dff_g        = dff.dropna(subset=["Precio_100g"])
    precio_prom  = dff["Precio"].mean()
    pkg_prom     = dff_g["Precio_100g"].mean() * 10
    p100_min     = dff_g.groupby("Cadena")["Precio_100g"].mean()
    cadena_barata = p100_min.idxmin() if not p100_min.empty else "—"
    n_oferta     = len(df_of)
    pct_of       = n_oferta / max(len(dff), 1) * 100
    desc_prom    = df_of["Descuento_pct"].mean() if not df_of.empty else 0
    ahorro_prom  = (df_of["Precio"] - df_of["Precio_oferta"]).mean() if not df_of.empty else 0
    variedad_top = dff["Variedad"].value_counts().idxmax() if not dff.empty else "—"
    marcas_n     = dff["Marca_cat"].nunique()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    kpis = [
        ("",       "SKUs relevados",    f"{dff['SKU_canonico'].nunique():,}", f"{dff['Cadena'].nunique()} cadenas"),
        ("green",  "$ promedio",        f"${precio_prom:,.0f}" if precio_prom else "—", "precio góndola"),
        ("teal",   "$/kg promedio",     f"${pkg_prom:,.0f}" if pkg_prom else "—", "base sin escurrir"),
        ("orange", "Cadena más barata", cadena_barata, "menor $/kg promedio"),
        ("purple", "Variedad top",      variedad_top,  "más SKUs en góndola"),
        ("red",    "En oferta",         f"{n_oferta:,}", f"{pct_of:.0f}% del total"),
        ("yellow", "Dto. prom.",        f"{desc_prom:.0f}%" if desc_prom > 0 else "—", f"{marcas_n} marcas"),
    ]
    kpis = [
        ("blue",   "Productos relevados", f"{dff['SKU_canonico'].nunique():,}", f"{dff['Cadena'].nunique()} cadenas"),
        ("green",  "Precio prom. góndola", f"${precio_prom:,.0f}" if pd.notna(precio_prom) else "—", "precio sin descuento"),
        ("orange", "Precio/kg prom.", f"${pkg_prom:,.0f}" if pd.notna(pkg_prom) else "—", "promedio por kilo"),
        ("purple", "Cadena más barata", cadena_barata, "menor precio/kg"),
        ("red",    "Productos en oferta", f"{n_oferta:,}", f"{pct_of:.0f}% del total"),
        ("teal",   "Ahorro prom. oferta", f"${ahorro_prom:,.0f}" if ahorro_prom > 0 else "—",
                   f"dto. {desc_prom:.0f}%" if desc_prom > 0 else "sin datos"),
    ]
    for col, (cls, label, val, sub) in zip([c1, c2, c3, c4, c5, c6], kpis):
        with col:
            st.markdown(f"""<div class="kpi-card {cls}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="font-size:{'1.2rem' if len(val)>9 else '1.7rem'};word-break:break-word">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown('<div style="margin-bottom:0.5rem"></div>', unsafe_allow_html=True)

    # ── Novedades ────────────────────────────────────────────────────────
    _pord = sorted(df_full["Periodo"].unique(),
                   key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min())
    _ult_p  = _pord[-1] if _pord else None
    _pen_p  = _pord[-2] if len(_pord) >= 2 else None
    _fecha_max = df_full["Fecha"].max()
    _all_dates = sorted(df_full["Fecha"].unique())

    # Cambios de precio ≥ 3% vs semana anterior
    _cambios: list[dict] = []
    if _ult_p and _pen_p:
        # Comparar producto a producto (no agrupado por SKU_canonico) para
        # evitar mezclar productos distintos bajo el mismo bucket de gramaje.
        _df_u = (dff[dff["Periodo"] == _ult_p]
                 .groupby(["Cadena", "Producto"])
                 .agg(Precio=("Precio", "mean"), URL=("URL", "first"))
                 .reset_index())
        _df_p = (dff[dff["Periodo"] == _pen_p]
                 .groupby(["Cadena", "Producto"])["Precio"].mean()
                 .reset_index())
        _merged = _df_u.merge(_df_p, on=["Cadena", "Producto"], suffixes=("_n", "_v"))
        for _, _row in _merged.iterrows():
            _pn, _pv = float(_row["Precio_n"]), float(_row["Precio_v"])
            if _pv == 0:
                continue
            _cp = (_pn - _pv) / _pv * 100
            if abs(_cp) >= 3:
                _url_c = _row.get("URL", "")
                _cambios.append({"cadena": _row["Cadena"], "sku": _row["Producto"],
                                 "viejo": _pv, "nuevo": _pn, "pct": _cp,
                                 "url": _url_c if isinstance(_url_c, str) else ""})
        _cambios.sort(key=lambda x: abs(x["pct"]), reverse=True)

    # Ofertas activas en última fecha
    _of_now = df_full[
        (df_full["Fecha"] == _fecha_max) &
        df_full["En_oferta"] &
        df_full["Cadena"].isin(cadenas_sel)
    ].copy()

    _top_of: list[dict] = []
    _dest_of: list[dict] = []
    if not _of_now.empty:
        # URL: la del producto con menor precio de oferta (mismo que se muestra en la card)
        _of_url_df = (_of_now.sort_values("Precio_oferta", ascending=True)
                      .dropna(subset=["URL"])
                      .groupby(["Cadena", "SKU_canonico", "Marca_cat"])["URL"]
                      .first().reset_index())
        _of_agg = (_of_now
                   .groupby(["Cadena", "SKU_canonico", "Marca_cat"])
                   .agg(desc=("Descuento_pct", "max"),
                        pof=("Precio_oferta", "min"),
                        pg=("Precio", "mean"))
                   .reset_index()
                   .merge(_of_url_df, on=["Cadena", "SKU_canonico", "Marca_cat"], how="left")
                   .rename(columns={"URL": "url"})
                   .sort_values("desc", ascending=False)
                   .reset_index(drop=True))
        _top_of   = _of_agg.head(3).to_dict("records")
        _MARCAS_TOP3 = {"La Toscana", "Castell", "Nucete"}
        _dest_of  = _of_agg[_of_agg["Marca_cat"].isin(_MARCAS_TOP3)].to_dict("records")

    with st.expander("🔔 Novedades", expanded=True):
            _cn_l, _cn_r, _cn_dest = st.columns(3, gap="large")

            with _cn_l:
                st.markdown('<div class="chart-note">📊 Cambios de precio vs semana anterior</div>',
                            unsafe_allow_html=True)
                if not _cambios:
                    st.markdown('<div style="color:#9CA3AF;font-size:0.8rem">Sin cambios significativos esta semana.</div>',
                                unsafe_allow_html=True)
                else:
                    for _c in _cambios[:8]:
                        _arr = "▲" if _c["pct"] > 0 else "▼"
                        _clr = "#EF4444" if _c["pct"] > 0 else "#16A34A"
                        _ver = (f'<a href="{_c["url"]}" target="_blank" '
                                f'style="font-size:0.62rem;color:#3B82F6;font-weight:600;'
                                f'text-decoration:none;display:block;margin-top:3px">Ver →</a>'
                                ) if _c.get("url", "").startswith("http") else ""
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:0.8rem;
                                    background:#FAFAFA;border-radius:9px;
                                    padding:0.55rem 0.85rem;margin-bottom:0.4rem;
                                    border-left:4px solid {_clr}">
                          <div style="flex:1;min-width:0">
                            <div style="font-size:0.77rem;font-weight:700;color:#111827;word-break:break-word">{_c['sku']}</div>
                            <div style="font-size:0.69rem;color:#6B7280">{_c['cadena']}</div>
                            {_ver}
                          </div>
                          <div style="text-align:right;white-space:nowrap;flex-shrink:0">
                            <span style="font-size:0.88rem;font-weight:800;color:{_clr}">{_arr} {abs(_c['pct']):.1f}%</span><br>
                            <span style="font-size:0.68rem;color:#9CA3AF">${_c['viejo']:,.0f} → ${_c['nuevo']:,.0f}</span>
                          </div>
                        </div>""", unsafe_allow_html=True)

            with _cn_r:
                st.markdown('<div class="chart-note">🏷️ Top ofertas activas esta semana</div>',
                            unsafe_allow_html=True)
                _MEDALS = ["🥇", "🥈", "🥉"]
                if not _top_of:
                    st.markdown('<div style="color:#9CA3AF;font-size:0.8rem">Sin ofertas activas.</div>',
                                unsafe_allow_html=True)
                else:
                    for _i, _o in enumerate(_top_of):
                        _o_url = _o.get("url", "")
                        _ver_o = (f'<a href="{_o_url}" target="_blank" '
                                  f'style="font-size:0.62rem;color:#3B82F6;font-weight:600;text-decoration:none">Ver →</a>'
                                  ) if _o_url and _o_url.startswith("http") else ""
                        st.markdown(
                        f'<div style="background:#fff;border-radius:8px;padding:0.55rem 0.75rem;'
                        f'margin-bottom:0.4rem;border-left:3px solid #3B82F6;'
                        f'box-shadow:0 1px 4px rgba(0,0,0,0.07)">'
                        f'<div style="font-size:0.75rem;font-weight:700;color:#111827;margin-bottom:0.35rem">'
                        f'{_MEDALS[_i] if _i < 3 else "⭐"} {_o["SKU_canonico"][:55]}</div>'
                        f'<div style="display:flex;gap:1.2rem;align-items:flex-end">'
                        f'<div><div style="font-size:0.58rem;color:#374151;text-transform:uppercase">Precio oferta</div>'
                        f'<div style="font-size:0.95rem;font-weight:800;color:#16A34A">${_o["pof"]:,.0f}</div></div>'
                        f'<div><div style="font-size:0.58rem;color:#374151;text-transform:uppercase">Góndola</div>'
                        f'<div style="font-size:0.95rem;font-weight:800;color:#6B7280"><s>${_o["pg"]:,.0f}</s></div></div>'
                        f'<div><div style="font-size:0.58rem;color:#374151;text-transform:uppercase">Dto.</div>'
                        f'<div style="font-size:0.95rem;font-weight:800;color:#DC2626">-{_o["desc"]:.0f}%</div></div>'
                        f'</div>'
                        f'<div style="font-size:0.65rem;color:#374151;margin-top:0.3rem;'
                        f'display:flex;justify-content:space-between;align-items:center">'
                        f'<span>🏪 {_o["Cadena"]}</span>{_ver_o}</div>'
                        f'</div>',
                        unsafe_allow_html=True)

            with _cn_dest:
                st.markdown('<div class="chart-note">⭐ La Toscana · Castell · Nucete</div>',
                            unsafe_allow_html=True)
                if not _dest_of:
                    st.markdown('<div style="color:#9CA3AF;font-size:0.8rem">Sin ofertas activas para estas marcas.</div>',
                                unsafe_allow_html=True)
                else:
                    for _od in _dest_of[:5]:
                        _clr_d = COLORES_MARCA_AC.get(_od["Marca_cat"], "#3B82F6")
                        _od_url = _od.get("url", "")
                        _ver_d = (f'<a href="{_od_url}" target="_blank" '
                                  f'style="font-size:0.62rem;color:#3B82F6;font-weight:600;text-decoration:none">Ver →</a>'
                                  ) if _od_url and _od_url.startswith("http") else ""
                        st.markdown(
                        f'<div style="background:#fff;border-radius:8px;padding:0.55rem 0.75rem;'
                        f'margin-bottom:0.4rem;border-left:3px solid {_clr_d};'
                        f'box-shadow:0 1px 4px rgba(0,0,0,0.07)">'
                        f'<div style="font-size:0.75rem;font-weight:700;color:#111827;margin-bottom:0.35rem">'
                        f'⭐ {_od["SKU_canonico"][:55]}</div>'
                        f'<div style="display:flex;gap:1.2rem;align-items:flex-end">'
                        f'<div><div style="font-size:0.58rem;color:#374151;text-transform:uppercase">Precio oferta</div>'
                        f'<div style="font-size:0.95rem;font-weight:800;color:#16A34A">${_od["pof"]:,.0f}</div></div>'
                        f'<div><div style="font-size:0.58rem;color:#374151;text-transform:uppercase">Góndola</div>'
                        f'<div style="font-size:0.95rem;font-weight:800;color:#6B7280"><s>${_od["pg"]:,.0f}</s></div></div>'
                        f'<div><div style="font-size:0.58rem;color:#374151;text-transform:uppercase">Dto.</div>'
                        f'<div style="font-size:0.95rem;font-weight:800;color:#DC2626">-{_od["desc"]:.0f}%</div></div>'
                        f'</div>'
                        f'<div style="font-size:0.65rem;color:#374151;margin-top:0.3rem;'
                        f'display:flex;justify-content:space-between;align-items:center">'
                        f'<span>🏪 {_od["Cadena"]}</span>{_ver_d}</div>'
                        f'</div>',
                        unsafe_allow_html=True)

    # ── Insights ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("💡 Insights del mercado", expanded=True):
        def _insight_card(icon, titulo, valor, detalle, color="#0F3460"):
            st.markdown(f"""
            <div style="background:#fff;border-radius:12px;padding:0.9rem 1.1rem;
                        border-left:4px solid {color};box-shadow:0 1px 6px rgba(0,0,0,0.07)">
              <div style="font-size:1.2rem;margin-bottom:0.2rem">{icon}</div>
              <div style="font-size:0.65rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.12rem">{titulo}</div>
              <div style="font-size:1.05rem;font-weight:800;color:#111827;line-height:1.2;margin-bottom:0.18rem">{valor}</div>
              <div style="font-size:0.71rem;color:#374151;line-height:1.4">{detalle}</div>
            </div>""", unsafe_allow_html=True)

        _ins = dff[dff["Fecha"] == dff["Fecha"].max()].copy()
        _ins_g = _ins.dropna(subset=["Precio_100g"])
        _cad_p100 = (_ins_g.groupby(["Cadena", "SKU_canonico"])["Precio_100g"].mean()
                     .reset_index().groupby("Cadena")["Precio_100g"].mean().reset_index(name="p100"))
        _cad_barata = _cad_p100.sort_values("p100").iloc[0] if not _cad_p100.empty else None
        _cad_cara   = _cad_p100.sort_values("p100").iloc[-1] if not _cad_p100.empty else None
        _ins_marcas = _ins[~_ins["Marca"].isin(_MARCAS_AGREGADAS_EXCLUIDAS_AC)].copy()
        _sku_x_marca = (_ins_marcas.groupby("Marca")["SKU_canonico"].nunique()
                        .reset_index(name="n").sort_values("n", ascending=False))
        _cad_x_marca = (_ins_marcas.groupby("Marca")["Cadena"].nunique()
                        .reset_index(name="n").sort_values("n", ascending=False))
        _of_x_cad = (_ins[_ins["Cadena"].isin(cadenas_sel)]
                     .groupby("Cadena")["En_oferta"].mean().mul(100)
                     .reset_index(name="pct").sort_values("pct", ascending=False))
        _of_x_marca = (_ins[
                           _ins["Cadena"].isin(cadenas_sel)
                           & _ins["Marca"].isin(MARCAS_DESTACADAS_AC)
                       ]
                       .groupby("Marca")["En_oferta"].mean().mul(100)
                       .reset_index(name="pct").sort_values("pct", ascending=False))

        _ri1, _ri2, _ri3, _ri4 = st.columns(4, gap="medium")
        with _ri1:
            if not _sku_x_marca.empty:
                r = _sku_x_marca.iloc[0]
                _insight_card("📦", "Marca con más SKUs activos",
                              str(r["Marca"]), f"{int(r['n'])} SKUs distintos", "#0F3460")
        with _ri2:
            if not _cad_x_marca.empty:
                r = _cad_x_marca.iloc[0]
                _insight_card("🌐", "Marca con más presencia",
                              str(r["Marca"]), f"activa en {int(r['n'])} cadenas", "#7C3AED")
        with _ri3:
            if _cad_barata is not None:
                _insight_card("✅", "Cadena más barata",
                              _cad_barata["Cadena"], f"${_cad_barata['p100']:,.0f}/100g promedio", "#16A34A")
        with _ri4:
            if _cad_cara is not None:
                _insight_card("🏅", "Cadena más cara",
                              _cad_cara["Cadena"], f"${_cad_cara['p100']:,.0f}/100g promedio", "#7C3AED")

        st.markdown("<br>", unsafe_allow_html=True)
        _ri5, _ri6, _ri7, _ri8 = st.columns(4, gap="medium")
        with _ri5:
            if not _of_x_cad.empty:
                r = _of_x_cad.iloc[0]
                _insight_card("🏪", "Cadena con más ofertas",
                              r["Cadena"], f"{r['pct']:.0f}% de sus productos en oferta", "#B45309")
        with _ri6:
            if not _of_x_marca.empty:
                r = _of_x_marca.iloc[0]
                _insight_card("🔥", "Marca destacada con más descuentos",
                              r["Marca"], f"{r['pct']:.0f}% de registros en oferta", "#DC2626")
        with _ri7:
            _top_var = dff["Variedad"].value_counts()
            if not _top_var.empty:
                _insight_card("🫒", "Variedad más relevada",
                              _top_var.index[0], f"{int(_top_var.iloc[0])} registros", "#4CAF50")
        with _ri8:
            _n_marcas_dest = dff[dff["Marca_cat"].isin(MARCAS_DESTACADAS_AC)]["Marca_cat"].nunique()
            _n_skus_dest   = dff[dff["Marca_cat"].isin(MARCAS_DESTACADAS_AC)]["SKU_canonico"].nunique()
            _insight_card("🏷️", "Marcas destacadas",
                          f"{_n_marcas_dest} presentes", f"{_n_skus_dest} SKUs distintos", "#2E86AB")

    # ── Distribución general ─────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📊 Resumen de SKUs", expanded=True):
        c_pie, c_pie2, c_bar = st.columns([1, 1, 2])
        with c_pie:
            st.markdown('<div class="chart-title">SKUs por variedad</div>', unsafe_allow_html=True)
            var_cnt = dff["Variedad"].value_counts().reset_index()
            var_cnt.columns = ["Variedad", "SKUs"]
            fig_pie = px.pie(var_cnt, values="SKUs", names="Variedad",
                             color="Variedad", color_discrete_map=COLORES_VARIEDAD, hole=0.4)
            fig_pie.update_traces(textposition="inside", textinfo="percent+label",
                                  textfont=dict(color="#111827"))
            fig_pie.update_layout(**_BASE_CORE, height=320,
                                  margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        with c_pie2:
            st.markdown('<div class="chart-title">SKUs por tipo de envase</div>', unsafe_allow_html=True)
            _env_cnt = dff["Envase"].value_counts().reset_index()
            _env_cnt.columns = ["Envase", "SKUs"]
            _colores_env = {
                "Doypack":      "#F59E0B",
                "Frasco":       "#3B82F6",
                "Lata":         "#6B7280",
                "Bandeja":      "#10B981",
                "Sin detectar": "#E5E7EB",
            }
            fig_pie2 = px.pie(_env_cnt, values="SKUs", names="Envase",
                              color="Envase", color_discrete_map=_colores_env, hole=0.4)
            fig_pie2.update_traces(textposition="inside", textinfo="percent+label",
                                   textfont=dict(color="#111827"))
            fig_pie2.update_layout(**_BASE_CORE, height=320,
                                   margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_pie2, use_container_width=True)

        with c_bar:
            st.markdown('<div class="chart-title">$/kg promedio por variedad</div>', unsafe_allow_html=True)
            var_p = (dff.dropna(subset=["Precio_100g"])
                     .groupby("Variedad")["Precio_100g"].mean().mul(10).sort_values().reset_index())
            fig_v = hbar(var_p["Precio_100g"].tolist(), var_p["Variedad"].tolist(),
                         [cv(v) for v in var_p["Variedad"]],
                         [f"${v:,.0f}" for v in var_p["Precio_100g"]], "$/kg",
                         altura=max(280, len(var_p) * 32))
            st.plotly_chart(fig_v, use_container_width=True)

    # ── Movimientos de catálogo ──────────────────────────────────────────
    st.markdown("---")
    with st.expander("🆕 Novedades de catálogo", expanded=True):
        fechas_ord = sorted(df_full["Fecha"].unique())
        _cat_l, _cat_r = st.columns([2, 1])

        with _cat_l:
            st.markdown('<div class="chart-note">🆕 Entradas y ⚠️ salidas vs semana anterior</div>',
                        unsafe_allow_html=True)
            if len(fechas_ord) >= 2:
                f_rec, f_prev = fechas_ord[-1], fechas_ord[-2]
                skus_rec  = set(zip(df_full[df_full["Fecha"] == f_rec]["SKU_canonico"],
                                    df_full[df_full["Fecha"] == f_rec]["Cadena"]))
                skus_prev = set(zip(df_full[df_full["Fecha"] == f_prev]["SKU_canonico"],
                                    df_full[df_full["Fecha"] == f_prev]["Cadena"]))
                movs = pd.DataFrame(
                    [{"SKU": s, "Cadena": c, "Estado": "🆕 Entrada"} for s, c in skus_rec - skus_prev] +
                    [{"SKU": s, "Cadena": c, "Estado": "⚠️ Salida"}  for s, c in skus_prev - skus_rec]
                )
                if not movs.empty:
                    st.dataframe(movs, use_container_width=True, hide_index=True, height=300)
                else:
                    st.info("Sin cambios de catálogo entre las dos últimas semanas.")
            else:
                st.info("Sin datos de semana anterior para comparar. Se muestran los productos actuales.")

        with _cat_r:
            _cat_r_hdr, _cat_r_ord = st.columns([2, 1])
            with _cat_r_hdr:
                st.markdown('<div class="chart-note">🏷️ Todas las ofertas activas esta semana</div>',
                            unsafe_allow_html=True)
            with _cat_r_ord:
                _of_all_sort = st.radio("Ord.", ["Descuento", "Marca"], horizontal=True,
                                        key="of_all_ord", label_visibility="collapsed")
            _of_all = df_full[
                (df_full["Fecha"] == df_full["Fecha"].max()) & df_full["En_oferta"]
            ][["Cadena", "Marca_cat", "SKU_canonico", "Producto", "Descuento_pct",
               "Precio", "Precio_oferta", "URL"]].copy()
            if _of_all_sort == "Marca":
                _mk_ord_all = {m: i for i, m in enumerate(ORDEN_MARCAS_AC)}
                _of_all["_mk_ord"] = _of_all["Marca_cat"].map(_mk_ord_all).fillna(99)
                _of_all = _of_all.sort_values(["_mk_ord", "SKU_canonico"]).drop(columns="_mk_ord")
            else:
                _of_all = _of_all.sort_values("Descuento_pct", ascending=False)
            render_offer_cards(_of_all, compact=True, max_height=420)


# ── TAB 6: Comparativa ─────────────────────────────────────────────────────
if active_page == "Comparativa":
    st.markdown('<div class="chart-note">Seleccioná dos marcas y luego un SKU de cada una para comparar su precio de góndola en el tiempo</div>',
                unsafe_allow_html=True)

    _cmp_f1, _cmp_f2, _cmp_f3, _ = st.columns([1.2, 1.2, 1.2, 2.4])
    with _cmp_f1:
        _cmp_var = st.selectbox("Variedad", ["Todas"] + variedades_disp, key="cmp_var_aceitunas")
    with _cmp_f2:
        _cmp_gram = st.selectbox("Gramaje", ["Todos"] + grupos_labels, key="cmp_gram_aceitunas")
    with _cmp_f3:
        _cmp_envase = st.selectbox("Envase", ["Todos"] + envases_disp, key="cmp_envase_aceitunas")

    _cmp_gram_key = None
    if _cmp_gram != "Todos":
        _cmp_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _cmp_gram), None)

    _cmp_base = dff.dropna(subset=["Marca", "SKU_canonico", "_met"]).copy()
    if _cmp_var != "Todas":
        _cmp_base = _cmp_base[_cmp_base["Variedad"] == _cmp_var]
    if _cmp_gram_key:
        _cmp_base = _cmp_base[_cmp_base["Gramaje"] == _cmp_gram_key]
    if _cmp_envase != "Todos":
        _cmp_base = _cmp_base[_cmp_base["Envase"] == _cmp_envase]

    if _cmp_base.empty:
        st.info("No hay datos comparables con los filtros actuales.")
    else:
        marcas_comp = sorted(_cmp_base["Marca"].dropna().unique(), key=marca_sort_key_ac)
        col_m1, col_m2 = st.columns(2, gap="large")

        with col_m1:
            st.markdown("**Marca 1**")
            marca_c1 = st.selectbox("Marca 1", marcas_comp, key="comp_marca1_aceitunas", label_visibility="collapsed")
            skus_c1 = sorted(_cmp_base[_cmp_base["Marca"] == marca_c1]["SKU_canonico"].dropna().unique())
            sku_c1 = st.selectbox("SKU 1", skus_c1, key="comp_sku1_aceitunas", label_visibility="collapsed")

        with col_m2:
            st.markdown("**Marca 2**")
            default_m2 = marcas_comp[1] if len(marcas_comp) > 1 else marcas_comp[0]
            idx_m2 = marcas_comp.index(default_m2)
            marca_c2 = st.selectbox("Marca 2", marcas_comp, index=idx_m2, key="comp_marca2_aceitunas", label_visibility="collapsed")
            skus_c2 = sorted(_cmp_base[_cmp_base["Marca"] == marca_c2]["SKU_canonico"].dropna().unique())
            sku_c2 = st.selectbox("SKU 2", skus_c2, key="comp_sku2_aceitunas", label_visibility="collapsed")

        orden_per8 = sorted(_cmp_base["Periodo"].unique(), key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min())

        def sku_evol(sku_name: str, label: str) -> pd.DataFrame:
            df_s = (_cmp_base[_cmp_base["SKU_canonico"] == sku_name]
                    .groupby("Periodo")["_met"].mean().reset_index())
            df_s["Periodo"] = pd.Categorical(df_s["Periodo"], categories=orden_per8, ordered=True)
            df_s["SKU"] = label
            return df_s

        def sku_oferta_por_periodo(sku_name: str) -> set[str]:
            return set(_cmp_base[(_cmp_base["SKU_canonico"] == sku_name) & _cmp_base["En_oferta"]]["Periodo"].unique())

        lbl1 = sku_c1
        lbl2 = sku_c2
        df_comp = pd.concat([sku_evol(sku_c1, lbl1), sku_evol(sku_c2, lbl2)], ignore_index=True)
        _of_pers1 = sku_oferta_por_periodo(sku_c1)
        _of_pers2 = sku_oferta_por_periodo(sku_c2)

        if df_comp.empty:
            st.info("No hay datos de evolución para los SKUs seleccionados.")
        else:
            color1 = color_marca_real_ac(marca_c1)
            color2 = color_marca_real_ac(marca_c2) if marca_c2 != marca_c1 else "#C73E1D"
            fig = px.line(df_comp, x="Periodo", y="_met", color="SKU", markers=True,
                          color_discrete_map={lbl1: color1, lbl2: color2},
                          labels={"_met": _met_lbl, "Periodo": ""}, height=420)
            fig.update_traces(line=dict(width=3), marker=dict(size=8))

            df_ev1 = sku_evol(sku_c1, lbl1)
            df_ev2 = sku_evol(sku_c2, lbl2)
            df_ev1_of = df_ev1[df_ev1["Periodo"].isin(_of_pers1)]
            df_ev2_of = df_ev2[df_ev2["Periodo"].isin(_of_pers2)]
            if not df_ev1_of.empty:
                fig.add_trace(go.Scatter(
                    x=df_ev1_of["Periodo"], y=df_ev1_of["_met"], mode="markers",
                    name=f"{lbl1} · en oferta",
                    marker=dict(symbol="star", size=16, color=color1, line=dict(color="#fff", width=1.5)),
                ))
            if not df_ev2_of.empty:
                fig.add_trace(go.Scatter(
                    x=df_ev2_of["Periodo"], y=df_ev2_of["_met"], mode="markers",
                    name=f"{lbl2} · en oferta",
                    marker=dict(symbol="star", size=16, color=color2, line=dict(color="#fff", width=1.5)),
                ))
            fig.update_layout(**BASE,
                              yaxis=dict(title=_met_lbl, tickprefix="$", tickformat=",",
                                         tickfont=dict(size=12, color="#111827")),
                              xaxis=dict(tickfont=dict(size=12, color="#111827")))
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Semanas en oferta", expanded=True):
                _of_rows = []
                for _pe in orden_per8:
                    _of_rows.append({
                        "Período": _pe,
                        lbl1[:35]: "✓" if _pe in _of_pers1 else "—",
                        lbl2[:35]: "✓" if _pe in _of_pers2 else "—",
                    })
                st.dataframe(pd.DataFrame(_of_rows),
                             height=min(400, len(orden_per8) * 38 + 60),
                             hide_index=True)

            with st.expander("Precio por cadena y período", expanded=True):
                st.markdown(f'<div class="chart-note">{_met_lbl} promedio por cadena en cada semana/mes</div>',
                            unsafe_allow_html=True)

                def _cad_per_heatmap(sku_name: str, label: str, color_hi: str) -> None:
                    _df_cp = (_cmp_base[_cmp_base["SKU_canonico"] == sku_name]
                              .groupby(["Cadena", "Periodo"])["_met"].mean().round(0).unstack("Periodo"))
                    _df_cp = _df_cp.reindex(columns=[p for p in orden_per8 if p in _df_cp.columns])
                    if _df_cp.empty:
                        st.info(f"Sin datos para {label[:40]}")
                        return
                    _txt_cp = [[f"${v:,.0f}" if not pd.isna(v) else "—" for v in row] for row in _df_cp.values]
                    _vmin = float(_df_cp.min().min()) if not _df_cp.empty else 0
                    _vmax = float(_df_cp.max().max()) if not _df_cp.empty else 1
                    _fig_cp = go.Figure(go.Heatmap(
                        z=_df_cp.values,
                        x=_df_cp.columns.tolist(),
                        y=_df_cp.index.tolist(),
                        colorscale=[[0, "#D1FAE5"], [0.5, "#34D399"], [1, color_hi]],
                        zmin=_vmin,
                        zmax=_vmax,
                        text=_txt_cp,
                        texttemplate="%{text}",
                        textfont=dict(size=12, color="#111827"),
                        showscale=False,
                    ))
                    _fig_cp.update_layout(**_BASE_CORE,
                                          height=max(220, len(_df_cp) * 44 + 100),
                                          margin=dict(l=10, r=10, t=50, b=10),
                                          title=dict(text=label[:50], font=dict(size=12, color="#374151"), x=0.01),
                                          xaxis=dict(tickfont=dict(size=11, color="#111827"), side="top", tickangle=-25),
                                          yaxis=dict(tickfont=dict(size=12, color="#111827")))
                    st.plotly_chart(_fig_cp, use_container_width=True)

                _col_cp1, _col_cp2 = st.columns(2, gap="large")
                with _col_cp1:
                    _cad_per_heatmap(sku_c1, lbl1, "#065F46")
                with _col_cp2:
                    _cad_per_heatmap(sku_c2, lbl2, "#7C1D2D")

            with st.expander("Precio por cadena · último período disponible", expanded=True):
                ult_per8 = orden_per8[-1] if orden_per8 else None
                if ult_per8:
                    df_cmp_tbl = _cmp_base[
                        (_cmp_base["Periodo"] == ult_per8)
                        & (_cmp_base["SKU_canonico"].isin([sku_c1, sku_c2]))
                    ][["Cadena", "SKU_canonico", "Variedad", "Envase", "Gramaje", "_met", "En_oferta"]].copy()
                    _precio_cmp_lbl = "$/kg góndola" if _met_kg else "Precio góndola ($)"
                    df_cmp_tbl.columns = ["Cadena", "SKU", "Variedad", "Envase", "Gramaje", _precio_cmp_lbl, "En oferta"]
                    st.dataframe(
                        df_cmp_tbl.sort_values(["SKU", "Cadena"]),
                        height=320,
                        column_config={
                            _precio_cmp_lbl: st.column_config.NumberColumn(format="$%d"),
                            "En oferta": st.column_config.CheckboxColumn(),
                        },
                        hide_index=True,
                    )

            if df_comp["Periodo"].nunique() > 1:
                with st.expander("Diferencia de precio entre SKUs por período", expanded=True):
                    st.markdown('<div class="chart-note">Verde = SKU 1 más barato · Rojo = SKU 2 más barato</div>',
                                unsafe_allow_html=True)
                    piv_comp = df_comp.pivot(index="Periodo", columns="SKU", values="_met")
                    if lbl1 in piv_comp.columns and lbl2 in piv_comp.columns:
                        piv_comp["Diferencia"] = piv_comp[lbl1] - piv_comp[lbl2]
                        piv_comp = piv_comp.dropna(subset=["Diferencia"]).reset_index()
                        fig = go.Figure(go.Bar(
                            x=piv_comp["Periodo"],
                            y=piv_comp["Diferencia"],
                            marker_color=["#00B050" if v <= 0 else "#EF4444" for v in piv_comp["Diferencia"]],
                            text=[f"${v:+,.0f}" for v in piv_comp["Diferencia"]],
                            textposition="outside",
                            textfont=dict(size=12, color="#111827"),
                            cliponaxis=False,
                        ))
                        fig.update_layout(**_BASE_CORE,
                                          height=320,
                                          margin=dict(l=10, r=10, t=60, b=40),
                                          xaxis=dict(tickfont=dict(size=12, color="#111827"), tickangle=-20),
                                          yaxis=dict(title=f"Diferencia ({_met_lbl})", tickprefix="$",
                                                     tickformat=",", tickfont=dict(size=12, color="#111827")),
                                          showlegend=False,
                                          shapes=[dict(type="line", x0=-0.5, x1=len(piv_comp) - 0.5, y0=0, y1=0,
                                                       line=dict(color="#9CA3AF", width=1.5, dash="dot"))],
                                          title=dict(text=f"{lbl1[:30]} vs {lbl2[:30]}",
                                                     font=dict(size=12, color="#6B7280"), x=0.01))
                        st.plotly_chart(fig, use_container_width=True)


# ── TAB 3: Por Cadena ─────────────────────────────────────────────────────
if active_page == "Por Cadena":
    # ── Filtros globales del tab (arriba de todo) ──────────────────────────
    _c3f1, _c3f2, _c3f3, _c3sp = st.columns([1, 1, 1, 3])
    with _c3f1:
        st.markdown('<p style="color:#111827;font-size:0.78rem;font-weight:700;margin-bottom:1px">Variedad</p>', unsafe_allow_html=True)
        _c3_var = st.selectbox("Variedad", ["Todas"] + variedades_disp, key="c3_var", label_visibility="collapsed")
    with _c3f2:
        st.markdown('<p style="color:#111827;font-size:0.78rem;font-weight:700;margin-bottom:1px">Gramaje</p>', unsafe_allow_html=True)
        _c3_gram_lbl = st.selectbox("Gramaje", ["Todos"] + grupos_labels, key="c3_gram", label_visibility="collapsed")
    with _c3f3:
        st.markdown('<p style="color:#111827;font-size:0.78rem;font-weight:700;margin-bottom:1px">Envase</p>', unsafe_allow_html=True)
        _c3_envase = st.selectbox("Envase", ["Todos"] + envases_disp, key="c3_envase", label_visibility="collapsed")

    # Aplica el filtro a TODOS los gráficos del tab
    dff_c3 = dff.copy()
    if _c3_var != "Todas":
        dff_c3 = dff_c3[dff_c3["Variedad"] == _c3_var]
    if _c3_gram_lbl != "Todos":
        _c3_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _c3_gram_lbl), None)
        if _c3_gram_key:
            dff_c3 = dff_c3[dff_c3["Gramaje"] == _c3_gram_key]
    if _c3_envase != "Todos":
        dff_c3 = dff_c3[dff_c3["Envase"] == _c3_envase]
    st.markdown("---")

    with st.expander(f"{_met_lbl} promedio & Productos por cadena", expanded=True):
        col_l, col_r = st.columns([3, 2], gap="large")
        with col_l:
            cad_p = (dff_c3.dropna(subset=["_met"])
                     .groupby("Cadena")["_met"].mean()
                     .reset_index().sort_values("_met"))
            fig_c = hbar(cad_p["_met"].tolist(), cad_p["Cadena"].tolist(),
                         [cc(c) for c in cad_p["Cadena"]],
                         [f"${v:,.0f}" for v in cad_p["_met"]], _met_lbl)
            st.plotly_chart(fig_c, use_container_width=True)
        with col_r:
            df_pie_c = dff_c3.groupby("Cadena").size().reset_index(name="n")
            fig_pie_c = go.Figure(go.Pie(
                labels=df_pie_c["Cadena"], values=df_pie_c["n"],
                marker_colors=[cc(c) for c in df_pie_c["Cadena"]],
                hole=0.55, textinfo="label+percent",
                textposition="outside",
                textfont=dict(size=12, color="#111827"),
            ))
            fig_pie_c.update_layout(**_BASE_CORE, height=320,
                                    margin=dict(l=10, r=10, t=40, b=40), showlegend=False)
            st.plotly_chart(fig_pie_c, use_container_width=True)

    with st.expander(f"Distribución de precios por cadena ({_met_lbl})", expanded=True):
        st.markdown('<div class="chart-note">Caja = rango intercuartil (Q1–Q3) · Línea central = mediana · Bigotes = 1.5×IQR</div>',
                    unsafe_allow_html=True)
        _p10 = float(dff_c3["_met"].dropna().quantile(0.10)) if not dff_c3.empty else 0
        _p90 = float(dff_c3["_met"].dropna().quantile(0.90)) if not dff_c3.empty else 3000
        fig_box_c = go.Figure()
        for cadena in sorted(dff_c3["Cadena"].unique()):
            sub = dff_c3[dff_c3["Cadena"] == cadena]["_met"].dropna()
            if sub.empty:
                continue
            fig_box_c.add_trace(go.Box(
                y=sub, name=cadena, marker_color=cc(cadena),
                boxmean=True, line_width=2, marker=dict(size=4, opacity=0.4),
            ))
        fig_box_c.update_layout(**_BASE_CORE, height=420,
                                yaxis=dict(title=_met_lbl, tickprefix="$", tickformat=",",
                                           tickfont=dict(size=12, color="#111827"),
                                           range=[max(0, _p10 * 0.7), _p90 * 1.25]),
                                xaxis=dict(tickfont=dict(size=13, color="#111827")),
                                showlegend=False)
        st.plotly_chart(fig_box_c, use_container_width=True)

    with st.expander(f"{_met_lbl} promedio — Cadena × Marca", expanded=True):
        pivot_cm = (dff_c3.dropna(subset=["_met"])
                    .groupby(["Marca_cat", "Cadena"])["_met"]
                    .mean().round(0).unstack("Cadena"))
        pivot_cm = pivot_cm.reindex([m for m in ORDEN_MARCAS_AC if m in pivot_cm.index])
        if not pivot_cm.empty:
            text_cm = [[f"${v:,.0f}" if not pd.isna(v) else "—" for v in row]
                       for row in pivot_cm.values]
            fig_hm_cm = go.Figure(go.Heatmap(
                z=pivot_cm.values, x=pivot_cm.columns.tolist(), y=pivot_cm.index.tolist(),
                colorscale="RdYlGn_r",
                text=text_cm, texttemplate="%{text}",
                textfont=dict(size=12, color="#111827"),
                colorbar=dict(title=_met_lbl, tickprefix="$", tickformat=",",
                              tickfont=dict(color="#111827"),
                              title_font=dict(color="#111827")),
            ))
            fig_hm_cm.update_layout(**_BASE_CORE, height=max(320, len(pivot_cm) * 48 + 80),
                                    xaxis=dict(tickfont=dict(size=13, color="#111827"), side="top"),
                                    yaxis=dict(tickfont=dict(size=13, color="#111827")))
            st.plotly_chart(fig_hm_cm, use_container_width=True)

    with st.expander(f"{_met_lbl} mínimo por cadena y marca", expanded=True):
        df_min_cm = dff_c3.dropna(subset=["_met"]).groupby(["Marca_cat", "Cadena"])["_met"].min().reset_index()
        df_min_cm["Marca_cat"] = pd.Categorical(df_min_cm["Marca_cat"],
                                                 categories=ORDEN_MARCAS_AC, ordered=True)
        df_min_cm = df_min_cm.sort_values("Marca_cat")
        fig_min = px.bar(df_min_cm, x="Marca_cat", y="_met", color="Cadena",
                         barmode="group", color_discrete_map=COLORS_CADENAS,
                         labels={"_met": f"{_met_lbl} mínimo", "Marca_cat": ""},
                         height=420, category_orders={"Marca_cat": ORDEN_MARCAS_AC})
        fig_min.update_layout(**_BASE_CORE,
                              yaxis=dict(tickprefix="$", tickformat=",",
                                         tickfont=dict(size=12, color="#111827")),
                              xaxis=dict(tickfont=dict(size=13, color="#111827"), tickangle=-20))
        st.plotly_chart(fig_min, use_container_width=True)


# ── TAB 4: Por Marca ──────────────────────────────────────────────────────
if active_page == "Por Marca":
    _mk_fv, _mk_fg, _mk_fe = st.columns(3)
    with _mk_fv:
        st.markdown('<p style="color:#111827;font-size:0.8rem;font-weight:600;margin-bottom:2px">Variedad</p>', unsafe_allow_html=True)
        var_mk = st.selectbox("Variedad", ["Todas"] + variedades_disp, key="mk_var", label_visibility="collapsed")
    with _mk_fg:
        st.markdown('<p style="color:#111827;font-size:0.8rem;font-weight:600;margin-bottom:2px">Gramaje</p>', unsafe_allow_html=True)
        gram_mk_labels = ["Todos"] + grupos_labels
        gram_mk_sel    = st.selectbox("Gramaje", gram_mk_labels, key="mk_gram", label_visibility="collapsed")
    with _mk_fe:
        st.markdown('<p style="color:#111827;font-size:0.8rem;font-weight:600;margin-bottom:2px">Envase</p>', unsafe_allow_html=True)
        envase_mk_sel = st.selectbox("Envase", ["Todos"] + envases_disp, key="mk_envase", label_visibility="collapsed")

    dff_mk = dff.copy()
    if var_mk != "Todas":
        dff_mk = dff_mk[dff_mk["Variedad"] == var_mk]
    if gram_mk_sel != "Todos":
        gram_mk_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == gram_mk_sel), None)
        if gram_mk_key:
            dff_mk = dff_mk[dff_mk["Gramaje"] == gram_mk_key]
    if envase_mk_sel != "Todos":
        dff_mk = dff_mk[dff_mk["Envase"] == envase_mk_sel]

    with st.expander("📊 Ranking y distribución de marcas", expanded=True):
        c_l, c_r = st.columns(2)
        with c_l:
            st.markdown(f'<div class="chart-title">Ranking de marcas por {_met_lbl} promedio</div>',
                        unsafe_allow_html=True)
            mk_p = (dff_mk.dropna(subset=["_met"])
                    .groupby("Marca_cat")["_met"].mean().sort_values().reset_index())
            _mk_colors = [COLORES_MARCA_AC.get(m, "#6B7280") for m in mk_p["Marca_cat"]]
            fig_mk = hbar(mk_p["_met"].tolist(), mk_p["Marca_cat"].tolist(),
                          _mk_colors,
                          [f"${v:,.0f}" for v in mk_p["_met"]], _met_lbl,
                          altura=max(300, len(mk_p) * 34))
            st.plotly_chart(fig_mk, use_container_width=True)

        with c_r:
            st.markdown('<div class="chart-title">SKUs únicos en góndola por marca</div>',
                        unsafe_allow_html=True)
            mk_sku = (dff_mk.groupby("Marca_cat")["SKU_canonico"]
                      .nunique().reset_index(name="SKUs")
                      .sort_values("SKUs", ascending=False))
            fig_sku = go.Figure(go.Bar(
                x=mk_sku["Marca_cat"], y=mk_sku["SKUs"],
                marker_color=[COLORES_MARCA_AC.get(m, "#6B7280") for m in mk_sku["Marca_cat"]],
                text=mk_sku["SKUs"], textposition="outside",
                textfont=dict(color="#111827"),
            ))
            fig_sku.update_layout(**_BASE_CORE, height=340,
                                  margin=dict(l=10, r=10, t=40, b=10),
                                  yaxis_title="SKUs únicos", showlegend=False,
                                  xaxis=dict(tickfont=dict(color="#111827")))
            st.plotly_chart(fig_sku, use_container_width=True)

    with st.expander("🌡️ Heatmap marca × cadena", expanded=True):
        st.markdown(f'<div class="chart-title">Heatmap marca × cadena ({_met_lbl} promedio)</div>',
                    unsafe_allow_html=True)
        pivot_mk_c = (dff_mk.dropna(subset=["_met"])
                      .groupby(["Marca_cat", "Cadena"])["_met"]
                      .mean().round(0).unstack("Cadena"))
        pivot_mk_c = pivot_mk_c.reindex([m for m in ORDEN_MARCAS_AC if m in pivot_mk_c.index])
        if not pivot_mk_c.empty:
            text_mk_c = [[f"${v:,.0f}" if not pd.isna(v) else "—" for v in row]
                         for row in pivot_mk_c.values]
            fig_hm_mk = go.Figure(go.Heatmap(
                z=pivot_mk_c.values, x=pivot_mk_c.columns.tolist(), y=pivot_mk_c.index.tolist(),
                colorscale="RdYlGn_r",
                text=text_mk_c, texttemplate="%{text}",
                textfont=dict(size=12, color="#111827"),
                colorbar=dict(title=_met_lbl, tickprefix="$", tickformat=",",
                              tickfont=dict(color="#111827"),
                              title_font=dict(color="#111827")),
            ))
            fig_hm_mk.update_layout(**_BASE_CORE,
                                    height=max(300, len(pivot_mk_c) * 40 + 80),
                                    margin=dict(l=10, r=10, t=30, b=10),
                                    xaxis=dict(tickfont=dict(size=13, color="#111827")),
                                    yaxis=dict(tickfont=dict(size=13, color="#111827")))
            st.plotly_chart(fig_hm_mk, use_container_width=True)

    with st.expander("📋 Resumen por marca", expanded=False):
        mk_resumen = (dff_mk.groupby("Marca_cat").agg(
            SKUs=("SKU_canonico", "nunique"),
            Precio_prom=("_met", "mean"),
            En_oferta_pct=("En_oferta", lambda s: s.mean() * 100),
            Cadenas=("Cadena", "nunique"),
            Variedades=("Variedad", "nunique"),
        ).round(1).reset_index().sort_values("SKUs", ascending=False))
        mk_resumen["Precio_prom"] = mk_resumen["Precio_prom"].apply(
            lambda v: f"${v:,.0f}" if pd.notna(v) else "—")
        mk_resumen["En_oferta_pct"] = mk_resumen["En_oferta_pct"].apply(lambda v: f"{v:.0f}%")
        mk_resumen.columns = ["Marca", "SKUs únicos", f"{_met_lbl} prom.", "% en oferta",
                              "Cadenas presentes", "Variedades"]
        st.dataframe(mk_resumen, use_container_width=True, hide_index=True)


# ── TAB 5: Evolución ──────────────────────────────────────────────────────
if active_page == "Evolución":

    _ev_base = dff.dropna(subset=["Precio_100g"]).copy()

    # Deduplicar: si hay 2 scrapes en el mismo día, quedarse con el último
    _ev_base["Fecha_dia"] = pd.to_datetime(_ev_base["Fecha"]).dt.date
    _ev_base = (
        _ev_base.sort_values("Fecha")
        .drop_duplicates(subset=["Fecha_dia", "Cadena", "Producto"], keep="last")
        .copy()
    )

    def _agg_fecha_ev(df: pd.DataFrame, gran: str) -> pd.DataFrame:
        """Devuelve df con columna '_fev' = fecha agrupada según granularidad."""
        df = df.copy()
        fechas = pd.to_datetime(df["Fecha_dia"])
        if gran == "Semana":
            df["_fev"] = fechas.dt.to_period("W-MON").dt.start_time.dt.date
        elif gran == "Mes":
            df["_fev"] = fechas.dt.to_period("M").dt.start_time.dt.date
        else:
            df["_fev"] = df["Fecha_dia"]
        return df

    _marcas_ev_disp  = sorted(_ev_base["Marca_cat"].dropna().unique())
    _vars_ev_disp    = sorted(_ev_base["Variedad"].dropna().unique())
    _skus_ev_disp    = sorted(_ev_base["Producto"].dropna().unique())

    def _ev_layout(height=400, legend_override=None, gran="Día", tickvals=None):
        base = {**_BASE_CORE}
        if gran == "Mes":
            x_fmt, x_dtick = "%b '%y", "M1"
        elif gran == "Semana":
            x_fmt, x_dtick = "%d %b '%y", "D7"
        else:
            x_fmt, x_dtick = "%d %b '%y", "D1"
        xaxis_cfg = dict(tickfont=dict(color="#111827"), type="date",
                         tickformat=x_fmt, dtick=x_dtick)
        if tickvals is not None:
            xaxis_cfg.update(tickmode="array", tickvals=tickvals)
        base.update(dict(
            height=height,
            margin=dict(l=10, r=10, t=40, b=10),
            yaxis=dict(tickprefix="$", tickformat=",", tickfont=dict(color="#111827")),
            xaxis=xaxis_cfg,
        ))
        if legend_override:
            base["legend"] = legend_override
        return base

    # ── Gráfico 1: Evolución por Marca ──────────────────────────────────────
    with st.expander("📈 Evolución de precio por Marca ($/kg)", expanded=True):
        # — Toggle granularidad —
        _g1_col_gran, _ = st.columns([2, 8])
        with _g1_col_gran:
            _ev1_gran = st.radio("Ver por", ["Día", "Semana", "Mes"],
                                 horizontal=True, key="ev1_gran")
        # — Filtros —
        _f1c1, _f1c2, _f1c3, _f1c4, _f1c5 = st.columns(5)
        with _f1c1:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">Gramaje</p>', unsafe_allow_html=True)
            _ev1_gram_lbl = st.selectbox("Gramaje", ["Todos"] + grupos_labels, key="ev1_gram", label_visibility="collapsed")
        with _f1c2:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">Variedad</p>', unsafe_allow_html=True)
            _ev1_var = st.selectbox("Variedad", ["Todas"] + _vars_ev_disp, key="ev1_var", label_visibility="collapsed")
        with _f1c3:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">Marca</p>', unsafe_allow_html=True)
            _ev1_marcas = st.multiselect("Marca", _marcas_ev_disp, default=_marcas_ev_disp[:6], key="ev1_marca", label_visibility="collapsed")
        with _f1c4:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">Envase</p>', unsafe_allow_html=True)
            _ev1_envase = st.selectbox("Envase", ["Todos"] + envases_disp, key="ev1_envase", label_visibility="collapsed")
        with _f1c5:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">SKU</p>', unsafe_allow_html=True)
            _ev1_sku = st.selectbox("SKU", ["Todos"] + list(_skus_ev_disp), key="ev1_sku", label_visibility="collapsed")

        _d1 = _ev_base.copy()
        if _ev1_gram_lbl != "Todos":
            _gk1 = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _ev1_gram_lbl), None)
            if _gk1: _d1 = _d1[_d1["Gramaje"] == _gk1]
        if _ev1_var != "Todas":
            _d1 = _d1[_d1["Variedad"] == _ev1_var]
        if _ev1_marcas:
            _d1 = _d1[_d1["Marca_cat"].isin(_ev1_marcas)]
        if _ev1_envase != "Todos":
            _d1 = _d1[_d1["Envase"] == _ev1_envase]
        if _ev1_sku != "Todos":
            _d1 = _d1[_d1["Producto"] == _ev1_sku]

        if _d1.empty:
            st.info("Sin datos con esta selección.")
        else:
            _d1 = _agg_fecha_ev(_d1, _ev1_gran)
            _grp1 = (_d1.groupby(["_fev", "Marca_cat"])["Precio_100g"]
                     .mean().mul(10).round(0).reset_index()
                     .rename(columns={"_fev": "Fecha"}))
            _fig1 = go.Figure()
            for _m in sorted(_grp1["Marca_cat"].unique()):
                _sub = _grp1[_grp1["Marca_cat"] == _m].sort_values("Fecha")
                _col = COLORES_MARCA_AC.get(_m, "#9CA3AF")
                _fig1.add_trace(go.Scatter(
                    x=_sub["Fecha"], y=_sub["Precio_100g"],
                    mode="lines+markers", name=_m,
                    line=dict(color=_col, width=2),
                    marker=dict(size=6),
                ))
            _tv1 = sorted(_grp1["Fecha"].unique())
            _fig1.update_layout(**_ev_layout(420, gran=_ev1_gran, tickvals=_tv1))
            st.plotly_chart(_fig1, use_container_width=True)

    # ── Gráfico 2: Evolución por SKU (producto individual) ──────────────────
    with st.expander("🔍 Evolución de precio por SKU ($/kg)", expanded=True):
        # — Toggle granularidad —
        _g2_col_gran, _ = st.columns([2, 8])
        with _g2_col_gran:
            _ev2_gran = st.radio("Ver por", ["Día", "Semana", "Mes"],
                                 horizontal=True, key="ev2_gran")
        # — Filtros —
        _f2c1, _f2c2, _f2c3, _f2c4, _f2c5 = st.columns(5)
        with _f2c1:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">Gramaje</p>', unsafe_allow_html=True)
            _ev2_gram_lbl = st.selectbox("Gramaje", ["Todos"] + grupos_labels, key="ev2_gram", label_visibility="collapsed")
        with _f2c2:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">Variedad</p>', unsafe_allow_html=True)
            _ev2_var = st.selectbox("Variedad", ["Todas"] + _vars_ev_disp, key="ev2_var", label_visibility="collapsed")
        with _f2c3:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">Marca</p>', unsafe_allow_html=True)
            _ev2_marca = st.selectbox("Marca", ["Todas"] + _marcas_ev_disp, key="ev2_marca", label_visibility="collapsed")
        with _f2c4:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">Envase</p>', unsafe_allow_html=True)
            _ev2_envase = st.selectbox("Envase", ["Todos"] + envases_disp, key="ev2_envase", label_visibility="collapsed")
        with _f2c5:
            st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#111827;margin-bottom:2px">SKU</p>', unsafe_allow_html=True)
            _ev2_sku_opts = sorted(_ev_base["Producto"].dropna().unique())
            _ev2_skus = st.multiselect("SKU", _ev2_sku_opts, default=[], key="ev2_sku",
                                       placeholder="Elegí productos…", label_visibility="collapsed")

        _d2 = _ev_base.copy()
        if _ev2_gram_lbl != "Todos":
            _gk2 = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _ev2_gram_lbl), None)
            if _gk2: _d2 = _d2[_d2["Gramaje"] == _gk2]
        if _ev2_var != "Todas":
            _d2 = _d2[_d2["Variedad"] == _ev2_var]
        if _ev2_marca != "Todas":
            _d2 = _d2[_d2["Marca_cat"] == _ev2_marca]
        if _ev2_envase != "Todos":
            _d2 = _d2[_d2["Envase"] == _ev2_envase]
        if _ev2_skus:
            _d2 = _d2[_d2["Producto"].isin(_ev2_skus)]

        if _d2.empty or (not _ev2_skus and _ev2_marca == "Todas" and _ev2_var == "Todas"):
            st.info("Usá los filtros de arriba para elegir productos específicos a comparar.")
        else:
            _d2 = _agg_fecha_ev(_d2, _ev2_gran)
            _grp2 = (_d2.groupby(["_fev", "Producto"])["Precio_100g"]
                     .mean().mul(10).round(0).reset_index()
                     .rename(columns={"_fev": "Fecha"}))
            _fig2 = go.Figure()
            _palette = ["#0F3460","#16A34A","#DC2626","#D97706","#7C3AED",
                        "#0891B2","#DB2777","#65A30D","#EA580C","#0284C7"]
            for _i, _prod in enumerate(_grp2["Producto"].unique()):
                _sub2 = _grp2[_grp2["Producto"] == _prod].sort_values("Fecha")
                _col2 = _palette[_i % len(_palette)]
                # Nombre corto para la leyenda
                _lbl = _prod if len(_prod) <= 45 else _prod[:43] + "…"
                _fig2.add_trace(go.Scatter(
                    x=_sub2["Fecha"], y=_sub2["Precio_100g"],
                    mode="lines+markers", name=_lbl,
                    line=dict(color=_col2, width=2),
                    marker=dict(size=6),
                    hovertemplate=f"<b>{_prod}</b><br>%{{x|%d %b %Y}}<br>${{y:,.0f}}/kg<extra></extra>",
                ))
            _tv2 = sorted(_grp2["Fecha"].unique())
            _fig2.update_layout(**_ev_layout(450, gran=_ev2_gran, tickvals=_tv2,
                                             legend_override=dict(
                orientation="v", x=1.01, xanchor="left",
                font=dict(size=10, color="#111827"), bgcolor="rgba(0,0,0,0)")))
            st.plotly_chart(_fig2, use_container_width=True)


# ── TAB 6: Ofertas ────────────────────────────────────────────────────────
if active_page == "__OfertasLegacy__":
    df_of_ult = df_ult[df_ult["En_oferta"]].copy()
    if df_of_ult.empty:
        st.info("Sin productos en oferta en la última semana.")
    else:
        df_of_ult = df_of_ult.sort_values("Descuento_pct", ascending=False)

        # ── Barra resumen de ofertas ──────────────────────────────────
        _n_of      = len(df_of_ult)
        _pct_of    = _n_of / len(df_ult) * 100 if len(df_ult) > 0 else 0
        _dto_prom  = df_of_ult["Descuento_pct"].mean()
        _dto_max   = df_of_ult["Descuento_pct"].max()
        _cad_of    = df_of_ult["Cadena"].nunique()
        _marca_top_of = (df_of_ult["Marca_cat"].value_counts().index[0]
                         if not df_of_ult["Marca_cat"].value_counts().empty else "—")
        _n_marca_top  = (df_of_ult["Marca_cat"].value_counts().iloc[0]
                         if not df_of_ult["Marca_cat"].value_counts().empty else 0)
        _oc1, _oc2, _oc3, _oc4, _oc5, _oc6 = st.columns(6)
        with _oc1:
            _kpi_mini("🏷️", "Ofertas activas", str(_n_of), "productos en descuento")
        with _oc2:
            _kpi_mini("📊", "% del catálogo", f"{_pct_of:.0f}%", "SKUs con oferta")
        with _oc3:
            _kpi_mini("📉", "Dto. promedio", f"{_dto_prom:.0f}%", "sobre precio góndola")
        with _oc4:
            _kpi_mini("🔥", "Dto. máximo", f"{_dto_max:.0f}%", "mayor descuento activo")
        with _oc5:
            _kpi_mini("🏪", "Cadenas activas", str(_cad_of), "con productos en oferta")
        with _oc6:
            _kpi_mini("🏆", "Marca con más", _marca_top_of, f"{_n_marca_top} ofertas")
        st.markdown("---")

        with st.expander("📊 Descuentos por cadena y variedad", expanded=True):
            c_l, c_r = st.columns(2)
            with c_l:
                of_cad = (df_of_ult.groupby("Cadena")["Descuento_pct"]
                          .mean().sort_values(ascending=False).reset_index())
                fig_of2 = go.Figure(go.Bar(
                    x=of_cad["Cadena"], y=of_cad["Descuento_pct"],
                    marker_color=[cc(c) for c in of_cad["Cadena"]],
                    text=[f"{v:.0f}%" for v in of_cad["Descuento_pct"]],
                    textposition="outside", textfont=dict(color="#111827"),
                ))
                fig_of2.update_layout(**_BASE_CORE, height=340,
                                      margin=dict(l=10, r=10, t=40, b=10),
                                      yaxis=dict(title="% descuento promedio",
                                                 tickfont=dict(color="#111827")),
                                      xaxis=dict(tickfont=dict(color="#111827")),
                                      showlegend=False)
                st.plotly_chart(fig_of2, use_container_width=True)

            with c_r:
                of_var = (df_of_ult.groupby("Variedad")["Descuento_pct"]
                          .mean().sort_values(ascending=False).reset_index())
                fig_of_var = go.Figure(go.Bar(
                    x=of_var["Variedad"], y=of_var["Descuento_pct"],
                    marker_color=[cv(v) for v in of_var["Variedad"]],
                    text=[f"{v:.0f}%" for v in of_var["Descuento_pct"]],
                    textposition="outside", textfont=dict(color="#111827"),
                ))
                fig_of_var.update_layout(**_BASE_CORE, height=340,
                                         margin=dict(l=10, r=10, t=40, b=10),
                                         yaxis=dict(title="% descuento promedio",
                                                    tickfont=dict(color="#111827")),
                                         xaxis=dict(tickfont=dict(color="#111827"), tickangle=-20),
                                         showlegend=False)
                st.plotly_chart(fig_of_var, use_container_width=True)

        with st.expander("🔖 Detalle de ofertas activas", expanded=True):
            _of_ord_col, _ = st.columns([1, 3])
            with _of_ord_col:
                st.markdown('<p style="color:#111827;font-size:0.82rem;font-weight:700;margin-bottom:2px">🔃 Ordenar por</p>', unsafe_allow_html=True)
                _of_orden = st.radio("Ordenar por", ["Mayor descuento", "Marca"],
                                     horizontal=True, key="of_orden", label_visibility="collapsed")
            _df_of_cards = df_of_ult[["Cadena", "Marca_cat", "SKU_canonico", "Producto",
                                       "Descuento_pct", "Precio", "Precio_oferta", "URL"]].copy()
            if _of_orden == "Marca":
                _marca_orden_map = {m: i for i, m in enumerate(ORDEN_MARCAS_AC)}
                _df_of_cards["_mk_ord"] = _df_of_cards["Marca_cat"].map(_marca_orden_map).fillna(99)
                _df_of_cards = _df_of_cards.sort_values(["_mk_ord", "SKU_canonico"]).drop(columns="_mk_ord")
            render_offer_cards(_df_of_cards, compact=False, grid_cols=3, max_height=600)


# ── TAB 7: Quiebres ───────────────────────────────────────────────────────
if active_page == "Ofertas":
    _todos_periodos_of = sorted(
        df_full["Periodo"].unique(),
        key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min(),
    )
    _periodos_of_default = [_todos_periodos_of[-1]] if _todos_periodos_of else []
    _of_f1, _of_f2, _of_f3, _of_f4 = st.columns([2.2, 1.4, 1.4, 1.3])
    with _of_f1:
        _periodos_of_sel = st.multiselect(
            "Semanas / Meses",
            _todos_periodos_of,
            default=_periodos_of_default,
            key="periodos_of_aceitunas",
        )
    with _of_f2:
        _of_var_sel = st.selectbox("Variedad", ["Todas"] + variedades_disp, key="of_var_aceitunas")
    with _of_f3:
        _of_gram_sel = st.selectbox("Gramaje", ["Todos"] + grupos_labels, key="of_gram_aceitunas")
    with _of_f4:
        _of_envase_sel = st.selectbox("Envase", ["Todos"] + envases_disp, key="of_envase_aceitunas")

    _periodos_of_activos = _periodos_of_sel if _periodos_of_sel else _periodos_of_default
    _of_gram_key = None
    if _of_gram_sel != "Todos":
        _of_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _of_gram_sel), None)

    _mask_of = (
        df_full["Periodo"].isin(_periodos_of_activos)
        & df_full["Cadena"].isin(cadenas_sel)
        & df_full["Variedad"].isin(variedades_sel)
        & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
        & df_full["Envase"].isin(envases_sel)
        & df_full["En_oferta"]
    )
    if _of_var_sel != "Todas":
        _mask_of &= df_full["Variedad"].eq(_of_var_sel)
    if _of_gram_key:
        _mask_of &= df_full["Gramaje"].eq(_of_gram_key)
    if _of_envase_sel != "Todos":
        _mask_of &= df_full["Envase"].eq(_of_envase_sel)

    df_of5 = df_full[_mask_of].copy()
    _orden_per_of5 = [p for p in _todos_periodos_of if p in _periodos_of_activos]
    _fecha_hoy = df_of5["Fecha"].max() if not df_of5.empty else df_full["Fecha"].max()
    df_of5_hoy = df_of5[df_of5["Fecha"] == _fecha_hoy].copy()

    _precio_gondola_lbl = "$/kg góndola" if _met_kg else "Precio góndola ($)"
    _precio_oferta_lbl = "$/kg oferta" if _met_kg else "Precio oferta ($)"
    _precio_gondola_prom_lbl = "$/kg góndola prom." if _met_kg else "Precio góndola prom."
    _precio_oferta_prom_lbl = "$/kg oferta prom." if _met_kg else "Precio oferta prom."

    if df_of5.empty:
        st.info("No hay productos en oferta con los filtros actuales.")
    else:
        with st.expander("Resumen de ofertas de hoy", expanded=True):
            _src_kpi = df_of5_hoy if not df_of5_hoy.empty else df_of5
            _lbl_hoy = _fecha_hoy.strftime("%d/%m/%Y") if hasattr(_fecha_hoy, "strftime") else str(_fecha_hoy)
            _oferta_prom = _src_kpi["_met_of"].dropna().mean()
            _gondola_prom = _src_kpi["_met"].dropna().mean()
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#7C2D12,#C2410C);border-radius:14px;
                        padding:1.2rem 2rem;margin-bottom:1.2rem;display:flex;gap:3rem;align-items:center">
              <div>
                <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:1px;color:rgba(255,255,255,0.6)">Ofertas hoy · {_lbl_hoy}</div>
                <div style="font-size:2rem;font-weight:800;color:#fff">{len(_src_kpi):,}</div>
              </div>
              <div>
                <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:1px;color:rgba(255,255,255,0.6)">Descuento promedio</div>
                <div style="font-size:2rem;font-weight:800;color:#fff">{_src_kpi["Descuento_pct"].mean():.0f}%</div>
              </div>
              <div>
                <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:1px;color:rgba(255,255,255,0.6)">{_precio_oferta_prom_lbl}</div>
                <div style="font-size:2rem;font-weight:800;color:#fff">{f"${_oferta_prom:,.0f}" if pd.notna(_oferta_prom) else "—"}</div>
              </div>
              <div>
                <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:1px;color:rgba(255,255,255,0.6)">{_precio_gondola_prom_lbl}</div>
                <div style="font-size:2rem;font-weight:800;color:rgba(255,255,255,0.7)">{f"${_gondola_prom:,.0f}" if pd.notna(_gondola_prom) else "—"}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            col_l, col_r = st.columns([1, 1], gap="large")
            with col_l:
                df_desc_c = (_src_kpi.groupby("Cadena")["Descuento_pct"].mean().reset_index().sort_values("Descuento_pct"))
                fig = go.Figure(go.Bar(
                    x=df_desc_c["Descuento_pct"],
                    y=df_desc_c["Cadena"],
                    orientation="h",
                    marker_color=[cc(c) for c in df_desc_c["Cadena"]],
                    text=[f"{v:.0f}%" for v in df_desc_c["Descuento_pct"]],
                    textposition="outside",
                    textfont=dict(size=13, color="#111827"),
                    cliponaxis=False,
                ))
                _vmax_d = df_desc_c["Descuento_pct"].max() if not df_desc_c.empty else 1
                fig.update_layout(**_BASE_CORE,
                                  height=320,
                                  margin=dict(l=10, r=120, t=40, b=10),
                                  xaxis=dict(title="Descuento %", ticksuffix="%",
                                             tickfont=dict(size=12, color="#111827"),
                                             range=[0, _vmax_d * 1.4 if _vmax_d else 1]),
                                  yaxis=dict(tickfont=dict(size=13, color="#111827")),
                                  showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col_r:
                df_of_cnt = _src_kpi.groupby("Cadena").size().reset_index(name="n")
                fig = go.Figure(go.Pie(
                    labels=df_of_cnt["Cadena"],
                    values=df_of_cnt["n"],
                    marker_colors=[cc(c) for c in df_of_cnt["Cadena"]],
                    hole=0.55,
                    textinfo="label+percent",
                    textposition="outside",
                    textfont=dict(size=12, color="#111827"),
                ))
                fig.update_layout(**_BASE_CORE, height=320, margin=dict(l=10, r=10, t=40, b=40), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        with st.expander("Precio góndola vs precio oferta por marca", expanded=True):
            st.markdown('<div class="chart-note">La diferencia entre las barras = ahorro de la oferta</div>',
                        unsafe_allow_html=True)
            _gvof_gram_opts = [l for g, l in zip(grupos_disp, grupos_labels) if df_of5["Gramaje"].eq(g).any()]
            _gvof_gram_sel = st.selectbox("Gramaje", ["Todos"] + _gvof_gram_opts, key="gram_gvof_aceitunas")
            _df_gvof_src = df_of5.copy()
            if _gvof_gram_sel != "Todos":
                _gvof_gram_key = next((g for g, l in zip(grupos_disp, grupos_labels) if l == _gvof_gram_sel), None)
                if _gvof_gram_key:
                    _df_gvof_src = _df_gvof_src[_df_gvof_src["Gramaje"] == _gvof_gram_key]
            _df_gvof_src = _df_gvof_src[~_df_gvof_src["Marca"].isin(_MARCAS_AGREGADAS_EXCLUIDAS_AC)].copy()
            if _df_gvof_src.empty:
                st.info("Sin ofertas para la selección actual.")
            else:
                df_gvof = (_df_gvof_src.groupby("Marca")
                                      .agg(gondola=("_met", "mean"), oferta=("_met_of", "mean"))
                                      .reset_index())
                df_gvof = df_gvof.sort_values("Marca", key=lambda s: s.map(marca_sort_key_ac))
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name="Precio góndola",
                    x=df_gvof["Marca"],
                    y=df_gvof["gondola"],
                    marker_color="#D1D5DB",
                    text=[f"${v:,.0f}" for v in df_gvof["gondola"]],
                    textposition="outside",
                    textfont=dict(size=12, color="#374151"),
                ))
                fig.add_trace(go.Bar(
                    name="Precio oferta",
                    x=df_gvof["Marca"],
                    y=df_gvof["oferta"],
                    marker_color=[color_marca_real_ac(m) for m in df_gvof["Marca"]],
                    text=[f"${v:,.0f}" for v in df_gvof["oferta"]],
                    textposition="outside",
                    textfont=dict(size=12, color="#111827"),
                ))
                _ymax = df_gvof["gondola"].max() if not df_gvof.empty else 1
                fig.update_layout(**BASE,
                                  barmode="overlay",
                                  height=420,
                                  yaxis=dict(title=_met_lbl, tickprefix="$", tickformat=",",
                                             tickfont=dict(size=12, color="#111827"),
                                             range=[0, _ymax * 1.25 if _ymax else 1]),
                                  xaxis=dict(tickfont=dict(size=13, color="#111827"), tickangle=-20))
                st.plotly_chart(fig, use_container_width=True)

        if df_of5["Periodo"].nunique() >= 2:
            with st.expander("Ofertas en el tiempo por marca & cadena", expanded=True):
                col_ol, col_or = st.columns(2, gap="large")
                _df_brand_time = df_of5[~df_of5["Marca_cat"].isin(_MARCAS_AGREGADAS_EXCLUIDAS_AC)].copy()
                if _df_brand_time.empty:
                    _df_brand_time = df_of5.copy()

                with col_ol:
                    df_of_t_m = (_df_brand_time.groupby(["Periodo", "Marca_cat"]).size().reset_index(name="n"))
                    df_of_t_m["Periodo"] = pd.Categorical(df_of_t_m["Periodo"], categories=_orden_per_of5, ordered=True)
                    fig = px.bar(df_of_t_m, x="Periodo", y="n", color="Marca_cat", barmode="stack",
                                 color_discrete_map=COLORES_MARCA_AC, labels={"n": "Cantidad de ofertas", "Periodo": ""},
                                 height=380, category_orders={"Marca_cat": ORDEN_MARCAS_AC})
                    fig.update_layout(**BASE,
                                      xaxis=dict(tickfont=dict(size=12, color="#111827"), tickangle=-20),
                                      yaxis=dict(tickfont=dict(size=12, color="#111827")))
                    st.plotly_chart(fig, use_container_width=True)

                with col_or:
                    df_of_t_c = (df_of5.groupby(["Periodo", "Cadena"]).size().reset_index(name="n"))
                    df_of_t_c["Periodo"] = pd.Categorical(df_of_t_c["Periodo"], categories=_orden_per_of5, ordered=True)
                    fig = px.bar(df_of_t_c, x="Periodo", y="n", color="Cadena", barmode="stack",
                                 color_discrete_map=COLORS_CADENAS, labels={"n": "Cantidad de ofertas", "Periodo": ""},
                                 height=380)
                    fig.update_layout(**BASE,
                                      xaxis=dict(tickfont=dict(size=12, color="#111827"), tickangle=-20),
                                      yaxis=dict(tickfont=dict(size=12, color="#111827")))
                    st.plotly_chart(fig, use_container_width=True)

        with st.expander("Top 20 · Mejores descuentos del período", expanded=True):
            df_top = (
                df_of5.sort_values("Descuento_pct", ascending=False)
                .head(20)[["Cadena", "Marca", "Producto", "Variedad", "Envase", "Gramaje", "_met", "_met_of", "Descuento_pct"]]
                .copy()
            )
            df_top.columns = ["Cadena", "Marca", "Producto", "Variedad", "Envase", "Gramaje",
                              _precio_gondola_lbl, _precio_oferta_lbl, "Descuento %"]
            st.dataframe(
                df_top,
                height=420,
                column_config={
                    _precio_gondola_lbl: st.column_config.NumberColumn(format="$%d"),
                    _precio_oferta_lbl: st.column_config.NumberColumn(format="$%d"),
                    "Descuento %": st.column_config.NumberColumn(format="%.0f%%"),
                },
                hide_index=True,
            )

        with st.expander("Presencia de ofertas · marcas seleccionadas", expanded=True):
            st.markdown('<div class="chart-note">✓ = hubo oferta ese período · — = sin oferta</div>',
                        unsafe_allow_html=True)
            _marcas_of2_base = df_full[
                df_full["Periodo"].isin(_periodos_of_activos)
                & df_full["Cadena"].isin(cadenas_sel)
                & df_full["Variedad"].isin(variedades_sel)
                & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
                & df_full["Envase"].isin(envases_sel)
            ].copy()
            if _of_var_sel != "Todas":
                _marcas_of2_base = _marcas_of2_base[_marcas_of2_base["Variedad"] == _of_var_sel]
            if _of_gram_key:
                _marcas_of2_base = _marcas_of2_base[_marcas_of2_base["Gramaje"] == _of_gram_key]
            if _of_envase_sel != "Todos":
                _marcas_of2_base = _marcas_of2_base[_marcas_of2_base["Envase"] == _of_envase_sel]

            _marcas_of2_disp = sorted(_marcas_of2_base["Marca"].dropna().unique(), key=marca_sort_key_ac)
            _marcas_of2_default = [m for m in ["La Toscana", "Castell", "Nucete"] if m in _marcas_of2_disp]
            if not _marcas_of2_default:
                _marcas_of2_default = _marcas_of2_disp[:3]

            _of2_fa, _of2_fb, _of2_fc = st.columns([2.2, 1.6, 1.2])
            with _of2_fa:
                _marcas_of2_sel = st.multiselect(
                    "Marca", _marcas_of2_disp, default=_marcas_of2_default,
                    key="of2_marcas_aceitunas", placeholder="Elegí marcas",
                )
            _cadenas_of2_disp = sorted(_marcas_of2_base["Cadena"].dropna().unique())
            with _of2_fb:
                _cadenas_of2_sel = st.multiselect(
                    "Cadena", _cadenas_of2_disp, default=_cadenas_of2_disp,
                    key="of2_cadenas_aceitunas", placeholder="Todas las cadenas",
                )
            with _of2_fc:
                _of2_gran = st.selectbox("Temporalidad", ["Semanal", "Mensual"], key="of2_gran_aceitunas")

            _marcas_of2_act = _marcas_of2_sel if _marcas_of2_sel else _marcas_of2_default
            _cadenas_of2_act = _cadenas_of2_sel if _cadenas_of2_sel else _cadenas_of2_disp
            _df_dest = _marcas_of2_base[
                _marcas_of2_base["Marca"].isin(_marcas_of2_act)
                & _marcas_of2_base["Cadena"].isin(_cadenas_of2_act)
            ].copy()

            if _df_dest.empty:
                st.info("No hay SKUs para las marcas seleccionadas con estos filtros.")
            else:
                if _of2_gran == "Mensual":
                    _df_dest["_col_per"] = pd.to_datetime(_df_dest["Fecha"]).dt.strftime("%b %Y")
                    _pers_dest_ord = [
                        ts.strftime("%b %Y")
                        for ts in sorted(pd.to_datetime(_df_dest["Fecha"]).dt.to_period("M").dt.to_timestamp().unique())
                    ]
                else:
                    _df_dest["_col_per"] = _df_dest["Periodo"]
                    _pers_dest_ord = [p for p in _orden_per_of5 if p in set(_df_dest["Periodo"])]

                _of_mask_dest = (
                    df_full["En_oferta"]
                    & df_full["Marca"].isin(_marcas_of2_act)
                    & df_full["Periodo"].isin(_periodos_of_activos)
                    & df_full["Cadena"].isin(_cadenas_of2_act)
                    & df_full["Variedad"].isin(variedades_sel)
                    & (df_full["Gramaje"].isna() | df_full["Gramaje"].isin(buckets_sel))
                    & df_full["Envase"].isin(envases_sel)
                )
                if _of_var_sel != "Todas":
                    _of_mask_dest &= df_full["Variedad"].eq(_of_var_sel)
                if _of_gram_key:
                    _of_mask_dest &= df_full["Gramaje"].eq(_of_gram_key)
                if _of_envase_sel != "Todos":
                    _of_mask_dest &= df_full["Envase"].eq(_of_envase_sel)

                _df_of_mask = df_full[_of_mask_dest].copy()
                _df_of_mask["_col_per"] = (
                    pd.to_datetime(_df_of_mask["Fecha"]).dt.strftime("%b %Y")
                    if _of2_gran == "Mensual"
                    else _df_of_mask["Periodo"]
                )
                _skus_dest = sorted(_df_dest["SKU_canonico"].dropna().unique())
                _of_set = set(zip(_df_of_mask["SKU_canonico"], _df_of_mask["_col_per"]))
                _hmap_rows = []
                for _sk in _skus_dest:
                    _row = {"SKU": _sk}
                    for _pe in _pers_dest_ord:
                        _row[_pe] = "✓" if (_sk, _pe) in _of_set else "—"
                    _hmap_rows.append(_row)
                _hmap_df = pd.DataFrame(_hmap_rows).set_index("SKU")
                _hmap_num = _hmap_df.applymap(lambda x: 1.0 if x == "✓" else 0.0)
                fig_oh = go.Figure(go.Heatmap(
                    z=_hmap_num.values,
                    x=_pers_dest_ord,
                    y=_hmap_num.index.tolist(),
                    text=_hmap_df.values,
                    texttemplate="%{text}",
                    colorscale=[[0, "#F1F5F9"], [1, "#15803D"]],
                    zmin=0,
                    zmax=1,
                    showscale=False,
                    xgap=2,
                    ygap=2,
                    textfont=dict(size=11, color="#111827"),
                ))
                fig_oh.update_layout(**_BASE_CORE,
                                     height=max(120, len(_skus_dest) * 24 + 70),
                                     margin=dict(l=10, r=10, t=10, b=10),
                                     xaxis=dict(tickfont=dict(size=10, color="#374151"), tickangle=-30, side="top"),
                                     yaxis=dict(tickfont=dict(size=10, color="#374151"), autorange="reversed"))
                st.plotly_chart(fig_oh, use_container_width=True)

if active_page == "Quiebres":
    st.markdown(
        '<div class="chart-note">Un <b>quiebre</b> ocurre cuando un producto estaba disponible '
        'en un período y dejó de aparecer en el siguiente. '
        '✓ verde = presente &nbsp;·&nbsp; ✗ rojo = quiebre &nbsp;·&nbsp; — gris = sin datos.</div>',
        unsafe_allow_html=True,
    )

    _qb_colorscale = [
        [0.00, "#FCA5A5"], [0.33, "#FCA5A5"],
        [0.34, "#F3F4F6"], [0.66, "#F3F4F6"],
        [0.67, "#86EFAC"], [1.00, "#86EFAC"],
    ]

    _qb_fa, _qb_fb, _qb_fc, _ = st.columns([1, 1, 1, 3])
    with _qb_fa:
        st.markdown('<p style="color:#111827;font-size:0.82rem;font-weight:700;margin-bottom:1px">🏷️ Marca</p>', unsafe_allow_html=True)
        _qb_marca_opts = sorted(df_full["Marca_cat"].unique())
        _qb_marca = st.selectbox("Marca", _qb_marca_opts, key="qb_marca", label_visibility="collapsed")
    with _qb_fb:
        st.markdown('<p style="color:#111827;font-size:0.82rem;font-weight:700;margin-bottom:1px">🏪 Cadena</p>', unsafe_allow_html=True)
        _qb_cad_opts = ["Todas las cadenas"] + sorted(
            df_full[df_full["Marca_cat"] == _qb_marca]["Cadena"].unique()
        )
        _qb_cadena = st.selectbox("Cadena", _qb_cad_opts, key="qb_cadena", label_visibility="collapsed")
    with _qb_fc:
        st.markdown('<p style="color:#111827;font-size:0.82rem;font-weight:700;margin-bottom:1px">📅 Temporalidad</p>', unsafe_allow_html=True)
        _qb_gran = st.selectbox("Temporalidad", ["Semanal", "Mensual"], key="qb_gran", label_visibility="collapsed")

    _qb_src = df_full[df_full["Marca_cat"] == _qb_marca].copy()
    if _qb_cadena != "Todas las cadenas":
        _qb_src = _qb_src[_qb_src["Cadena"] == _qb_cadena].copy()

    if _qb_src.empty:
        st.info("Sin datos para la selección.")
    else:
        if _qb_gran == "Mensual":
            _qb_src["_pqb"] = _qb_src["Fecha"].dt.strftime("%b %Y")
            _seen_m: list = []
            for _x in (_qb_src[["Fecha", "_pqb"]].drop_duplicates()
                       .sort_values("Fecha")["_pqb"].tolist()):
                if _x not in _seen_m:
                    _seen_m.append(_x)
            _qb_cols_ord = _seen_m
        else:
            _qb_src["_pqb"] = _qb_src["Periodo"]
            _qb_cols_ord = sorted(
                _qb_src["_pqb"].unique(),
                key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min(),
            )

        _qb_pres  = _qb_src.groupby(["_pqb", "SKU_canonico"]).size().reset_index(name="_n")
        _qb_pivot = (
            _qb_pres.pivot(index="SKU_canonico", columns="_pqb", values="_n")
            .reindex(columns=[c for c in _qb_cols_ord if c in _qb_pres["_pqb"].unique()])
            .fillna(0)
        )

        if not _qb_pivot.empty:
            with st.expander("📅 Evolución de SKU por temporalidad", expanded=True):
                _qb_status = _qb_pivot.copy().astype(float)
                _qb_text   = _qb_pivot.copy().astype(object)
                for _ri in range(len(_qb_pivot)):
                    _seen_flag = False
                    for _ci in range(len(_qb_pivot.columns)):
                        _v = _qb_pivot.iloc[_ri, _ci]
                        if _v > 0:
                            _qb_status.iloc[_ri, _ci] = 1
                            _qb_text.iloc[_ri, _ci]   = "✓"
                            _seen_flag = True
                        elif _seen_flag:
                            _qb_status.iloc[_ri, _ci] = -1
                            _qb_text.iloc[_ri, _ci]   = "✗"
                        else:
                            _qb_status.iloc[_ri, _ci] = 0
                            _qb_text.iloc[_ri, _ci]   = "—"

                fig_qb = go.Figure(go.Heatmap(
                    z=_qb_status.values,
                    x=_qb_status.columns.tolist(),
                    y=_qb_status.index.tolist(),
                    colorscale=_qb_colorscale, zmin=-1, zmax=1,
                    text=_qb_text.values, texttemplate="%{text}",
                    textfont=dict(size=13, color="#111827"),
                    showscale=False, xgap=2, ygap=2,
                ))
                fig_qb.update_layout(**_BASE_CORE,
                                     height=max(280, len(_qb_pivot) * 40 + 100),
                                     xaxis=dict(tickfont=dict(size=11, color="#111827"),
                                                side="bottom", tickangle=-20),
                                     yaxis=dict(tickfont=dict(size=11, color="#111827")))
                st.plotly_chart(fig_qb, use_container_width=True)

                _qb_n_breaks = (_qb_status == -1).sum(axis=1)
                _qb_with_breaks = _qb_n_breaks[_qb_n_breaks > 0].sort_values(ascending=False)
                if not _qb_with_breaks.empty:
                    st.markdown('<div class="chart-title">Resumen de quiebres por SKU</div>',
                                unsafe_allow_html=True)
                    _qb_unit = {"Semanal": "semanas", "Mensual": "meses"}[_qb_gran]
                    _qb_rows = []
                    for _sk, _nb in _qb_with_breaks.items():
                        _per_afect = [_qb_status.columns[_ci]
                                      for _ci in range(len(_qb_status.columns))
                                      if _qb_status.loc[_sk, _qb_status.columns[_ci]] == -1]
                        _qb_rows.append({
                            "SKU": _sk,
                            f"Quiebres ({_qb_unit})": int(_nb),
                            "Períodos afectados": ", ".join(_per_afect),
                        })
                    _qb_col, _ = st.columns([3, 1])
                    with _qb_col:
                        st.dataframe(pd.DataFrame(_qb_rows), hide_index=True)
                else:
                    st.success("✅ No se detectaron quiebres en el período seleccionado.")

    # ── Presencia SKU × Cadena ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📍 Presencia por cadena — SKU × Cadena</div>',
                unsafe_allow_html=True)

    _qb_src_marca = df_full[df_full["Marca_cat"] == _qb_marca].copy()
    if not _qb_src_marca.empty:
        _qb_fechas_disp = sorted(df_full["Fecha"].unique())
        if _qb_gran == "Mensual":
            _seen_mes: dict = {}
            for _f in _qb_fechas_disp:
                _k = pd.Timestamp(_f).strftime("%b %Y")
                _seen_mes.setdefault(_k, []).append(_f)
            _qb_per_labels = list(_seen_mes.keys())
            _qb_per_map    = _seen_mes
        else:
            _seen_sem: dict = {}
            for _f in _qb_fechas_disp:
                _ts = pd.Timestamp(_f)
                _k  = f"Sem {_ts.isocalendar().week} · {_ts.strftime('%b %Y')}"
                _seen_sem.setdefault(_k, []).append(_f)
            _qb_per_labels = list(_seen_sem.keys())
            _qb_per_map    = _seen_sem

        _pres_lbl = st.selectbox("🗓️ Período a visualizar", _qb_per_labels,
                                  index=len(_qb_per_labels) - 1, key="qb_pres_ventana")
        _pres_fechas = _qb_per_map[_pres_lbl]

        st.markdown(
            f'<div class="chart-note">🟢 activo en <b>{_pres_lbl}</b> &nbsp;·&nbsp; '
            '🔴 estuvo antes pero no en este período &nbsp;·&nbsp; — nunca en esa cadena.</div>',
            unsafe_allow_html=True)

        _ventana_df    = _qb_src_marca[_qb_src_marca["Fecha"].isin(_pres_fechas)]
        _pres_set      = set(zip(_ventana_df["SKU_canonico"], _ventana_df["Cadena"]))
        _todos_skus    = sorted(_qb_src_marca["SKU_canonico"].unique())
        _todas_cad     = sorted(df_full["Cadena"].unique())
        _historial_set = set(zip(_qb_src_marca["SKU_canonico"], _qb_src_marca["Cadena"]))

        _z, _txt = [], []
        for _sk in _todos_skus:
            _rz, _rt = [], []
            for _cd in _todas_cad:
                if (_sk, _cd) in _pres_set:
                    _rz.append(1);  _rt.append("✓")
                elif (_sk, _cd) in _historial_set:
                    _rz.append(-1); _rt.append("✗")
                else:
                    _rz.append(0);  _rt.append("—")
            _z.append(_rz); _txt.append(_rt)

        fig_pres = go.Figure(go.Heatmap(
            z=_z, x=_todas_cad, y=_todos_skus,
            colorscale=_qb_colorscale, zmin=-1, zmax=1,
            text=_txt, texttemplate="%{text}",
            textfont=dict(size=13, color="#111827"),
            showscale=False, xgap=3, ygap=3,
        ))
        fig_pres.update_layout(**_BASE_CORE,
                               height=max(200, len(_todos_skus) * 38 + 80),
                               xaxis=dict(tickfont=dict(size=12, color="#111827"), side="top"),
                               yaxis=dict(tickfont=dict(size=11, color="#111827")))
        st.plotly_chart(fig_pres, use_container_width=True)


# ── TAB 8: Tabla dinámica ─────────────────────────────────────────────────
if active_page == "Tabla dinámica":
    c_row, c_col, c_met = st.columns(3)
    with c_row:
        pivot_fila = st.selectbox("Filas", ["Variedad", "Marca_cat", "Cadena", "Gramaje", "Envase"],
                                   format_func=lambda x: x.replace("Marca_cat", "Marca"),
                                   key="piv_row")
    with c_col:
        opciones_col = [o for o in ["Cadena", "Variedad", "Periodo"] if o != pivot_fila]
        pivot_col = st.selectbox("Columnas", opciones_col,
                                  format_func=lambda x: x.replace("Periodo", "Período"),
                                  key="piv_col")
    with c_met:
        pivot_met = st.selectbox("Métrica",
                                  ["$/100g promedio", "SKUs únicos", "% en oferta"],
                                  key="piv_met")

    if pivot_met == "$/100g promedio":
        tbl = (dff.dropna(subset=["Precio_100g"])
               .groupby([pivot_fila, pivot_col])["Precio_100g"]
               .mean().round(0).unstack(pivot_col))
        fmt = "${:,.0f}"
    elif pivot_met == "SKUs únicos":
        tbl = (dff.groupby([pivot_fila, pivot_col])["SKU_canonico"]
               .nunique().unstack(pivot_col).fillna(0).astype(int))
        fmt = "{:,}"
    else:
        tbl = (dff.groupby([pivot_fila, pivot_col])["En_oferta"]
               .mean().mul(100).round(1).unstack(pivot_col))
        fmt = "{:.1f}%"

    if tbl.empty:
        st.info("Sin datos para esta combinación.")
    else:
        fila_lbl = pivot_fila.replace("Marca_cat", "Marca")
        col_lbl  = pivot_col.replace("Periodo", "Período")
        st.markdown(f'<div class="chart-title">{pivot_met} · {fila_lbl} × {col_lbl}</div>',
                    unsafe_allow_html=True)
        st.dataframe(tbl.style.format(fmt, na_rep="—"), use_container_width=True)


# ── TAB 9: Base ───────────────────────────────────────────────────────────
if active_page == "Base":
    st.markdown('<div class="chart-title">Datos completos</div>', unsafe_allow_html=True)

    c_s1, c_s2, c_s3 = st.columns([3, 1, 1])
    with c_s1:
        busqueda = st.text_input("Buscar en nombre", placeholder="ej: rellena, nucete…",
                                 label_visibility="collapsed")
    with c_s2:
        solo_oferta = st.checkbox("Solo en oferta")
    with c_s3:
        solo_destacadas = st.checkbox("Solo marcas dest.")

    df_base = dff.copy()
    if busqueda:
        df_base = df_base[df_base["Producto"].str.contains(busqueda, case=False, na=False)]
    if solo_oferta:
        df_base = df_base[df_base["En_oferta"]]
    if solo_destacadas:
        df_base = df_base[df_base["Marca_cat"].isin(MARCAS_DESTACADAS_AC)]

    cols_base = ["Periodo", "Cadena", "Marca", "Marca_cat", "Variedad", "Gramaje",
                 "Envase", "Producto", "Gramos", "Precio", "Precio_oferta",
                 "Precio_100g", "Precio_100g_oferta", "Descuento_pct",
                 "En_oferta", "Gramaje_conf", "Gramaje_fuente", "URL"]
    st.dataframe(
        df_base[cols_base]
        .sort_values(["Cadena", "Variedad", "Precio_100g"])
        .rename(columns={
            "Marca_cat":           "Categoría",
            "Precio":              "Góndola ($)",
            "Precio_oferta":       "Oferta ($)",
            "Precio_100g":         "$/100g",
            "Precio_100g_oferta":  "$/100g oferta",
            "Descuento_pct":       "Dto. %",
            "En_oferta":           "En oferta",
            "Gramaje_conf":        "Conf. gramaje",
            "Gramaje_fuente":      "Fuente gramaje",
            "Gramos":              "Gramos (g)",
        }),
        use_container_width=True, hide_index=True, height=600,
    )


if active_page == "Mi Marca":
    _mm_marcas_opts = sorted(
        m for m in df_full["Marca"].dropna().unique()
        if str(m).strip() and str(m).strip().lower() != "desconocida"
    )
    if not _mm_marcas_opts:
        st.info("Sin marcas disponibles para analizar.")
    else:
        _mm_def_idx = _mm_marcas_opts.index("La Toscana") if "La Toscana" in _mm_marcas_opts else 0

        _mm_c1, _mm_c2, _mm_c3, _mm_c4, _mm_c5 = st.columns([2.1, 1.4, 1.2, 1.2, 1.3])
        with _mm_c1:
            st.markdown('<p style="color:#111827;font-size:0.8rem;font-weight:700;margin-bottom:2px">🎯 Marca</p>', unsafe_allow_html=True)
            _mm_sel = st.selectbox("Marca", _mm_marcas_opts, index=_mm_def_idx,
                                   key="mm_ac_marca", label_visibility="collapsed")

        _mm_hist_base = df_full[(df_full["Marca"] == _mm_sel) & (df_full["Cadena"].isin(cadenas_sel))].copy()
        _mm_vars_opts = sorted(_mm_hist_base["Variedad"].dropna().unique())
        _mm_gram_keys = [g for g in GRAMAJE_GRUPOS if _mm_hist_base["Gramaje"].eq(g).any()]
        _mm_gram_labels = [gramaje_grupo_label(g) for g in _mm_gram_keys]
        _mm_env_opts = [e for e in envases_disp if (_mm_hist_base["Envase"] == e).any()]

        with _mm_c2:
            st.markdown('<p style="color:#111827;font-size:0.8rem;font-weight:700;margin-bottom:2px">Variedad</p>', unsafe_allow_html=True)
            _mm_var_sel = st.selectbox("Variedad", ["Todas"] + _mm_vars_opts,
                                       key="mm_ac_var", label_visibility="collapsed")
        with _mm_c3:
            st.markdown('<p style="color:#111827;font-size:0.8rem;font-weight:700;margin-bottom:2px">Gramaje</p>', unsafe_allow_html=True)
            _mm_gram_lbl = st.selectbox("Gramaje", ["Todos"] + _mm_gram_labels,
                                        key="mm_ac_gram", label_visibility="collapsed")
        with _mm_c4:
            st.markdown('<p style="color:#111827;font-size:0.8rem;font-weight:700;margin-bottom:2px">Envase</p>', unsafe_allow_html=True)
            _mm_env_sel = st.selectbox("Envase", ["Todos"] + _mm_env_opts,
                                       key="mm_ac_env", label_visibility="collapsed")
        with _mm_c5:
            st.markdown('<p style="color:#111827;font-size:0.8rem;font-weight:700;margin-bottom:2px">Comparar por</p>', unsafe_allow_html=True)
            _mm_mode = st.selectbox("Comparar por", ["$/kg", "Precio góndola"],
                                    key="mm_ac_mode", label_visibility="collapsed")

        _mm_gram_sel = next(
            (g for g, lbl in zip(_mm_gram_keys, _mm_gram_labels) if lbl == _mm_gram_lbl),
            "Todos",
        )
        _mm_hist_filtered = aplicar_filtros_mi_marca_ac(
            _mm_hist_base, _mm_var_sel, _mm_gram_sel, _mm_env_sel
        )
        _mm_dff = aplicar_filtros_mi_marca_ac(
            dff[(dff["Marca"] == _mm_sel) & (dff["Cadena"].isin(cadenas_sel))].copy(),
            _mm_var_sel, _mm_gram_sel, _mm_env_sel
        )
        _mm_resto = aplicar_filtros_mi_marca_ac(
            dff[(dff["Marca"] != _mm_sel) & (dff["Cadena"].isin(cadenas_sel))].copy(),
            _mm_var_sel, _mm_gram_sel, _mm_env_sel
        )
        _mm_market = aplicar_filtros_mi_marca_ac(
            dff[dff["Cadena"].isin(cadenas_sel)].copy(),
            _mm_var_sel, _mm_gram_sel, _mm_env_sel
        )

        _mm_metric_brand, _mm_metric_unit, _mm_metric_axis = preparar_metrica_mi_marca_ac(_mm_dff, _mm_mode)
        _mm_metric_resto, _, _ = preparar_metrica_mi_marca_ac(_mm_resto, _mm_mode)
        _mm_metric_market, _, _ = preparar_metrica_mi_marca_ac(_mm_market, _mm_mode)

        if _mm_hist_filtered.empty or _mm_metric_brand.empty:
            st.info("Sin datos para esa marca con los filtros actuales.")
        else:
            _mm_fmt = (lambda v: f"${v:,.0f}/kg") if _mm_mode == "$/kg" else (lambda v: f"${v:,.0f}")
            _mm_avg_brand = _mm_metric_brand["_mm_metric"].mean() if not _mm_metric_brand.empty else 0
            _mm_avg_market = _mm_metric_resto["_mm_metric"].mean() if not _mm_metric_resto.empty else 0
            _mm_prima = ((_mm_avg_brand / _mm_avg_market) - 1) * 100 if _mm_avg_market > 0 else 0
            _mm_skus = _mm_hist_filtered["SKU_canonico"].nunique()
            _mm_cadenas = _mm_hist_filtered["Cadena"].nunique()
            _mm_marca_color = color_marca_real_ac(_mm_sel)

            _mm_k1, _mm_k2, _mm_k3, _mm_k4, _mm_k5 = st.columns(5)
            _mm_kpis = [
                ("orange", f"{_mm_metric_unit} marca", _mm_fmt(_mm_avg_brand), f"promedio {_mm_sel}"),
                ("", f"{_mm_metric_unit} mercado", _mm_fmt(_mm_avg_market) if _mm_avg_market else "—", "promedio resto marcas"),
                ("red" if _mm_prima > 0 else "green", "Prima vs mercado", f"{_mm_prima:+.1f}%", "más cara" if _mm_prima > 0 else "más barata"),
                ("purple", "SKUs activos", str(_mm_skus), "familias visibles de la marca"),
                ("teal", "Presencia", str(_mm_cadenas), "cadenas donde figura"),
            ]
            for _col_mm, (_cls, _lab, _val, _sub) in zip([_mm_k1, _mm_k2, _mm_k3, _mm_k4, _mm_k5], _mm_kpis):
                with _col_mm:
                    st.markdown(
                        f"""<div class="kpi-card {_cls}">
                        <div class="kpi-label">{_lab}</div>
                        <div class="kpi-value" style="font-size:{'1.05rem' if len(_val)>12 else '1.55rem'}">{_val}</div>
                        <div class="kpi-sub">{_sub}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

            with st.expander("📊 Precio relativo vs mercado", expanded=True):
                _mm_by_brand = (_mm_metric_market.groupby("Marca")["_mm_metric"]
                                .mean().sort_values().reset_index())
                if not _mm_by_brand.empty:
                    _mm_colors = [
                        _mm_marca_color if m == _mm_sel else "#E5E7EB"
                        for m in _mm_by_brand["Marca"]
                    ]
                    fig_mm_bar = hbar(
                        _mm_by_brand["_mm_metric"].tolist(),
                        _mm_by_brand["Marca"].tolist(),
                        _mm_colors,
                        [_mm_fmt(v) for v in _mm_by_brand["_mm_metric"]],
                        _mm_metric_axis,
                        altura=max(320, len(_mm_by_brand) * 32 + 80),
                    )
                    st.plotly_chart(fig_mm_bar, use_container_width=True)

            with st.expander("🏪 Presencia por cadena", expanded=True):
                _mm_heat_src = _mm_dff.dropna(subset=["Precio"]).copy()
                _mm_pres_piv = (_mm_heat_src.groupby(["SKU_canonico", "Cadena"])["Precio"]
                                .mean().round(0).unstack("Cadena"))
                if not _mm_pres_piv.empty:
                    _mm_text = [[f"${v:,.0f}" if not pd.isna(v) else "—" for v in row]
                                for row in _mm_pres_piv.values]
                    fig_mm_h = go.Figure(go.Heatmap(
                        z=_mm_pres_piv.values,
                        x=_mm_pres_piv.columns.tolist(),
                        y=_mm_pres_piv.index.tolist(),
                        colorscale="RdYlGn_r",
                        text=_mm_text,
                        texttemplate="%{text}",
                        textfont=dict(size=12, color="#111827"),
                        colorbar=dict(title="Precio góndola", tickprefix="$", tickformat=",",
                                      tickfont=dict(color="#111827"),
                                      title_font=dict(color="#111827")),
                    ))
                    fig_mm_h.update_layout(
                        **_BASE_CORE,
                        height=max(300, len(_mm_pres_piv) * 42 + 80),
                        xaxis=dict(tickfont=dict(size=12, color="#111827"), side="top"),
                        yaxis=dict(tickfont=dict(size=11, color="#111827")),
                    )
                    st.plotly_chart(fig_mm_h, use_container_width=True)

                    _mm_cad_x_sku = (_mm_hist_filtered.groupby("SKU_canonico")["Cadena"]
                                     .nunique().reset_index(name="n_cad")
                                     .sort_values("n_cad", ascending=False))
                    if not _mm_cad_x_sku.empty:
                        _mm_cols_pres = st.columns(min(6, len(_mm_cad_x_sku)))
                        for _ci, (_, _row_pres) in enumerate(_mm_cad_x_sku.head(6).iterrows()):
                            with _mm_cols_pres[_ci]:
                                st.markdown(
                                    f"<div style='background:#F9FAFB;border-radius:8px;padding:0.55rem 0.7rem;font-size:0.72rem;text-align:center'>"
                                    f"<b style='color:#111827'>{_row_pres['n_cad']}</b><br>"
                                    f"<span style='color:#6B7280'>{_row_pres['SKU_canonico'][:24]}...</span></div>",
                                    unsafe_allow_html=True,
                                )
                else:
                    st.info("Sin datos de presencia para esa selección.")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="chart-title">⚔️ Comparativa vs competidores</div>', unsafe_allow_html=True)
            _mm_other_brands = sorted(
                m for m in _mm_market["Marca"].dropna().unique()
                if m != _mm_sel
            )
            if not _mm_other_brands:
                st.info("No hay competidores suficientes con los filtros actuales.")
            else:
                _mm_cc1, _mm_cc2, _ = st.columns([2, 2, 3])
                with _mm_cc1:
                    _mm_comp1 = st.selectbox("Competidor 1", _mm_other_brands,
                                             key="mm_ac_comp1", index=0)
                with _mm_cc2:
                    _mm_comp2_idx = 1 if len(_mm_other_brands) > 1 else 0
                    _mm_comp2 = st.selectbox("Competidor 2", _mm_other_brands,
                                             key="mm_ac_comp2", index=_mm_comp2_idx)

                _mm_ev_base = aplicar_filtros_mi_marca_ac(
                    dff[dff["Marca"].isin([_mm_sel, _mm_comp1, _mm_comp2])].copy(),
                    _mm_var_sel, _mm_gram_sel, _mm_env_sel,
                )
                _mm_ev_metric, _, _ = preparar_metrica_mi_marca_ac(_mm_ev_base, _mm_mode)
                _orden_per_mm = sorted(
                    dff["Periodo"].unique(),
                    key=lambda p: df_full[df_full["Periodo"] == p]["Fecha"].min(),
                )
                _mm_ev_df = (_mm_ev_metric.groupby(["Periodo", "Marca"])["_mm_metric"]
                             .mean().reset_index())
                _mm_ev_df["Periodo"] = pd.Categorical(
                    _mm_ev_df["Periodo"], categories=_orden_per_mm, ordered=True
                )
                _mm_ev_cmap = {
                    _mm_sel: _mm_marca_color,
                    _mm_comp1: "#9CA3AF",
                    _mm_comp2: "#D1D5DB",
                }
                if len(_orden_per_mm) < 2:
                    _mm_bar_df = (_mm_ev_df.groupby("Marca")["_mm_metric"]
                                  .mean().reset_index().sort_values("_mm_metric"))
                    fig_mm_ev = go.Figure(go.Bar(
                        x=_mm_bar_df["_mm_metric"], y=_mm_bar_df["Marca"],
                        orientation="h",
                        marker_color=[_mm_ev_cmap.get(m, "#9CA3AF") for m in _mm_bar_df["Marca"]],
                        text=[_mm_fmt(v) for v in _mm_bar_df["_mm_metric"]],
                        textposition="outside", cliponaxis=False,
                    ))
                    fig_mm_ev.update_layout(
                        **_BASE_CORE,
                        height=260,
                        margin=dict(l=10, r=160, t=30, b=10),
                        xaxis=dict(title=_mm_metric_axis, tickprefix="$", tickformat=",",
                                   tickfont=dict(size=12, color="#111827")),
                        showlegend=False,
                    )
                else:
                    fig_mm_ev = px.line(
                        _mm_ev_df, x="Periodo", y="_mm_metric", color="Marca",
                        markers=True, color_discrete_map=_mm_ev_cmap,
                        labels={"_mm_metric": _mm_metric_axis, "Periodo": "", "Marca": "Marca"},
                        height=400,
                    )
                    fig_mm_ev.update_traces(line=dict(width=2.5), marker=dict(size=8))
                    fig_mm_ev.update_layout(
                        **_BASE_CORE,
                        yaxis=dict(title=_mm_metric_axis, tickprefix="$", tickformat=",",
                                   tickfont=dict(size=12, color="#111827")),
                        xaxis=dict(tickfont=dict(size=12, color="#111827")),
                    )
                st.plotly_chart(fig_mm_ev, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="chart-title">🏷️ Comportamiento de ofertas</div>', unsafe_allow_html=True)
            _mm_of_src = _mm_hist_filtered.copy()
            _mm_of_rate = (_mm_of_src.groupby(["SKU_canonico", "Periodo"])["En_oferta"]
                           .max().reset_index()
                           .groupby("SKU_canonico")["En_oferta"]
                           .mean().mul(100).reset_index(name="pct_sem_of"))
            _mm_of_cadenas = (_mm_of_src[_mm_of_src["En_oferta"]]
                              .groupby("SKU_canonico")["Cadena"]
                              .apply(lambda x: ", ".join(sorted(x.unique())))
                              .reset_index(name="cadenas_oferta"))
            _mm_desc_avg = (_mm_of_src[_mm_of_src["En_oferta"]]
                            .groupby("SKU_canonico")["Descuento_pct"]
                            .mean().reset_index(name="desc_prom"))
            _mm_of_tbl = (_mm_of_rate.merge(_mm_desc_avg, on="SKU_canonico", how="left")
                                     .merge(_mm_of_cadenas, on="SKU_canonico", how="left")
                                     .fillna({"desc_prom": 0, "cadenas_oferta": "—"}))
            _mm_of_tbl.columns = ["SKU", "% sem. en oferta", "Dto. prom. (%)", "Cadenas donde ofertó"]
            _mm_desc_merc = aplicar_filtros_mi_marca_ac(
                df_full[(df_full["Marca"] != _mm_sel) & df_full["En_oferta"] & (df_full["Cadena"].isin(cadenas_sel))].copy(),
                _mm_var_sel, _mm_gram_sel, _mm_env_sel,
            )["Descuento_pct"].mean()
            _mm_cd1, _mm_cd2 = st.columns(2)
            with _mm_cd1:
                _mm_skus_con_of = _mm_of_src[_mm_of_src["En_oferta"]]["SKU_canonico"].nunique()
                _mm_skus_total = _mm_of_src["SKU_canonico"].nunique()
                _mm_pct_of_marca = (_mm_skus_con_of / _mm_skus_total * 100) if _mm_skus_total > 0 else 0
                st.markdown(
                    f"<div style='background:#FFF7ED;border-radius:10px;padding:0.8rem 1rem;border-left:3px solid #F97316'>"
                    f"<span style='font-size:0.65rem;text-transform:uppercase;color:#9CA3AF'>% del portfolio con descuento · {_mm_sel}</span><br>"
                    f"<span style='font-size:1.6rem;font-weight:800;color:#111827'>{_mm_pct_of_marca:.1f}%</span></div>",
                    unsafe_allow_html=True,
                )
            with _mm_cd2:
                _mm_desc_m = (_mm_of_src[_mm_of_src["En_oferta"]]["Descuento_pct"].mean()
                              if _mm_of_src["En_oferta"].any() else 0)
                st.markdown(
                    f"<div style='background:#F0FDF4;border-radius:10px;padding:0.8rem 1rem;border-left:3px solid #16A34A'>"
                    f"<span style='font-size:0.65rem;text-transform:uppercase;color:#9CA3AF'>Dto. prom. marca vs mercado</span><br>"
                    f"<span style='font-size:1.6rem;font-weight:800;color:#111827'>{_mm_desc_m:.0f}% vs {_mm_desc_merc:.0f}%</span></div>",
                    unsafe_allow_html=True,
                )
            st.markdown("<br>", unsafe_allow_html=True)
            if not _mm_of_tbl.empty:
                st.dataframe(
                    _mm_of_tbl,
                    height=min(400, len(_mm_of_tbl) * 38 + 60),
                    hide_index=True,
                    column_config={
                        "% sem. en oferta": st.column_config.NumberColumn(format="%.1f%%"),
                        "Dto. prom. (%)": st.column_config.NumberColumn(format="%.0f%%"),
                    },
                )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="chart-title">📦 Tracking de distribución</div>', unsafe_allow_html=True)
            _mm_ult_f = df_full["Fecha"].max()
            _mm_dist_rows = []
            for (_sku_d, _cad_d), _grp_d in _mm_hist_filtered.groupby(["SKU_canonico", "Cadena"]):
                _mm_dist_rows.append({
                    "SKU": _sku_d,
                    "Cadena": _cad_d,
                    "Primera vez": _grp_d["Fecha"].min().strftime("%d/%m/%Y"),
                    "Última vez": _grp_d["Fecha"].max().strftime("%d/%m/%Y"),
                    "Estado": "✓ Activo" if _grp_d["Fecha"].max() == _mm_ult_f else "✗ Salió",
                })
            if _mm_dist_rows:
                _mm_dist_df = pd.DataFrame(_mm_dist_rows).sort_values(["Estado", "SKU"])
                st.dataframe(_mm_dist_df, height=min(500, len(_mm_dist_df) * 38 + 60), hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="chart-title">📍 Presencia por cadena — SKU × Cadena</div>', unsafe_allow_html=True)
            _mm_pres_fechas = sorted(_mm_hist_filtered["Fecha"].unique())
            _mm_seen_sem = {}
            for _f in _mm_pres_fechas:
                _ts = pd.Timestamp(_f)
                _k = f"Sem {_ts.isocalendar().week} · {_ts.strftime('%b %Y')}"
                _mm_seen_sem.setdefault(_k, []).append(_f)
            _mm_per_labels = list(_mm_seen_sem.keys())
            if _mm_per_labels:
                _mm_pres_lbl = st.selectbox(
                    "🗓️ Período a visualizar",
                    _mm_per_labels,
                    index=len(_mm_per_labels) - 1,
                    key="mm_ac_pres_ventana",
                )
                _mm_pres_fechas_sel = _mm_seen_sem[_mm_pres_lbl]
                st.markdown(
                    f'<div class="chart-note">🟢 activo en al menos 1 scrape de <b>{_mm_pres_lbl}</b> &nbsp;·&nbsp; 🔴 estuvo antes pero no en este período &nbsp;·&nbsp; — nunca en esa cadena.</div>',
                    unsafe_allow_html=True,
                )
                _mm_ventana_df = _mm_hist_filtered[_mm_hist_filtered["Fecha"].isin(_mm_pres_fechas_sel)]
                _mm_pres_set = set(zip(_mm_ventana_df["SKU_canonico"], _mm_ventana_df["Cadena"]))
                _mm_todos_skus = sorted(_mm_hist_filtered["SKU_canonico"].unique())
                _mm_todas_cad = sorted(df_full[df_full["Cadena"].isin(cadenas_sel)]["Cadena"].unique())
                _mm_hist_set = set(zip(_mm_hist_filtered["SKU_canonico"], _mm_hist_filtered["Cadena"]))
                _mm_pz, _mm_pt = [], []
                for _sk in _mm_todos_skus:
                    _rz, _rt = [], []
                    for _cd in _mm_todas_cad:
                        if (_sk, _cd) in _mm_pres_set:
                            _rz.append(1)
                            _rt.append("✓")
                        elif (_sk, _cd) in _mm_hist_set:
                            _rz.append(-1)
                            _rt.append("✗")
                        else:
                            _rz.append(0)
                            _rt.append("—")
                    _mm_pz.append(_rz)
                    _mm_pt.append(_rt)
                fig_mm_pres = go.Figure(go.Heatmap(
                    z=_mm_pz,
                    x=_mm_todas_cad,
                    y=_mm_todos_skus,
                    colorscale=[
                        [0.00, "#FCA5A5"], [0.33, "#FCA5A5"],
                        [0.34, "#F3F4F6"], [0.66, "#F3F4F6"],
                        [0.67, "#86EFAC"], [1.00, "#86EFAC"],
                    ],
                    zmin=-1, zmax=1,
                    text=_mm_pt, texttemplate="%{text}",
                    textfont=dict(size=13, color="#111827"),
                    showscale=False, xgap=3, ygap=3,
                ))
                fig_mm_pres.update_layout(
                    **_BASE_CORE,
                    height=max(220, len(_mm_todos_skus) * 38 + 80),
                    xaxis=dict(tickfont=dict(size=12, color="#111827"), side="top"),
                    yaxis=dict(tickfont=dict(size=11, color="#111827")),
                )
                st.plotly_chart(fig_mm_pres, use_container_width=True)
