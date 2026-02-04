# -*- coding: utf-8 -*-

"""
Módulo de configuração para o Toolkit.
Armazena constantes e a estrutura do menu.
"""

# --- CONFIGURAÇÕES PARA O COMPILADOR DE CÓDIGO (FERRAMENTA 1) ---
EXTENSOES_CODIGO = [
    '.html', '.htm', '.css', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte',
    '.py', '.php', '.java', '.cs', '.go', '.rb', '.rs', '.mjs', '.sql',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.md', '.sh', '.bat',
    '.c', '.cpp', '.h', '.hpp'
]

PASTAS_A_IGNORAR = [
    'node_modules', '.git', 'dist', 'build', '__pycache__',
    'venv', 'target', 'bin', 'obj', 'temp', 'tmp'
]

ARQUIVOS_A_IGNORAR = [
    'package-lock.json', 
    'yarn.lock',         
    '.env',              
    'eng.traineddata',
    'por.traineddata'
]

# Limite para a Opção 1 (Compilar Códigos)
LIMITE_PALAVRAS_COMPILADOR = 300000
MAX_ARQUIVOS_SAIDA = 99 

# --- ESTRUTURA DO MENU DINÂMICO ---

TOOLKIT_FEATURES = {
    '1': {
        "description": "Compilar Códigos-Fontes em arquivos de texto",
        "module": "features.code_compiler",
        "class": "CodeCompiler"
    },
    '2': {
        "description": "Extrair Metadados de um Banco de Dados",
        "module": "features.db_extractor",
        "class": "DbExtractor"
    },
    '3': {
        "description": "Coletar Metadados de Diretórios",
        "module": "features.dir_metadata",
        "class": "DirMetadataCollector"
    },
    '4': {
        "description": "[DIAGNÓSTICO] Encontrar arquivos de código muito grandes",
        "module": "features.large_file_finder",
        "class": "LargeFileFinder"
    },
    '5': {
        "description": "Extrair Texto de PDF para Markdown",
        "module": "features.pdf_extractor",
        "class": "PdfExtractor"
    },
    '6': {
        "description": "Gerar Token de Segurança Criptograficamente Seguro",
        "module": "features.token_generator",
        "class": "TokenGeneratorFeature"
    },
    '7': {
        "description": "Converter Imagem para .webp",
        "module": "features.image_converter",
        "class": "ImageConverter"
    },
    '8': {
        "description": "Extrair Código-Fonte JS de PDF",
        "module": "features.pdf_js_extractor",
        "class": "PdfJsExtractor"
    },
    '9': {
        "description": "Executar Scripts MySQL em Lote (Restore)",
        "module": "features.mysql_runner",
        "class": "MySQLBatchRunner"
    },
    '10': {
        "description": "Migrador Firebird (2.5 -> 4.0 via Docker)",
        "module": "features.firebird_migrator",
        "class": "FirebirdMigrator"
    }
}
