# %%
import pandas as pd
from pathlib import Path
from datetime import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io

# %%
st.set_page_config(page_title="Dashboard - Custos Análises", layout="wide")

# Estilo CSS Personalizado
st.markdown(
    """
    <style>
    [data-testid = "stMetricValue"] { font-size: 24px; font-weight: 700; }
    .stTabs [data-baseweb = "tab_list"] { gap: 24px; }
    .stTabs [data-baseweb = "tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
    div[data-baseweb = "select"] span[data-baseweb = "tag"] {background-color: #5cb23f; color: white; font-weight: bold;}
    [data-testid = "stSidebar"] { background-color: #fff7fb; }
    </style>
    """, unsafe_allow_html=True
)

@st.cache_data()
def carregar_processar():
    # CAMINHO RELATIVO: Funciona no PC e no GitHub
    # Procura a pasta 'dados' no mesmo local onde este script está salvo
    caminho_base = Path(__file__).parent / "dados"
    caminho_csv = caminho_base / "dados_concatenado.csv"

    if not caminho_csv.exists():
        return None, None

    # Lemos o CSV que o seu arquivo .BAT + Script de Sincronização geraram
    df_base = pd.read_csv(caminho_csv)

    tabela_precos = {
        'Analise': ['CHN', 'K_P_Mehlich', 'Macro', 'Micro', 'MO', 'pH_CaCl2',
                    'pH_H2O', 'P_Resina', 'S_ICP', 'S_Turbidimetria', 'Textura'],
        'Valor_Amostra': [50.0, 3.75, 5.29, 5.11, 1.48, 1.32,
                          1.32, 3.76, 5.14, 3.13, 5.64]
    }

    valores_series = pd.Series(tabela_precos['Valor_Amostra'], index=tabela_precos['Analise'])
    analises = tabela_precos['Analise']

    # Agrupamento e Cálculos
    df_contagem = df_base.groupby(['OS', 'Ano'])[analises].count()
    df_custos = df_contagem.mul(valores_series, axis=1)

    df_contagem['Total_Amostras'] = df_contagem.sum(axis=1)
    df_custos['Custo_Total'] = df_custos.sum(axis=1)

    return df_contagem.reset_index(), df_custos.reset_index()

# Tabela de Lotes (Parâmetros fixos)
tabela_PL = {
    'Analise': ['CHN', 'K_P_Mehlich', 'Macro', 'Micro', 'MO', 'pH_CaCl2',
                'pH_H2O', 'P_Resina', 'S_ICP', 'S_Turbidimetria', 'Textura'],
    'Total': [7, 12, 12, 12, 6, 5, 5, 6, 12, 12, 2],
    'Valor': [50.0, 3.75, 5.29, 5.11, 1.48, 1.32, 1.32, 3.76, 5.14, 3.13, 5.64],
    'Amostras_p_Lote': [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 10]
}
df_pls = pd.DataFrame(tabela_PL).set_index('Analise')

# Carregamento dos dados
contagem, custos = carregar_processar()

if custos is not None:
    # --- CÁLCULOS DE PL ---
    custo_pls = (
        contagem.iloc[:, 2:-1]
        .div(df_pls['Amostras_p_Lote'], axis=1)
        .mul(df_pls['Total'], axis=1)
        .round(0)
        .mul(df_pls['Valor'], axis=1)
    )
    custo_pls['Custo_Total'] = custo_pls.sum(axis=1)
    custo_pls = pd.concat([(contagem.iloc[:, 0:2]), custo_pls], axis=1)
    
    # Inserção do custo PL na base principal
    custos['Custo_PL'] = custo_pls['Custo_Total']

    # --- SIDEBAR ---
    with st.sidebar:

        st.image(r"logo-agrorobotica-png.png", use_container_width=True)
        
        st.title("Filtros")
        if st.button("Limpar Cache / Sincronizar"):
            st.cache_data.clear()
            st.rerun()
        
        ano_lista = sorted(custos['Ano'].unique(), reverse=True)
        sel_anos = st.multiselect("Ano de Referência", ano_lista, default=ano_lista[0])

        os_lista = sorted(custos[custos['Ano'].isin(sel_anos)]['OS'].unique())
        sel_os = st.multiselect("Ordem de Serviço", os_lista, default=os_lista)
    
    # Filtragem dos DataFrames baseada nos filtros da Sidebar
    df_custos = custos[(custos['Ano'].isin(sel_anos)) & (custos['OS'].isin(sel_os))]
    df_contagem = contagem[(contagem['Ano'].isin(sel_anos)) & (contagem['OS'].isin(sel_os))]
    df_pl_custo = custo_pls[(custo_pls['Ano'].isin(sel_anos)) & (custo_pls['OS'].isin(sel_os))]
    
    # Merge para cálculo do Custo Total (Amostras + PL)
    df_custo_total = pd.merge(
        df_custos[['OS', 'Ano', 'Custo_Total']],
        df_pl_custo[['OS', 'Ano', 'Custo_Total']],
        on=['OS', 'Ano'],
        suffixes=('_Amostras', '_PL')
    )
    df_custo_total['Custo_Total'] = df_custo_total['Custo_Total_Amostras'] + df_custo_total['Custo_Total_PL']

    # --- HEADER ---
    st.title("Gestão de Custos - Análises Laboratório Químico")
    st.caption(f"Última atualização de dados: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.divider()

    # --- MÉTRICAS ---
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Custo Total OS", f"R$ {df_custo_total['Custo_Total'].sum():,.1f}")
    m2.metric("Custo Amostras", f"R$ {df_custo_total['Custo_Total_Amostras'].sum():,.1f}")
    m3.metric("Custo PL", f"R$ {df_custo_total['Custo_Total_PL'].sum():,.1f}")
    m4.metric("Volume Amostras", f"{int(df_contagem['Total_Amostras'].sum()):,}".replace(",", "."))
    m5.metric("Nº Ordens de Serviço", len(df_contagem))
    m6.metric("Custo Médio OS", f"R$ {df_custo_total['Custo_Total'].mean():,.1f}")

    st.divider()

    # --- GRÁFICOS ---
    col_main, col_side = st.columns([1.5, 1.0])

    with col_main:
        st.subheader("Custo Total por OS")
        fig_barra = px.bar(df_custo_total, x='OS', y='Custo_Total', text='Custo_Total',
                           labels={'Custo_Total': 'Custo Total (R$)', 'OS': 'Ordem de Serviço'})
        fig_barra.update_traces(marker_color='#5cb23f', texttemplate='R$ %{text:.2f}', textposition='outside')
        fig_barra.update_xaxes(type='category')
        fig_barra.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_barra, use_container_width=True)

    with col_side:
        st.subheader("% Custo por Análise")
        cols_analise = [c for c in df_custos if c not in ['OS', 'Ano', 'Custo_Total', 'Custo_PL']]
        soma_analise = df_custos[cols_analise].sum().sort_values(ascending=False)
        
        fig_rosca = px.pie(names=soma_analise.index, values=soma_analise.values, hole=0.6,
                           color_discrete_sequence=px.colors.sequential.Greens_r)
        fig_rosca.update_traces(sort=False) # Mantém a ordem do degradê verde
        fig_rosca.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20),
                                legend=dict(orientation='v', yanchor='middle', xanchor='left', x=1.0, y=0.5))
        st.plotly_chart(fig_rosca, use_container_width=True)
    
    st.divider()

    # --- QUANTITATIVO POR ANÁLISE ---
    st.subheader("Quantitativo por Análise")
    soma_q = df_contagem[cols_analise].sum().sort_values(ascending=False).reset_index()
    soma_q.columns = ['Análise', 'Volume']
    fig_qtd = px.bar(soma_q, x='Volume', y='Análise', orientation='h', text_auto=True)
    fig_qtd.update_traces(marker_color='#5cb23f')
    fig_qtd.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_qtd, use_container_width=True)

    st.divider()

    # --- TABELAS ---
    tab1, tab2 = st.tabs(['Demonstrativo de Custos', 'Demonstrativo Quantitativo'])

    with tab1:
        st.dataframe(df_custos, use_container_width=True, hide_index=True,
                     column_config={
                         'Custo_Total': st.column_config.NumberColumn("Custo Amostras", format="R$ %.2f"),
                         'Custo_PL': st.column_config.NumberColumn("Custo PL", format="R$ %.2f"),
                         'Ano': st.column_config.TextColumn("Ano")
                     })
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_custos.to_excel(writer, index=False)
        st.download_button("Exportar Custos (Excel)", buffer.getvalue(), "custos_quimico.xlsx", "application/vnd.ms-excel")
        
    with tab2:
        st.dataframe(df_contagem, use_container_width=True, hide_index=True,
                     column_config={
                         'Total_Amostras': st.column_config.ProgressColumn("Total Amostras", format="%d", min_value=0, 
                                                                          max_value=int(df_contagem['Total_Amostras'].max())),
                         'Ano': st.column_config.TextColumn("Ano")
                     })
        
        buffer_q = io.BytesIO()
        with pd.ExcelWriter(buffer_q, engine='openpyxl') as writer:
            df_contagem.to_excel(writer, index=False)
        st.download_button("Exportar Quantitativo (Excel)", buffer_q.getvalue(), "quantitativo_amostras.xlsx", "application/vnd.ms-excel")
        
else:
    st.warning("Arquivo 'dados_concatenado.csv' não encontrado. Execute a sincronização via arquivo .BAT primeiro.")