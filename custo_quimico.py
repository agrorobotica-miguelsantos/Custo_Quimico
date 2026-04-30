# %% Importação de bibliotecas
import pandas as pd
from pathlib import Path
from datetime import datetime
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
        [data-testeid = "stMetricValue"] { font-size = 24px; font-weight: 700; }
        .stTabs [data-baseweb = "tab_list"] { gap: 24px; }
        .stTabs [data-baseweb = "tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
        div[data-baseweb = "select"] span[data-baseweb = "tag"] { background-color: #5cb23f; color: white; font-weight: bold; }
        [data-testid = "stSidebar"] { background-color: #fff7fb}
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
        st.rerun()
    
    # seleção do que será colocado no filtro de tempo
    ano_lista = sorted(custos['Ano'].unique(), reverse = True)
    # caixa multiselect para selecionar ano
    sel_anos = st.multiselect("Ano de Referência", ano_lista, default = ano_lista[0])
    
    os_lista = sorted(custos[custos['Ano'].isin(sel_anos)]['OS'].unique())
    sel_os = st.multiselect("Ordem de Serviço", os_lista, default = os_lista)
