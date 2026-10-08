"""Dashboard interactivo del modelo financiero.

Ejecución:
    streamlit run app.py

Yahoo Finance alimenta precios, fundamentales y noticias. Los indicadores se
calculan localmente con pandas-ta. Los datos macro y sectoriales están marcados
como simulados para no confundirlos con observaciones de mercado.
"""
from __future__ import annotations

from datetime import datetime
from html import escape
import json
from pathlib import Path
import re
import zlib

import numpy as np
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output" / "real"
YFINANCE_CACHE = ROOT / "data" / ".yfinance_cache"
YFINANCE_CACHE.mkdir(parents=True, exist_ok=True)
# yfinance guarda cookies y zonas horarias en SQLite. Mantener ese caché dentro
# del proyecto evita depender de un directorio de usuario que pueda ser de sólo lectura.
yf.set_tz_cache_location(str(YFINANCE_CACHE))

GREEN = "#00C853"
RED = "#FF1744"
AMBER = "#FFC107"
BLUE = "#40C4FF"
BACKGROUND = "#0E1117"
PANEL = "#151A23"
TEXT = "#EAEAEA"
MUTED = "#9AA4B2"

TIMEFRAMES = {
    "1d": ("1d", "5m"),
    "5d": ("5d", "15m"),
    "1mo": ("1mo", "1h"),
    "3mo": ("3mo", "1d"),
    "6mo": ("6mo", "1d"),
    "1y": ("1y", "1d"),
    "5y": ("5y", "1d"),
    "Max": ("max", "1d"),
}


st.set_page_config(
    page_title="Terminal de Finanzas · Bonos 60%",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
    <style>
    .stApp {{ background: {BACKGROUND}; color: {TEXT}; }}
    header[data-testid="stHeader"] {{ background: rgba(14,17,23,.92); }}
    [data-testid="stMetric"] {{
        background: linear-gradient(145deg, #171D27, #11161E);
        border: 1px solid #273140; border-radius: 8px; padding: 12px 14px;
    }}
    [data-testid="stMetricLabel"] {{ color: {MUTED}; }}
    [data-testid="stMetricValue"] {{ color: {TEXT}; font-family: Consolas, monospace; }}
    .terminal-title {{ font-family: Consolas, monospace; letter-spacing: .08em; }}
    .terminal-subtitle {{ color: {MUTED}; margin-top: -.7rem; }}
    .section-label {{ color: {BLUE}; font-family: Consolas, monospace;
        font-size: .78rem; letter-spacing: .12em; margin: .9rem 0 .3rem 0; }}
    .data-card {{ background: {PANEL}; border: 1px solid #273140;
        border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; min-height: 67px; }}
    .data-label {{ color: {MUTED}; font-size: .76rem; text-transform: uppercase; }}
    .data-value {{ color: {TEXT}; font: 600 1.10rem Consolas, monospace; }}
    .alert-red {{ border-left: 4px solid {RED}; }}
    .alert-amber {{ border-left: 4px solid {AMBER}; }}
    .alert-green {{ border-left: 4px solid {GREEN}; }}
    .simulated {{ color: {AMBER}; font-size: .72rem; }}
    .news-card {{ background: {PANEL}; border: 1px solid #273140;
        border-radius: 8px; padding: 10px 12px; margin-bottom: 9px; }}
    .news-title {{ color: {TEXT}; font-weight: 600; line-height: 1.25; }}
    .news-meta {{ color: {MUTED}; font-size: .75rem; margin-top: 4px; }}
    div.stButton > button {{ border: 1px solid #344052; border-radius: 6px; }}
    div[data-testid="stPlotlyChart"] {{ background: {PANEL}; border-radius: 8px; }}
    #MainMenu, footer {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _flatten_yahoo_columns(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Normaliza las dos variantes de columnas que devuelve yfinance."""
    result = frame.copy()
    if isinstance(result.columns, pd.MultiIndex):
        for level in range(result.columns.nlevels):
            values = result.columns.get_level_values(level).astype(str)
            if ticker in set(values):
                result = result.xs(ticker, axis=1, level=level, drop_level=True)
                break
        if isinstance(result.columns, pd.MultiIndex):
            result.columns = result.columns.get_level_values(0)
    result.columns = [str(column).title() for column in result.columns]
    return result


@st.cache_data(ttl=300, show_spinner=False)
def fetch_price_history(ticker: str, period: str, interval: str, refresh_token: int) -> pd.DataFrame:
    """Descarga OHLCV. refresh_token sólo invalida el caché al pulsar Actualizar."""
    del refresh_token
    data = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
        group_by="column",
    )
    data = _flatten_yahoo_columns(data, ticker)
    needed = ["Open", "High", "Low", "Close", "Volume"]
    if data.empty or any(column not in data for column in needed):
        return pd.DataFrame(columns=needed)
    data = data[needed].apply(pd.to_numeric, errors="coerce").dropna(subset=needed[:4])
    if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
        data.index = data.index.tz_localize(None)
    return data[~data.index.duplicated(keep="last")].sort_index()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_fundamentals(ticker: str, refresh_token: int) -> dict:
    del refresh_token
    try:
        return dict(yf.Ticker(ticker).get_info() or {})
    except Exception:
        return {}


def _news_item(item: dict) -> dict | None:
    """Acepta la estructura histórica y la estructura `content` nueva de yfinance."""
    content = item.get("content", item) if isinstance(item, dict) else {}
    title = content.get("title") or item.get("title")
    if not title:
        return None
    provider = content.get("provider") or item.get("publisher") or {}
    if isinstance(provider, dict):
        provider = provider.get("displayName", "Yahoo Finance")
    published = content.get("pubDate") or item.get("providerPublishTime")
    if isinstance(published, (int, float)):
        published = datetime.fromtimestamp(published).strftime("%d/%m/%Y %H:%M")
    elif published:
        try:
            published = pd.Timestamp(published).strftime("%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            published = str(published)
    links = [content.get("clickThroughUrl"), content.get("canonicalUrl")]
    url = item.get("link", "")
    for link in links:
        if isinstance(link, dict) and link.get("url"):
            url = link["url"]
            break
    return {"title": str(title), "provider": str(provider or "Yahoo Finance"),
            "published": str(published or "Fecha no disponible"), "url": str(url or "")}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(ticker: str, refresh_token: int) -> list[dict]:
    del refresh_token
    try:
        raw = yf.Ticker(ticker).get_news(count=10)
        parsed = [_news_item(item) for item in raw]
        return [item for item in parsed if item][:3]
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def load_local_csv(path_text: str, modified_ns: int, refresh_token: int) -> pd.DataFrame:
    del modified_ns, refresh_token
    path = Path(path_text)
    try:
        return pd.read_csv(path) if path.exists() else pd.DataFrame()
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def load_local_json(path_text: str, modified_ns: int, refresh_token: int) -> dict:
    del modified_ns, refresh_token
    path = Path(path_text)
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError, UnicodeDecodeError):
        return {}


def load_csv(name: str, refresh_token: int) -> pd.DataFrame:
    path = OUTPUT / name
    modified = path.stat().st_mtime_ns if path.exists() else 0
    return load_local_csv(str(path), modified, refresh_token)


def load_json(name: str, refresh_token: int) -> dict:
    path = OUTPUT / name
    modified = path.stat().st_mtime_ns if path.exists() else 0
    return load_local_json(str(path), modified, refresh_token)


def calculate_indicators(history: pd.DataFrame) -> pd.DataFrame:
    """Agrega los indicadores requeridos sin rellenar artificialmente su warm-up."""
    result = history.copy()
    close = result["Close"].astype(float)
    for length in (20, 50, 200):
        result[f"SMA_{length}"] = ta.sma(close, length=length)
    result["RSI_14"] = ta.rsi(close, length=14)
    macd = ta.macd(close, fast=12, slow=26, signal=9)
    if macd is not None and not macd.empty:
        result["MACD"] = macd.filter(like="MACD_").iloc[:, 0]
        result["MACD_SIGNAL"] = macd.filter(like="MACDs_").iloc[:, 0]
        result["MACD_HIST"] = macd.filter(like="MACDh_").iloc[:, 0]
    else:
        result[["MACD", "MACD_SIGNAL", "MACD_HIST"]] = np.nan
    return result


def _format_number(value: object, decimals: int = 2, prefix: str = "") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/D"
    if not np.isfinite(number):
        return "N/D"
    return f"{prefix}{number:,.{decimals}f}"


def _format_compact(value: object, prefix: str = "") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/D"
    if not np.isfinite(number):
        return "N/D"
    for divisor, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(number) >= divisor:
            return f"{prefix}{number/divisor:,.2f}{suffix}"
    return f"{prefix}{number:,.0f}"


def _format_percent(value: object, scale: float = 100) -> str:
    try:
        number = float(value) * scale
    except (TypeError, ValueError):
        return "N/D"
    return f"{number:,.2f}%" if np.isfinite(number) else "N/D"


def _currency(info: dict) -> str:
    symbol = info.get("currency", "USD")
    return {"USD": "US$", "ARS": "ARS ", "EUR": "€", "GBP": "£"}.get(symbol, f"{symbol} ")


def build_market_chart(data: pd.DataFrame, ticker: str) -> go.Figure:
    """Cuatro filas: precio, volumen, RSI y MACD."""
    figure = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[0.53, 0.15, 0.14, 0.18],
        subplot_titles=(f"{ticker} · Precio", "Volumen", "RSI (14)", "MACD (12, 26, 9)"),
    )
    figure.add_trace(
        go.Candlestick(
            x=data.index, open=data["Open"], high=data["High"], low=data["Low"],
            close=data["Close"], name="OHLC",
            increasing_line_color=GREEN, decreasing_line_color=RED,
        ), row=1, col=1,
    )
    for column, color, width in (("SMA_20", "#40C4FF", 1.4),
                                  ("SMA_50", "#FFC107", 1.4),
                                  ("SMA_200", "#E040FB", 1.7)):
        if data[column].notna().any():
            figure.add_trace(go.Scatter(x=data.index, y=data[column], name=column.replace("_", "(" ) + ")",
                                        line={"color": color, "width": width}), row=1, col=1)
    volume_colors = np.where(data["Close"] >= data["Open"], GREEN, RED)
    figure.add_trace(go.Bar(x=data.index, y=data["Volume"], marker_color=volume_colors,
                            name="Volumen", opacity=.72), row=2, col=1)
    figure.add_trace(go.Scatter(x=data.index, y=data["RSI_14"], name="RSI",
                                line={"color": BLUE, "width": 1.5}), row=3, col=1)
    figure.add_hline(y=70, line_dash="dash", line_color=RED, opacity=.8, row=3, col=1)
    figure.add_hline(y=30, line_dash="dash", line_color=GREEN, opacity=.8, row=3, col=1)
    histogram_colors = np.where(data["MACD_HIST"].fillna(0) >= 0, GREEN, RED)
    figure.add_trace(go.Bar(x=data.index, y=data["MACD_HIST"], name="Histograma",
                            marker_color=histogram_colors, opacity=.55), row=4, col=1)
    figure.add_trace(go.Scatter(x=data.index, y=data["MACD"], name="MACD",
                                line={"color": BLUE, "width": 1.4}), row=4, col=1)
    figure.add_trace(go.Scatter(x=data.index, y=data["MACD_SIGNAL"], name="Señal",
                                line={"color": AMBER, "width": 1.3}), row=4, col=1)
    figure.update_layout(
        template="plotly_dark", paper_bgcolor=BACKGROUND, plot_bgcolor=PANEL,
        font={"color": TEXT, "family": "Arial"}, height=870,
        margin={"l": 30, "r": 20, "t": 42, "b": 25},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        hovermode="x unified", bargap=.05, xaxis_rangeslider_visible=False,
    )
    figure.update_xaxes(gridcolor="#252D38", showgrid=True)
    figure.update_yaxes(gridcolor="#252D38", showgrid=True, zerolinecolor="#3A4554")
    figure.update_yaxes(range=[0, 100], row=3, col=1)
    return figure


def _data_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f'<div class="data-card"><div class="data-label">{escape(label)}</div>'
        f'<div class="data-value">{escape(value)}</div>'
        f'<div class="news-meta">{escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


def simulated_sector_returns(ticker: str) -> pd.DataFrame:
    """Serie estable por ticker; siempre se rotula como simulación."""
    seed = zlib.crc32(ticker.encode("utf-8"))
    rng = np.random.default_rng(seed)
    sectors = ["Tecnología", "Finanzas", "Energía", "Salud", "Industriales"]
    return pd.DataFrame({"sector": sectors, "return": rng.normal(.004, .018, len(sectors))})


def sample_news(ticker: str) -> list[dict]:
    return [
        {"title": f"Resumen de mercado para {ticker}", "provider": "Dato de muestra",
         "published": "Sin conexión con Yahoo Finance", "url": ""},
        {"title": "Los mercados revisan tasas, inflación y resultados corporativos",
         "provider": "Dato de muestra", "published": "Contenido ilustrativo", "url": ""},
        {"title": "La volatilidad y el volumen concentran la atención de los inversores",
         "provider": "Dato de muestra", "published": "Contenido ilustrativo", "url": ""},
    ]


def _parse_cash_weight(target_text: object) -> float:
    match = re.search(r"CASH:([0-9.,]+)%", str(target_text))
    return float(match.group(1).replace(",", ".")) / 100 if match else np.nan


def group_model_history(decisions: pd.DataFrame, period: str) -> pd.DataFrame:
    if decisions.empty or "generated_at" not in decisions:
        return pd.DataFrame()
    frame = decisions.copy()
    frame["generated_at"] = pd.to_datetime(frame["generated_at"], errors="coerce")
    frame = frame.dropna(subset=["generated_at"]).sort_values("generated_at")
    frame["cash_weight"] = frame.get("target", pd.Series(index=frame.index, dtype=str)).map(_parse_cash_weight)
    frame["invested_weight"] = 1 - frame["cash_weight"]
    if period == "Mes":
        frame["period"] = frame.generated_at.dt.to_period("M").astype(str)
    elif period == "Trimestre":
        frame["period"] = frame.generated_at.dt.to_period("Q").astype(str)
    elif period == "Semestre":
        frame["period"] = (frame.generated_at.dt.year.astype(str) + " S" +
                           (((frame.generated_at.dt.month - 1) // 6) + 1).astype(str))
    else:
        frame["period"] = frame.generated_at.dt.year.astype(str)
    return frame.groupby("period", as_index=False).agg(
        equity=("equity", "last"), invested_weight=("invested_weight", "last"),
        drawdown=("drawdown", "last"), observations=("generated_at", "size"))


def group_cost_history(ledger: pd.DataFrame, period: str) -> pd.DataFrame:
    if ledger.empty or not {"date", "cost"}.issubset(ledger):
        return pd.DataFrame()
    frame = ledger.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["cost"] = pd.to_numeric(frame["cost"], errors="coerce").fillna(0)
    if "strategy" in frame:
        frame = frame[frame.strategy.eq("ROBUST_MEAN_VARIANCE")]
    if period == "Mes":
        frame["period"] = frame.date.dt.to_period("M").astype(str)
    elif period == "Trimestre":
        frame["period"] = frame.date.dt.to_period("Q").astype(str)
    elif period == "Semestre":
        frame["period"] = (frame.date.dt.year.astype(str) + " S" +
                           (((frame.date.dt.month - 1) // 6) + 1).astype("Int64").astype(str))
    else:
        frame["period"] = frame.date.dt.year.astype("Int64").astype(str)
    return frame.dropna(subset=["date"]).groupby("period", as_index=False).cost.sum()


def collect_risk_alerts(data: pd.DataFrame, optimization: dict, risk: dict,
                        orders: pd.DataFrame, ledger: pd.DataFrame) -> list[dict]:
    alerts: list[dict] = []
    returns = data["Close"].pct_change().dropna()
    if len(returns) >= 20:
        volatility = returns.tail(20).std()
        zscore = ((returns.iloc[-1] - returns.tail(20).mean()) / volatility
                  if volatility and np.isfinite(volatility) else 0)
        if abs(zscore) >= 2.5:
            alerts.append({"level": "red", "title": "Anomalía de precio",
                           "detail": f"El último retorno está a {zscore:.1f} desvíos del promedio reciente."})
    if len(data) >= 20:
        median_volume = data["Volume"].tail(20).median()
        if median_volume > 0 and data["Volume"].iloc[-1] > median_volume * 3:
            alerts.append({"level": "amber", "title": "Volumen atípico",
                           "detail": "El volumen supera tres veces la mediana de 20 observaciones."})
    rsi = data["RSI_14"].dropna()
    if len(rsi) and (rsi.iloc[-1] > 70 or rsi.iloc[-1] < 30):
        zone = "sobrecompra" if rsi.iloc[-1] > 70 else "sobreventa"
        alerts.append({"level": "amber", "title": "RSI extremo",
                       "detail": f"RSI {rsi.iloc[-1]:.1f}: zona técnica de {zone}."})
    realized = optimization.get("max_risk_contribution_realized")
    warning = optimization.get("risk_contribution_warning_level")
    if realized is not None and warning is not None and float(realized) > float(warning):
        alerts.append({"level": "amber", "title": "Concentración de riesgo",
                       "detail": f"Aporte máximo {float(realized):.1%}; referencia {float(warning):.1%}."})
    if risk.get("validation_errors"):
        alerts.append({"level": "red", "title": "Cartera fuera de límites",
                       "detail": " · ".join(map(str, risk["validation_errors"]))})
    readiness = orders.get("execution_ready", pd.Series(True, index=orders.index))
    readiness = readiness.map(lambda value: value if isinstance(value, (bool, np.bool_))
                              else str(value).strip().lower() in {"true", "1", "yes", "si", "sí"})
    unavailable = orders[~readiness]
    if len(unavailable):
        alerts.append({"level": "red", "title": "Riesgo de liquidez",
                       "detail": f"{len(unavailable)} propuestas no tienen una punta ejecutable válida."})
    coverage = risk.get("risk_model_coverage_weight")
    invested = risk.get("invested_weight")
    if coverage is not None and invested is not None and float(coverage) + 1e-8 < float(invested):
        alerts.append({"level": "red", "title": "Cobertura incompleta de riesgo",
                       "detail": "Parte de la cartera invertida carece de historia común suficiente."})
    if not ledger.empty and {"cost", "starting_equity"}.issubset(ledger):
        sample = ledger.copy()
        if "strategy" in sample:
            sample = sample[sample.strategy.eq("ROBUST_MEAN_VARIANCE")]
        ratios = (pd.to_numeric(sample.cost, errors="coerce") /
                  pd.to_numeric(sample.starting_equity, errors="coerce")).replace([np.inf, -np.inf], np.nan).dropna()
        if len(ratios) >= 10 and ratios.iloc[-1] > ratios.quantile(.95) and ratios.iloc[-1] > 0:
            alerts.append({"level": "amber", "title": "Desvío de costos",
                           "detail": f"Costo de la última rueda {ratios.iloc[-1]:.3%}, sobre el percentil 95 histórico."})
    research = risk.get("research", {})
    if research and not research.get("valuation_complete", True):
        alerts.append({"level": "amber", "title": "Validación histórica incompleta",
                       "detail": "Hay marcas faltantes; el MCS no certifica superioridad del modelo."})
    return alerts or [{"level": "green", "title": "Sin alertas automáticas",
                       "detail": "No se detectaron anomalías con las reglas y datos disponibles."}]


def show_alerts(alerts: list[dict]) -> None:
    st.markdown('<div class="section-label">ALERTAS AUTOMÁTICAS</div>', unsafe_allow_html=True)
    columns = st.columns(min(3, len(alerts)))
    for index, alert in enumerate(alerts):
        with columns[index % len(columns)]:
            st.markdown(
                f'<div class="data-card alert-{alert["level"]}">'
                f'<div class="data-label">{escape(alert["title"])}</div>'
                f'<div class="news-meta">{escape(alert["detail"])}</div></div>',
                unsafe_allow_html=True,
            )


def show_portfolio_section(refresh_token: int) -> None:
    target = load_csv("target_portfolio.csv", refresh_token)
    decisions = load_csv("decision_log.csv", refresh_token)
    ledger = load_csv("backtest_ledger.csv", refresh_token)
    if target.empty:
        return
    st.markdown('<div class="section-label">MODELO LOCAL · CARTERA Y COSTOS</div>', unsafe_allow_html=True)
    period = st.radio("Agrupar historial", ["Mes", "Trimestre", "Semestre", "Año"],
                      horizontal=True, label_visibility="collapsed")
    left, center, right = st.columns(3)
    target["target_value"] = pd.to_numeric(target.get("target_value"), errors="coerce").fillna(0)
    factor = target.groupby("economic_factor", as_index=False).target_value.sum()
    donut = go.Figure(go.Pie(labels=factor.economic_factor, values=factor.target_value,
                             hole=.62, textinfo="label+percent", marker={"line": {"color": BACKGROUND, "width": 2}}))
    donut.update_layout(template="plotly_dark", paper_bgcolor=BACKGROUND, plot_bgcolor=PANEL,
                        height=340, margin={"l": 10, "r": 10, "t": 45, "b": 10},
                        title="Composición por factor", showlegend=False, font={"color": TEXT})
    left.plotly_chart(donut, width="stretch", config={"displayModeBar": False, "responsive": True})

    costs = group_cost_history(ledger, period)
    if not costs.empty:
        cost_fig = go.Figure(go.Bar(x=costs.period, y=costs.cost, marker_color=AMBER,
                                    hovertemplate="%{x}<br>ARS %{y:,.0f}<extra></extra>"))
        cost_fig.update_layout(template="plotly_dark", paper_bgcolor=BACKGROUND, plot_bgcolor=PANEL,
                               height=340, title=f"Costos por {period.lower()}",
                               margin={"l": 15, "r": 10, "t": 45, "b": 30}, font={"color": TEXT})
        center.plotly_chart(cost_fig, width="stretch",
                            config={"displayModeBar": False, "responsive": True})
    else:
        center.info("Todavía no hay costos históricos para esta agrupación.")

    history = group_model_history(decisions, period)
    if not history.empty:
        trend = make_subplots(specs=[[{"secondary_y": True}]])
        trend.add_trace(go.Scatter(x=history.period, y=history.equity, mode="lines+markers",
                                   name="Patrimonio", line={"color": GREEN, "width": 2}), secondary_y=False)
        trend.add_trace(go.Scatter(x=history.period, y=history.invested_weight, mode="lines+markers",
                                   name="Invertido", line={"color": BLUE, "width": 1.5}), secondary_y=True)
        trend.update_yaxes(tickformat=".0%", range=[0, 1.05], secondary_y=True)
        trend.update_layout(template="plotly_dark", paper_bgcolor=BACKGROUND, plot_bgcolor=PANEL,
                            height=340, title="Tendencia del modelo", hovermode="x unified",
                            margin={"l": 15, "r": 10, "t": 45, "b": 30}, font={"color": TEXT})
        right.plotly_chart(trend, width="stretch",
                           config={"displayModeBar": False, "responsive": True})
    else:
        right.info("Todavía no hay decisiones registradas para esta agrupación.")

    show_bond_section(refresh_token)


def show_bond_section(refresh_token: int) -> None:
    """Resume cobertura, analítica y estado de elegibilidad de renta fija."""
    signals = load_csv("bond_signals.csv", refresh_token)
    report = load_json("bond_report.json", refresh_token)
    analytics_path = ROOT / "data" / "fixed_income" / "live_analytics.csv"
    modified = analytics_path.stat().st_mtime_ns if analytics_path.exists() else 0
    analytics = load_local_csv(str(analytics_path), modified, refresh_token)
    st.markdown('<div class="section-label">BONOS ARGENTINOS · ESTADO DEL MOTOR</div>',
                unsafe_allow_html=True)
    cards = st.columns(4)
    cards[0].metric("Modalidad", "ON" if report.get("enabled") else "OFF")
    cards[1].metric("Contratos verificados", int(report.get("verified_instruments", 0)))
    cards[2].metric("Elegibles hoy", int(report.get("eligible_with_inputs", 0)))
    cards[3].metric("TIR en vivo", len(analytics))
    st.caption(
        "ON habilita la clase. Un bono aparece como elegible sólo después de tener "
        "contrato, al menos 66 ruedas de retorno total, TIR vigente y escenario ARS."
    )
    if signals.empty:
        st.info("Ejecutá `modelo.cmd calcular` para generar el diagnóstico de bonos.")
        return
    columns = [name for name in (
        "ticker", "family", "fi_status", "fi_strategy", "fi_yield_annual",
        "fi_carry_annual_ars", "fi_duration", "fi_volatility",
    ) if name in signals]
    table = signals[columns].copy()
    if not analytics.empty:
        current = analytics.sort_values("fetched_at").drop_duplicates("ticker", keep="last")
        available = [name for name in (
            "ticker", "parity", "modified_duration", "yield_annual",
        ) if name in current]
        current = current[available].rename(columns={
            "yield_annual": "live_yield_annual",
            "modified_duration": "live_modified_duration",
        })
        table = table.merge(current, on="ticker", how="left")
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption(
        "NO_TOTAL_RETURN_HISTORY: falta la primera carga histórica. "
        "NO_YIELD_OBSERVATIONS: aún no hay una TIR conocida antes de la decisión. "
        "ELIGIBLE_SUBJECT_TO_PORTFOLIO_FILTERS: puede competir por peso, sujeto a límites."
    )


def main() -> None:
    if "timeframe" not in st.session_state:
        st.session_state.timeframe = "1y"
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = 0

    st.markdown('<h2 class="terminal-title">FINANCE TERMINAL <span style="color:#00C853">●</span></h2>',
                unsafe_allow_html=True)
    st.markdown('<div class="terminal-subtitle">Mercado · fundamentales · cartera · riesgo</div>',
                unsafe_allow_html=True)

    page = st.radio("Navegación", ["Inicio y guía", "Cartera y bonos", "Mercado"],
                    horizontal=True, label_visibility="collapsed")
    if page == "Inicio y guía":
        st.title("Una cartera con 60% en bonos")
        st.write("Retorno esperado neto de costos, sujeto a crédito, liquidez y riesgo de tasas.")
        for column, label, value in zip(st.columns(3),
                                        ["Objetivo bonos", "Otros activos", "Liquidez"],
                                        ["60%", "Hasta 35%", "Desde 5%"]):
            column.metric(label, value)
        risk = load_json("risk_report.json", st.session_state.refresh_token)
        allocation = risk.get("allocation", {})
        if allocation:
            st.info(f"Último cálculo: {risk.get('as_of', 's/d')} · "
                    f"Bonos propuestos: {allocation['proposed_bond_weight']:.1%} · "
                    f"Faltante: ARS {allocation['bond_shortfall_ars']:,.0f} · "
                    f"{allocation['status']}")
        else:
            st.info("Todavía no hay un cálculo guardado con el perfil Bonos 60%.")
        st.caption("El faltante permanece en caja. La caja no cuenta como bonos. "
                   "Moneda y horizonte provisionales: ARS / 12 meses.")
        guide = ROOT / "GUIA_USO.md"
        guide_text = guide.read_text(encoding="utf-8")
        st.download_button("Descargar guía unificada", guide_text,
                           file_name="GUIA_USO.md", mime="text/markdown")
        st.markdown(guide_text)
        with st.expander("Leer criterios, supuestos y bibliografía de bonos"):
            strategy_text = (ROOT / "ESTRATEGIA_BONOS_60.md").read_text(encoding="utf-8")
            st.markdown(strategy_text)
            st.download_button("Descargar política de inversión", strategy_text,
                               file_name="ESTRATEGIA_BONOS_60.md", mime="text/markdown")
        return
    if page == "Cartera y bonos":
        show_portfolio_section(st.session_state.refresh_token)
        stress = load_csv("bond_stress.csv", st.session_state.refresh_token)
        if not stress.empty and load_json("risk_report.json", 0).get("allocation"):
            st.subheader("Escenarios adversos del bloque de bonos")
            st.dataframe(stress, hide_index=True, width="stretch")
            st.caption("Shocks hipotéticos sin probabilidad asignada. No representan pérdida máxima.")
        return

    controls = st.columns([2.3] + [.62] * len(TIMEFRAMES) + [1.05])
    ticker = controls[0].text_input("Ticker", value="AAPL", placeholder="Ej.: AAPL, GGAL.BA").strip().upper()
    for column, label in zip(controls[1:-1], TIMEFRAMES):
        if column.button(label, key=f"tf_{label}", use_container_width=True,
                         type="primary" if st.session_state.timeframe == label else "secondary"):
            st.session_state.timeframe = label
    if controls[-1].button("Actualizar", use_container_width=True, type="primary"):
        st.session_state.refresh_token += 1
        fetch_price_history.clear()
        fetch_fundamentals.clear()
        fetch_news.clear()

    if not ticker:
        st.error("Ingresá un ticker válido. Podés comenzar con AAPL.")
        st.stop()
    period, interval = TIMEFRAMES[st.session_state.timeframe]
    with st.spinner(f"Actualizando {ticker} · {st.session_state.timeframe}…"):
        try:
            history = fetch_price_history(ticker, period, interval, st.session_state.refresh_token)
        except Exception as exc:
            st.error(f"No se pudo consultar Yahoo Finance: {exc}. Probá nuevamente o usá AAPL.")
            st.stop()
    if history.empty:
        st.error(f"No encontramos precios para “{ticker}”. Revisá el símbolo o probá AAPL.")
        st.stop()
    data = calculate_indicators(history)
    info = fetch_fundamentals(ticker, st.session_state.refresh_token)
    news = fetch_news(ticker, st.session_state.refresh_token)
    currency = _currency(info)

    latest = data.iloc[-1]
    previous = data.iloc[-2] if len(data) > 1 else latest
    change_amount = float(latest.Close - previous.Close)
    change_pct = change_amount / float(previous.Close) if previous.Close else 0.0
    high_52 = info.get("fiftyTwoWeekHigh", data.High.max())
    low_52 = info.get("fiftyTwoWeekLow", data.Low.min())

    st.markdown('<div class="section-label">RESUMEN DE MERCADO</div>', unsafe_allow_html=True)
    kpis = st.columns(6)
    kpis[0].metric("Precio actual", _format_number(latest.Close, 2, currency),
                   _format_percent(change_pct), delta_color="normal")
    kpis[1].metric("Cambio", _format_percent(change_pct),
                   _format_number(change_amount, 2, currency), delta_color="normal")
    kpis[2].metric("Volumen", _format_compact(latest.Volume))
    kpis[3].metric("Capitalización", _format_compact(info.get("marketCap"), currency))
    kpis[4].metric("Máximo 52 semanas", _format_number(high_52, 2, currency))
    kpis[5].metric("Mínimo 52 semanas", _format_number(low_52, 2, currency))

    optimization = load_json("optimization_report.json", st.session_state.refresh_token)
    risk = load_json("risk_report.json", st.session_state.refresh_token)
    orders = load_csv("orders.csv", st.session_state.refresh_token)
    ledger = load_csv("backtest_ledger.csv", st.session_state.refresh_token)
    alerts = collect_risk_alerts(data, optimization, risk, orders, ledger)
    show_alerts(alerts)

    st.markdown('<div class="section-label">PRECIO E INDICADORES</div>', unsafe_allow_html=True)
    st.plotly_chart(build_market_chart(data, ticker), width="stretch",
                    config={"displaylogo": False, "responsive": True,
                            "modeBarButtonsToRemove": ["lasso2d", "select2d"]})

    st.markdown('<div class="section-label">FUNDAMENTALES · MACRO · NOTICIAS</div>', unsafe_allow_html=True)
    fundamentals_col, macro_col, news_col = st.columns(3)
    with fundamentals_col:
        st.subheader("Datos fundamentales")
        _data_card("PER (trailing)", _format_number(info.get("trailingPE"), 2))
        _data_card("Yield de dividendo", _format_percent(info.get("dividendYield")))
        _data_card("Beneficio por acción", _format_number(info.get("trailingEps"), 2, currency))
        _data_card("Rango 52 semanas",
                   f"{_format_number(low_52, 2, currency)} — {_format_number(high_52, 2, currency)}")

    with macro_col:
        st.subheader("Contexto macro")
        macro_left, macro_right = st.columns(2)
        with macro_left:
            _data_card("Tasa Fed", "5,50%", "SIMULADO")
        with macro_right:
            _data_card("IPC interanual", "3,20%", "SIMULADO")
        sectors = simulated_sector_returns(ticker)
        colors = np.where(sectors["return"] >= 0, GREEN, RED)
        sector_chart = go.Figure(go.Bar(
            x=sectors["return"], y=sectors["sector"], orientation="h",
            marker_color=colors, text=sectors["return"].map(lambda value: f"{value:.1%}"),
            textposition="outside", hovertemplate="%{y}: %{x:.2%}<extra></extra>",
        ))
        sector_chart.update_layout(
            template="plotly_dark", paper_bgcolor=BACKGROUND, plot_bgcolor=PANEL,
            height=260, title="Rendimiento sectorial · SIMULADO", showlegend=False,
            margin={"l": 10, "r": 40, "t": 45, "b": 20}, font={"color": TEXT},
            xaxis={"tickformat": ".0%"}, yaxis={"autorange": "reversed"},
        )
        st.plotly_chart(sector_chart, width="stretch",
                        config={"displayModeBar": False, "responsive": True})

    with news_col:
        st.subheader(f"Noticias y eventos · {ticker}")
        items = news or sample_news(ticker)
        if not news:
            st.caption("Yahoo Finance no respondió; se muestran ejemplos identificados como muestra.")
        for item in items[:3]:
            title = escape(item["title"])
            url = item.get("url", "")
            title_markup = f'<a href="{escape(url, quote=True)}" target="_blank" class="news-title">{title}</a>' if url.startswith("http") else f'<div class="news-title">{title}</div>'
            st.markdown(
                f'<div class="news-card">{title_markup}'
                f'<div class="news-meta">{escape(item["provider"])} · {escape(item["published"])}</div></div>',
                unsafe_allow_html=True,
            )

    show_portfolio_section(st.session_state.refresh_token)
    st.caption(
        "Precios, fundamentales y noticias: Yahoo Finance, caché 5 minutos. "
        "Fed, IPC y sectores: simulados. Señales y alertas son diagnósticos; las propuestas locales no se ejecutan automáticamente."
    )


if __name__ == "__main__":
    main()
