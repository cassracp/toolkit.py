# -*- coding: utf-8 -*-

"""
Módulo de funções utilitárias para o Toolkit.
"""

import tkinter as tk
from tkinter import filedialog

def selecionar_diretorio(titulo):
    """Abre uma janela para o usuário selecionar um diretório."""
    root = tk.Tk()
    root.withdraw()
    caminho = filedialog.askdirectory(title=titulo)
    return caminho

def selecionar_arquivo(titulo, tipos_arquivo):
    """Abre uma janela para o usuário selecionar um arquivo."""
    root = tk.Tk()
    root.withdraw()
    caminho = filedialog.askopenfilename(title=titulo, filetypes=tipos_arquivo)
    return caminho

def formatar_tamanho(tamanho_bytes):
    """Converte o tamanho de bytes para um formato legível (KB, MB, GB)."""
    if tamanho_bytes is None: return "0 Bytes"
    if tamanho_bytes < 1024: return f"{tamanho_bytes} Bytes"
    if tamanho_bytes < 1024**2: return f"{tamanho_bytes/1024:.2f} KB"
    if tamanho_bytes < 1024**3: return f"{tamanho_bytes/1024**2:.2f} MB"
    return f"{tamanho_bytes/1024**3:.2f} GB"

def contar_palavras(texto):
    """Conta o número de palavras em uma string, usando espaço como delimitador."""
    return len(texto.split())
