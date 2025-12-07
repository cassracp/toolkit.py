# -*- coding: utf-8 -*-

"""
SCRIPT DE DIAGNÓSTICO v2: LOCALIZADOR DE ARQUIVOS DE CÓDIGO GRANDES

Este script varre um diretório para encontrar arquivos QUE ESTEJAM NA
LISTA DE EXTENSÕES DE CÓDIGO e que contenham mais de 500.000 palavras.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog

# --- CONFIGURAÇÕES ---
LIMITE_PALAVRAS = 500000

# Reutilizando a mesma lista de pastas do script principal
PASTAS_A_IGNORAR = [
    'node_modules', '.git', 'dist', 'build', '__pycache__',
    'venv', 'target', 'bin', 'obj', 'temp', 'tmp'
]

# <<< IMPORTANTE: Verificando apenas as mesmas extensões do script principal
EXTENSOES_CODIGO = [
    '.html', '.htm', '.css', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte',
    '.py', '.php', '.java', '.cs', '.go', '.rb', '.rs', '.mjs', '.sql',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.md', '.sh', '.bat',
    '.c', '.cpp', '.h', '.hpp'
]
# --- FIM DAS CONFIGURAÇÕES ---

def contar_palavras(texto):
    """Conta o número de palavras em uma string, usando espaço como delimitador."""
    return len(texto.split())

def selecionar_diretorio(titulo):
    """Abre uma janela para o usuário selecionar um diretório."""
    root = tk.Tk()
    root.withdraw()
    caminho = filedialog.askdirectory(title=titulo)
    return caminho

def encontrar_arquivos_grandes():
    """
    Função principal que varre o diretório e imprime arquivos acima do limite.
    """
    print("--- Localizador de Arquivos de CÓDIGO com Muitas Palavras (v2) ---")
    diretorio_raiz = selecionar_diretorio("Selecione a pasta raiz do projeto para VERIFICAR")
    
    if not diretorio_raiz:
        print("Operação cancelada. Nenhum diretório selecionado.")
        return

    print(f"Iniciando varredura em: '{diretorio_raiz}'")
    print(f"Procurando por arquivos de CÓDIGO com mais de {LIMITE_PALAVRAS:,} palavras...")
    print(f"Ignorando pastas: {PASTAS_A_IGNORAR}")
    print("-" * 70)
    
    arquivos_encontrados = 0
    total_arquivos_lidos = 0
    
    try:
        for root, dirs, files in os.walk(diretorio_raiz):
            # Aplica a regra de ignorar pastas
            dirs[:] = [d for d in dirs if d not in PASTAS_A_IGNORAR]
            
            for nome_arquivo in files:
                
                # <<< MODIFICAÇÃO: Só verifica se a extensão for de código
                if not any(nome_arquivo.lower().endswith(ext) for ext in EXTENSOES_CODIGO):
                    continue # Pula este arquivo

                caminho_completo = os.path.join(root, nome_arquivo)
                
                try:
                    with open(caminho_completo, "r", encoding="utf-8", errors="ignore") as f:
                        conteudo = f.read()
                    
                    total_arquivos_lidos += 1
                    contagem = contar_palavras(conteudo)
                    
                    if contagem > LIMITE_PALAVRAS:
                        print(f"!!! ARQUIVO DE CÓDIGO GRANDE ENCONTRADO !!!")
                        print(f"  -> Caminho: {caminho_completo}")
                        print(f"  -> Contagem: {contagem:,.0f} palavras")
                        print("-" * 30)
                        arquivos_encontrados += 1
                        
                except Exception:
                    # Ignora arquivos que não podem ser lidos
                    pass 

    except Exception as e:
        print(f"Ocorreu um erro durante a varredura: {e}")
        
    print("\n" + "=" * 70)
    print(f"Varredura concluída. Total de {total_arquivos_lidos} arquivos de código lidos.")
    if arquivos_encontrados > 0:
        print(f"Sucesso! Encontrado(s) {arquivos_encontrados} arquivo(s) acima do limite.")
        print("Adicione o(s) nome(s) desse(s) arquivo(s) à lista 'ARQUIVOS_A_IGNORAR' no script principal.")
    else:
        print("Nenhum arquivo de CÓDIGO encontrado acima do limite de 500.000 palavras.")
    print("=" * 70)

# --- Ponto de entrada do script ---
if __name__ == "__main__":
    try:
        encontrar_arquivos_grandes()
    except KeyboardInterrupt:
        print("\n\nVarredura interrompida pelo usuário.")
    
    input("\nPressione Enter para fechar esta janela...")
    sys.exit(0)