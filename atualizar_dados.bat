@echo off
:: Garante que caracteres especiais e acentos apareçam corretamente
chcp 65001 > nul

:: =====================================================================
:: SCRIPT DE ATUALIZAÇÃO: REDE AGRO -> CONCATENAÇÃO -> GITHUB
:: =====================================================================

:: 1. Definição de caminhos
set ORIGEM="\\Agroserver\gestao_projetos\08_Processo_Químico\02_Clientes\_teste_dash_custos_quimico"
set DESTINO="C:\Users\MiguelSantos\OneDrive - Agrorobotica Fotonica Em Certificacoes Agroambientais\AGROROBOTICA\PROJETOS\Custo Químico\dados"
set PASTA_PROJETO="C:\Users\MiguelSantos\OneDrive - Agrorobotica Fotonica Em Certificacoes Agroambientais\AGROROBOTICA\PROJETOS\Custo Químico"

echo [1/4] Sincronizando arquivos do servidor...
:: /MIR espelha a pasta | /XD oculta pastas temporárias do Excel
robocopy %ORIGEM% %DESTINO% /MIR /MT:8 /R:2 /W:5 /XD "~$"

echo.
echo [2/4] Executando Python: Varrendo e Concatenando planilhas...
cd /d %PASTA_PROJETO%
:: Rodar o script que cria o 'dados_concatenado.csv'
python sincronizar.py

echo.
echo [3/4] Preparando commit para o GitHub...
git add .
:: O commit leva a data e hora atual para melhor controle no GitHub
git commit -m "Sincronização automática: %date% %time%"

echo.
echo [4/4] Enviando para o Streamlit Cloud...
git push origin main

echo.
echo =====================================================================
echo SUCESSO! O Dashboard será atualizado em aprox. 1 minuto.
echo =====================================================================
exit