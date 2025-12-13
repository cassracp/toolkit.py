# -*- coding: utf-8 -*-

import os
import datetime
from toolkit.utils import selecionar_diretorio, contar_palavras
from toolkit.config import (
    EXTENSOES_CODIGO,
    PASTAS_A_IGNORAR,
    ARQUIVOS_A_IGNORAR,
    LIMITE_PALAVRAS_COMPILADOR,
    MAX_ARQUIVOS_SAIDA
)

class CodeCompiler:
    def __init__(self):
        print("\n--- Compilador de Códigos-Fontes ---")

    def run(self):
        diretorio_raiz = selecionar_diretorio("Selecione a pasta raiz do projeto para COMPILAR")
        if not diretorio_raiz:
            print("Operação cancelada. Nenhum diretório selecionado.")
            return

        diretorio_saida = selecionar_diretorio("Selecione a pasta para SALVAR o arquivo compilado")
        if not diretorio_saida:
            print("Operação cancelada. Nenhum diretório de saída selecionado.")
            return

        nome_pasta_raiz = os.path.basename(os.path.normpath(diretorio_raiz))
        nome_base_saida = f"{nome_pasta_raiz}-compiled-code"
        
        print(f"Iniciando a compilação de código do projeto em: '{diretorio_raiz}'")
        print(f"Os arquivos de saída serão salvos em: '{diretorio_saida}'")
        print(f"Limite por arquivo: {LIMITE_PALAVRAS_COMPILADOR} palavras.")
        print("-" * 100)
        
        arquivos_de_saida = [] 
        blocos_arquivo_atual = []
        
        contador_arquivos_processados = 0
        contador_arquivos_ignorados = 0
        contador_erros = 0
        separador = "-" * 100
        
cabecalho_template = (
            f"# Compilação de código-fonte do projeto: {diretorio_raiz}\n"
            f"# Data da extração: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"# PARTE [P] DE [T]\n"
            f"{ '=' * 80}\n\n"
        )
        
        contagem_palavras_atual = contar_palavras(cabecalho_template)

        for root, dirs, files in os.walk(diretorio_raiz):
            dirs[:] = [d for d in dirs if d not in PASTAS_A_IGNORAR]
            for nome_arquivo in files:
                
                if nome_arquivo in ARQUIVOS_A_IGNORAR:
                    contador_arquivos_ignorados += 1
                    continue

                if any(nome_arquivo.lower().endswith(ext) for ext in EXTENSOES_CODIGO):
                    caminho_completo = os.path.join(root, nome_arquivo)
                    try:
                        with open(caminho_completo, "r", encoding="utf-8", errors="ignore") as f_in:
                            conteudo = f_in.read()
                        
cabecalho_arquivo = f"### ARQUIVO: {caminho_completo}\n"
                        bloco_compilado = (
                            f"{separador}\n{cabecalho_arquivo}{separador}\n"
                            f"{conteudo}\n{separador}\n\n"
                        )
                        
                        palavras_do_bloco = contar_palavras(bloco_compilado)
                        
                        if (contagem_palavras_atual + palavras_do_bloco > LIMITE_PALAVRAS_COMPILADOR) and blocos_arquivo_atual:
                            arquivos_de_saida.append(blocos_arquivo_atual)
                            blocos_arquivo_atual = []
                            contagem_palavras_atual = contar_palavras(cabecalho_template)

                        blocos_arquivo_atual.append(bloco_compilado)
                        contagem_palavras_atual += palavras_do_bloco
                        contador_arquivos_processados += 1
                        
                    except Exception as e:
                        print(f"AVISO: Não foi possível ler o arquivo '{caminho_completo}'. Erro: {e}")
                        contador_erros += 1

        if blocos_arquivo_atual:
            arquivos_de_saida.append(blocos_arquivo_atual)

        if not arquivos_de_saida:
            print("\nNenhum arquivo de código-fonte válido encontrado.")
            return

        num_arquivos_necessarios = len(arquivos_de_saida)

        if num_arquivos_necessarios > MAX_ARQUIVOS_SAIDA:
            print(f"\nAVISO: COMPILAÇÃO MUITO GRANDE! Seriam necessários {num_arquivos_necessarios} arquivos.")
            print(f"O limite é de {MAX_ARQUIVOS_SAIDA} arquivos. Processo abortado.")
            return

        print(f"\nTotal de {contador_arquivos_processados} arquivos de código processados.")
        if contador_arquivos_ignorados > 0:
            print(f"{contador_arquivos_ignorados} arquivos foram ignorados (conforme lista).")
        print(f"Dividindo em {num_arquivos_necessarios} arquivo(s) de saída.")

        for i, blocos_do_arquivo in enumerate(arquivos_de_saida):
            nome_arquivo_saida = f"{nome_base_saida}.txt" if num_arquivos_necessarios == 1 else f"{nome_base_saida}_{i+1:02d}.txt"
            caminho_completo_saida = os.path.join(diretorio_saida, nome_arquivo_saida)
            
            try:
                with open(caminho_completo_saida, "w", encoding="utf-8") as f_out:
                    f_out.write(f"# Compilação de código-fonte do projeto: {diretorio_raiz}\n")
                    f_out.write(f"# Data da extração: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f_out.write(f"# PARTE {i+1} DE {num_arquivos_necessarios}\n")
                    f_out.write("=" * 80 + "\n\n")
                    
                    for bloco in blocos_do_arquivo:
                        f_out.write(bloco)
                    
                    print(f"Parte {i+1:02d} salva em: '{caminho_completo_saida}'")
            except IOError as e:
                print(f"ERRO FATAL ao escrever no arquivo '{caminho_completo_saida}'. Erro: {e}")
                return
        
        print("\n" + "=" * 30)
        print("Processo de compilação concluído!")
        print(f"Arquivos processados: {contador_arquivos_processados}")
        if contador_arquivos_ignorados > 0: print(f"Arquivos ignorados: {contador_arquivos_ignorados}")
        if contador_erros > 0: print(f"Erros de leitura: {contador_erros}")
        print("=" * 30)
