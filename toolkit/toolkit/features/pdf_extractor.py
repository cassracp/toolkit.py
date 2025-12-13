# -*- coding: utf-8 -*-

import os
import datetime
from toolkit.utils import selecionar_arquivo, selecionar_diretorio

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

class PdfExtractor:
    def __init__(self):
        print("\n--- Extrator de Texto de PDF para Markdown ---")
        if not fitz:
            print("ERRO: A biblioteca 'PyMuPDF' não está instalada.")
            print("Para usar esta função, por favor, instale-a com: pip install PyMuPDF")

    def run(self):
        if not fitz:
            return
            
        pdf_path = selecionar_arquivo(
            "Selecione o arquivo PDF para extrair",
            [("Arquivos PDF", "*.pdf")]
        )
        if not pdf_path:
            print("Operação cancelada. Nenhum arquivo PDF selecionado.")
            return

        diretorio_saida = selecionar_diretorio("Selecione a pasta para SALVAR o arquivo .md")
        if not diretorio_saida:
            print("Operação cancelada. Nenhum diretório de saída selecionado.")
            return

        nome_base_arquivo = os.path.splitext(os.path.basename(pdf_path))[0]
        nome_arquivo_saida = f"{nome_base_arquivo}-extracao.md"
        caminho_completo_saida = os.path.join(diretorio_saida, nome_arquivo_saida)

        print(f"\nIniciando extração do PDF: '{pdf_path}'")
        print(f"O arquivo de saída será: '{caminho_completo_saida}'")

        try:
            doc = fitz.open(pdf_path)
            texto_completo = []
            total_paginas = len(doc)
            
            print(f"O PDF tem {total_paginas} página(s). Processando...")

            texto_completo.append(f"# Extração de Texto do PDF: {os.path.basename(pdf_path)}\n")
            texto_completo.append(f"**Data da extração:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            texto_completo.append("---\n\n")

            for i, page in enumerate(doc):
                print(f"  - Lendo página {i + 1}/{total_paginas}...")
                texto_completo.append(f"## Página {i + 1}\n\n")
                texto_completo.append(page.get_text("text", sort=True))
                texto_completo.append("\n\n---\n\n")
            
            doc.close()

            with open(caminho_completo_saida, "w", encoding="utf-8") as f_out:
                f_out.write("".join(texto_completo))

            print("\n" + "=" * 30)
            print("Processo de extração de PDF concluído com sucesso!")
            print(f"Texto salvo em: '{caminho_completo_saida}'")
            print("=" * 30)

        except Exception as e:
            print(f"\nERRO FATAL durante a extração do PDF. Erro: {e}")
            print("Verifique se o arquivo não está corrompido ou se o PDF é baseado em imagem (scan).")
