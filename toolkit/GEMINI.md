# Diretrizes do Gemini CLI para o Projeto Toolkit

Este documento contém diretrizes específicas para o Gemini CLI ao interagir com o projeto Toolkit.

## Desenvolvimento de Novas Funcionalidades

Qualquer nova funcionalidade deve ser implementada de maneira modular/apartada para manter o código organizado, escalável e de fácil manutenção. Isso significa:
-   Cada nova ferramenta deve residir em seu próprio arquivo Python dentro do diretório `features/`.
-   As ferramentas devem ser encapsuladas em classes com um método `run()` para execução.
-   A integração no menu principal deve ser feita através do arquivo `config.py`, sem modificar diretamente a lógica de `main.py` para cada nova ferramenta.

---
Este arquivo é gerenciado pelo Gemini CLI. Não deve ser deletado.
