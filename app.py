"""
================================================================================
 NEAR-EARTH ASTEROIDS (NEA) MONITORING DASHBOARD
================================================================================
Dashboard interattiva realizzata con Streamlit, Pandas e Plotly che interroga
l'API pubblica NASA NeoWs (Near Earth Object Web Service) per monitorare gli
asteroidi in avvicinamento alla Terra in un dato intervallo di date.

Avvio locale:
    streamlit run app.py

Requisiti:
    Vedi requirements.txt
================================================================================
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# ==============================================================================
# 1. CONFIGURAZIONE PAGINA
# ==============================================================================
st.set_page_config(
    page_title="NEA Monitoring Dashboard",
    page_icon="☄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------------------
# Token di design: palette "deep space" costruita sul contenuto (blu/ciano per
# gli oggetti sicuri, corallo per quelli pericolosi) invece di colori decorativi
# a caso. Tipografia: "Space Grotesk" per i titoli (geometrica, a tema spazio),
# "Inter" per il corpo del testo, "JetBrains Mono" per i numeri delle metriche
# (allineamento tabellare, utile su dati numerici).
# ------------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600&display=swap');

:root {
    --bg-base: #06070f;
    --bg-panel: #0d0f24;
    --border-soft: rgba(130, 140, 255, 0.18);
    --text-primary: #E8EAF6;
    --text-muted: #8891C4;
    --accent-safe: #4CC9F0;
    --accent-danger: #FF4D6D;
    --accent-violet: #7B61FF;
}

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 15% 0%, #10133a 0%, var(--bg-base) 45%, #030309 100%);
    color: var(--text-primary);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #090a1c 0%, #0d0f24 100%);
    border-right: 1px solid var(--border-soft);
}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
}

h1 {
    background: linear-gradient(90deg, var(--accent-violet), var(--accent-safe));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700 !important;
}

h2, h3 { color: var(--text-primary) !important; }

p, li, span, label { color: var(--text-primary); }

/* Card delle metriche */
div[data-testid="stMetric"] {
    background: var(--bg-panel);
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    padding: 14px 16px 10px 16px;
}
div[data-testid="stMetricLabel"] { color: var(--text-muted) !important; }
div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--text-primary) !important;
}

/* Bottoni */
.stButton>button, button[kind="secondaryFormSubmit"], button[kind="primaryFormSubmit"] {
    background: linear-gradient(90deg, var(--accent-violet), var(--accent-safe));
    color: #06070f;
    border: none;
    border-radius: 8px;
    font-weight: 600;
}
.stButton>button:hover, button[kind="secondaryFormSubmit"]:hover, button[kind="primaryFormSubmit"]:hover {
    filter: brightness(1.1);
}

/* Tabella dati */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border-soft);
    border-radius: 10px;
}

hr { border-color: var(--border-soft); }

/* Link */
a { color: var(--accent-safe) !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# 2. COSTANTI
# ==============================================================================
NASA_NEO_FEED_URL: str = "https://api.nasa.gov/neo/rest/v1/feed"
MAX_DATE_RANGE_DAYS: int = 7  # Limite imposto dall'API NASA NeoWs

COLOR_SAFE: str = "#4CC9F0"      # Ciano — asteroidi non pericolosi
COLOR_HAZARDOUS: str = "#FF4D6D"  # Corallo/rosso — potenzialmente pericolosi


# ==============================================================================
# 3. FETCH DATI DALL'API NASA (con caching e gestione errori)
# ==============================================================================
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_neo_feed(api_key: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Interroga l'endpoint 'feed' della NASA NeoWs API per ottenere gli asteroidi
    near-Earth in un dato intervallo di date.

    Args:
        api_key: chiave API NASA (o "DEMO_KEY" per test rapidi).
        start_date: data di inizio in formato ISO 'YYYY-MM-DD'.
        end_date: data di fine in formato ISO 'YYYY-MM-DD'.

    Returns:
        Il corpo della risposta JSON come dizionario Python.

    Raises:
        RuntimeError: messaggio leggibile in caso di errore di rete, di
            autenticazione, di rate-limit o di risposta non valida.
    """
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": api_key.strip() or "DEMO_KEY",
    }

    try:
        response = requests.get(NASA_NEO_FEED_URL, params=params, timeout=15)
    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "⏱️ Timeout: la NASA API non ha risposto in tempo. Riprova tra poco."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            "🌐 Errore di connessione. Controlla la tua connessione internet."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"❌ Errore nella richiesta HTTP: {exc}") from exc

    # Gestione esplicita dei principali codici di errore HTTP
    if response.status_code == 429:
        raise RuntimeError(
            "🚦 Limite di richieste API superato (rate limit). La `DEMO_KEY` "
            "consente solo 30 richieste/ora e 50/giorno: attendi qualche minuto "
            "oppure inserisci una chiave API personale gratuita da api.nasa.gov."
        )
    if response.status_code in (401, 403):
        raise RuntimeError("🔑 Chiave API non valida o non autorizzata.")
    if response.status_code == 400:
        raise RuntimeError(
            "⚠️ Richiesta non valida: controlla che le date siano corrette e "
            "che l'intervallo non superi i 7 giorni."
        )
    if not response.ok:
        raise RuntimeError(
            f"❌ Errore NASA API (HTTP {response.status_code}): {response.text[:200]}"
        )

    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("❌ Risposta non valida: JSON non decodificabile.") from exc


# ==============================================================================
# 4. DATA PROCESSING
# ==============================================================================
def parse_neo_data(raw_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Converte il JSON grezzo del NeoWs feed in un DataFrame Pandas pulito,
    con una riga per ogni evento di avvicinamento di ciascun asteroide.

    Args:
        raw_data: JSON di risposta della NASA NeoWs API.

    Returns:
        DataFrame con colonne pulite e tipizzate pronte per analisi/plotting.
    """
    records: List[Dict[str, Any]] = []
    neo_by_date: Dict[str, List[Dict[str, Any]]] = raw_data.get("near_earth_objects", {})

    for approach_date, neo_list in neo_by_date.items():
        for neo in neo_list:
            # Ogni NEO nel feed ha tipicamente un solo evento di avvicinamento
            # relativo alla data corrente; prendiamo il primo per sicurezza.
            close_approach_list = neo.get("close_approach_data", [])
            cad: Dict[str, Any] = close_approach_list[0] if close_approach_list else {}

            diameter_m = neo.get("estimated_diameter", {}).get("meters", {})
            diam_min = float(diameter_m.get("estimated_diameter_min", 0.0))
            diam_max = float(diameter_m.get("estimated_diameter_max", 0.0))

            # NASA restituisce velocità e distanze come STRINGHE: cast a float.
            velocity_kmh = float(
                cad.get("relative_velocity", {}).get("kilometers_per_hour", 0.0)
            )
            miss_distance_ld = float(cad.get("miss_distance", {}).get("lunar", 0.0))
            miss_distance_km = float(cad.get("miss_distance", {}).get("kilometers", 0.0))

            records.append(
                {
                    "Data Avvicinamento": cad.get("close_approach_date", approach_date),
                    "Nome": neo.get("name", "N/D").strip("()"),
                    "ID": neo.get("id"),
                    "Pericoloso": bool(neo.get("is_potentially_hazardous_asteroid", False)),
                    "Diametro Min (m)": round(diam_min, 1),
                    "Diametro Max (m)": round(diam_max, 1),
                    "Diametro Medio (m)": round((diam_min + diam_max) / 2, 1),
                    "Velocità (km/h)": round(velocity_kmh, 0),
                    "Distanza (LD)": round(miss_distance_ld, 3),
                    "Distanza (km)": round(miss_distance_km, 0),
                    "Magnitudine (H)": neo.get("absolute_magnitude_h"),
                    "URL JPL": neo.get("nasa_jpl_url", ""),
                }
            )

    df = pd.DataFrame.from_records(records)
    if not df.empty:
        df["Data Avvicinamento"] = pd.to_datetime(df["Data Avvicinamento"])
        df = df.sort_values("Data Avvicinamento").reset_index(drop=True)
    return df


def compute_global_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calcola le metriche globali richieste: velocità media, diametro medio
    stimato e distanza lunare (LD) minima registrata nel periodo.

    Args:
        df: DataFrame già processato con parse_neo_data.

    Returns:
        Dizionario con le metriche aggregate.
    """
    if df.empty:
        return {
            "totale": 0,
            "pericolosi": 0,
            "velocita_media": 0.0,
            "diametro_medio": 0.0,
            "distanza_min_ld": 0.0,
        }
    return {
        "totale": int(len(df)),
        "pericolosi": int(df["Pericoloso"].sum()),
        "velocita_media": float(df["Velocità (km/h)"].mean()),
        "diametro_medio": float(df["Diametro Medio (m)"].mean()),
        "distanza_min_ld": float(df["Distanza (LD)"].min()),
    }


# ==============================================================================
# 5. VISUALIZZAZIONI (Plotly - tema "plotly_dark")
# ==============================================================================
def build_scatter_plot(df: pd.DataFrame) -> go.Figure:
    """Crea lo scatter plot Distanza (LD) vs Dimensione stimata (m)."""
    fig = go.Figure()

    trace_config = [
        (False, COLOR_SAFE, "Non pericoloso", "circle", 9),
        (True, COLOR_HAZARDOUS, "Potenzialmente pericoloso", "diamond", 13),
    ]

    for is_hazardous, color, label, symbol, size in trace_config:
        subset = df[df["Pericoloso"] == is_hazardous]
        if subset.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=subset["Distanza (LD)"],
                y=subset["Diametro Medio (m)"],
                mode="markers",
                name=label,
                marker=dict(
                    size=size,
                    color=color,
                    symbol=symbol,
                    opacity=0.85,
                    line=dict(width=1, color="rgba(255,255,255,0.5)"),
                ),
                customdata=subset[["Nome", "Velocità (km/h)", "Data Avvicinamento"]],
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Distanza: %{x:.2f} LD<br>"
                    "Diametro medio: %{y:.1f} m<br>"
                    "Velocità: %{customdata[1]:,.0f} km/h<br>"
                    "Data: %{customdata[2]|%d/%m/%Y}"
                    "<extra></extra>"
                ),
            )
        )

    # Linea di riferimento: distanza media della Luna dalla Terra (1 LD)
    fig.add_vline(
        x=1,
        line_dash="dash",
        line_color="rgba(255,255,255,0.35)",
        annotation_text="Distanza Luna (1 LD)",
        annotation_font_color="rgba(255,255,255,0.6)",
        annotation_position="top",
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#E8EAF6"),
        title="Distanza dalla Terra vs Dimensione Stimata",
        xaxis_title="Distanza dalla Terra (Distanze Lunari, LD) — scala log",
        yaxis_title="Diametro medio stimato (metri)",
        xaxis=dict(type="log", gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        height=520,
        margin=dict(t=90, l=10, r=10, b=10),
    )
    return fig


def build_timeline_chart(df: pd.DataFrame) -> go.Figure:
    """Crea un grafico a barre impilate: n. asteroidi per giorno, per rischio."""
    daily = (
        df.assign(Giorno=df["Data Avvicinamento"].dt.date)
        .groupby(["Giorno", "Pericoloso"])
        .size()
        .reset_index(name="Conteggio")
    )

    fig = go.Figure()
    for is_hazardous, color, label in [
        (False, COLOR_SAFE, "Non pericolosi"),
        (True, COLOR_HAZARDOUS, "Potenzialmente pericolosi"),
    ]:
        subset = daily[daily["Pericoloso"] == is_hazardous]
        if subset.empty:
            continue
        fig.add_trace(
            go.Bar(x=subset["Giorno"], y=subset["Conteggio"], name=label, marker_color=color)
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#E8EAF6"),
        barmode="stack",
        title="Numero di Asteroidi Rilevati per Giorno",
        xaxis_title="Data",
        yaxis_title="N. asteroidi",
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        height=380,
        margin=dict(t=60, l=10, r=10, b=10),
    )
    return fig


def style_dataframe(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    """Applica formattazione condizionale: righe pericolose evidenziate in rosso."""
    display_cols = [
        "Data Avvicinamento",
        "Nome",
        "Pericoloso",
        "Diametro Medio (m)",
        "Velocità (km/h)",
        "Distanza (LD)",
        "Distanza (km)",
        "Magnitudine (H)",
    ]
    display_df = df[display_cols].copy()
    display_df["Data Avvicinamento"] = display_df["Data Avvicinamento"].dt.strftime("%d/%m/%Y")

    def highlight_hazardous(row: pd.Series) -> List[str]:
        if row["Pericoloso"]:
            return ["background-color: rgba(255, 77, 109, 0.18); color: #FFD3DC;"] * len(row)
        return [""] * len(row)

    styler = (
        display_df.style.apply(highlight_hazardous, axis=1).format(
            {
                "Diametro Medio (m)": "{:.1f}",
                "Velocità (km/h)": "{:,.0f}",
                "Distanza (LD)": "{:.2f}",
                "Distanza (km)": "{:,.0f}",
            }
        )
    )
    return styler


# ==============================================================================
# 6. SIDEBAR — INPUT UTENTE
# ==============================================================================
def render_sidebar() -> Tuple[str, date, date, bool]:
    """Disegna la sidebar con i controlli di ricerca e restituisce gli input."""
    st.sidebar.markdown("## ⚙️ Impostazioni di ricerca")
    st.sidebar.markdown(
        "Inserisci una tua chiave API NASA oppure lascia `DEMO_KEY` per "
        "un test rapido (limite: 30 richieste/ora, 50/giorno)."
    )

    with st.sidebar.form("search_form"):
        api_key = st.text_input(
            "🔑 NASA API Key",
            value="DEMO_KEY",
            type="password",
            help="Ottieni una chiave gratuita su https://api.nasa.gov",
        )

        today = date.today()
        start_date = st.date_input(
            "📅 Data inizio",
            value=today,
            min_value=date(1900, 1, 1),
            max_value=today + timedelta(days=365),
        )
        end_date = st.date_input(
            "📅 Data fine",
            value=today + timedelta(days=6),
            min_value=date(1900, 1, 1),
            max_value=today + timedelta(days=365),
        )

        submitted = st.form_submit_button("🚀 Cerca asteroidi", use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "ℹ️ L'API NASA NeoWs impone un limite massimo di **7 giorni** "
        "per ogni intervallo di ricerca."
    )
    st.sidebar.markdown(
        "[📖 Documentazione NeoWs](https://api.nasa.gov/) &nbsp;·&nbsp; "
        "[🔑 Richiedi una API Key](https://api.nasa.gov/#signUp)"
    )

    return api_key, start_date, end_date, submitted


# ==============================================================================
# 7. MAIN APP
# ==============================================================================
def main() -> None:
    st.title("☄️ Near-Earth Asteroids Monitoring Dashboard")
    st.caption(
        "Monitoraggio degli asteroidi in avvicinamento alla Terra, basato sui "
        "dati pubblici della NASA Near Earth Object Web Service (NeoWs)."
    )

    api_key, start_date, end_date, submitted = render_sidebar()

    # --- VALIDAZIONE INPUT -----------------------------------------------
    if start_date > end_date:
        st.error("⚠️ La data di inizio non può essere successiva alla data di fine.")
        st.stop()

    delta_days = (end_date - start_date).days
    if delta_days > MAX_DATE_RANGE_DAYS:
        st.error(
            f"⚠️ Intervallo troppo ampio: {delta_days} giorni selezionati. "
            f"L'API NASA NeoWs consente al massimo {MAX_DATE_RANGE_DAYS} giorni. "
            "Riduci l'intervallo e riprova."
        )
        st.stop()

    # --- RECUPERO DATI (con stato di sessione per evitare fetch inutili) --
    if "df" not in st.session_state:
        st.session_state["df"] = None

    if submitted or st.session_state["df"] is None:
        with st.spinner("🔭 Recupero dati dagli osservatori NASA..."):
            try:
                raw_data = fetch_neo_feed(api_key, start_date.isoformat(), end_date.isoformat())
                st.session_state["df"] = parse_neo_data(raw_data)
            except RuntimeError as err:
                st.error(str(err))
                st.stop()
            except Exception as err:  # rete di sicurezza per errori imprevisti
                st.error(f"❌ Errore imprevisto durante l'elaborazione dei dati: {err}")
                st.stop()

    df: Optional[pd.DataFrame] = st.session_state["df"]

    if df is None or df.empty:
        st.warning("Nessun asteroide trovato per l'intervallo di date selezionato.")
        st.stop()

    # --- METRICHE GLOBALI ---------------------------------------------------
    metrics = compute_global_metrics(df)
    st.markdown("### 📊 Statistiche generali")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Asteroidi rilevati", metrics["totale"])
    col2.metric("Potenzialmente pericolosi", metrics["pericolosi"])
    col3.metric("Velocità media", f"{metrics['velocita_media']:,.0f} km/h")
    col4.metric("Diametro medio", f"{metrics['diametro_medio']:,.0f} m")
    col5.metric("Distanza minima", f"{metrics['distanza_min_ld']:.2f} LD")

    st.markdown("---")

    # --- SCATTER PLOT ---------------------------------------------------
    st.markdown("### 🛰️ Distanza dalla Terra vs Dimensione stimata")
    st.plotly_chart(build_scatter_plot(df), use_container_width=True)

    # --- TIMELINE CHART ---------------------------------------------------
    st.markdown("### 📆 Asteroidi rilevati per giorno")
    st.plotly_chart(build_timeline_chart(df), use_container_width=True)

    st.markdown("---")

    # --- TABELLA DATI GREZZI ---------------------------------------------------
    st.markdown("### 📋 Dati grezzi")
    st.dataframe(style_dataframe(df), use_container_width=True, height=420)

    csv_bytes = df.drop(columns=["URL JPL"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Scarica CSV completo",
        data=csv_bytes,
        file_name=f"nea_data_{start_date.isoformat()}_{end_date.isoformat()}.csv",
        mime="text/csv",
    )

    st.caption("Fonte dati: NASA Near Earth Object Web Service (NeoWs) — https://api.nasa.gov/")


if __name__ == "__main__":
    main()
