# %% [1] IMPORTAÇÃO DE BIBLIOTECAS
import pandas as pd
from pathlib import Path
import datetime as dt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io

# %% [2] CONFIGURAÇÕES E CONSTANTES
TABELA_PRECOS = {
    'CHN': 50.0, 'K_P_Mehlich': 3.75, 'Macro': 5.29, 'Micro': 5.11,
    'MO': 1.48, 'pH_CaCl2': 1.32, 'pH_H2O': 1.32, 'P_Resina': 3.76,
    'S_ICP': 5.14, 'S_Turbidimetria': 3.13, 'Textura': 5.64
}

# Configuração da página
st.set_page_config(page_title="Painel - Custo Químico", layout="wide")

# Estilo CSS Personalizado
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
    unsafe_allow_html=True
)

# %% [3] FUNÇÕES DE SUPORTE (FORMATAÇÃO E CACHE)
def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

@st.cache_data(show_spinner="Carregando dados... ")
def carregar_processar():
    caminho_base = Path(__file__).parent / "dados"
    caminho_csv = caminho_base / "dados_concatenado.csv"

    if not caminho_csv.exists():
        return None, None
    
    df_base = pd.read_csv(caminho_csv)
    df_base['Data'] = pd.to_datetime(df_base['Data']).dt.date

    analises = list(TABELA_PRECOS.keys())
    valores_series = pd.Series(TABELA_PRECOS)

    # Agrupamentos e Cálculos
    df_contagem = df_base.groupby(['Ano', 'OS', 'Data'])[analises].count()
    df_custos = df_contagem.mul(valores_series, axis=1)

    df_contagem['Total_Amostras'] = df_contagem.sum(axis=1)
    df_custos['Custo_Total'] = df_custos.sum(axis=1)

    return df_contagem.reset_index(), df_custos.reset_index()

# %% [4] CARREGAMENTO DOS DADOS
contagem, custos = carregar_processar()

# %% [5] INTERFACE - BARRA LATERAL (FILTROS)
if custos is not None:
    with st.sidebar:
        st.image("logo-agrorobotica-png.png")
        st.title("Filtros de Pesquisa")

        if st.button("Sincronizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.divider()

        # Seleção de Ano
        ano_lista = sorted(custos['Ano'].unique(), reverse=True)
        sel_anos = st.multiselect("Anos:", ano_lista, default=ano_lista[:1])

        # Seleção de OS
        os_lista = sorted(custos[custos['Ano'].isin(sel_anos)]['OS'].unique())
        sel_os = st.multiselect("Ordens de Serviço:", os_lista, default=os_lista)

        # Seleção de Período
        data_min, data_max = custos['Data'].min(), custos['Data'].max()
        
        # Input manual de datas
        d = st.date_input(
            "Período personalizado:",
            value = (data_min, data_max),
            min_value=data_min,
            max_value=data_max,
            format='DD/MM/YYYY'
        )

        # Tratamento da data selecionada
        if isinstance(d, tuple) and len(d) == 2:
            start_date, end_date = d
        else:
            start_date = end_date = (d[0] if isinstance(d, tuple) else d)

        # Aplicação dos Filtros (Máscara)
        mask = (
            (custos['Ano'].isin(sel_anos)) & 
            (custos['OS'].isin(sel_os)) &
            (custos['Data'].between(start_date, end_date))
        )
        df_custos_f = custos[mask]
        df_cont_f = contagem[mask]

        if st.button("Limpar Filtros"):
            st.session_state.clear()
            st.rerun()

    # %% [6] INTERFACE - CORPO PRINCIPAL
    st.title("Gestão de Custos - Análises Laboratório Químico")
    st.caption(f"Última atualização dos dados: {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.divider()

    # Bloco de Métricas (KPIs)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Custo Total",
                  format_brl(df_custos_f['Custo_Total'].sum()))
    with m2:
        st.metric("Ordens de Serviço",
                  len(df_custos_f['OS'].unique()))
    with m3:
        custo_medio = df_custos_f['Custo_Total'].mean() if not df_custos_f.empty else 0
        st.metric("Custo Médio / OS",
                  format_brl(custo_medio))

    st.divider()

    # Bloco de Gráficos Superiores
    col1, col2 = st.columns([1.5, 1.0])

    with col1:
        df_barra = df_custos_f.sort_values('Custo_Total', ascending = False).round(2).copy()

        df_barra['texto'] = df_barra['Custo_Total'].apply(
            lambda x: format_brl(x)
        )

        st.subheader("Custo por Ordem de Serviço")

        fig_barra = px.bar(
            df_barra,
            x = 'OS',
            y = 'Custo_Total',
            color_discrete_sequence = ['#2e7d32'],
            text_auto = 'texto'
        )
        
        fig_barra.update_traces(
            textfont = dict(
                color = 'white',
                size = 12
            ),
            textposition='inside'
        )

        fig_barra.update_yaxes(
            tickprefix="R$ ",
            tickformat=",.0f"
        )

        fig_barra.update_layout(
            separators=",.",
            xaxis_type='category',
            height=400,
            margin=dict(t=10),
            yaxis_title='Custo Total (R$)'
        )

        st.plotly_chart(fig_barra, use_container_width=True)

    with col2:
            st.subheader("Distribuição do Custo")
            cols_analise = list(TABELA_PRECOS.keys())
            soma_analise = df_custos_f[cols_analise].sum().sort_values(ascending = True) # Ascending True para as maiores ficarem no topo no gráfico 'h'
            
            # Preparação dos dados para o gráfico
            df_dist = soma_analise.reset_index()
            df_dist.columns = ['Análise', 'Custo']
            total_custo = df_dist['Custo'].sum()
            
            # Criação do texto personalizado: R$ Valor (0.0%)
            df_dist['texto_label'] = df_dist.apply(
                lambda x: (
                    f"{format_brl(x['Custo'])} ({ (x['Custo']/total_custo)*100:.1f}%)"
                    if x['Custo'] > 0 and total_custo > 0
                    else ""
                ),
                axis=1
            )
            
            limite = df_dist['Custo'].max() * 0.15

            df_dist['text_position'] = df_dist['Custo'].apply(
                lambda x: (

                'inside' if x > limite
                else 'outside' if x > 0
                else 'none'
                )
            )
            
            fig_dist_barra = px.bar(
                df_dist,
                x = 'Custo',
                y = 'Análise',
                orientation = 'h',
                text = 'texto_label',
                color_discrete_sequence = ['#2e7d32']
            )

            fig_dist_barra.update_traces(
                textposition=df_dist['text_position'],
                textfont=dict(size=13),
                insidetextfont=dict(color='white'),
                outsidetextfont=dict(color='black'),
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Custo: %{text}<extra></extra>"
            )

            fig_dist_barra.update_layout(
                height = 400,
                margin = dict(t = 10, b = 10, l = 10, r = 10),
                xaxis_title = None,
                yaxis_title = None,
                xaxis_showticklabels = False,
                xaxis_visible = False,
                uniformtext_minsize = 12,
                uniformtext_mode = 'show'
            )

            st.plotly_chart(fig_dist_barra, use_container_width = True)

    # Bloco de Volume (Horizontal)
    st.divider()
    st.subheader("Volume por Tipo de Análise")
    soma_q = df_cont_f[cols_analise].sum().reset_index()
    soma_q.columns = ['Análise', 'Qtd']
    fig_qtd = px.bar(
        soma_q.sort_values('Qtd', ascending=False), 
        x='Qtd', y='Análise',
        orientation='h',
        text_auto=True
    )
    fig_qtd.update_traces(marker_color='#2e7d32')
    st.plotly_chart(fig_qtd, use_container_width=True)

    # Bloco de Tabelas e Exportação
    st.divider()
    t1, t2 = st.tabs(['📂 Demonstrativo Financeiro', '📊 Demonstrativo Quantitativo'])

    with t1:
        st.dataframe(
            df_custos_f, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Custo_Total": st.column_config.NumberColumn("Total (R$)", format="%.2f"),
                "Ano": st.column_config.TextColumn("Ano")
            }
        )
        st.download_button(
            label="Exportar Planilha - Custos (Excel)",
            data=to_excel(df_custos_f),
            file_name="custos_quimico.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with t2:
        st.dataframe(
            df_cont_f,
            use_container_width=True,
            hide_index=True,
            column_config={"Total_Amostras": st.column_config.NumberColumn("Total Amostras")}
        )
        st.download_button(
            label="Exportar Planilha - Quantitativo (Excel)",
            data=to_excel(df_cont_f),
            file_name="quantitativo_quimico.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.error("⚠️ Erro: Arquivo 'dados_concatenado.csv' não encontrado na pasta raiz.")