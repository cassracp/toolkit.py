# -*- coding: utf-8 -*-

import os
import time
import re
from toolkit.utils import selecionar_diretorio

class OilFantasyScraper:
    def __init__(self):
        print("\n--- Raspador do Manifesto Oil Fantasy ---")
        self.index_url = "https://oilfantasy.blogspot.com/p/manifesto-oil-fantasy.html"

    def _check_dependencies(self):
        try:
            import requests
            from bs4 import BeautifulSoup
            return requests, BeautifulSoup
        except ImportError:
            print("\n[ERRO] Dependências ausentes!")
            print("Para usar esta ferramenta, instale as bibliotecas necessárias:")
            print("pip install requests beautifulsoup4")
            return None, None

    def _clean_text(self, soup_element):
        """
        Limpa e converte o HTML do corpo do post para um formato próximo ao Markdown/Texto Limpo.
        """
        if not soup_element:
            return ""

        # Remove scripts e estilos
        for script in soup_element(["script", "style"]):
            script.decompose()

        text_parts = []
        
        # Itera sobre os elementos para tentar preservar alguma estrutura
        for element in soup_element.descendants:
            if element.name in ['h1', 'h2', 'h3']:
                text_parts.append(f"\n## {element.get_text(strip=True)}\n")
            elif element.name == 'p':
                text_parts.append(f"{element.get_text(strip=True)}\n")
            elif element.name == 'li':
                text_parts.append(f"- {element.get_text(strip=True)}")
            elif element.name == 'br':
                text_parts.append("\n")
        
        # Fallback simples se a iteração acima não capturar bem, 
        # ou apenas pega o texto cru se preferir.
        # Mas vamos usar o get_text do soup com separador para garantir.
        
        text = soup_element.get_text(separator="\n\n", strip=True)
        return text

    def run(self):
        requests, BeautifulSoup = self._check_dependencies()
        if not requests:
            return

        print(f"Alvo: {self.index_url}")
        print("Este script irá acessar o índice, coletar os links dos artigos e gerar um arquivo único.")

        diretorio_saida = selecionar_diretorio("Selecione a pasta para SALVAR o arquivo compilado (.md)")
        if not diretorio_saida:
            print("Operação cancelada.")
            return

        arquivo_saida = os.path.join(diretorio_saida, "Oil_Fantasy_Compilado.md")

        try:
            # 1. Obter a página de índice
            print("Acessando índice...")
            response = requests.get(self.index_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # 2. Encontrar a área de conteúdo (post-body geralmente no Blogspot)
            content_div = soup.find(class_='post-body')
            if not content_div:
                # Tenta fallback comum
                content_div = soup.find(class_='entry-content')

            if not content_div:
                print("ERRO: Não foi possível encontrar o corpo do manifesto no HTML.")
                return

            # 3. Extrair links válidos
            links_encontrados = []
            # Adiciona o próprio manifesto como primeiro item, se desejar, ou apenas os links.
            # O usuário pediu "raspar os dados de todas as paginas do manifesto... tendo o link para todos os artigos"
            # Vamos assumir que ele quer o conteúdo dos links listados.
            
            for a_tag in content_div.find_all('a', href=True):
                href = a_tag['href']
                text = a_tag.get_text(strip=True)
                
                # Filtros básicos para garantir que é um artigo do blog e não link externo ou lixo
                if "oilfantasy.blogspot.com" in href and "html" in href:
                    if href not in [x['href'] for x in links_encontrados]: # Evita duplicatas
                        links_encontrados.append({'href': href, 'title': text})

            print(f"Encontrados {len(links_encontrados)} artigos para processar.")
            
            # 4. Processar cada link
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                f.write("# Oil Fantasy - Compilado\n\n")
                f.write(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Fonte Original: {self.index_url}\n\n")
                f.write("---\n\n")

                for i, item in enumerate(links_encontrados):
                    url = item['href']
                    titulo_link = item['title']
                    
                    print(f"[{i+1}/{len(links_encontrados)}] Processando: {titulo_link}...")
                    
                    try:
                        art_response = requests.get(url)
                        art_soup = BeautifulSoup(art_response.content, 'html.parser')
                        
                        # Tenta pegar o título real do post
                        post_title = art_soup.find(class_='post-title')
                        if post_title:
                            final_title = post_title.get_text(strip=True)
                        else:
                            final_title = titulo_link

                        # Pega o corpo
                        post_body = art_soup.find(class_='post-body')
                        if not post_body:
                            post_body = art_soup.find(class_='entry-content')
                        
                        texto_artigo = self._clean_text(post_body) if post_body else "[Conteúdo não detectado]"

                        # Escreve no arquivo
                        f.write(f"# {final_title}\n\n")
                        f.write(f"*Link original: {url}*\n\n")
                        f.write(texto_artigo)
                        f.write("\n\n---\n\n")
                        
                        # Pausa para ser gentil com o servidor
                        time.sleep(1)

                    except Exception as e:
                        print(f"  ERRO ao processar {url}: {e}")
                        f.write(f"# Erro ao ler: {titulo_link}\nLink: {url}\nErro: {str(e)}\n\n---\n\n")

            print("\n" + "=" * 30)
            print("Processo concluído!")
            print(f"Arquivo salvo em: {arquivo_saida}")
            print("=" * 30)

        except Exception as e:
            print(f"ERRO FATAL: {e}")
