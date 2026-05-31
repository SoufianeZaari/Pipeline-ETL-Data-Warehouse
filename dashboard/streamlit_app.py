"""Mexora BI Dashboard - version web deployable (Streamlit).

Lit les CSV de dashboard/data/ générés par scripts/export_streamlit_data.py.
Ne nécessite aucune connexion PostgreSQL en production / sur Streamlit Cloud.

Lancer localement :
    streamlit run dashboard/streamlit_app.py

Déployer sur Streamlit Cloud :
    push sur GitHub → share.streamlit.io
    main file : dashboard/streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Config page ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mexora BI Dashboard",
    page_icon="MX",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
  --mexora-navy:#102A43;
  --mexora-blue:#2563A9;
  --mexora-light:#F5F8FC;
  --mexora-border:#D8E2EF;
  --mexora-muted:#62748A;
}
.block-container {
  padding-top: 1.6rem;
}
.main-header {
  background: linear-gradient(135deg, #102A43 0%, #1D4E89 100%);
  color: white;
  border-radius: 8px;
  padding: 1.35rem 1.5rem;
  margin-bottom: 1rem;
  box-shadow:0 8px 24px rgba(16,42,67,.15);
}
.main-header h1 {
  font-size: 2rem;
  margin: 0 0 .25rem 0;
  letter-spacing: 0;
}
.main-header p {
  margin: 0;
  color: #DDEAF7;
  font-size: 1rem;
}
.academic-card {
  background: var(--mexora-light);
  border: 1px solid var(--mexora-border);
  border-left: 4px solid var(--mexora-blue);
  border-radius: 8px;
  padding: .85rem 1rem;
  color: var(--mexora-navy);
  margin-bottom: 1rem;
}
.academic-card strong {
  color: var(--mexora-navy);
}
.link-row a {
  color: var(--mexora-blue);
  font-weight: 600;
  text-decoration: none;
  margin-right: 1rem;
}
.kpi-card {
  background:#ffffff; border-left:4px solid #2C6EAB;
  border-radius:6px; padding:.9rem 1.1rem;
  box-shadow:0 1px 4px rgba(0,0,0,.08); margin-bottom:.4rem;
}
.kpi-label { font-size:.74rem; color:#6b7280;
             text-transform:uppercase; letter-spacing:.06em; margin-bottom:.1rem; }
.kpi-value { font-size:1.5rem; font-weight:700; color:#1A1A2E; }
.kpi-unit  { font-size:.74rem; color:#6b7280; margin-left:.15rem; }
section[data-testid="stSidebar"] {
  background: #F7FAFD;
}
</style>
""", unsafe_allow_html=True)

# ── Constantes ───────────────────────────────────────────────────────────────
PALETTE = ["#2C6EAB", "#C0392B", "#27AE60", "#E67E22", "#8E44AD", "#16A085"]
NO_DATA = (
    "Fichiers CSV manquants dans `dashboard/data/`.\n\n"
    "Exécutez d'abord :\n```bash\npython scripts/export_streamlit_data.py\n```"
)


# ── Helpers ──────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load(filename: str) -> pd.DataFrame | None:
    p = DATA_DIR / filename
    return pd.read_csv(p) if p.exists() else None


def kpi(label: str, value: str, unit: str = "") -> None:
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}'
        f'<span class="kpi-unit">&nbsp;{unit}</span></div></div>',
        unsafe_allow_html=True,
    )


def fmt_mad(v: float) -> str:
    if v >= 1_000_000:
        return f"{v/1_000_000:.2f} M"
    if v >= 1_000:
        return f"{v/1_000:.1f} K"
    return f"{v:.0f}"


def retour_badge(pct: float) -> str:
    if pct > 5:
        return f"Rouge - {pct:.1f}%"
    if pct >= 3:
        return f"Orange - {pct:.1f}%"
    return f"Vert - {pct:.1f}%"


def render_header() -> None:
    st.markdown(
        """
        <div class="main-header">
          <h1>Mexora BI Dashboard</h1>
          <p>Pipeline ETL &amp; Data Warehouse - E-commerce Analytics</p>
        </div>
        <div class="academic-card">
          <strong>Faculte des Sciences et Techniques de Tanger</strong><br>
          Universite Abdelmalek Essaadi<br>
          Module : Business Intelligence / Data Warehouse<br>
          Encadrant : Prof. Hassan Zili<br>
          Realise par : Soufiane Zaari
          <div class="link-row" style="margin-top:.55rem;">
            <a href="https://github.com/SoufianeZaari/Pipeline-ETL-Data-Warehouse" target="_blank">GitHub</a>
            <a href="https://pipeline-etl-data-warehouse.streamlit.app/" target="_blank">Streamlit deploye</a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Guard: data must exist ────────────────────────────────────────────────────
kpis_df = load("kpis.csv")
if kpis_df is None:
    st.error(NO_DATA)
    st.stop()

kpis = kpis_df.iloc[0]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Mexora BI")
    st.markdown("*Data Engineering & BI Project*")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        [
            "Page 1 — Vue générale",
            "Page 2 — Analyse régionale",
            "Page 3 — Analyse clients",
            "Page 4 — Analyse produits",
            "Page 5 — Retours & Ramadan",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption(
        "Pipeline ETL Mexora  \nPostgreSQL 16 · Pandas · Plotly  \n"
        "[GitHub](https://github.com/SoufianeZaari/Pipeline-ETL-Data-Warehouse)"
    )

render_header()

# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Vue générale
# ════════════════════════════════════════════════════════════════════════════
if page == "Page 1 — Vue générale":
    st.title("Page 1 — Vue générale")
    st.markdown("Vue synthétique des performances commerciales issues du Data Warehouse.")
    st.markdown("---")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: kpi("CA Total", fmt_mad(float(kpis["ca_total"])), "MAD")
    with c2: kpi("Commandes", f"{int(kpis['nb_commandes']):,}")
    with c3: kpi("Clients", f"{int(kpis['nb_clients']):,}")
    with c4: kpi("Panier moyen", fmt_mad(float(kpis["panier_moyen"])), "MAD")
    with c5: kpi("Taux retour", f"{float(kpis['taux_retour_pct']):.1f}", "%")
    with c6: kpi("Délai moyen", f"{float(kpis['delai_moyen_jours']):.1f}", "j")

    st.markdown("---")
    ca_df = load("ca_mensuel.csv")
    if ca_df is not None:
        col_l, col_r = st.columns([3, 2])

        with col_l:
            st.subheader("Évolution du CA mensuel")
            monthly = (
                ca_df.groupby(["annee", "mois"])["ca_ttc"].sum().reset_index()
            )
            monthly["periode"] = (
                monthly["annee"].astype(str)
                + "-"
                + monthly["mois"].astype(str).str.zfill(2)
            )
            fig = px.area(
                monthly.sort_values("periode"),
                x="periode", y="ca_ttc",
                labels={"periode": "Période", "ca_ttc": "CA TTC (MAD)"},
                color_discrete_sequence=[PALETTE[0]],
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.subheader("CA par catégorie")
            cat = (
                ca_df.groupby("categorie")["ca_ttc"]
                .sum().reset_index()
                .sort_values("ca_ttc", ascending=False)
            )
            fig2 = px.pie(
                cat, values="ca_ttc", names="categorie",
                color_discrete_sequence=PALETTE, hole=0.4,
            )
            fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Analyse régionale
# ════════════════════════════════════════════════════════════════════════════
elif page == "Page 2 — Analyse régionale":
    st.title("Page 2 — Analyse régionale")
    st.markdown("---")

    reg_df = load("ca_region.csv")
    ca_df = load("ca_mensuel.csv")
    if reg_df is None:
        st.warning(NO_DATA)
        st.stop()

    top_reg = reg_df.iloc[0]
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Top région", str(top_reg["region_admin"]))
    with c2: kpi("CA top région", fmt_mad(float(top_reg["ca_ttc"])), "MAD")
    with c3: kpi("Villes analysées", str(len(reg_df)))

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("CA par ville (commandes livrées)")
        fig = px.bar(
            reg_df.sort_values("ca_ttc", ascending=True),
            x="ca_ttc", y="ville", orientation="h",
            color="ca_ttc", color_continuous_scale="Blues",
            labels={"ca_ttc": "CA TTC (MAD)", "ville": "Ville"},
            text_auto=".2s",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0),
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        if ca_df is not None:
            st.subheader("Évolution mensuelle par région")
            mr = (
                ca_df.groupby(["annee", "mois", "region_admin"])["ca_ttc"]
                .sum().reset_index()
            )
            mr["periode"] = (
                mr["annee"].astype(str)
                + "-"
                + mr["mois"].astype(str).str.zfill(2)
            )
            fig2 = px.line(
                mr.sort_values("periode"),
                x="periode", y="ca_ttc", color="region_admin",
                color_discrete_sequence=PALETTE,
                labels={"periode": "Période", "ca_ttc": "CA TTC (MAD)",
                        "region_admin": "Région"},
            )
            fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

    pct = float(top_reg["ca_ttc"]) / float(reg_df["ca_ttc"].sum()) * 100
    st.info(
        f"**Insight automatique :** {top_reg['ville']} ({top_reg['region_admin']}) "
        f"représente **{pct:.1f}%** du CA livré total — "
        f"{fmt_mad(float(top_reg['ca_ttc']))} MAD pour "
        f"{int(top_reg['nb_commandes']):,} commandes."
    )


# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Clients & Segments
# ════════════════════════════════════════════════════════════════════════════
elif page == "Page 3 — Analyse clients":
    st.title("Page 3 — Analyse clients")
    st.markdown("---")

    seg_df = load("segments_clients.csv")
    if seg_df is None:
        st.warning(NO_DATA)
        st.stop()

    cols = st.columns(len(seg_df))
    for i, (_, row) in enumerate(seg_df.iterrows()):
        with cols[i]:
            kpi(
                f"Segment {row['segment_client']}",
                fmt_mad(float(row["panier_moyen"])),
                "MAD / commande",
            )

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Répartition CA par segment")
        color_map = {"Gold": "#F1C40F", "Silver": "#95A5A6", "Bronze": "#CD6133"}
        fig = px.pie(
            seg_df, values="ca_total", names="segment_client",
            color="segment_client", color_discrete_map=color_map, hole=0.45,
        )
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Panier moyen & commandes")
        fig2 = go.Figure()
        colors = [color_map.get(s, "#2C6EAB") for s in seg_df["segment_client"]]
        fig2.add_trace(go.Bar(
            name="Panier moyen (MAD)",
            x=seg_df["segment_client"], y=seg_df["panier_moyen"],
            marker_color=colors, yaxis="y",
        ))
        fig2.add_trace(go.Scatter(
            name="Nb commandes",
            x=seg_df["segment_client"], y=seg_df["nb_commandes"],
            mode="lines+markers", marker_color="#2C6EAB", yaxis="y2",
        ))
        fig2.update_layout(
            yaxis=dict(title="Panier moyen (MAD)"),
            yaxis2=dict(title="Nb commandes", overlaying="y", side="right"),
            legend=dict(orientation="h"),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Tableau détaillé")
    disp = seg_df.copy()
    disp["ca_total"] = disp["ca_total"].apply(lambda v: f"{float(v):,.0f} MAD")
    disp["panier_moyen"] = disp["panier_moyen"].apply(lambda v: f"{float(v):,.0f} MAD")
    disp["pct_ca"] = disp["pct_ca"].apply(lambda v: f"{float(v):.1f}%")
    st.dataframe(disp, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Produits
# ════════════════════════════════════════════════════════════════════════════
elif page == "Page 4 — Analyse produits":
    st.title("Page 4 — Analyse produits")
    st.markdown("---")

    prod_df = load("top_produits_tanger.csv")
    ca_df = load("ca_mensuel.csv")
    if prod_df is None:
        st.warning(NO_DATA)
        st.stop()

    nb_show = st.slider("Nombre de produits", 5, min(20, len(prod_df)), 10)
    top = prod_df.head(nb_show)

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader(f"Top {nb_show} produits à Tanger (CA)")
        fig = px.bar(
            top.sort_values("ca_total", ascending=True),
            x="ca_total", y="nom_produit", orientation="h",
            color="categorie", color_discrete_sequence=PALETTE,
            labels={"ca_total": "CA TTC (MAD)", "nom_produit": "Produit"},
            text_auto=".2s",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0),
                          legend_title="Catégorie")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Quantité vendue (top 10)")
        fig2 = px.bar(
            top.sort_values("qte_totale", ascending=True).head(10),
            x="qte_totale", y="nom_produit", orientation="h",
            color="categorie", color_discrete_sequence=PALETTE,
            labels={"qte_totale": "Quantité", "nom_produit": "Produit"},
            text_auto=True,
        )
        fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    if ca_df is not None:
        st.markdown("---")
        st.subheader("CA par catégorie — toutes régions")
        cat = (
            ca_df.groupby("categorie")["ca_ttc"]
            .sum().reset_index()
            .sort_values("ca_ttc", ascending=False)
        )
        fig3 = px.bar(
            cat, x="categorie", y="ca_ttc",
            color="categorie", color_discrete_sequence=PALETTE,
            labels={"ca_ttc": "CA TTC (MAD)", "categorie": "Catégorie"},
            text_auto=".2s",
        )
        fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Retours & Ramadan
# ════════════════════════════════════════════════════════════════════════════
elif page == "Page 5 — Retours & Ramadan":
    st.title("Page 5 — Retours & Ramadan")
    st.markdown("---")

    ret_df = load("taux_retour_categorie.csv")
    ram_df = load("ramadan_food.csv")
    liv_df = load("livraison_retours.csv")

    # ---- Taux de retour ----
    if ret_df is not None:
        st.subheader("Taux de retour par catégorie")
        col_l, col_r = st.columns([2, 3])

        with col_l:
            disp = ret_df.copy()
            disp["taux"] = disp["taux_retour_pct"].apply(retour_badge)
            disp_show = disp[["categorie", "nb_total", "nb_retours", "taux"]].copy()
            disp_show.columns = ["Catégorie", "Total", "Retours", "Taux"]
            st.dataframe(disp_show, use_container_width=True, hide_index=True)

        with col_r:
            fig = px.bar(
                ret_df.sort_values("taux_retour_pct", ascending=True),
                x="taux_retour_pct", y="categorie", orientation="h",
                color="taux_retour_pct",
                color_continuous_scale=["#27AE60", "#E67E22", "#C0392B"],
                range_color=[0, 10],
                labels={"taux_retour_pct": "Taux (%)", "categorie": "Catégorie"},
                text_auto=".1f",
            )
            fig.add_vline(x=5, line_dash="dash", line_color="#C0392B",
                          annotation_text="Seuil 5%")
            fig.add_vline(x=3, line_dash="dot", line_color="#E67E22",
                          annotation_text="Seuil 3%")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0),
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        st.caption("Seuils d'alerte : Rouge > 5% · Orange 3-5% · Vert < 3%")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    # ---- Effet Ramadan ----
    with col_l:
        st.subheader("Effet Ramadan — Alimentation")
        if ram_df is not None and not ram_df.empty:
            ram_df["periode"] = (
                ram_df["annee"].astype(str)
                + "-"
                + ram_df["mois"].astype(str).str.zfill(2)
            )
            fig_r = px.bar(
                ram_df.sort_values("periode"),
                x="periode", y="ca_ttc",
                color=ram_df["periode_ramadan"].astype(str),
                color_discrete_map={"True": "#C0392B", "False": "#2C6EAB"},
                labels={"periode": "Mois", "ca_ttc": "CA Food (MAD)",
                        "color": "Ramadan"},
                barmode="overlay",
            )
            fig_r.update_layout(margin=dict(l=0, r=0, t=10, b=0),
                                legend_title="Ramadan")
            st.plotly_chart(fig_r, use_container_width=True)

            # Indice simplifié
            n_ram = ram_df[ram_df["periode_ramadan"] == True]
            n_hors = ram_df[ram_df["periode_ramadan"] == False]
            if len(n_ram) > 0 and len(n_hors) > 0:
                avg_ram = n_ram["ca_ttc"].mean()
                avg_hors = n_hors["ca_ttc"].mean()
                indice = avg_ram / avg_hors * 100 if avg_hors > 0 else None
                if indice:
                    st.metric(
                        "Indice Ramadan (base 100 = hors Ramadan)",
                        f"{indice:.1f}",
                        delta=f"{indice-100:.1f}",
                    )
        else:
            st.info("Données Alimentation non disponibles.")

    # ---- Livreurs ----
    with col_r:
        st.subheader("Performance livreurs")
        if liv_df is not None and not liv_df.empty:
            filt = liv_df[liv_df["nom_livreur"] != "Livreur inconnu"]
            if not filt.empty:
                fig_l = px.bar(
                    filt.sort_values("delai_moyen"),
                    x="nom_livreur", y="delai_moyen",
                    color="taux_retard_pct",
                    color_continuous_scale="RdYlGn_r",
                    labels={"nom_livreur": "Livreur",
                            "delai_moyen": "Délai moyen (j)",
                            "taux_retard_pct": "% Retard"},
                    text_auto=".1f",
                )
                fig_l.add_hline(y=3, line_dash="dash", line_color="#C0392B",
                                annotation_text="Seuil 3j")
                fig_l.update_layout(margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig_l, use_container_width=True)
            else:
                st.info("Données livreurs insuffisantes.")
        else:
            st.warning(NO_DATA)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;font-size:.75rem;color:#9ca3af;'>"
    "Dashboard généré à partir du Data Warehouse PostgreSQL Mexora · "
    "Version web déployée avec Streamlit · "
    "<a href='https://github.com/SoufianeZaari/Pipeline-ETL-Data-Warehouse'"
    " target='_blank'>GitHub</a>"
    "</p>",
    unsafe_allow_html=True,
)
