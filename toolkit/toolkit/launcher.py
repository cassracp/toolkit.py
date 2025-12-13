# -*- coding: utf-8 -*- 
import sys
import os
import subprocess
from colorama import Fore, Style, init

# Inicializa o colorama
init(autoreset=True)

UPDATE_EXIT_CODE = 100

def run_from_source():
    """
    Lógica original para rodar a partir do código fonte (com suporte a atualizações).
    """
    while True:
        # Assume que o main.py está no mesmo diretório deste script
        main_script_path = os.path.join(os.path.dirname(__file__), 'main.py')
        
        # Executa o main.py em um subserviço
        # sys.executable aponta para o python.exe em execução
        process = subprocess.run([sys.executable, main_script_path])

        if process.returncode == UPDATE_EXIT_CODE:
            print("\n" + "="*50)
            print("\nIniciando a atualização automática...\n")
            print("="*50)
            
            try:
                update_process = subprocess.run(
                    "git pull && pip install --upgrade .", 
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )

                if update_process.returncode == 0:
                    print("\n" + Fore.GREEN + "\nAtualização concluída com sucesso!\n")
                    print("Reiniciando a ferramenta...")
                    input("Pressione Enter para continuar...")
                    continue
                else:
                    print("\n" + Fore.RED + "\nOcorreu um erro durante a atualização.\n")
                    print(update_process.stdout)
                    print(update_process.stderr)
            except Exception as e:
                print("\n" + Fore.RED + f"\nErro ao tentar atualizar: {e}")
            
            print("--------------------------")
            input("Pressione Enter para sair.")
            break
        else:
            break

def main():
    """
    Ponto de entrada do Launcher.
    """
    # Verifica se está rodando como executável compilado (Frozen)
    if getattr(sys, 'frozen', False):
        # Modo Compilado: Não suporta auto-update via git/pip
        # Importa e roda diretamente para evitar loop de subprocessos
        try:
            # Tenta importar main do pacote 'toolkit' (estrutura empacotada)
            from toolkit.main import main as app_main
            app_main()
        except ImportError:
            # Fallback: Tenta importar main localmente (caso a estrutura seja diferente)
            try:
                from main import main as app_main
                app_main()
            except ImportError as e:
                print(Fore.RED + f"Erro fatal: Não foi possível carregar o main.py no modo Frozen: {e}")
                input("Pressione Enter para sair...")
    else:
        # Modo Script (Source): Usa o loop de subprocessos para permitir updates
        run_from_source()

if __name__ == "__main__":
    main()