# -*- coding: utf-8 -*-

"""
PDF JS Monolith Extractor
Gera um único arquivo .js contendo todo o código JavaScript do PDF,
organizado por seções para facilitar a leitura e debug.
"""

import os
import sys
import datetime
import tkinter as tk
from tkinter import filedialog
import pikepdf

def select_file():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Selecione o PDF para extração monolítica",
        filetypes=[("PDF Files", "*.pdf")]
    )
    root.destroy()
    return path

def select_save_location(default_name="full_source.js"):
    root = tk.Tk()
    root.withdraw()
    path = filedialog.asksaveasfilename(
        title="Salvar arquivo JS unificado como...",
        defaultextension=".js",
        initialfile=default_name,
        filetypes=[("JavaScript Files", "*.js")]
    )
    root.destroy()
    return path

class PdfMonolithExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.pdf = pikepdf.open(pdf_path)
        self.output_buffer = []
        self.separator_width = 78

    def _resolve_js_content(self, js_obj):
        """Extrai string de um objeto JS (Stream ou String)."""
        try:
            if isinstance(js_obj, pikepdf.Stream):
                return js_obj.read_bytes().decode('utf-8', errors='replace')
            return str(js_obj)
        except Exception:
            return None

    def _add_section_header(self, title):
        header = f"\n\n{'/'*self.separator_width}\n"
        header += f"// SEÇÃO: {title}\n"
        header += f"{'/'*self.separator_width}\n"
        self.output_buffer.append(header)

    def _add_block(self, type_label, name_label, event_label, code):
        if not code or not code.strip():
            return

        # Formatando o cabeçalho do bloco estilo "Monolito"
        # // ==============================================================================
        # // TIPO: Global Script | NOME: init_d20_functions
        # // ==============================================================================
        
        info_line = f"// TIPO: {type_label:<14} | NOME: {name_label}"
        if event_label:
            info_line += f" | EVENTO: {event_label}"

        block = f"\n// {'='*(self.separator_width - 3)}\n"
        block += f"{info_line}\n"
        block += f"// {'='*(self.separator_width - 3)}\n"
        block += f"{code.strip()}\n"
        
        self.output_buffer.append(block)

    def extract_globals(self):
        """SEÇÃO 1: Document Level Scripts"""
        self._add_section_header("1. GLOBAL / DOCUMENT LEVEL SCRIPTS")
        
        try:
            if "/Names" in self.pdf.root and "/JavaScript" in self.pdf.root.Names:
                js_names = self.pdf.root.Names.JavaScript
                if "/Names" in js_names:
                    names_array = js_names.Names
                    # A estrutura é [String, Obj, String, Obj...]
                    for i in range(0, len(names_array), 2):
                        script_name = str(names_array[i])
                        js_obj = names_array[i+1]
                        
                        if "/JS" in js_obj:
                            code = self._resolve_js_content(js_obj.JS)
                            self._add_block("Global Script", script_name, None, code)
        except Exception as e:
            self.output_buffer.append(f"// [ERRO ao extrair Globais: {e}]\n")

    def extract_open_action(self):
        """SEÇÃO 2: OpenAction"""
        self._add_section_header("2. OPEN ACTION (Ao Abrir)")
        
        try:
            if "/OpenAction" in self.pdf.root:
                oa = self.pdf.root.OpenAction
                if "/JS" in oa:
                    code = self._resolve_js_content(oa.JS)
                    self._add_block("OpenAction", "Document_Open", "Run", code)
        except Exception as e:
            self.output_buffer.append(f"// [ERRO ao extrair OpenAction: {e}]\n")

    def extract_fields(self):
        """SEÇÃO 3: AcroForm Fields"""
        self._add_section_header("3. ACROFORM FIELDS (Campos)")
        
        try:
            if "/AcroForm" in self.pdf.root and "/Fields" in self.pdf.root.AcroForm:
                self._recurse_fields(self.pdf.root.AcroForm.Fields)
        except Exception as e:
            self.output_buffer.append(f"// [ERRO ao extrair Campos: {e}]\n")

    def _recurse_fields(self, fields, parent_name=""):
        for field in fields:
            # Determina o nome completo do campo (Fully Qualified Name)
            partial_name = str(field.get("/T", ""))
            
            # Se não tiver nome, tenta usar ID ou fallback
            if not partial_name:
                partial_name = f"Obj_{field.objgen}" if hasattr(field, 'objgen') else "Unnamed"
            
            full_name = f"{parent_name}.{partial_name}" if parent_name else partial_name

            # 1. Ação Direta (/JS)
            if "/JS" in field:
                code = self._resolve_js_content(field.JS)
                self._add_block("Field Script", full_name, "Direct Action", code)

            # 2. Additional Actions (/AA) - Eventos
            if "/AA" in field:
                aa = field.AA
                for key in aa.keys():
                    # /C = Calculate, /V = Validate, /F = Format, /K = Keystroke
                    event_code = str(key).replace("/", "")
                    event_map = {
                        "C": "Calculate", "V": "Validate", "F": "Format", 
                        "K": "Keystroke", "Fo": "Focus", "Bl": "Blur",
                        "D": "Mouse Down", "U": "Mouse Up", "E": "Mouse Enter", "X": "Mouse Exit"
                    }
                    event_name = event_map.get(event_code, f"Unknown({event_code})")
                    
                    if "/JS" in aa[key]:
                        code = self._resolve_js_content(aa[key].JS)
                        self._add_block("Field Script", full_name, f"{event_name} (/{event_code})", code)

            # Recursão para filhos (Kids)
            if "/Kids" in field:
                self._recurse_fields(field.Kids, full_name)

    def run(self, save_path):
        # Cabeçalho do Arquivo
        self.output_buffer.append("/**")
        self.output_buffer.append(f" * EXTRAÇÃO MONOLÍTICA DE JAVASCRIPT")
        self.output_buffer.append(f" * Fonte: {os.path.basename(self.pdf_path)}")
        self.output_buffer.append(f" * Data: {datetime.datetime.now()}")
        self.output_buffer.append(f" * Aviso: Este arquivo contém todo o código extraído para análise.")
        self.output_buffer.append(" */")

        # Processamento em Ordem
        self.extract_globals()
        self.extract_open_action()
        self.extract_fields()

        # Salvar
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.output_buffer))
            print(f"\n[SUCESSO] Arquivo gerado em: {save_path}")
            print(f"Total de linhas geradas: {len(self.output_buffer)}")
        except Exception as e:
            print(f"\n[ERRO] Não foi possível salvar o arquivo: {e}")

if __name__ == "__main__":
    print("--- PDF Monolith Js Extractor ---")
    
    # Seleção de Entrada
    target_pdf = select_file()
    if not target_pdf:
        print("Nenhum PDF selecionado.")
        sys.exit()

    # Seleção de Saída
    default_out_name = os.path.splitext(os.path.basename(target_pdf))[0] + "_full.js"
    target_save = select_save_location(default_out_name)
    if not target_save:
        print("Nenhum local de salvamento selecionado.")
        sys.exit()

    # Execução
    extractor = PdfMonolithExtractor(target_pdf)
    extractor.run(target_save)
