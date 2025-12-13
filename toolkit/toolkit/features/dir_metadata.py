# -*- coding: utf-8 -*-

import os
import datetime
from toolkit.utils import selecionar_diretorio, formatar_tamanho

class DirMetadataCollector:
    def __init__(self):
        print("\n--- Coletor de Metadados de Diretórios ---")

    def run(self):
        diretorio_raiz = selecionar_diretorio("Selecione a pasta para COLETAR os metadados")
        if not diretorio_raiz:
            print("Operação cancelada. Nenhum diretório selecionado.")
            return

        diretorio_saida = selecionar_diretorio("Selecione a pasta para SALVAR o relatório de metadados")
        if not diretorio_saida:
            print("Operação cancelada. Nenhum diretório de saída selecionado.")
            return

        nome_pasta_raiz = os.path.basename(os.path.normpath(diretorio_raiz))
        nome_arquivo_saida = f"{nome_pasta_raiz}-dir-metadatas.txt"
        caminho_completo_saida = os.path.join(diretorio_saida, nome_arquivo_saida)

        print(f"Iniciando a verificação em: '{diretorio_raiz}'")
        print(f"O arquivo de saída será: '{caminho_completo_saida}'")
        
        contador_arquivos = 0
        contador_erros = 0

        try:
            with open(caminho_completo_saida, "w", encoding="utf-8") as f_out:
                f_out.write(f"# Metadados dos arquivos do diretório: {diretorio_raiz}\n")
                f_out.write(f"# Data da extração: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                for root, _, files in os.walk(diretorio_raiz):
                    for nome_arquivo in files:
                        caminho_completo = os.path.join(root, nome_arquivo)
                        try:
                            stats = os.stat(caminho_completo)
                            f_out.write("-" * 50 + "\n")
                            f_out.write(f"Caminho Completo: {caminho_completo}\n")
                            f_out.write(f"Tamanho: {formatar_tamanho(stats.st_size)} ({stats.st_size} Bytes)\n")
                            f_out.write(f"Data de Modificação: {datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f_out.write(f"Data de Criação: {datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f_out.write("-" * 50 + "\n\n")
                            contador_arquivos += 1
                        except OSError as e:
                            print(f"AVISO: Não foi possível ler metadados de '{caminho_completo}'. Erro: {e}")
                            contador_erros += 1
            
            print("\n" + "=" * 30)
            print("Processo de coleta de metadados de diretório concluído!")
            print(f"Metadados de {contador_arquivos} arquivos salvos.")
            if contador_erros > 0: print(f"Ocorreram {contador_erros} erros de acesso.")
            print("=" * 30)
        except IOError as e:
            print(f"ERRO FATAL ao escrever no arquivo de saída. Erro: {e}")
