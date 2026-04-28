# Gestão de Custos — Análises Laboratório Químico

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

Este painel foi desenvolvido para centralizar, calcular e visualizar os custos operacionais das análises do laboratório químico da **Agrorobótica**. A ferramenta automatiza a transformação de dados brutos de Ordens de Serviço (OS) em indicadores financeiros e quantitativos.

Painel: ![Painel - Análises Laboratório Químico](https://custoquimico-agrorobotica.streamlit.app/)

---

## Funcionalidades

* **Cálculo Automatizado de Custos**: Processamento instantâneo do custo por amostra e custo de padrões laboratoriais (PL).
* **Filtros Dinâmicos**: Navegação intuitiva por Ano de Referência e Ordem de Serviço via Sidebar.
* **Métricas de Controle**: Visualização de Custo Total, Custo de PL, Volume de Amostras e Ticket Médio por OS.
* **Visualização Interativa**: 
    * Custo Total por OS (Gráfico de Barras).
    * Distribuição percentual por tipo de análise (Gráfico de Rosca).
    * Volume físico de análises (Gráfico de Barra Horizontal).
* **Exportação de Relatórios**: Funcionalidade para download de demonstrativos detalhados em Excel (`.xlsx`).

---

## Requisitos e Instalação

### Pré-requisitos
* **Python 3.8** ou superior.
* Bibliotecas necessárias: `pandas`, `streamlit`, `plotly`, `openpyxl`.