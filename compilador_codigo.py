# -*- coding: utf-8 -*-

import os
import datetime
import math
import sys

# --- CONFIGURAÇÃO ---
# Adicione ou remova as extensões de arquivo que você deseja processar.
EXTENSOES_CODIGO = [
    # Web Frontend
    '.html', '.htm', '.css', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte',
    # Web Backend / Geral
    '.py', '.php', '.java', '.cs', '.go', '.rb', '.rs', '.mjs',
    # Configuração / Dados
    '.json', '.xml', '.yaml', '.yml', '.toml', '.md', '.sh', '.bat',
    # C / C++
    '.c', '.cpp', '.h', '.hpp',
    # SQL
    '.sql'
]

# --- NOVO: PASTAS A IGNORAR ---
# Adicione aqui os nomes de pastas (diretórios) que você deseja ignorar
# durante a compilação do código.
PASTAS_A_IGNORAR = [
    "ModelosMigracao",
    'node_modules', 
    '.git', 
    'dist', 
    'build', 
    '__pycache__',
    'venv', # Ambientes virtuais Python
    'target', # Ambientes de build Java/Rust
    'bin', 'obj', # Ambientes .NET
    'temp', 'tmp' # Pastas temporárias
]
# --------------------

# --- REGRAS PARA GEMS DO GEMINI ---
# Tamanho máximo do arquivo de saída em bytes (50 MB)
TAMANHO_MAX_BYTES = 50 * 1024 * 1024
# Número máximo de arquivos de saída
MAX_ARQUIVOS_SAIDA = 10
# ---------------------------------

# --- DIRETÓRIO DE SAÍDA ---
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'toolkit'))
try:
    from toolkit.user_config import UserConfigManager
    config = UserConfigManager()
    DIRETORIO_SAIDA = config.get('diretorio_saida', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saida'))
except ImportError:
    DIRETORIO_SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saida')

def extrair_codigo_fonte(diretorio_raiz):
    """
    Percorre um diretório de projeto, lê o conteúdo dos arquivos de código-fonte
    e compila o conteúdo, dividindo-o em vários arquivos de saída se necessário,
    de acordo com as restrições de tamanho e quantidade.

    :param diretorio_raiz: O caminho da pasta do projeto a ser verificada.
    """
    
    # 1. Configuração do arquivo de saída
    nome_pasta_raiz = os.path.basename(os.path.normpath(diretorio_raiz))
    nome_base_saida = f"migrador-{nome_pasta_raiz}_codigo_fonte_compilado"
    
    # 2. Garante que o diretório de saída exista
    os.makedirs(DIRETORIO_SAIDA, exist_ok=True)
    
    print(f"Iniciando a extração de código do projeto em: '{diretorio_raiz}'")
    print(f"Os arquivos de saída serão salvos em: '{DIRETORIO_SAIDA}'")
    print("-" * 100)
    
    # 3. Coleta todo o conteúdo e informações dos arquivos
    conteudo_compilado_list = []
    tamanho_total_bytes = 0
    contador_arquivos = 0
    contador_erros = 0
    
    separador = "-" * 100 # Define o separador uma vez
    
    for root, dirs, files in os.walk(diretorio_raiz):
        # Ignora pastas definidas na lista PASTAS_A_IGNORAR
        dirs[:] = [d for d in dirs if d not in PASTAS_A_IGNORAR]
        
        for nome_arquivo in files:
            # Verifica se a extensão do arquivo está na lista de interesse
            if any(nome_arquivo.lower().endswith(ext) for ext in EXTENSOES_CODIGO):
                caminho_completo = os.path.join(root, nome_arquivo)
                
                try:
                    # Lê o conteúdo do arquivo
                    with open(caminho_completo, "r", encoding="utf-8", errors="ignore") as f_in:
                        conteudo = f_in.read()
                    
                    # CORREÇÃO DEFINITIVA: 
                    # Usa uma variável para o cabeçalho para evitar qualquer multiplicação acidental.
                    cabecalho_arquivo = f"### ARQUIVO: {caminho_completo}\n"
                    
                    bloco_compilado = (
                        separador + "\n" +
                        cabecalho_arquivo +
                        separador + "\n" + # Separador logo abaixo do nome do arquivo
                        f"{conteudo}\n" +   # Conteúdo do arquivo
                        separador + "\n\n" # Separador final
                    )
                    
                    conteudo_compilado_list.append(bloco_compilado)
                    
                    # O tamanho é aproximado, pois a conversão para bytes é mais precisa na hora de salvar,
                    # mas serve para o cálculo de divisão.
                    tamanho_bloco_bytes = len(bloco_compilado.encode('utf-8'))
                    tamanho_total_bytes += tamanho_bloco_bytes
                    
                    contador_arquivos += 1
                    
                except Exception as e:
                    print(f"AVISO: Não foi possível ler o arquivo '{caminho_completo}'. Erro: {e}")
                    contador_erros += 1

    # 4. Cálculo de Divisão
    
    # Adiciona o cabeçalho ao tamanho total (aproximadamente)
    tamanho_cabecalho_bytes = len(separador) + len(cabecalho_arquivo) # Recalcula com o separador
    tamanho_total_bytes += (len(conteudo_compilado_list) * tamanho_cabecalho_bytes)
    
    # Calcula quantos arquivos serão necessários
    num_arquivos_necessarios = math.ceil(tamanho_total_bytes / TAMANHO_MAX_BYTES)

    if num_arquivos_necessarios > MAX_ARQUIVOS_SAIDA:
        print("\n" + "=" * 80)
        print("AVISO: COMPILAÇÃO MUITO GRANDE!")
        print(f"O conteúdo total requereria {num_arquivos_necessarios} arquivos para respeitar o limite de 50MB.")
        print(f"O limite máximo de arquivos é {MAX_ARQUIVOS_SAIDA} para a criação de Gems do Gemini.")
        print("Processo abortado. Considere ignorar mais pastas/arquivos.")
        print("=" * 80)
        return
    
    if tamanho_total_bytes == 0:
        print("\nNenhum arquivo de código-fonte válido encontrado no diretório especificado.")
        return

    # 5. Distribuição e Escrita dos Arquivos
    
    # Divide os blocos de conteúdo igualmente (em termos de quantidade de arquivos)
    blocos_por_arquivo = math.ceil(len(conteudo_compilado_list) / num_arquivos_necessarios)
    
    print(f"\nTamanho total estimado do código: {tamanho_total_bytes / (1024 * 1024):.2f} MB")
    print(f"Dividindo o conteúdo em {num_arquivos_necessarios} arquivo(s) de saída (Máx 50MB/arquivo).")

    for i in range(num_arquivos_necessarios):
        # Define o nome do arquivo de saída com o índice (ex: nome_compilado_01.txt)
        if num_arquivos_necessarios == 1:
            nome_arquivo_saida = f"{nome_base_saida}.txt"
        else:
            nome_arquivo_saida = f"{nome_base_saida}_{i+1:02d}.txt"
            
        caminho_completo_saida = os.path.join(DIRETORIO_SAIDA, nome_arquivo_saida)
        
        # Pega a fatia do conteúdo para este arquivo
        inicio = i * blocos_por_arquivo
        fim = inicio + blocos_por_arquivo
        blocos_do_arquivo = conteudo_compilado_list[inicio:fim]

        try:
            with open(caminho_completo_saida, "w", encoding="utf-8") as f_out:
                # Escreve o cabeçalho do arquivo
                f_out.write(f"# Compilação de código-fonte do projeto: {diretorio_raiz}\n")
                f_out.write(f"# PARTE {i+1} DE {num_arquivos_necessarios}\n")
                f_out.write(f"# Data da extração: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f_out.write("=" * 80 + "\n\n")

                # Escreve os blocos de conteúdo
                for bloco in blocos_do_arquivo:
                    f_out.write(bloco)
                
                print(f"Parte {i+1:02d} salva em: '{caminho_completo_saida}'")

        except IOError as e:
            print(f"ERRO FATAL: Não foi possível criar ou escrever no arquivo de saída '{caminho_completo_saida}'. Erro: {e}")
            return # Aborta em caso de erro de escrita

    # 6. Conclusão
    print("\n" + "=" * 30)
    print("Processo concluído com sucesso!")
    print(f"Total de arquivos de código-fonte processados: {contador_arquivos}")
    print(f"Conteúdo salvo em {num_arquivos_necessarios} arquivo(s) de saída.")
    if contador_erros > 0:
        print(f"Ocorreram {contador_erros} erros ao tentar ler alguns arquivos.")
    print("=" * 30)


if __name__ == "__main__":
    caminho_pasta = input("Por favor, digite o caminho completo da pasta do projeto e pressione Enter: ")

    if os.path.isdir(caminho_pasta):
        # Normaliza o caminho para garantir que os.path.basename funcione corretamente
        caminho_pasta_normalizado = os.path.normpath(caminho_pasta)
        extrair_codigo_fonte(caminho_pasta_normalizado)
    else:
        print(f"Erro: O caminho '{caminho_pasta}' não foi encontrado ou não é uma pasta válida.")
        print("Por favor, execute o script novamente com um caminho correto.")
