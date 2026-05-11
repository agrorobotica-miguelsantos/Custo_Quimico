# %%
# ============================================================
# PAINEL - CUSTOS LABORATORIAIS | Agrorobótica
# ============================================================

import io
import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# CONFIGURAÇÕES GERAIS
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

CORES = {
    "verde_escuro": "#12372A",
    "verde": "#2D6A4F",
    "verde_claro": "#74C69D",
    "fundo": "#FFFFFF",
    "card": "#FFFFFF",
    "texto": "#1F2937",
    "cinza": "#6B7280",
    "borda": "#E5E7EB",
    "alerta": "#F59E0B",
    "azul": "#2563EB",
    "vermelho": "#DC2626",
}

# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>
        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }}

        .main {{
            background-color: {CORES["fundo"]};
        }}

        section[data-testid="stSidebar"] {{
            background-color: #FFFFFF;
            border-right: 1px solid {CORES["borda"]};
        }}

        .hero {{
            background: linear-gradient(135deg, #12372A 0%, #2D6A4F 60%, #40916C 100%);
            padding: 28px 32px;
            border-radius: 24px;
            color: white;
            margin-bottom: 22px;
            box-shadow: 0 12px 30px rgba(18, 55, 42, 0.18);
        }}

        .hero-title {{
            font-size: 34px;
            font-weight: 800;
            margin-bottom: 6px;
        }}

        .hero-subtitle {{
            font-size: 15px;
            color: #E8F5E9;
        }}

        .kpi-card {{
            background-color: white;
            border-radius: 20px;
            padding: 20px 22px;
            border: 1px solid {CORES["borda"]};
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
            min-height: 125px;
        }}

        .kpi-label {{
            font-size: 14px;
            color: {CORES["cinza"]};
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .kpi-value {{
            font-size: 30px;
            color: {CORES["verde_escuro"]};
            font-weight: 800;
            margin-bottom: 4px;
        }}

        .kpi-help {{
            font-size: 13px;
            color: {CORES["cinza"]};
        }}

        .section-card {{
            background-color: white;
            padding: 22px;
            border-radius: 22px;
            border: 1px solid {CORES["borda"]};
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
            margin-bottom: 18px;
        }}

        .insight-box {{
            background-color: #ECFDF5;
            color: #064E3B;
            padding: 18px 20px;
            border-radius: 18px;
            border: 1px solid #A7F3D0;
            font-weight: 500;
            margin-bottom: 16px;
        }}

        .warning-box {{
            background-color: #FFFBEB;
            color: #92400E;
            padding: 18px 20px;
            border-radius: 18px;
            border: 1px solid #FDE68A;
            font-weight: 500;
            margin-bottom: 16px;
        }}

        div[data-testid="stMetricValue"] {{
            font-size: 28px;
            font-weight: 800;
            color: {CORES["verde_escuro"]};
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 12px;
        }}

        .stTabs [data-baseweb="tab"] {{
            background-color: white;
            border-radius: 14px;
            padding: 10px 20px;
            border: 1px solid {CORES["borda"]};
        }}

        .stTabs [aria-selected="true"] {{
            background-color: #ECFDF5;
            color: {CORES["verde_escuro"]};
            font-weight: 700;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# FUNÇÕES
# ============================================================

def format_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_num(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    return output.getvalue()


def card_kpi(titulo, valor, detalhe):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{titulo}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-help">{detalhe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Carregando e processando dados...")
def carregar_dados():
    caminho = Path(__file__).parent / "dados" / "dados_concatenado.csv"

    if not caminho.exists():
        return None, None, None

    df = pd.read_csv(caminho)

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date
    df["Ano"] = df["Ano"].astype(str)
    df["OS"] = df["OS"].astype(str)

    valores = pd.Series(TABELA_PRECOS)

    df_contagem = (
        df.groupby(["Ano", "OS", "Data"], dropna=False)[ANALISES]
        .count()
        .reset_index()
    )

    df_custos = df_contagem.copy()

    for col in ANALISES:
        df_custos[col] = df_custos[col] * valores[col]

    df_contagem["Total_Amostras"] = df_contagem[ANALISES].sum(axis=1)
    df_custos["Custo_Total"] = df_custos[ANALISES].sum(axis=1)

    df_base = df.copy()

    return df_base, df_contagem, df_custos


def aplicar_layout_grafico(fig, altura=420):
    fig.update_layout(
        height=altura,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=40, b=30, l=20, r=20),
        font=dict(color=CORES["texto"]),
    )
    return fig


# ============================================================
# CARREGAMENTO
# ============================================================

df_base, contagem, custos = carregar_dados()

if custos is None:
    st.error("Arquivo não encontrado: `dados/dados_concatenado.csv`")
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    logo_path = Path(__file__).parent / "logo-agrorobotica-png.png"

    if logo_path.exists():
        st.image(str(logo_path), width=250)

    st.markdown("## Gestão de Custos")
    st.caption("Filtros gerais")

    if st.button("🔄 Atualizar base de dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    pagina = st.radio(
        "Navegação",
        [
            "Visão Geral",
            "Análise Financeira",
            "Base de Dados",
        ],
    )

    st.divider()

    anos = sorted(custos["Ano"].dropna().unique(), reverse=True)

    anos_sel = st.multiselect(
        "Ano",
        anos,
        default=anos[:1],
    )

    os_disponiveis = sorted(
        custos.loc[custos["Ano"].isin(anos_sel), "OS"].dropna().unique()
    )

    os_sel = st.multiselect(
        "Ordens de Serviço",
        os_disponiveis,
        default=os_disponiveis,
    )

    data_min = custos["Data"].min()
    data_max = custos["Data"].max()

    periodo = st.date_input(
        "Período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max,
        format="DD/MM/YYYY",
    )

    if isinstance(periodo, tuple) and len(periodo) == 2:
        data_ini, data_fim = periodo
    elif isinstance(periodo, tuple) and len(periodo) == 1:
        data_ini = data_fim = periodo[0]
    else:
        data_ini = data_fim = periodo

    st.divider()

    analises_sel = st.multiselect(
        "Tipos de análise",
        ANALISES,
        default=ANALISES,
    )

    st.divider()

    if st.button("Limpar filtros", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ============================================================
# FILTROS
# ============================================================

mask = (
    custos["Ano"].isin(anos_sel)
    & custos["OS"].isin(os_sel)
    & custos["Data"].between(data_ini, data_fim)
)

df_custos = custos.loc[mask].copy()
df_cont = contagem.loc[mask].copy()

if analises_sel:
    df_custos["Custo_Total"] = df_custos[analises_sel].sum(axis=1)
    df_cont["Total_Amostras"] = df_cont[analises_sel].sum(axis=1)


# ============================================================
# MÉTRICAS
# ============================================================

mask_base = (
    df_base["Ano"].astype(str).isin(anos_sel)
    & df_base["OS"].astype(str).isin(os_sel)
    & df_base["Data"].between(data_ini, data_fim)
)

df_base_filtrado = df_base.loc[mask_base].copy()

total_custo = df_custos["Custo_Total"].sum()
total_os = df_custos["OS"].nunique()

# Total de amostras recebidas
total_amostras_recebidas = df_base_filtrado.shape[0]

# Total de amostras com pelo menos uma análise feita no lab químico
total_amostras_quimico = (
    df_base_filtrado[analises_sel]
    .eq("X")
    .any(axis=1)
    .sum()
)

# Total de análises realizadas no lab químico
total_analises = (
    df_base_filtrado[analises_sel]
    .eq("X")
    .sum()
    .sum()
)

# Percentual de amostras atendidas pelo laboratório químico
perc_amostras_quimico = (
    total_amostras_quimico / total_amostras_recebidas
    if total_amostras_recebidas > 0 else 0
)

ticket_os = total_custo / total_os if total_os > 0 else 0

ticket_amostra = (
    total_custo / total_amostras_quimico
    if total_amostras_quimico > 0 else 0
)

soma_custos_analises = df_custos[analises_sel].sum().sort_values(ascending=False)

soma_qtd_analises = (
    df_base_filtrado[analises_sel]
    .eq("X")
    .sum()
    .sort_values(ascending=False)
)

analise_maior_custo = soma_custos_analises.idxmax() if not soma_custos_analises.empty else "-"
analise_maior_volume = soma_qtd_analises.idxmax() if not soma_qtd_analises.empty else "-"

os_mais_cara = (
    df_custos.sort_values("Custo_Total", ascending=False).iloc[0]["OS"]
    if not df_custos.empty
    else "-"
)

# ============================================================
# COBERTURA DOS PARÂMETROS
# ============================================================

total_amostras_recebidas = df_base_filtrado.shape[0]

df_cobertura = pd.DataFrame({
    "Análise": analises_sel,
})

df_cobertura["Qtd_Realizada"] = df_cobertura["Análise"].apply(
    lambda x: df_base_filtrado[x].eq("X").sum()
)

df_cobertura["Cobertura"] = (
    df_cobertura["Qtd_Realizada"] / total_amostras_recebidas
)

df_cobertura["Cobertura_%"] = (
    df_cobertura["Cobertura"] * 100
).round(1)

df_cobertura = df_cobertura.sort_values(
    "Cobertura",
    ascending=False
)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">Painel de Custos - Laboratório Químico | Agrorobótica</div>
        <div class="hero-subtitle">
            Monitoramento de custos do laboratório químico |
            Atualizado em {dt.datetime.now().strftime("%d/%m/%Y %H:%M")}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PÁGINA 1 - VISÃO GERAL
# ============================================================

if pagina == "Visão Geral":

    st.markdown('## Visão Geral')

    c1, c2, c3, c5 = st.columns(4)

    with c1:
        card_kpi("Custo Total", format_brl(total_custo), "Valor total filtrado")

    with c2:
        card_kpi(
            "Amostras Recebidas",
            format_num(total_amostras_recebidas),
            "Total de linhas da base"
        )

    with c3:
        card_kpi(
            "Amostras no Lab Químico",
            format_num(total_amostras_quimico),
            f"{perc_amostras_quimico:.1%} do total"
        )

    #with c4:
        #card_kpi(
            #"Análises Realizadas",
            #format_num(total_analises),
            #"Parâmetros marcados com X"
        #)

    with c5:
        card_kpi(
            "Custo por Amostra",
            format_brl(ticket_amostra),
            "Considerando amostras feitas no químico"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if not df_custos.empty and total_custo > 0:
        perc_top = soma_custos_analises.iloc[0] / total_custo

        st.markdown(
            f"""
            <div class="insight-box">
                <b></b>{analise_maior_custo}</b>
                é a maior responsável pelo custo no período, representando
                <b>{perc_top:.1%}</b> do custo total. A OS de maior custo é a 
                <b>OS {os_mais_cara}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="warning-box">
                Nenhum dado encontrado para os filtros selecionados.
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown("### Ranking de custo por OS")

        df_rank_os = (
            df_custos.groupby("OS", as_index=False)["Custo_Total"]
            .sum()
            .sort_values("Custo_Total", ascending=False)
            .head(15)
        )

        fig = px.bar(
            df_rank_os,
            x="OS",
            y="Custo_Total",
            text="Custo_Total",
            color="Custo_Total",
            color_continuous_scale="Greens",
        )

        fig.update_traces(
            texttemplate="R$ %{y:,.0f}",
            textposition="outside",
            hovertemplate="<b>OS %{x}</b><br>Custo: R$ %{y:,.2f}<extra></extra>",
        )

        fig.update_layout(
            xaxis_title="",
            xaxis_type = "category",
            yaxis_title="Custo total",
            showlegend=False,
            coloraxis_showscale=False,
        )

        st.plotly_chart(aplicar_layout_grafico(fig, 430), use_container_width=True)

    with col2:
        st.markdown("### Distribuição do Custo")

        df_dist = soma_custos_analises.sort_values(ascending=True).reset_index()
        df_dist.columns = ["Análise", "Custo"]

        total_custo_dist = df_dist["Custo"].sum()

        df_dist["texto_label"] = df_dist.apply(
            lambda x: (
                f"{format_brl(x['Custo'])} ({(x['Custo'].round(1) / total_custo_dist) * 100:.1f}%)"
                if x["Custo"] > 0 and total_custo_dist > 0
                else ""
            ),
            axis=1,
        )

        limite = df_dist["Custo"].max() * 0.30 if not df_dist.empty else 0

        df_dist["text_position"] = df_dist["Custo"].apply(
            lambda x: (
                "inside"
                if x > limite
                else "outside"
                if x > 0
                else "none"
            )
        )

        fig_dist_barra = px.bar(
            df_dist,
            x="Custo",
            y="Análise",
            orientation="h",
            text="texto_label",
            color_discrete_sequence=[CORES["verde"]],
        )

        fig_dist_barra.update_traces(
            textposition=df_dist["text_position"],
            textfont=dict(size=13),
            insidetextfont=dict(color="white"),
            outsidetextfont=dict(color="black"),
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Custo: %{text}<extra></extra>",
        )

        fig_dist_barra.update_layout(
            height=430,
            margin=dict(t=20, b=10, l=10, r=10),
            xaxis_title=None,
            yaxis_title=None,
            xaxis_showticklabels=False,
            xaxis_visible=False,
            uniformtext_minsize=12,
            uniformtext_mode="show",
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
        )

        st.plotly_chart(fig_dist_barra, use_container_width=True)

    with col3:
        st.markdown("### Cobertura dos Parâmetros")

        df_cob = df_cobertura.sort_values("Cobertura", ascending=True).copy()

        df_cob["texto_label"] = df_cob.apply(
            lambda x: (
                f"{x['Qtd_Realizada']:.0f} ({x['Cobertura_%']:.1f}%)"
                if x["Qtd_Realizada"] > 0
                else ""
            ),
            axis=1,
        )

        limite_cob = df_cob["Cobertura"].max() * 0.15 if not df_cob.empty else 0

        df_cob["text_position"] = df_cob["Cobertura"].apply(
            lambda x: (
                "inside"
                if x > limite_cob
                else "outside"
                if x > 0
                else "none"
            )
        )

        fig_cobertura = px.bar(
            df_cob,
            x="Cobertura",
            y="Análise",
            orientation="h",
            text="texto_label",
            color_discrete_sequence=[CORES["verde"]],
        )

        fig_cobertura.update_traces(
            textposition=df_cob["text_position"],
            textfont=dict(size=13),
            insidetextfont=dict(color="white"),
            outsidetextfont=dict(color="black"),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Realizadas: %{customdata[0]:.0f}<br>"
                "Cobertura: %{customdata[1]:.1f}%<extra></extra>"
            ),
            customdata=df_cob[["Qtd_Realizada", "Cobertura_%"]],
        )

        fig_cobertura.update_layout(
            height=430,
            margin=dict(t=20, b=10, l=10, r=10),
            xaxis_title=None,
            yaxis_title=None,
            xaxis_showticklabels=False,
            xaxis_visible=False,
            uniformtext_minsize=12,
            uniformtext_mode="show",
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
        )

        st.plotly_chart(
            fig_cobertura,
            use_container_width=True,
            key="grafico_cobertura_parametros"
        )


# ============================================================
# PÁGINA 2 - ANÁLISE FINANCEIRA
# ============================================================

elif pagina == "Análise Financeira":

    st.markdown("## Análise Financeira")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Custo total", format_brl(total_custo))

    with c2:
        st.metric("Custo médio por OS", format_brl(ticket_os))

    with c3:
        st.metric("Análise de maior custo", analise_maior_custo)

    st.divider()

    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.markdown("### Pareto de custos por análise")

        df_pareto = soma_custos_analises.reset_index()
        df_pareto.columns = ["Análise", "Custo"]

        if df_pareto["Custo"].sum() > 0:
            df_pareto["Percentual"] = df_pareto["Custo"] / df_pareto["Custo"].sum()
            df_pareto["Percentual_Acumulado"] = df_pareto["Percentual"].cumsum()

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=df_pareto["Análise"],
                    y=df_pareto["Custo"],
                    name="Custo",
                    text=df_pareto["Custo"],
                    texttemplate="R$ %{text:,.0f}",
                    marker_color=CORES["verde"],
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=df_pareto["Análise"],
                    y=df_pareto["Percentual_Acumulado"] * 100,
                    name="% acumulado",
                    mode="lines+markers",
                    yaxis="y2",
                    line=dict(width=3, color=CORES["alerta"]),
                )
            )

            fig.update_layout(
                yaxis=dict(title="Custo total"),
                yaxis2=dict(
                    title="% acumulado",
                    overlaying="y",
                    side="right",
                    range=[0, 110],
                    ticksuffix="%",
                ),
                legend=dict(orientation="h", y=1.1),
            )

            st.plotly_chart(aplicar_layout_grafico(fig, 470), use_container_width=True)

    with col2:
        st.markdown("### Ranking financeiro")

        df_rank_analise = df_pareto.copy()
        df_rank_analise["Custo"] = df_rank_analise["Custo"].map(format_brl)

        st.dataframe(
            df_rank_analise,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Custo detalhado por OS e análise")

    df_melt_custos = df_custos.melt(
        id_vars=["Ano", "OS", "Data", "Custo_Total"],
        value_vars=analises_sel,
        var_name="Análise",
        value_name="Custo",
    )

    df_melt_custos = df_melt_custos[df_melt_custos["Custo"] > 0]

    fig = px.bar(
        df_melt_custos,
        x="OS",
        y="Custo",
        color="Análise",
        hover_data=["Data"],
    )

    fig.update_layout(
        xaxis_title="OS",
        xaxis_type = "category",
        yaxis_title="Custo",
        legend_title="Análise",
    )

    st.plotly_chart(aplicar_layout_grafico(fig, 500), use_container_width=True)


# ============================================================
# PÁGINA 3 - BASE DE DADOS
# ============================================================

elif pagina == "Base de Dados":

    st.markdown("## 📂 Base de Dados e Exportações")

    tab1, tab2 = st.tabs(
        [
            "Custos",
            "Quantitativo"
        ]
    )

    with tab1:
        st.markdown("### Demonstrativo financeiro")

        st.dataframe(
            df_custos,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Custo_Total": st.column_config.NumberColumn(
                    "Custo Total",
                    format="R$ %.2f",
                )
            },
        )

        st.download_button(
            "⬇️ Baixar custos em Excel",
            data=to_excel(df_custos),
            file_name="demonstrativo_custos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with tab2:
        st.markdown("### Demonstrativo quantitativo")

        st.dataframe(
            df_cont,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Baixar quantitativo em Excel",
            data=to_excel(df_cont),
            file_name="demonstrativo_quantitativo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ============================================================
# RODAPÉ
# ============================================================

st.divider()
st.caption(
    "Dashboard executivo desenvolvido para acompanhamento financeiro e operacional de análises laboratoriais."
)