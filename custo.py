# %%

import pandas as pd
from pathlib import Path
from datetime import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io

# %%

st.set_page_config(page_title = "Dashboard - Custos Análises", layout = "wide")

st.markdown(
    """
    <style>
    [data-testid = "stMetricValue"] { font-size: 24px; font-weight: 700, color = #1E88E5; }
    .stTabs [data-baseweb = "tab_list"] { gap: 24px; }
    .stTabs [data-baseweb = "tab"] { height: 50px; white-space: pre-wrap/ font-size: 16px; }
    div[data-baseweb = "select"] span[data-baseweb = "tag"] {background-color: #5cb23f; color: white; font-weight: bold;}
    [data-testid = "stSidebar"] { background-color: #fff7fb; }
    </style>
    """, unsafe_allow_html = True
)

@st.cache_data()
def carregar_processar(caminho_entrada):

    tabela_precos = {
        'Analise': ['CHN', 'K_P_Mehlich', 'Macro', 'Micro', 'MO', 'pH_CaCl2',
                    'pH_H2O', 'P_Resina', 'S_ICP', 'S_Turbidimetria', 'Textura'],
        'Valor_Amostra': [50.0, 3.75, 5.29, 5.11, 1.48, 1.32,
                          1.32, 3.76, 5.14, 3.13, 5.64]
    }

    valores_series = pd.Series(tabela_precos['Valor_Amostra'], index = tabela_precos['Analise'])

    diretorio = Path(caminho_entrada)
    arquivos = list(diretorio.glob("OS_*/Fazenda_*.xlsx"))

    arquivos = [f for f in arquivos if f.is_file() and not f.name.startswith("~$")]

    if not arquivos:
        return None, None
    
    lista_dfs = []
    analises = tabela_precos['Analise']

    for arquivo in arquivos:
        try:
            df = pd.read_excel(arquivo, usecols = analises, engine = 'calamine')
            os_id = arquivo.parent.name.split("_")[1]
            ano_modificacao = datetime.fromtimestamp(arquivo.stat().st_mtime).year

            df.insert(0, 'OS', os_id)
            df.insert(1, 'Ano', ano_modificacao)
            lista_dfs.append(df)
        except Exception as e:
            print(f"Erro ao ler o arquivo {arquivo.name}: {e}")
    
    if not lista_dfs:
        return None, None
    
    df_base = pd.concat(lista_dfs, ignore_index = True)

    df_contagem = df_base.groupby(['OS', 'Ano'])[analises].count()
    df_custos = df_contagem.mul(valores_series, axis=1)

    df_contagem['Total_Amostras'] = df_contagem.sum(axis=1)
    df_custos['Custo_Total'] = df_custos.sum(axis=1)

    return df_contagem.reset_index(), df_custos.reset_index()

tabela_PL = {
    'Analise': ['CHN', 'K_P_Mehlich', 'Macro', 'Micro', 'MO', 'pH_CaCl2',
                'pH_H2O', 'P_Resina', 'S_ICP', 'S_Turbidimetria', 'Textura'],
    'Total': [7, 12, 12, 12, 6, 5,
              5, 6, 12, 12, 2],
    'Valor': [50.0, 3.75, 5.29, 5.11, 1.48, 1.32,
                          1.32, 3.76, 5.14, 3.13, 5.64],
    'Amostras_p_Lote': [100, 100, 100, 100, 100, 100,
                       100, 100, 100, 100, 10]
}

df_pls = pd.DataFrame(tabela_PL).set_index('Analise')

# %%

CAMINHO_DADOS = r"C:\Users\MiguelSantos\OneDrive - Agrorobotica Fotonica Em Certificacoes Agroambientais\AGROROBOTICA\PROJETOS\Custo Químico\dados"

contagem, custos = carregar_processar(CAMINHO_DADOS)

custo_pls = (
    contagem.iloc[:, 2:-1]
    .div(df_pls['Amostras_p_Lote'], axis = 1)
    .mul(df_pls['Total'], axis = 1)
    .round(0)
    .mul(df_pls['Valor'], axis = 1)
)

custo_pls['Custo_Total'] = custo_pls.sum(axis = 1)
custo_pls = pd.concat([(contagem.iloc[:, 0:2]), custo_pls], axis = 1)

custos.insert(13, 'Custo_PL', custo_pls['Custo_Total'])

if custos is not None:

    with st.sidebar:

        st.image(r"C:\Users\MiguelSantos\Downloads\custo_quimico\logo-agrorobotica-png.png",
                 use_container_width = True)
        
        st.title("Filtros")
        if st.button("Sincronizar Diretório"):
            st.cache_data.clear()
            st.rerun()
        
        ano_lista = sorted(custos['Ano'].unique(), reverse = True)
        sel_anos = st.multiselect("Ano de Referência", ano_lista, default = ano_lista[0])

        os_lista = sorted(custos[custos['Ano'].isin(sel_anos)]['OS'].unique())
        sel_os = st.multiselect("Ordem de Serviço", os_lista, default = os_lista)
    
    df_custos = custos[(custos['Ano'].isin(sel_anos)) & (custos['OS'].isin(sel_os))]
    df_contagem = contagem[(contagem['Ano'].isin(sel_anos)) & (contagem['OS'].isin(sel_os))]
    df_pl_custo = custo_pls[(custo_pls['Ano'].isin(sel_anos)) & (custo_pls['OS'].isin(sel_os))]
    
    col_merge = ['OS', 'Ano', 'Custo_Total']

    df_custo_total = pd.merge(
        df_custos[col_merge],
        df_pl_custo[col_merge],
        on = ['OS', 'Ano'],
        suffixes = ('_Amostras', '_PL')
        )
    
    df_custo_total['Custo_Total'] = (
        df_custo_total['Custo_Total_Amostras'] + df_custo_total['Custo_Total_PL']
    )

    # --- HEADER ---
    st.title("Gestão de Custos - Análises Laboratório Químico")
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    st.divider()

    # --- MÉTRICAS ---
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m2.metric("Custo Análises Amostras", f"R$ {df_custo_total['Custo_Total_Amostras'].sum():,.1f}")
    m3.metric("Custo PL", f"R$ {df_custo_total['Custo_Total_PL'].sum():,.1f}")
    m1.metric("Custo Total OS", f"R$ {((df_custo_total['Custo_Total_Amostras'].sum()) + (df_custo_total['Custo_Total_PL'].sum())):,.1f}")
    m4.metric("Volume de Amostras", f"{int(df_contagem['Total_Amostras'].sum()):,}".replace(",", "."))
    m5.metric("N Ordens de Serviço", len(df_contagem))
    m6.metric("Custo Médio OS", f"R$ {((df_custo_total['Custo_Total_Amostras'].mean()) + (df_custo_total['Custo_Total_PL'].mean())):,.1f}")

    st.divider()

    # --- GRÁFICOS ---
    col_main, col_side = st.columns([1.5, 1.0])

    with col_main:
        st.subheader("Custo Total por OS")
        fig_barra = px.bar(df_custo_total,
                           x = 'OS',
                           y = 'Custo_Total',
                           text = 'Custo_Total',
                           labels = {'Custo_Total': 'Custo Total (R$)',
                                     'OS': 'Ordem de Serviço'})
        fig_barra.update_traces(marker_color = '#5cb23f')
        fig_barra.update_xaxes(type = 'category')
        fig_barra.update_layout(height = 400,
                                margin = dict(t = 20, b = 20, l = 20, r = 20),
                                coloraxis_showscale = False)
        st.plotly_chart(fig_barra, use_container_width = True)

    with col_side:
        st.subheader("% Custo por Análise")
        cols_analise = [c for c in df_custos if c not in ['OS', 'Ano', 'Custo_Total']]
        soma_analise = df_custos[cols_analise].sum().sort_values(ascending = False)
        
        fig_rosca = px.pie(names = soma_analise.index,
                            values = soma_analise.values,
                            hole = 0.6,
                            color_discrete_sequence = px.colors.sequential.Greens_r)
        fig_rosca.update_layout(height = 400,
                                margin = dict(t = 20, b = 20, l = 20, r = 20),
                                showlegend = True,
                                legend = dict(
                                    orientation = 'v',
                                    yanchor = 'middle',
                                    xanchor = 'left',
                                    x = 1.00,
                                    y = 0.50)
                                )
        st.plotly_chart(fig_rosca, use_container_width = True)
    
    st.divider()

    # --- GRÁFICO: QUANTITATIVO POR ANÁLISE ---
    st.subheader("Quantitativo por Análise")
    soma_q = df_contagem[cols_analise[0:-1]].sum().sort_values(ascending = False).reset_index()
    soma_q.columns = ['Análise', 'Volume']
    fig_qtd = px.bar(soma_q,
                     x = 'Volume',
                     y = 'Análise',
                     orientation = 'h',
                     text_auto = True)
    fig_qtd.update_traces(marker_color = '#5cb23f')
    fig_qtd.update_layout(height = 400,
                          margin = dict(t = 20, b = 20, l = 20, r = 20))
    st.plotly_chart(fig_qtd, use_container_width = True)

    st.divider()

    # --- TABELAS DETALHADAS ---

    tab1, tab2 = st.tabs(['Demonstrativo de Custos', 'Demonstrantivo Quantitativo'])

    with tab1:

        st.dataframe(df_custos,
                     width = 'stretch',
                     hide_index = True,
                     column_config = {
                         'Custo_Total': st.column_config.NumberColumn("Custo Total", format = "R$ %.2f"),
                         'Ano': st.column_config.TextColumn("Ano")
                     })
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine = 'openpyxl') as writer:
            df_custos.to_excel(writer, index = False)
        st.download_button("Exportar Dados de Custo (Excel)", buffer.getvalue(),
                           "relatorio_custos_analises.xlsx", "application/vnd.ms-excel")
        
    with tab2:

        st.dataframe(df_contagem,
                     width = 'stretch',
                     hide_index = True,
                     column_config = {
                         'Total_Amostras': st.column_config.ProgressColumn("Volume de Amostras",
                                                                           format = "%d",
                                                                           min_value = 0,
                                                                           max_value = int(df_contagem['Total_Amostras'].max())),
                         'Ano': st.column_config.TextColumn("Ano")
                     })
        
        buffer_q = io.BytesIO()
        with pd.ExcelWriter(buffer_q, engine = 'openpyxl') as writer:
            df_contagem.to_excel(writer, index = False)
        st.download_button("Exportar Dados Quantitativos (Excel)", buffer_q.getvalue(),
                           "relatorio_quantitaivo_amostras.xlsx", "application/vnd.ms-excel")
        
else:
    st.warning("Verifique a conexão com o diretório especificado.")