"""
Dashboard Streamlit — consomme exclusivement l'API FastAPI.
Jamais de lecture directe du Parquet ici.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="Dashboard Ventes",
    page_icon="📊",
    layout="wide",
)


# ── Ressources globales (une seule instance partagée entre toutes les sessions) ──

@st.cache_resource
def get_http_session() -> requests.Session:
    """Session HTTP persistante avec connection pooling — évite de rouvrir une
    connexion TCP à chaque requête."""
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=2, pool_maxsize=10)
    session.mount("http://", adapter)
    return session


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Paramètres")

    api_url = st.text_input("URL de l'API", value="http://localhost:8000")
    annee = st.selectbox("Année", options=[2025, 2024], index=0)

    session = get_http_session()
    try:
        health = session.get(f"{api_url}/health", timeout=3).json()
        st.success(f"API connectée ✅  ({health['dataset_rows']:,} lignes)")
        api_ok = True
    except Exception:
        st.error("API inaccessible ❌")
        st.info("Lancez l'API avec : `just api`")
        api_ok = False

    region_selection = st.multiselect(
        "Régions",
        options=["Nord", "Sud", "Est", "Ouest", "Île-de-France"],
        default=[],
        placeholder="Toutes les régions",
    )
    region_param: str | None = region_selection[0] if len(region_selection) == 1 else None


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_euros(montant: float) -> str:
    return f"{montant:,.0f} €".replace(",", "\u202f")


def _get(url: str, params: dict) -> dict | list:
    return get_http_session().get(url, params=params, timeout=10).json()


@st.cache_data(ttl=300)
def fetch_contexte(api_url: str, annee: int, region: str | None) -> dict:
    """Données partagées par les KPIs et les graphiques — chargées en parallèle."""
    region_q = {"region": region} if region else {}
    calls = {
        "resume":     (f"{api_url}/api/v1/ventes",              {"annee": annee, "limit": 1, **region_q}),
        "par_region": (f"{api_url}/api/v1/ventes/par-region",   {"annee": annee}),
        "par_cat":    (f"{api_url}/api/v1/ventes/par-categorie", {"annee": annee, **region_q}),
        "evolution":  (f"{api_url}/api/v1/ventes/evolution",    {"annee": annee, **region_q}),
    }
    results = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_get, url, p): key for key, (url, p) in calls.items()}
        for f in as_completed(futures):
            results[futures[f]] = f.result()
    return results


@st.cache_data(ttl=300)
def fetch_top_clients(api_url: str, annee: int, region: str | None, top_n: int) -> list[dict]:
    region_q = {"region": region} if region else {}
    return _get(f"{api_url}/api/v1/ventes/top-clients", {"annee": annee, "top_n": top_n, **region_q})


# ── Layout principal ──────────────────────────────────────────────────────────

st.title("📊 Dashboard Ventes")
region_label = region_param if region_param else "Toutes les régions"
st.caption(f"Année {annee} · {region_label}")

if not api_ok:
    st.warning("Le dashboard nécessite que l'API soit lancée. Vérifiez la sidebar.")
    st.stop()

try:
    ctx = fetch_contexte(api_url, annee, region_param)
except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────

resume = ctx["resume"]["resume"]
col1, col2, col3, col4 = st.columns(4)
col1.metric("CA Total", fmt_euros(resume["total_ca"]))
col2.metric("Transactions", f"{resume['nb_transactions']:,}".replace(",", "\u202f"))
col3.metric("Panier moyen", fmt_euros(resume["panier_moyen"]))
col4.metric("Régions", len(resume["regions_disponibles"]))

st.divider()

# ── Graphiques ────────────────────────────────────────────────────────────────

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("CA par région")
    fig = px.bar(
        ctx["par_region"],
        x="region", y="ca_total", color="region", text="part_ca_pct",
        labels={"ca_total": "CA (€)", "region": "Région", "part_ca_pct": "Part (%)"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig, width="stretch")

with col_right:
    st.subheader("CA par catégorie")
    fig = px.bar(
        ctx["par_cat"],
        x="categorie", y="ca_total", color="categorie",
        labels={"ca_total": "CA (€)", "categorie": "Catégorie"},
    )
    fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig, width="stretch")

st.divider()

# ── Évolution mensuelle ────────────────────────────────────────────────────────

st.subheader("Évolution mensuelle du CA")
fig = px.line(
    ctx["evolution"],
    x="mois", y="ca_total", markers=True,
    labels={"ca_total": "CA (€)", "mois": "Mois"},
)
fig.update_layout(height=300)
st.plotly_chart(fig, width="stretch")

st.divider()

# ── Top clients — fragment indépendant ────────────────────────────────────────
# @st.fragment : ce bloc a son propre widget (top_n). Quand l'utilisateur
# change le slider, seul ce fragment se re-exécute — pas le reste du dashboard.

@st.fragment
def section_top_clients() -> None:
    st.subheader("Top clients")
    top_n = st.slider("Nombre de clients", min_value=3, max_value=50, value=10, step=1)
    try:
        clients = fetch_top_clients(api_url, annee, region_param, top_n)
        rows = [{**c, "ca_total": fmt_euros(c["ca_total"])} for c in clients]
        st.dataframe(
            rows,
            column_config={
                "client_id": "Client",
                "ca_total": st.column_config.TextColumn("CA Total"),
                "nb_transactions": st.column_config.NumberColumn("Transactions"),
            },
            width="stretch",
            hide_index=True,
        )
    except Exception as e:
        st.error(f"Erreur : {e}")


section_top_clients()

# ── Footer ─────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "Démo réalisée pour la [Newsletter DataGyver #11](https://datagyver.fr) · "
    "[Code source sur GitHub](https://github.com/datagyver/api-pour-analystes)"
)
