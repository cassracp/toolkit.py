# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import shutil
import getpass
from toolkit.utils import limpar_tela, aguardar_enter

class MySQLBatchRunner:
    """
    Ferramenta para executar múltiplos scripts SQL em lote usando o cliente nativo mysql.exe.
    """

    def run(self):
        limpar_tela()
        print("=== Executor de Scripts MySQL em Lote ===")
        print("Esta ferramenta permite restaurar/executar múltiplos arquivos .sql de uma pasta")
        print("diretamente no banco de dados, mantendo a ordem alfabética.")
        print("-" * 60)

        # 1. Obter credenciais e configurações
        host = input("Host (padrão: localhost): ").strip() or "localhost"
        port = input("Porta (padrão: 3308): ").strip() or "3308"
        user = input("Usuário (padrão: root): ").strip() or "root"
        password = getpass.getpass("Senha: ").strip()
        database = input("Nome do Banco de Dados alvo: ").strip()

        if not database:
            print("[ERRO] O nome do banco de dados é obrigatório.")
            aguardar_enter()
            return

        # 2. Localizar a pasta dos scripts
        scripts_dir = input("Caminho da pasta com os scripts .sql: ").strip()
        if not os.path.isdir(scripts_dir):
            print(f"[ERRO] Diretório não encontrado: {scripts_dir}")
            aguardar_enter()
            return

        # 3. Localizar o binário mysql.exe
        mysql_path = self._find_mysql_binary()
        if not mysql_path:
            print("[ERRO] Não foi possível localizar o executável do MySQL.")
            aguardar_enter()
            return

        print(f"\n[INFO] Usando executável: {mysql_path}")
        print(f"[INFO] Varrendo diretório: {scripts_dir} ...")

        # 4. Coletar arquivos .sql recursivamente
        sql_files = []
        for root, dirs, files in os.walk(scripts_dir):
            for file in files:
                if file.lower().endswith('.sql'):
                    full_path = os.path.join(root, file)
                    sql_files.append(full_path)

        if not sql_files:
            print("[AVISO] Nenhum arquivo .sql encontrado na pasta especificada.")
            aguardar_enter()
            return

        # Ordenar para garantir execução sequencial correta (ex: 01_..., 02_...)
        sql_files.sort()

        print(f"[INFO] Encontrados {len(sql_files)} scripts para execução.")
        confirm = input("Deseja iniciar a execução? (S/N): ").strip().lower()
        if confirm != 's':
            print("Operação cancelada.")
            aguardar_enter()
            return

        # 5. Executar scripts
        sucessos = 0
        erros = 0

        for file_path in sql_files:
            print(f"\nExecutando: {os.path.basename(file_path)} ...")
            try:
                # Construção do comando: mysql -h... -u... -p... database < file
                # Usamos stdin para passar o conteúdo do arquivo, que é mais seguro e robusto
                # do que passar o caminho do arquivo para o mysql (evita problemas de path com espaços/encoding)
                
                # Nota: A senha é passada diretamente. Em ambientes muito restritos,
                # isso pode gerar aviso de segurança no stderr, mas é funcional.
                cmd = [
                    mysql_path,
                    f"-h{host}",
                    f"-P{port}",
                    f"-u{user}",
                    f"-p{password}",
                    database,
                    "--default-character-set=utf8mb4" # Força UTF-8 para evitar erros de encoding comuns
                ]

                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    # Executa o processo passando o arquivo como entrada padrão (stdin)
                    result = subprocess.run(
                        cmd,
                        stdin=f,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                if result.returncode == 0:
                    print("  -> SUCESSO")
                    sucessos += 1
                else:
                    print(f"  -> FALHA (Código {result.returncode})")
                    print(f"  Erro: {result.stderr}")
                    erros += 1

            except Exception as e:
                print(f"  -> ERRO CRÍTICO: {str(e)}")
                erros += 1

        print("-" * 60)
        print(f"Processamento concluído.")
        print(f"Sucessos: {sucessos}")
        print(f"Erros: {erros}")
        aguardar_enter()

    def _find_mysql_binary(self):
        """
        Tenta localizar o mysql.exe usando config do usuário, PATH, ou solicitando ao usuário.
        """
        from toolkit.user_config import UserConfigManager
        config = UserConfigManager()
        
        # 1. Tentar ler da configuração do usuário
        saved_path = config.get('mysql_path')
        if saved_path and os.path.exists(saved_path):
            return saved_path

        # 2. Tentar pelo PATH do sistema
        path = shutil.which("mysql")
        if path:
            config.set('mysql_path', path)
            return path

        # 3. Solicitar ao usuário se não encontrar
        print("\n[AVISO] 'mysql.exe' não encontrado automaticamente (nem no config, nem no PATH).")
        user_path = input("Por favor, digite o caminho completo para o arquivo mysql.exe (será salvo para as próximas vezes): ").strip()
        
        # Remove aspas caso o usuário tenha copiado como "Caminho"
        user_path = user_path.replace('"', '')
        
        if os.path.exists(user_path) and user_path.lower().endswith("mysql.exe"):
            config.set('mysql_path', user_path)
            return user_path
        
        return None
