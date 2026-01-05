# -*- coding: utf-8 -*-

"""
Ferramenta para extração monolítica de JavaScript de PDF.
Gera um único arquivo .js contendo todo o código encontrado, organizado por seções.
"""

import os
import datetime
from toolkit.utils import selecionar_arquivo, selecionar_diretorio

try:
    import pikepdf
except ImportError:
    pikepdf = None

class PdfJsExtractor:
    def __init__(self):
        print("\n" + "="*50)
        print("   EXTRATOR JS DE PDF")
        print("="*50)
        if not pikepdf:
            print("\n[!] A biblioteca 'pikepdf' não está instalada.")
            print("Execute: pip install pikepdf")

    def _resolve_js(self, js_obj):
        """Extrai string de um objeto JS."""
        try:
            if isinstance(js_obj, pikepdf.Stream):
                return js_obj.read_bytes().decode('utf-8', errors='replace')
            return str(js_obj)
        except Exception:
            return None

    def _add_section_header(self, title, buffer):
        sep = "/" * 78
        header = f"\n\n{sep}\n// SEÇÃO: {title}\n{sep}\n"
        buffer.append(header)

    def _add_block(self, type_label, name_label, event_label, code, buffer):
        if not code or not code.strip():
            return
        
        sep = "=" * 75
        info = f"// TIPO: {type_label:<14} | NOME: {name_label}"
        if event_label:
            info += f" | EVENTO: {event_label}"
            
        block = f"\n// {sep}\n{info}\n// {sep}\n{code.strip()}\n"
        buffer.append(block)

    def _recurse_fields(self, fields, buffer, parent_name=""):
        for field in fields:
            partial_name = str(field.get("/T", ""))
            if not partial_name:
                partial_name = f"Obj_{field.objgen}" if hasattr(field, 'objgen') else "Unnamed"
            
            full_name = f"{parent_name}.{partial_name}" if parent_name else partial_name

            # Coleta para o índice
            if hasattr(self, 'field_index'):
                self.field_index.append(full_name)

            # 1. Direto (/JS)
            if "/JS" in field:
                code = self._resolve_js(field.JS)
                self._add_block("Field Script", full_name, "Direct Action", code, buffer)

            # 2. Eventos (/AA)
            if "/AA" in field:
                aa = field.AA
                for key in aa.keys():
                    event_code = str(key).replace("/", "")
                    event_map = {
                        "C": "Calculate", "V": "Validate", "F": "Format", "K": "Keystroke",
                        "Fo": "Focus", "Bl": "Blur", "D": "Mouse Down", "U": "Mouse Up",
                        "E": "Mouse Enter", "X": "Mouse Exit"
                    }
                    event_name = event_map.get(event_code, event_code)
                    if "/JS" in aa[key]:
                        code = self._resolve_js(aa[key].JS)
                        self._add_block("Field Script", full_name, f"{event_name} (/{event_code})", code, buffer)

            # Recursão
            if "/Kids" in field:
                self._recurse_fields(field.Kids, buffer, full_name)

    def _scan_pages(self, pdf, buffer):
        """Varre páginas e anotações por scripts órfãos/widgets."""
        try:
            for i, page in enumerate(pdf.pages):
                p_num = i + 1
                
                # Ações de Página (/AA)
                if "/AA" in page:
                    for key in page.AA.keys():
                        if "/JS" in page.AA[key]:
                            # O = Open, C = Close
                            evt = str(key).replace("/", "")
                            code = self._resolve_js(page.AA[key].JS)
                            self._add_block("Page Action", f"Page {p_num}", f"Page Event {evt}", code, buffer)

                # Anotações (/Annots)
                if "/Annots" in page:
                    for annot in page.Annots:
                        # Tenta pegar nome (T) ou usa ID
                        t_name = str(annot.get("/T", ""))
                        if not t_name:
                            t_name = f"Annot_{annot.objgen}" if hasattr(annot, 'objgen') else f"Unnamed_Annot_Page{p_num}"
                        
                        # Se já coletamos esse campo no AcroForm, talvez seja melhor não duplicar, 
                        # mas como é extração forense/debug, melhor pecar pelo excesso.
                        
                        # Widget Actions (/A) -> Mouse Up/Down costumam estar aqui em botões
                        if "/A" in annot and "/JS" in annot.A:
                            code = self._resolve_js(annot.A.JS)
                            self._add_block("Widget Action", t_name, "Action (/A)", code, buffer)
                        
                        # Widget AA (/AA)
                        if "/AA" in annot:
                            for key in annot.AA.keys():
                                if "/JS" in annot.AA[key]:
                                    evt = str(key).replace("/", "")
                                    code = self._resolve_js(annot.AA[key].JS)
                                    self._add_block("Widget AA", t_name, f"Event {evt}", code, buffer)
        except Exception:
            pass

    def run(self):
        if not pikepdf:
            return

        pdf_path = selecionar_arquivo("Selecione o PDF", [("Arquivos PDF", "*.pdf")])
        if not pdf_path:
            return

        diretorio_saida = selecionar_diretorio("Selecione onde salvar o arquivo gerado")
        if not diretorio_saida:
            return

        nome_original = os.path.splitext(os.path.basename(pdf_path))[0]
        nome_saida = f"{nome_original}_full_source.js"
        caminho_saida = os.path.join(diretorio_saida, nome_saida)

        print(f"\n[+] Processando: {nome_original}...")
        
        output_buffer = []
        
        # Header
        output_buffer.append("/**")
        output_buffer.append(f" * EXTRAÇÃO MONOLÍTICA DE JAVASCRIPT")
        output_buffer.append(f" * Fonte: {nome_original}")
        output_buffer.append(f" * Data: {datetime.datetime.now()}")
        output_buffer.append(" */")

        try:
            with pikepdf.open(pdf_path) as pdf:
                # 1. Globais
                self._add_section_header("1. GLOBAL / DOCUMENT LEVEL SCRIPTS", output_buffer)
                try:
                    # Tenta acessar Names -> JavaScript de forma segura
                    if "/Names" in pdf.Root and "/JavaScript" in pdf.Root.Names:
                        js_names = pdf.Root.Names.JavaScript
                        if "/Names" in js_names:
                            names_array = js_names.Names
                            for i in range(0, len(names_array), 2):
                                s_name = str(names_array[i])
                                js_obj = names_array[i+1]
                                if "/JS" in js_obj:
                                    code = self._resolve_js(js_obj.JS)
                                    self._add_block("Global Script", s_name, None, code, output_buffer)
                except Exception:
                    pass

                # 2. OpenAction
                self._add_section_header("2. OPEN ACTION", output_buffer)
                try:
                    if "/OpenAction" in pdf.Root:
                        oa = pdf.Root.OpenAction
                        if "/JS" in oa:
                            code = self._resolve_js(oa.JS)
                            self._add_block("OpenAction", "Document_Open", "Run", code, output_buffer)
                except Exception:
                    pass

                # 3. Campos
                self._add_section_header("3. ACROFORM FIELDS", output_buffer)
                try:
                    if "/AcroForm" in pdf.Root and "/Fields" in pdf.Root.AcroForm:
                        self.field_index = [] # Inicia lista de campos para o índice
                        self._recurse_fields(pdf.Root.AcroForm.Fields, output_buffer)
                except Exception:
                    pass

                # 4. Páginas e Anotações (Widgets soltos)
                self._add_section_header("4. PAGES & ANNOTATIONS", output_buffer)
                self._scan_pages(pdf, output_buffer)

                # INSERIR ÍNDICE NO INÍCIO (Seção 0)
                if hasattr(self, 'field_index') and self.field_index:
                    idx_buffer = []
                    self._add_section_header("0. ÍNDICE DE CAMPOS ENCONTRADOS", idx_buffer)
                    idx_buffer.append("/** LISTA DE CAMPOS:")
                    for idx, f_name in enumerate(sorted(self.field_index), 1):
                        idx_buffer.append(f" * {idx:03d}. {f_name}")
                    idx_buffer.append(" */")
                    # Insere logo após o cabeçalho inicial (índice 5 no array original)
                    output_buffer[5:5] = idx_buffer

            # Salvar
            with open(caminho_saida, "w", encoding="utf-8") as f:
                f.write("\n".join(output_buffer))
            
            print(f"\n[SUCESSO] Arquivo salvo em:\n{caminho_saida}")
            print(f"Linhas geradas: {len(output_buffer)}")
            print("="*50)

        except Exception as e:
            print(f"\n[ERRO] Falha na extração: {e}")
