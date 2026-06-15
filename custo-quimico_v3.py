# ============================================================
# PAINEL - CUSTOS LABORATORIAIS | Agrorobótica (REFORMULADO)
# ============================================================

import io
import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Painel - Custo Laboratório Químico",
    layout="wide",
    initial_sidebar_state="expanded"
)

TABELA_PRECOS = {
    "CHN": 50.0,
    "K_P_Mehlich": 3.75,
    "Macro": 5.29,
    "Micro": 5.11,
    "MO": 1.48,
    "pH_CaCl2": 1.32,
    "pH_H2O": 1.32,
    "P_Resina": 3.76,
    "S_ICP": 5.14,
    "S_Turbidimetria": 3.13,
    "Textura": 5.64,
}

ANALISES = list(TABELA_PRECOS.keys())


# ============================================================
# UTILITÁRIOS
# ============================================================

def format_brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_num(v):
    return f"{v:,.0f}".replace(",", ".")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    return output.getvalue()


def filtrar(df, anos, os, data_ini, data_fim):
    return df[
        df["Ano"].isin(anos)
        & df["OS"].isin(os)
        & df["Data"].between(data_ini, data_fim)
    ]


@st.cache_data
def carregar_dados():
    caminho = Path(__file__).parent / "dados" / "dados_concatenado.csv"

    if not caminho.exists():
        return None, None, None

    df = pd.read_csv(caminho)

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date
    df["Ano"] = df["Ano"].astype(str)
    df["OS"] = df["OS"].astype(str)

    precos = pd.Series(TABELA_PRECOS)

    df_count = (
        df.groupby(["Ano", "OS", "Data"])[ANALISES]
        .count()
        .reset_index()
    )

    df_cost = df_count.copy()

    for a in ANALISES:
        df_cost[a] *= precos[a]

    df_cost["Custo_Total"] = df_cost[ANALISES].sum(axis=1)
    df_count["Total_Amostras"] = df_count[ANALISES].sum(axis=1)

    return df, df_count, df_cost


def card_kpi(titulo, valor, detalhe):
    st.markdown(f"""
    <div style="padding:18px;border-radius:16px;border:1px solid #ddd;">
        <b>{titulo}</b><br>
        <span style="font-size:22px">{valor}</span><br>
        <small>{detalhe}</small>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# CARREGAMENTO
# ============================================================

df_base, df_count, df_cost = carregar_dados()

if df_base is None:
    st.error("Arquivo não encontrado.")
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("Gestão de Custos")

    pagina = st.radio(
        "Navegação",
        ["Visão Geral", "Análise Financeira", "Base de Dados"]
    )

    anos = sorted(df_cost["Ano"].unique(), reverse=True)
    anos_sel = st.multiselect("Ano", anos, default=anos[:1])

    os_disp = sorted(df_cost[df_cost["Ano"].isin(anos_sel)]["OS"].unique())
    os_sel = st.multiselect("OS", os_disp, default=os_disp)

    data_min = df_cost["Data"].min()
    data_max = df_cost["Data"].max()

    periodo = st.date_input("Período", (data_min, data_max))

    data_ini, data_fim = periodo if isinstance(periodo, tuple) else (periodo, periodo)

    analises_sel = st.multiselect("Análises", ANALISES, default=ANALISES)


# ============================================================
# FILTROS
# ============================================================

df_cost_f = filtrar(df_cost, anos_sel, os_sel, data_ini, data_fim)
df_base_f = filtrar(df_base, anos_sel, os_sel, data_ini, data_fim)
df_count_f = filtrar(df_count, anos_sel, os_sel, data_ini, data_fim)

# matriz binária (GANHO DE PERFORMANCE)
df_bin = df_base_f[analises_sel].eq("X").astype(int)


# ============================================================
# MÉTRICAS
# ============================================================

total_custo = df_cost_f["Custo_Total"].sum()
total_os = df_cost_f["OS"].nunique()
total_amostras = df_base_f.shape[0]

total_analises = df_bin.sum().sum()
amostras_lab = (df_bin.sum(axis=1) > 0).sum()

ticket_os = total_custo / total_os if total_os else 0
ticket_amostra = total_custo / amostras_lab if amostras_lab else 0

soma_custo_analise = df_cost_f[analises_sel].sum().sort_values(ascending=False)
soma_qtd = df_bin.sum().sort_values(ascending=False)

top_analise = soma_custo_analise.idxmax() if not soma_custo_analise.empty else "-"
top_os = df_cost_f.groupby("OS")["Custo_Total"].sum().idxmax()


# ============================================================
# HEADER
# ============================================================

st.title("Painel de Custos - Laboratório Químico")


# ============================================================
# VISÃO GERAL
# ============================================================

if pagina == "Visão Geral":

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Custo Total", format_brl(total_custo))
    c2.metric("Amostras", format_num(total_amostras))
    c3.metric("Amostras no Lab", format_num(amostras_lab))
    c4.metric("Ticket Amostra", format_brl(ticket_amostra))

    st.info(f"Maior custo: {top_analise} | OS crítica: {top_os}")

    st.subheader("Custo por OS")

    fig = px.bar(
        df_cost_f.groupby("OS")["Custo_Total"].sum().reset_index(),
        x="OS",
        y="Custo_Total"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Distribuição por análise")

    fig2 = px.bar(
        soma_custo_analise.reset_index(),
        x="index",
        y=0
    )

    st.plotly_chart(fig2, use_container_width=True)


# ============================================================
# ANÁLISE FINANCEIRA
# ============================================================

elif pagina == "Análise Financeira":

    st.metric("Custo Total", format_brl(total_custo))
    st.metric("Ticket OS", format_brl(ticket_os))

    st.subheader("Pareto")

    df_pareto = soma_custo_analise.reset_index()
    df_pareto.columns = ["Análise", "Custo"]
    df_pareto["perc"] = df_pareto["Custo"] / df_pareto["Custo"].sum()

    df_pareto["acum"] = df_pareto["perc"].cumsum()

    fig = go.Figure()

    fig.add_bar(x=df_pareto["Análise"], y=df_pareto["Custo"])
    fig.add_scatter(x=df_pareto["Análise"], y=df_pareto["acum"]*100)

    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# BASE
# ============================================================

elif pagina == "Base de Dados":

    st.dataframe(df_cost_f, use_container_width=True)

    st.download_button(
        "Download Excel",
        to_excel(df_cost_f),
        "custos.xlsx"
    )