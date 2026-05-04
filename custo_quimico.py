# %% Importação de bibliotecas
import pandas as pd
from pathlib import Path
import datetime as dt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io

# %%

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

# Armazenar o cachê
@st.cache_data()

def carregar_processar():
    # CAMINHO RELATIVO: Funciona tanto no PC quanto no GitHub
    # Procura a pasta 'dados' no mesmo local onde o scrip está salvo
    caminho_base = Path(__file__).parent / "dados"
    caminho_csv = caminho_base / "dados_concatenado.csv"

    # verificação da existência do arquivo
    if not caminho_csv.exists():
        return None, None
    
    # leitura do csv que o arquivo .BAT + sincronização.py irá gerar
    df_base = pd.read_csv(caminho_csv)

    # dicionario com as analises e valores
    tabela_precos = {
        'Analise': ['CHN', 'K_P_Mehlich', 'Macro', 'Micro', 'MO', 'pH_CaCl2',
                    'pH_H2O', 'P_Resina', 'S_ICP', 'S_Turbidimetria', 'Textura'],
        'Valor_Amostra': [50.0, 3.75, 5.29, 5.11, 1.48, 1.32,
                          1.32, 3.76, 5.14, 3.13, 5.64]
    }

    # series com valores, analise como index
    valores_series = pd.Series(tabela_precos['Valor_Amostra'], index = tabela_precos['Analise'])
    # geração de uma lista com as analises
    analises = tabela_precos['Analise']

    # agrupamentos e cálculos
    df_contagem = df_base.groupby(['OS', 'Ano'])[analises].count() # OS e Ano fazem agora fazem parte do indice
    # multiplicação do df agrupado pelas analises da serie
    df_custos = df_contagem.mul(valores_series, axis = 1) # .mul realiza uma multiplicação entre um df/series e outro objeto escalar, nesse caso uma serie

    # df de contagem das amostras e custos
    df_contagem['Total_Amostras'] = df_contagem.sum(axis = 1)
    df_custos['Custo_Total'] = df_custos.sum(axis = 1)

    return df_contagem.reset_index(), df_custos.reset_index()

contagem, custos = carregar_processar()

# criação de uma aba lateral para filtros
with st.sidebar:

    # adição da logo da agrorobotica
    st.image(r"logo-agrorobotica-png.png", width = 'stretch')
    # titulo da sidebar + botao de sincronização / limpeza de cachê
    st.title("Filtros")
    if st.button("Sincronizar"):
        st.cache_data.clear()
        st.rerun() # como faz um rerun, o painel é atualizado
    
    # seleção do que será colocado no filtro de tempo
    ano_lista = sorted(custos['Ano'].unique(), reverse = True)
    # caixa multiselect para selecionar ano
    sel_anos = st.multiselect("Ano de Referência", ano_lista, default = ano_lista[0])
    
    # filtro das OS que estão nos respectivos anos
    os_lista = sorted(custos[custos['Ano'].isin(sel_anos)]['OS'].unique())
    # caixa multiselect para OS
    sel_os = st.multiselect("Ordem de Serviço", os_lista, default = os_lista)

    # filtro de data
    today = dt.datetime.now()
    min_value = dt.datetime(today.year, 1, 1).date()  # Certifique-se de que é um objeto date
    max_value = dt.datetime(today.year, 12, 31).date()  # Certifique-se de que é um objeto date

    # Defina um valor padrão que esteja dentro do intervalo
    default_value = today  # Ou use um valor específico que você sabe que está dentro do intervalo

    d = st.date_input(
        "Selecione o período desejado",
        value = default_value,
        min_value = min_value,
        max_value = max_value,
        format = 'DD/MM/YYYY'
    )

# filtragem dos dataframes baseados nos filtros da sidebar
df_custos = custos[(custos['Ano'].isin(sel_anos)) & (custos['OS'].isin(sel_os))]
df_contagem = contagem[(contagem['Ano'].isin(sel_anos)) & (contagem['OS'].isin(sel_os))]

st.title("Gestão de Custos - Análises Laboratório Químico")
st.caption(f"Última atualização dos dados: {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.divider()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Custo Total OS", f"R$ {df_custos['Custo_Total'].sum():,.1f}".replace('.', ',').replace(',', '.', 1))
m2.metric("Volume de Amostras", f"{int(df_contagem['Total_Amostras'].sum()):,}".replace(",", ".").replace(',', '.', 1))
m3.metric("N° Ordens de Serviço", len(df_contagem))
m4.metric("Custo Médio OS", f"R$ {df_custos['Custo_Total'].mean():,.1f}".replace('.', ',').replace(',', '.', 1))

st.divider()

col1, col2 = st.columns([1.5, 1.0])

with col1:
    st.subheader("Custo Total por OS")
    fig_barra = px.bar(df_custos,
                       x='OS',
                       y='Custo_Total', 
                       text=df_custos['Custo_Total'].apply(lambda x: f'R$ {x:,.1f}'.replace('.', ',').replace(',', '.', 1)),
                       labels={'Custo_Total': 'Custo Total (R$)', 'OS': 'Ordem de Serviço'})

    fig_barra.update_traces(marker_color='#5cb23f', textposition='outside')
    fig_barra.update_xaxes(type='category')
    fig_barra.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_barra, width="stretch")

with col2:
    st.subheader("% Custo por Análise")
    cols_analise = [c for c in df_custos if c not in ['OS', 'Ano', 'Custo_Total']]
    soma_analise = df_custos[cols_analise].sum().sort_values(ascending=False)
        
    fig_rosca = px.pie(names=soma_analise.index, values=soma_analise.values, hole=0.6,
                    color_discrete_sequence=px.colors.sequential.Greens_r)
    fig_rosca.update_traces(sort=False) # Mantém a ordem do degradê verde
    fig_rosca.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20),
                        legend=dict(orientation='v', yanchor='middle', xanchor='left', x=1.0, y=0.5))
    st.plotly_chart(fig_rosca, width = "stretch")
    
st.divider()

st.subheader("Quantitativo por Análise")
soma_q = df_contagem[cols_analise].sum().sort_values(ascending=False).reset_index()
soma_q.columns = ['Análise', 'Volume']
fig_qtd = px.bar(soma_q, x='Volume', y='Análise', orientation='h', text_auto=True)

# Atualizando a cor do marcador e o estilo do texto
fig_qtd.update_traces(marker_color='#5cb23f', textfont=dict(size=12, color='white', weight='bold'))

# Atualizando layout do gráfico
fig_qtd.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20))
st.plotly_chart(fig_qtd, use_container_width=True)


st.divider()

if not df_custos.empty and not df_contagem.empty:

    tab1, tab2 = st.tabs(['Demonstrativo de Custos', 'Demonstrativo Quantitativo'])

    with tab1:
        st.dataframe(df_custos, width = "stretch", hide_index=True,
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
        st.dataframe(df_contagem, width = "stretch", hide_index=True,
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