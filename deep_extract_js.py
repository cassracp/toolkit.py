# -*- coding: utf-8 -*-

"""
Deep PDF JS Extractor - Digital Forensics Tool
Busca agressiva e recursiva de scripts JavaScript em estruturas PDF 1.7+
"""

import os
import pikepdf
import sys
import tkinter as tk
from tkinter import filedialog
from datetime import datetime

def select_file():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Selecione o PDF para análise forense", filetypes=[("PDF Files", "*.pdf")])
    root.destroy()
    return path

def select_folder():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askdirectory(title="Selecione a pasta para exportação dos scripts")
    root.destroy()
    return path

class DeepExtractor:
    def __init__(self, pdf_path, output_dir):
        self.pdf_path = pdf_path
        self.output_dir = os.path.join(output_dir, "deep_extracted_js")
        self.pdf = pikepdf.open(pdf_path)
        self.extracted_count = 0
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def resolve_js(self, obj):
        """Resolve o conteúdo de JS seja String ou Stream."""
        try:
            if isinstance(obj, pikepdf.Stream):
                return obj.read_bytes().decode('utf-8', errors='replace')
            return str(obj)
        except Exception:
            return None

    def save_script(self, name, content, source):
        if not content or not content.strip():
            return
        
        filename = f"{name}.js".replace("/", "_").replace("\\", "_").replace(" ", "_")
        target_path = os.path.join(self.output_dir, filename)
        
        header = f"/**\n * Source: {source}\n * Date: {datetime.now()}\n * Forensic extraction from: {os.path.basename(self.pdf_path)}\n */\n\n"
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(header + content)
        
        print(f"[+] Extraído: {filename}")
        self.extracted_count += 1

    def scan_document_level(self):
        """Busca em Root -> Names -> JavaScript -> Names"""
        print("[*] Escaneando Document Level Scripts...")
        try:
            if "/Names" in self.pdf.root and "/JavaScript" in self.pdf.root.Names:
                js_names = self.pdf.root.Names.JavaScript
                if "/Names" in js_names:
                    # O PDF armazena em pares [Nome, Objeto]
                    names_array = js_names.Names
                    for i in range(0, len(names_array), 2):
                        name = str(names_array[i])
                        js_obj = names_array[i+1]
                        if "/JS" in js_obj:
                            content = self.resolve_js(js_obj.JS)
                            self.save_script(f"Global_{name}", content, f"Document Level Script: {name}")
        except Exception as e:
            print(f"[!] Erro no Document Level: {e}")

    def scan_acroforms(self):
        """Busca recursiva em Root -> AcroForm -> Fields"""
        print("[*] Escaneando AcroForm Fields...")
        try:
            if "/AcroForm" in self.pdf.root and "/Fields" in self.pdf.root.AcroForm:
                fields = self.pdf.root.AcroForm.Fields
                self._recurse_fields(fields)
        except Exception as e:
            print(f"[!] Erro nos AcroForms: {e}")

    def _recurse_fields(self, fields):
        for field in fields:
            field_name = str(field.get("/T", "UnknownField"))
            
            # Ações diretas
            if "/JS" in field:
                content = self.resolve_js(field.JS)
                self.save_script(f"Field_{field_name}_Direct", content, f"Field Direct Action: {field_name}")
            
            # Additional Actions (AA)
            if "/AA" in field:
                aa = field.AA
                for key in aa.keys():
                    # Chaves comuns: /C, /V, /F, /K etc
                    event_name = str(key).replace("/", "")
                    action_obj = aa[key]
                    if "/JS" in action_obj:
                        content = self.resolve_js(action_obj.JS)
                        self.save_script(f"Field_{field_name}_{event_name}", content, f"Field AA ({event_name}): {field_name}")

            # Recursão para sub-campos (Kids)
            if "/Kids" in field:
                self._recurse_fields(field.Kids)

    def scan_openaction(self):
        """Busca em Root -> OpenAction"""
        print("[*] Escaneando OpenAction...")
        try:
            if "/OpenAction" in self.pdf.root:
                oa = self.pdf.root.OpenAction
                if "/JS" in oa:
                    content = self.resolve_js(oa.JS)
                    self.save_script("OpenAction_Initial", content, "Document OpenAction")
        except Exception as e:
            print(f"[!] Erro no OpenAction: {e}")

    def scan_pages_and_annots(self):
        """Busca em Page -> AA e Page -> Annots"""
        print("[*] Escaneando Páginas e Anotações...")
        try:
            for i, page in enumerate(self.pdf.pages):
                page_num = i + 1
                
                # Page Level Actions
                if "/AA" in page:
                    aa = page.AA
                    for key in aa.keys():
                        event_name = str(key).replace("/", "")
                        if "/JS" in aa[key]:
                            content = self.resolve_js(aa[key].JS)
                            self.save_script(f"Page{page_num}_{event_name}", content, f"Page {page_num} AA ({event_name})")

                # Annotations (Widgets são onde ficam a maioria dos scripts de campos se não estiverem no AcroForm)
                if "/Annots" in page:
                    for j, annot in enumerate(page.Annots):
                        annot_id = f"P{page_num}_A{j}"
                        # Nome do campo se for um Widget
                        field_name = str(annot.get("/T", annot_id))
                        
                        # Ações diretas (/A)
                        if "/A" in annot and "/JS" in annot.A:
                            content = self.resolve_js(annot.A.JS)
                            self.save_script(f"Annot_{field_name}_Action", content, f"Annotation Action: {field_name} (Page {page_num})")
                        
                        # Additional Actions (/AA)
                        if "/AA" in annot:
                            aa = annot.AA
                            for key in aa.keys():
                                event_name = str(key).replace("/", "")
                                if "/JS" in aa[key]:
                                    content = self.resolve_js(aa[key].JS)
                                    self.save_script(f"Annot_{field_name}_{event_name}", content, f"Annotation AA ({event_name}): {field_name} (Page {page_num})")
        except Exception as e:
            print(f"[!] Erro no Scan de Páginas/Anotações: {e}")

    def exhaustive_object_scan(self):
        """Scan 'Brute Force' em todos os objetos do PDF em busca de dicionários de JS"""
        print("[*] Iniciando Scan Exaustivo de todos os objetos (Brute-Force)...")
        found_ids = set()
        
        try:
            for obj in self.pdf.objects:
                if not isinstance(obj, pikepdf.Dictionary):
                    continue
                
                # Evita re-extrair o que já foi pego pela estrutura
                obj_id = str(obj.objgen) if hasattr(obj, 'objgen') else str(id(obj))
                
                is_target = False
                if obj.get("/S") == "/JavaScript" and "/JS" in obj:
                    is_target = True
                elif obj.get("/Type") == "/JavaScript" and "/JS" in obj:
                    is_target = True
                elif "/JS" in obj and "/S" not in obj:
                    # Alguns campos tem /JS direto sem o tipo /S definido
                    is_target = True

                if is_target:
                    content = self.resolve_js(obj.JS)
                    if content and content.strip():
                        # Hash simples do conteúdo para evitar duplicatas exatas
                        content_hash = hash(content)
                        if content_hash not in found_ids:
                            self.save_script(f"Orphan_Object_{obj_id}", content, f"Heuristic Scan - Object: {obj_id}")
                            found_ids.add(content_hash)
        except Exception as e:
            print(f"[!] Erro no Scan Exaustivo: {e}")

    def run(self):
        print(f"\n--- Iniciando Análise Forense Agressiva de {os.path.basename(self.pdf_path)} ---")
        self.scan_document_level()
        self.scan_openaction()
        self.scan_acroforms()
        self.scan_pages_and_annots()
        self.exhaustive_object_scan()
        print(f"\n--- Análise concluída. {self.extracted_count} scripts extraídos em: {self.output_dir} ---")

if __name__ == "__main__":
    p_path = select_file()
    if not p_path:
        print("Nenhum arquivo selecionado.")
        sys.exit()
        
    o_dir = select_folder()
    if not o_dir:
        print("Nenhuma pasta de saída selecionada.")
        sys.exit()

    try:
        extractor = DeepExtractor(p_path, o_dir)
        extractor.run()
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
