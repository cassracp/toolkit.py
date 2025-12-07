import os
import sys
from pypdf import PdfReader
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

# O diretório raiz a ser vasculhado.
# ATUALIZE ESTA VARIÁVEL com o caminho da sua pasta principal.
# Exemplo: DIRETORIO_RAIZ = r"C:\Users\cassr\OneDrive\Projetos\migrador2\DOC Migrador"
DIRETORIO_RAIZ = "D:/Tarefas/16694-NOSSA-SENHORA-DO-SOCORRO-IMAGENS/PROCURAÇÕES PÚBLICAS"

# Nome do arquivo de log onde os resultados serão salvos
NOME_ARQUIVO_LOG = "pdfs_com_mais_de_duas_paginas.log"

# Número mínimo de páginas para ser considerado "grande"
# O usuário pediu "mais de 2 páginas", então o limite é 3 ou mais.
LIMITE_PAGINAS = 2

# ==============================================================================
# FUNÇÕES PRINCIPAIS
# ==============================================================================

def contar_paginas_pdf(caminho_arquivo: str) -> int:
    """
    Tenta contar o número de páginas de um arquivo PDF.

    Args:
        caminho_arquivo: O caminho completo do arquivo PDF.

    Returns:
        O número de páginas do PDF, ou 0 em caso de erro.
    """
    try:
        # Usa PdfReader para abrir o arquivo
        reader = PdfReader(caminho_arquivo)
        return len(reader.pages)
    except Exception as e:
        # Imprime o erro no console e retorna 0 para que não seja processado
        print(f"[ERRO] Falha ao ler o PDF {caminho_arquivo}: {e}", file=sys.stderr)
        return 0

def procurar_e_logar_pdfs(diretorio_raiz: str, arquivo_log: str, limite_paginas: int):
    """
    Percorre o diretório raiz e subpastas procurando PDFs com mais de X páginas
    e loga seus caminhos em um arquivo.
    """
    if not os.path.isdir(diretorio_raiz):
        print(f"ERRO: O diretório raiz '{diretorio_raiz}' não foi encontrado ou é inválido.")
        return

    arquivos_encontrados = 0
    pdfs_grandes = []
    
    print(f"Iniciando a busca em: {diretorio_raiz}")
    print(f"Log de saída: {arquivo_log}")
    print(f"Critério de páginas: > {limite_paginas}")

    # Itera sobre o diretório e subdiretórios (recursivamente)
    for pasta_atual, _, arquivos in os.walk(diretorio_raiz):
        for nome_arquivo in arquivos:
            # Verifica se o arquivo é um PDF (case-insensitive)
            if nome_arquivo.lower().endswith('.pdf'):
                caminho_completo = os.path.join(pasta_atual, nome_arquivo)
                arquivos_encontrados += 1
                
                # Conta o número de páginas
                num_paginas = contar_paginas_pdf(caminho_completo)
                
                # Verifica o critério: mais de 2 páginas (ou seja, 3 ou mais)
                if num_paginas > limite_paginas:
                    print(f"  [ENCONTRADO] {caminho_completo} ({num_paginas} páginas)")
                    pdfs_grandes.append(f"{caminho_completo} ({num_paginas} páginas)")
                else:
                    print(f"  [IGNORADO] {caminho_completo} ({num_paginas} páginas)")

    # Escreve o log
    try:
        with open(arquivo_log, 'w', encoding='utf-8') as f:
            f.write(f"--- Relatório de Arquivos PDF com Mais de {limite_paginas} Páginas ---\n")
            f.write(f"Data da execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Diretório de busca: {os.path.abspath(diretorio_raiz)}\n")
            f.write(f"Total de arquivos PDF encontrados: {arquivos_encontrados}\n")
            f.write(f"PDFs que atendem ao critério ({len(pdfs_grandes)}): \n")
            f.write("-" * 50 + "\n")
            
            for linha in pdfs_grandes:
                f.write(linha + "\n")
                
            f.write("-" * 50 + "\n")
            f.write("Fim do relatório.\n")

        print("\n" + "=" * 50)
        print(f"Processo concluído! {len(pdfs_grandes)} arquivos PDF (de um total de {arquivos_encontrados}) ")
        print(f"com mais de {limite_paginas} páginas foram registrados em: {os.path.abspath(arquivo_log)}")
        print("=" * 50)

    except IOError as e:
        print(f"[ERRO FATAL] Não foi possível escrever no arquivo de log {arquivo_log}: {e}", file=sys.stderr)


# Execução principal
if __name__ == "__main__":
    procurar_e_logar_pdfs(DIRETORIO_RAIZ, NOME_ARQUIVO_LOG, LIMITE_PAGINAS)