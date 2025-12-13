# Toolkit de Análise e Compilação Unificada

Este projeto é um toolkit Python projetado para oferecer uma variedade de ferramentas de análise, compilação e utilitários. Com uma estrutura modular, permite a fácil adição de novas funcionalidades, mantendo o código organizado e de fácil manutenção.

## Funcionalidades Atuais

O toolkit apresenta um menu dinâmico que exibe as ferramentas disponíveis, permitindo ao usuário selecionar a função desejada. As funcionalidades incluem:

1.  **Compilador de Códigos-Fontes:** Converte múltiplos arquivos de código-fonte em um único arquivo de texto, útil para análise ou envio para LLMs.
2.  **Extrator de Metadados de Banco de Dados:** Coleta informações sobre esquemas de bancos de dados.
3.  **Coletor de Metadados de Diretórios:** Gera um resumo da estrutura e conteúdo de diretórios.
4.  **Localizador de Arquivos Grandes:** Ajuda a identificar arquivos de código excessivamente grandes.
5.  **Extrator de Texto de PDF para Markdown:** Converte o conteúdo textual de PDFs para o formato Markdown.
6.  **Gerador de Token de Segurança:** Cria tokens criptograficamente seguros para uso em APIs, etc.

## Como Executar

Para rodar o toolkit, certifique-se de ter Python 3.x instalado.

1.  **Clone o repositório:**
    `git clone <URL_DO_SEU_REPOSITORIO>`
    `cd toolkit`

2.  **Execute o script principal:**
    `python main.py`

    O script exibirá um menu interativo onde você poderá escolher a ferramenta a ser utilizada.

## Estrutura do Projeto

O projeto é organizado da seguinte forma:

-   `main.py`: O ponto de entrada principal, que gerencia o menu e a execução das ferramentas.
-   `config.py`: Contém as configurações globais e a definição das ferramentas para o menu dinâmico.
-   `utils.py`: Funções utilitárias comuns a diversas ferramentas.
-   `features/`: Diretório que contém as implementações de cada ferramenta. Cada ferramenta é geralmente uma classe separada, facilitando a modularidade.

## Como Adicionar Novas Funcionalidades

Novas funcionalidades devem ser implementadas de maneira modular:

1.  Crie um novo arquivo Python dentro do diretório `features/` (ex: `features/nova_ferramenta.py`).
2.  Defina uma classe dentro desse arquivo que contenha um método `run()`. Este método será o ponto de entrada da sua ferramenta.
3.  Adicione uma entrada para a sua nova ferramenta no dicionário `TOOLKIT_FEATURES` em `config.py`, especificando a descrição, o módulo e a classe.

---
Desenvolvido por Gemini CLI.
