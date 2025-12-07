# -*- coding: utf-8 -*-

import os
import datetime

# --- NOVO: DIRETÓRIO DE SAÍDA FIXO ---
# O diretório onde todos os arquivos de saída serão salvos, conforme solicitado.
DIRETORIO_SAIDA = r"C:\Users\cassr\OneDrive\MIG\Scripts\saida"

def formatar_tamanho(tamanho_bytes):
    """Converte o tamanho de bytes para um formato legível (KB, MB, GB)."""
    if tamanho_bytes is None:
        return "0 Bytes"
    if tamanho_bytes < 1024:
        return f"{tamanho_bytes} Bytes"
    elif tamanho_bytes < 1024**2:
        return f"{tamanho_bytes/1024:.2f} KB"
    elif tamanho_bytes < 1024**3:
        return f"{tamanho_bytes/1024**2:.2f} MB"
    else:
        return f"{tamanho_bytes/1024**3:.2f} GB"

def coletar_metadados(diretorio_raiz):
    """
    Percorre um diretório recursivamente, coleta metadados de todos os arquivos
    e salva as informações em um arquivo de texto no diretório de saída fixo.

    :param diretorio_raiz: O caminho da pasta a ser verificada.
    """
    
    # Extrai o nome da pasta raiz
    nome_pasta_raiz = os.path.basename(os.path.normpath(diretorio_raiz))
    
    # Constrói o nome do arquivo de saída no formato solicitado: migrador-nome_da_pasta_raiz_metadados.txt
    nome_arquivo_base = f"{nome_pasta_raiz}_dir_metadados.txt"
    
    # Constrói o caminho completo do arquivo de saída
    caminho_completo_saida = os.path.join(DIRETORIO_SAIDA, nome_arquivo_base)

    # Garante que o diretório de saída exista
    os.makedirs(DIRETORIO_SAIDA, exist_ok=True)
    
    contador_arquivos = 0
    contador_erros = 0

    try:
        # Abre o arquivo de saída no modo de escrita com codificação UTF-8
        with open(caminho_completo_saida, "w", encoding="utf-8") as f_out:
            print(f"Iniciando a verificação em: '{diretorio_raiz}'")
            print(f"O arquivo de saída será: '{caminho_completo_saida}'")
            
            f_out.write(f"# Metadados dos arquivos do diretório: {diretorio_raiz}\n")
            f_out.write(f"# Data da extração: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # os.walk() percorre a árvore de diretórios de forma recursiva
            for root, dirs, files in os.walk(diretorio_raiz):
                for nome_arquivo in files:
                    caminho_completo = os.path.join(root, nome_arquivo)
                    
                    try:
                        # Obtém as estatísticas do arquivo
                        stats = os.stat(caminho_completo)

                        # Extrai os metadados
                        tamanho = stats.st_size
                        data_modificacao = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        data_criacao = datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                        data_acesso = datetime.datetime.fromtimestamp(stats.st_atime).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Escreve os metadados formatados no arquivo
                        f_out.write("-" * 50 + "\n")
                        f_out.write(f"Caminho Completo: {caminho_completo}\n")
                        f_out.write(f"Nome do Arquivo: {nome_arquivo}\n")
                        f_out.write(f"Tamanho: {formatar_tamanho(tamanho)} ({tamanho} Bytes)\n")
                        f_out.write(f"Data de Modificação: {data_modificacao}\n")
                        f_out.write(f"Data de Criação: {data_criacao}\n")
                        f_out.write(f"Data de Último Acesso: {data_acesso}\n")
                        f_out.write("-" * 50 + "\n\n")
                        
                        contador_arquivos += 1

                    except OSError as e:
                        # Em caso de erro (ex: permissão negada), registra no arquivo e no console
                        print(f"AVISO: Não foi possível ler os metadados de '{caminho_completo}'. Erro: {e}")
                        f_out.write("-" * 50 + "\n")
                        f_out.write(f"ERRO: Não foi possível processar o arquivo.\n")
                        f_out.write(f"Caminho: {caminho_completo}\n")
                        f_out.write(f"Motivo: {e}\n")
                        f_out.write("-" * 50 + "\n\n")
                        contador_erros += 1

        print("\n" + "=" * 30)
        print("Processo concluído com sucesso!")
        print(f"Metadados de {contador_arquivos} arquivos foram salvos em '{caminho_completo_saida}'.")
        if contador_erros > 0:
            print(f"Ocorreram {contador_erros} erros ao tentar acessar alguns arquivos (verifique o log).")
        print("=" * 30)

    except IOError as e:
        print(f"ERRO FATAL: Não foi possível criar ou escrever no arquivo de saída '{caminho_completo_saida}'. Erro: {e}")
    except Exception as e:
        print(f"ERRO INESPERADO: Ocorreu um problema durante a execução. Erro: {e}")

if __name__ == "__main__":
    # Pede ao usuário para inserir o caminho da pasta
    caminho_pasta = input("Por favor, digite o caminho completo da pasta que deseja verificar e pressione Enter: ")

    # Verifica se o caminho inserido é um diretório válido
    if os.path.isdir(caminho_pasta):
        coletar_metadados(caminho_pasta)
    else:
        print(f"Erro: O caminho '{caminho_pasta}' não foi encontrado ou não é uma pasta válida.")
        print("Por favor, execute o script novamente com um caminho correto.")
