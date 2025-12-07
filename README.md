# Toolkit Unificado de Análise e Compilação

---

## Sumário

Este é um conjunto de ferramentas Python unificadas em uma única interface de linha de comando (CLI) para auxiliar em diversas tarefas de análise de código, metadados e documentos. O projeto foi refatorado para ser modular, escalável e fácil de estender.

---

## Funcionalidades

O Toolkit Unificado oferece as seguintes opções:

1.  **Compilador de Códigos-Fontes**: Consolida múltiplos arquivos de código de um diretório em um ou mais arquivos de texto, respeitando limites de palavras configuráveis.
2.  **Extrator de Metadados de Banco de Dados**: Coleta informações sobre schemas, tabelas e colunas de diversos SGBDs (PostgreSQL, MySQL, SQL Server, Firebird).
3.  **Coletor de Metadados de Diretórios**: Gera um relatório com metadados de todos os arquivos em uma pasta e suas subpastas (tamanho, datas de criação/modificação).
4.  **[DIAGNÓSTICO] Localizador de Arquivos de Código Grandes**: Varre um diretório em busca de arquivos de código que excedem um limite de palavras especificado, útil para identificar arquivos que podem ser problemáticos para análise ou compilação externa.
5.  **Extrator de Texto de PDF para Markdown**: Extrai todo o conteúdo textual de um arquivo PDF e o salva em um arquivo Markdown (`.md`), formatado página por página.

---

## Como Usar

1.  **Instalação de Dependências (veja abaixo)**: Certifique-se de ter as bibliotecas Python necessárias instaladas para as funcionalidades que deseja utilizar.
2.  **Executar o Toolkit**:
    *   Navegue até o diretório `Scripts` onde o `toolkit.bat` está localizado.
    *   Execute o `toolkit.bat` diretamente ou chame-o do terminal (se estiver no seu `PATH`).

    ```bash
    toolkit.bat
    ```
3.  **Navegar pelo Menu**: O programa apresentará um menu. Digite o número da opção desejada e pressione `Enter`.

---

## Instalação e Dependências

Este projeto requer **Python 3.x**.

**Dependências Gerais (para o ambiente Python):**

Para instalar as dependências de funcionalidades específicas, use os comandos `pip install` abaixo:

*   **Para a função "Extrator de Metadados de Banco de Dados" (Opção 2):**
    ```bash
    pip install SQLAlchemy "psycopg2-binary" "mysql-connector-python" "pyodbc" "fdb"
    ```
*   **Para a função "Extrator de Texto de PDF para Markdown" (Opção 5):**
    ```bash
    pip install PyMuPDF
    ```

---

## Estrutura do Projeto

O projeto foi refatorado para uma estrutura modular, visando facilitar a manutenção e a expansão:

```
Scripts/
├── toolkit.bat                   # Ponto de entrada para executar o Toolkit
├── README.md                     # Este arquivo
└── toolkit/                      # Pacote Python principal
    ├── __init__.py               # Indica que 'toolkit' é um pacote Python
    ├── main.py                   # Lógica principal: exibe o menu e executa as ferramentas
    ├── utils.py                  # Funções utilitárias compartilhadas (seleção de diretórios, formatação)
    ├── config.py                 # Configurações globais e definição do menu dinâmico
    └── features/                 # Sub-pacote contendo cada ferramenta como um módulo/classe
        ├── __init__.py           # Indica que 'features' é um sub-pacote
        ├── code_compiler.py      # Implementação da ferramenta de compilação de código
        ├── db_extractor.py       # Implementação da ferramenta de extração de metadados de DB
        ├── dir_metadata.py       # Implementação da ferramenta de coleta de metadados de diretórios
        ├── large_file_finder.py  # Implementação da ferramenta de diagnóstico de arquivos grandes
        └── pdf_extractor.py      # Implementação da ferramenta de extração de PDF
```

---

## Como Adicionar Novas Ferramentas

Graças à sua estrutura modular e ao menu dinâmico, adicionar novas ferramentas é um processo simples:

1.  **Crie um novo arquivo Python** para a sua ferramenta dentro do diretório `toolkit/features/`.
2.  Dentro deste arquivo, **implemente sua ferramenta como uma classe** que contenha um método `run()`. Por exemplo:

    ```python
    # toolkit/features/minha_nova_ferramenta.py
    class MinhaNovaFerramenta:
        def __init__(self):
            print("Iniciando minha nova ferramenta!")
        
        def run(self):
            # Sua lógica aqui
            print("Minha nova ferramenta foi executada com sucesso.")
    ```
3.  **Adicione uma entrada para sua ferramenta** no dicionário `TOOLKIT_FEATURES` em `toolkit/config.py`. Certifique-se de que a `key` seja um número sequencial único e aponte para o módulo e a classe corretos:

    ```python
    # toolkit/config.py
    TOOLKIT_FEATURES = {
        # ... outras ferramentas
        '6': { # Novo número de opção
            "description": "Minha Nova Ferramenta Incrível",
            "module": "features.minha_nova_ferramenta", # Nome do arquivo sem .py
            "class": "MinhaNovaFerramenta"              # Nome da classe
        }
    }
    ```
4.  O menu principal (`main.py`) detectará automaticamente a nova ferramenta e a exibirá para o usuário.

---

## Autor

*   **Cássio Rodolfo Alves de Carvalho Pinto/DeMaria Software** (com base nos scripts originais)
*   **Versão do Toolkit**: 3.5.0
*   **Data da Refatoração**: 2025-12-07
