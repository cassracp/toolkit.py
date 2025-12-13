# -*- coding: utf-8 -*-

"""
Ponto de entrada principal para a Ferramenta de Análise e Compilação Unificada.
Este script lê a configuração de ferramentas, exibe um menu dinâmico
e executa a ferramenta selecionada pelo usuário.
"""

import sys
import importlib
import subprocess
from .config import TOOLKIT_FEATURES
from colorama import Fore, Style, init

# Inicializa o colorama
init(autoreset=True)

# --- LÓGICA DE VERIFICAÇÃO DE ATUALIZAÇÃO ---
UPDATE_AVAILABLE = False
UPDATE_EXIT_CODE = 100

def check_for_updates():
    """
    Verifica se a branch local está atrás da branch remota.
    Retorna True se houver atualizações, False caso contrário.
    """
    try:
        # 1. Busca as atualizações mais recentes do remote sem aplicá-las.
        # Timeout para não prender a aplicação se a internet estiver lenta.
        subprocess.run(["git", "fetch"], timeout=5, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 2. Verifica o status. A saída de 'git status -uno' conterá 'Your branch is behind'
        status_output = subprocess.check_output(["git", "status", "-uno"], text=True, encoding='utf-8')
        
        return "Your branch is behind" in status_output

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        # Falha se o git não estiver instalado, não for um repo git,
        # ou se a rede falhar. Em qualquer caso, apenas ignoramos a verificação.
        return False

# --- FUNÇÕES DE MENU E EXECUÇÃO ---

def display_menu():
    """
    Exibe o menu principal, gerado dinamicamente a partir da configuração.
    """
    global UPDATE_AVAILABLE
    if UPDATE_AVAILABLE:
        print("\n" + Fore.YELLOW + "=" * 60)
        print("  AVISO: Uma nova versão do toolkit está disponível!")
        print("  Recomenda-se atualizar para a versão mais recente." + Style.RESET_ALL)
        print(Fore.YELLOW + "=" * 60)

    print("\n" + "=" * 50)
    print("      FERRAMENTA DE ANÁLISE E COMPILAÇÃO UNIFICADA")
    print("=" * 50)
    print("Selecione a função que deseja utilizar:")
    
    for key, feature in TOOLKIT_FEATURES.items():
        print(f"  {key}. {feature['description']}")
    
    print("-" * 50)
    if UPDATE_AVAILABLE:
        print(Fore.GREEN + "  0. Sair e Atualizar Automaticamente")
        print(Style.RESET_ALL + "\n  q. Sair (sem atualizar)")
    else:
        print("\n  0. Sair")
    print("-" * 50)

def main():
    """
    Loop principal que gerencia o menu e a execução das ferramentas.
    """
    global UPDATE_AVAILABLE
    UPDATE_AVAILABLE = check_for_updates()

    while True:
        display_menu()
        choice = input("Digite sua opção: ").lower()

        # Lógica de saída
        if choice == 'q':
            print("Saindo da ferramenta. Até logo!")
            break
        
        if choice == '0':
            if UPDATE_AVAILABLE:
                print("Sinalizando para o launcher iniciar a atualização...")
                sys.exit(UPDATE_EXIT_CODE)
            else:
                print("Saindo da ferramenta. Até logo!")
                break

        selected_feature = TOOLKIT_FEATURES.get(choice)

        if not selected_feature:
            print(Fore.RED + "\nOpção inválida. Por favor, tente novamente.")
            input("Pressione Enter para continuar...")
            continue

        try:
            module_name = "toolkit." + selected_feature['module']
            class_name = selected_feature['class']
            feature_module = importlib.import_module(module_name)
            FeatureClass = getattr(feature_module, class_name)
            instance = FeatureClass()
            instance.run()

        except ImportError as e:
            print(Fore.RED + f"\nERRO: Não foi possível carregar a ferramenta. Pode ser uma dependência faltando.")
            print(f"Detalhe do erro: {e}")
        except AttributeError:
            print(Fore.RED + f"\nERRO DE CONFIGURAÇÃO: A classe '{class_name}' não foi encontrada no módulo '{module_name}'.")
        except Exception as e:
            print(Fore.RED + f"\nERRO INESPERADO: Ocorreu um problema durante a execução.")
            print(f"Detalhe do erro: {e}")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação interrompida pelo usuário. Saindo.")
        sys.exit(0)
