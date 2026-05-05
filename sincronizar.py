# %%
import pandas as pd
from pathlib import Path
from datetime import datetime
import os

def processar_e_consolidar():

    caminho_entrada = r"C:\Users\MiguelSantos\OneDrive - Agrorobotica Fotonica Em Certificacoes Agroambientais\AGROROBOTICA\PROJETOS\Custo Químico\dados"
    arquivo_saida = os.path.join(caminho_entrada, "dados_concatenado.csv")

    diretorio = Path(caminho_entrada)
    arquivos = list(diretorio.glob("OS_*/Fazenda_*.xlsx"))
    arquivos = [f for f in arquivos if f.is_file() and not f.name.startswith("~$")]

    if not arquivos:
        print("Nenhum arquivo encontrado.")
        return

    lista_dfs = []
    for arquivo in arquivos:
        try:
            cols = ['CHN', 'K_P_Mehlich', 'Macro', 'Micro', 'MO', 'pH_CaCl2',
                    'pH_H2O', 'P_Resina', 'S_ICP', 'S_Turbidimetria', 'Textura']
            df = pd.read_excel(arquivo, usecols = cols, engine = 'calamine')
            os_id = arquivo.parent.name.split("_")[1]
            data = datetime.fromtimestamp(arquivo.stat().st_ctime)
            ano = data.year
            mes = data.month
            dia = data.day
            data = f"{dia}/{mes}/{ano}"
            
            df.insert(0, 'OS', os_id)
            df.insert(1, 'Ano', ano)
            df.insert(2, 'Data', data)

            df['Data'] = pd.to_datetime(df['Data'], format = '%d/%m/%Y')

            lista_dfs.append(df)
        except Exception as e:
            print(f"Erro no arquivo {arquivo.name}: {e}")

    if lista_dfs:
        df_base = pd.concat(lista_dfs, ignore_index=True)
        # Salva o arquivo consolidado que o Streamlit vai usar
        df_base.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
        print(f"Sucesso! Base consolidada gerada com {len(df_base)} linhas.")

if __name__ == "__main__":
    processar_e_consolidar()