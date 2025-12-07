# -*- coding: utf-8 -*-

"""
Ponto de entrada principal para a Ferramenta de Análise e Compilação Unificada.
Este script lê a configuração de ferramentas, exibe um menu dinâmico
e executa a ferramenta selecionada pelo usuário.
"""

import sys
import importlib
from toolkit.config import TOOLKIT_FEATURES

def display_menu():
    """
    Exibe o menu principal, gerado dinamicamente a partir da configuração.
    """
    print("\n" + "=" * 50)
    print("      FERRAMENTA DE ANÁLISE E COMPILAÇÃO UNIFICADA")
    print("=" * 50)
    print("Selecione a função que deseja utilizar:")
    
    # O menu é gerado automaticamente a partir do dicionário de configuração
    for key, feature in TOOLKIT_FEATURES.items():
        print(f"  {key}. {feature['description']}")
    
    print("\n  0. Sair")
    print("-" * 50)

def main():
    """
    Loop principal que gerencia o menu e a execução das ferramentas.
    """
    while True:
        display_menu()
        choice = input("Digite sua opção: ")

        if choice == '0':
            print("Saindo da ferramenta. Até logo!")
            break

        selected_feature = TOOLKIT_FEATURES.get(choice)

        if not selected_feature:
            print("\nOpção inválida. Por favor, tente novamente.")
            input("Pressione Enter para continuar...")
            continue

        try:
            # Importação e execução dinâmica da ferramenta
            module_name = "toolkit." + selected_feature['module']
            class_name = selected_feature['class']

            # Importa o módulo (ex: 'toolkit.features.pdf_extractor')
            feature_module = importlib.import_module(module_name)
            
            # Pega a classe dentro do módulo (ex: PdfExtractor)
            FeatureClass = getattr(feature_module, class_name)
            
            # Cria uma instância da classe e executa seu método 'run'
            instance = FeatureClass()
            instance.run()

        except ImportError as e:
            print(f"\nERRO: Não foi possível carregar a ferramenta. Pode ser uma dependência faltando.")
            print(f"Detalhe do erro: {e}")
        except AttributeError:
            print(f"\nERRO DE CONFIGURAÇÃO: A classe '{class_name}' não foi encontrada no módulo '{module_name}'.")
        except Exception as e:
            print(f"\nERRO INESPERADO: Ocorreu um problema durante a execução.")
            print(f"Detalhe do erro: {e}")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação interrompida pelo usuário. Saindo.")
        sys.exit(0)
