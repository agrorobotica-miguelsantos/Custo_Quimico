# %% Importação de bibliotecas
import pandas as pd
from pathlib import Path
import datetime as dt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io

# %%

TABELA_PRECOS = {
    'CHN': 50.0, 'K_P_Mehlich': 3.75, 'Macro': 5.29, 'Micro': 5.11,
    'MO': 1.48, 'pH_CaCl2': 1.32, 'pH_H2O': 1.32, 'P_Resina': 3.76,
    'S_ICP': 5.14, 'S_Turbidimetria': 3.13, 'Textura': 5.64
}

# 1. Configuração da página
st.set_page_config(page_title = "Painel - Custo Químico",
                   layout = "wide")

# 2. Configuração de Estilo CSS Personalizado
st.markdown(
    """
    <style>
    [data-testid = "stMetricValue"] { font-size: 30px; font-weight: 700; }
    .stTabs [data-baseweb = "tab_list"] { gap: 24px; }
    .stTabs [data-baseweb = "tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
    div[data-baseweb = "select"] span[data-baseweb = "tag"] { background-color: #5cb23f; color: white; font-weight: bold; }
    [data-testid = "stSidebar"] { background-color: #fff7fb}
    </style>
    """,
    unsafe_allow_html = True
)

def format_brl(valor):
    """
    Formata valores númericos para o padrão de moeda brasileiro
    """
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def to_excel(df):
    """
    Converte o dataframe para um buffer de Excel.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index = False, sheet_name = 'Dados')
    return output.getvalue()

# Armazenar o cachê
@st.cache_data(show_spinner = "Carregando dados...  ")
def carregar_processar():
    caminho_base = Path(__file__).parent / "dados"
    caminho_csv = caminho_base / "dados_concatenado.csv"

    if not caminho_csv.exists():
        return None, None
    
    df_base = pd.read_csv(caminho_csv)
    df_base['Data'] = pd.to_datetime(df_base['Data']).dt.date

    analises = list(TABELA_PRECOS.keys())
    valores_series = pd.Series(TABELA_PRECOS)

    # Agrupamentos
    df_contagem = df_base.groupby(['Ano', 'OS', 'Data'])[analises].count()
    df_custos = df_contagem.mul(valores_series, axis=1)

    df_contagem['Total_Amostras'] = df_contagem.sum(axis=1)
    df_custos['Custo_Total'] = df_custos.sum(axis=1)

    return df_contagem.reset_index(), df_custos.reset_index()

contagem, custos = carregar_processar()

if custos is not None:
    with st.sidebar:
        st.image("logo-agrorobotica-png.png", width = 'stretch')
        st.title("Filtros de Pesquisa")

        if st.button("Sincronizar Dados", width = 'stretch'):
            st.cache_data.clear()
            st.rerun()

        st.divider()

        ano_lista = sorted(custos['Ano'].unique(), reverse = True)
        sel_anos = st.multiselect("Anos:", ano_lista, default = ano_lista[:1])

        os_lista = sorted(custos[custos['Ano'].isin(sel_anos)]['OS'].unique())
        sel_os = st.multiselect("Ordens de Serviço:", os_lista, default = os_lista)

        data_min, data_max = custos['Data'].min(), custos['Data'].max()

        d = st.date_input(
            "Período:",
            value = (data_min, data_max),
            min_value = data_min,
            max_value = data_max,
            format = 'DD/MM/YYYY'
        )
        
        if isinstance(d, tuple) and len(d) == 2:
            start_date, end_date = d
        else:
            start_date = end_date = (d[0] if isinstance(d, tuple) else d)

        mask = (
            (custos['Ano'].isin(sel_anos)) & 
            (custos['OS'].isin(sel_os)) &
            (custos['Data'].between(start_date, end_date))
        )
        df_custos_f = custos[mask]
        df_cont_f = contagem[mask]

    st.title("Gestão de Custos - Análises Laboratório Químico")
    st.caption(f"Última atualização dos dados: {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.divider()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Custo Total", format_brl(df_custos_f['Custo_Total'].sum()))
    with m2:
        st.metric("Ordens de Serviço", len(df_custos_f['OS'].unique()))
    with m3:
        custo_medio = df_custos_f['Custo_Total'].mean() if not df_custos_f.empty else 0
        st.metric("Custo Médio / OS", format_brl(custo_medio))

    st.divider()

    # Gráficos
    col1, col2 = st.columns([1.5, 1.0])

    with col1:
            st.subheader("Custo por Ordem de Serviço")
            fig_barra = px.bar(
                df_custos_f.sort_values('Custo_Total', ascending = False),
                x = 'OS', y = 'Custo_Total',
                color_discrete_sequence = ['#5cb23f'],
                text_auto = True
            )
            fig_barra.update_layout(xaxis_type = 'category', height = 400, margin = dict(t = 10))
            fig_barra.update_layout(yaxis_title = 'Custo Total (R$)')
            st.plotly_chart(fig_barra, width = 'stretch')

    with col2:
        st.subheader("Distribuição do Custo")
        cols_analise = list(TABELA_PRECOS.keys())
        soma_analise = df_custos_f[cols_analise].sum().sort_values(ascending = False)
        
        fig_rosca = px.pie(
            names = soma_analise.index, 
            values = soma_analise.values, 
            hole = 0.5,
            color_discrete_sequence = px.colors.sequential.Greens_r
        )
        fig_rosca.update_layout(height = 400, margin = dict(t = 10), showlegend = True)
        st.plotly_chart(fig_rosca, width = 'stretch')

    # Detalhamento Quantitativo
    st.divider()
    st.subheader("Volume por Tipo de Análise")
    soma_q = df_cont_f[cols_analise].sum().reset_index()
    soma_q.columns = ['Análise', 'Qtd']
    fig_qtd = px.bar(soma_q.sort_values('Qtd', ascending = False), x = 'Qtd',
                     y = 'Análise',
                     orientation = 'h',
                     text_auto = True)
    fig_qtd.update_traces(marker_color = '#2e7d32')
    st.plotly_chart(fig_qtd, width = 'stretch')

    # Tabelas e Exportação
    st.divider()
    t1, t2 = st.tabs(['📂 Demonstrativo Financeiro', '📊 Demonstrativo Quantitativo'])

    with t1:
        st.dataframe(
            df_custos_f, 
            width = 'stretch', 
            hide_index = True,
            column_config = {
                "Custo_Total": st.column_config.NumberColumn("Total (R$)", format = "%.2f"),
                "Ano": st.column_config.TextColumn("Ano")
            }
        )

        excel_custos = to_excel(df_custos_f)
        st.download_button(
            label = "Exportar Planilha - Custos (Excel)",
            data = excel_custos,
            file_name = "custos_quimico.xlsx",
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with t2:
        st.dataframe(df_cont_f,
                     width = 'stretch',
                     hide_index = True,
                     column_config = {
                         "Total_Amostras": st.column_config.NumberColumn("Total Amostras")
                     }
        )

        excel_contagem = to_excel(df_cont_f)
        st.download_button(
            label = "Exportar Planilha - Quantitativo (Excel)",
            data = excel_contagem,
            file_name = "quantitativo_quimico.xlsx",
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.error("⚠️ Erro: Arquivo 'dados_concatenado.csv' não encontrado na pasta raiz.")