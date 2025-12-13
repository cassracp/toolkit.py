# -*- coding: utf-8 -*-

import os
from toolkit.utils import selecionar_diretorio, contar_palavras
from toolkit.config import EXTENSOES_CODIGO, PASTAS_A_IGNORAR

class LargeFileFinder:
    def __init__(self):
        print("\n--- [DIAGNÓSTICO] Localizador de Arquivos de Código Grandes ---")

    def run(self):
        try:
            limite_str = input("Qual limite de palavras você quer verificar? [Padrão: 500000]: ") or "500000"
            limite_palavras_verificacao = int(limite_str)
        except ValueError:
            print("Entrada inválida. Usando o padrão de 500.000.")
            limite_palavras_verificacao = 500000

        diretorio_raiz = selecionar_diretorio("Selecione a pasta raiz do projeto para VERIFICAR")
        
        if not diretorio_raiz:
            print("Operação cancelada. Nenhum diretório selecionado.")
            return

        print(f"Iniciando varredura em: '{diretorio_raiz}'")
        print(f"Procurando por arquivos de CÓDIGO com mais de {limite_palavras_verificacao:,} palavras...")
        print(f"Ignorando pastas: {PASTAS_A_IGNORAR}")
        print("-" * 70)
        
        arquivos_encontrados = 0
        total_arquivos_lidos = 0
        
        try:
            for root, dirs, files in os.walk(diretorio_raiz):
                dirs[:] = [d for d in dirs if d not in PASTAS_A_IGNORAR]
                
                for nome_arquivo in files:
                    if not any(nome_arquivo.lower().endswith(ext) for ext in EXTENSOES_CODIGO):
                        continue 

                    caminho_completo = os.path.join(root, nome_arquivo)
                    
                    try:
                        with open(caminho_completo, "r", encoding="utf-8", errors="ignore") as f:
                            conteudo = f.read()
                        
                        total_arquivos_lidos += 1
                        contagem = contar_palavras(conteudo)
                        
                        if contagem > limite_palavras_verificacao:
                            print(f"!!! ARQUIVO DE CÓDIGO GRANDE ENCONTRADO !!!")
                            print(f"  -> Caminho: {caminho_completo}")
                            print(f"  -> Contagem: {contagem:,.0f} palavras")
                            print("-" * 30)
                            arquivos_encontrados += 1
                            
                    except Exception:
                        pass 

        except Exception as e:
            print(f"Ocorreu um erro durante a varredura: {e}")
            
        print("\n" + "=" * 70)
        print(f"Varredura concluída. Total de {total_arquivos_lidos} arquivos de código lidos.")
        if arquivos_encontrados > 0:
            print(f"Sucesso! Encontrado(s) {arquivos_encontrados} arquivo(s) acima do limite.")
            print("Considere adicionar o(s) nome(s) desse(s) arquivo(s) à lista 'ARQUIVOS_A_IGNORAR' em config.py.")
        else:
            print(f"Nenhum arquivo de CÓDIGO encontrado acima do limite de {limite_palavras_verificacao:,} palavras.")
        print("=" * 70)
