# -*- coding: utf-8 -*-

"""
EXTRATOR DE METADADOS DE BANCO DE DADOS GENERALISTA

Este script se conecta a diferentes tipos de bancos de dados para extrair
e salvar seus metadados (tabelas, colunas, chaves primárias e estrangeiras)
em um arquivo de texto.

Autor: Cássio Rodolfo Alves de Carvalho Pinto/DeMaria Software
Versão: 2.4.0
Data: 2025-09-29

COMO USAR:
1. Instale as dependências necessárias:
   pip install SQLAlchemy "psycopg2-binary" "mysql-connector-python" "pyodbc" "fdb"

2. Execute o script no seu terminal:
   python extrator_metadata_generalista.py

3. Siga as instruções no terminal para selecionar o banco de dados e
   fornecer as informações de conexão.
"""

import getpass
import sys
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

def get_db_driver_choice():
    """Exibe o menu de opções e captura a escolha do usuário."""
    print("Selecione o tipo de banco de dados:")
    print("  1. PostgreSQL (versões 9.5 a 15+)")
    print("  2. MySQL (versões 5.1 a 5.7+)")
    print("  3. SQL Server")
    print("  4. Firebird")
    print("  0. Sair")
    
    while True:
        choice = input("Digite o número da sua opção: ")
        if choice in ['1', '2', '3', '4', '0']:
            return choice
        else:
            print("Opção inválida. Por favor, tente novamente.")

def build_connection_url(choice):
    """Constrói a URL de conexão do SQLAlchemy com base na entrada do usuário."""
    
    url = None
    
    try:
        if choice == '1': # PostgreSQL
            user = input("Usuário [postgres]: ") or 'postgres'
            password = getpass.getpass("Senha: ")
            host = input("Host (servidor) [localhost]: ") or 'localhost'
            port = input("Porta [5432]: ") or '5432'
            dbname = input("Nome do banco de dados: ")
            if not dbname:
                print("ERRO: Nome do banco de dados é obrigatório.")
                return None
            url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

        elif choice == '2': # MySQL
            user = input("Usuário [root]: ") or 'root'
            password = getpass.getpass("Senha: ")
            host = input("Host (servidor) [localhost]: ") or 'localhost'
            port = input("Porta [3306]: ") or '3306'
            dbname = input("Nome do banco de dados: ")
            if not dbname:
                print("ERRO: Nome do banco de dados é obrigatório.")
                return None
            # Adicionado '?charset=utf8' para compatibilidade com versões mais antigas do MySQL
            url = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}?charset=utf8"

        elif choice == '3': # SQL Server
            driver = "ODBC Driver 17 for SQL Server" # O mais comum atualmente
            host = input("Host (servidor ou instância, ex: localhost\\SQLEXPRESS): ")
            dbname = input("Nome do banco de dados: ")
            
            auth_choice = input("Usar Autenticação do Windows (S/N)? [S]: ").upper() or 'S'
            
            if auth_choice == 'S':
                url = f"mssql+pyodbc://{host}/{dbname}?driver={driver}&Trusted_Connection=yes"
            else:
                user = input("Usuário: ")
                password = getpass.getpass("Senha: ")
                url = f"mssql+pyodbc://{user}:{password}@{host}/{dbname}?driver={driver}"
        
        elif choice == '4': # Firebird
            user = input("Usuário [SYSDBA]: ") or 'SYSDBA'
            password = getpass.getpass("Senha [masterkey]: ") or 'masterkey'
            # Para Firebird, o 'host' pode ser um caminho de arquivo ou um servidor
            db_path = input("Caminho do arquivo .fdb (ex: C:/data/meubanco.fdb) ou 'servidor:alias': ")
            charset = input("Charset [UTF8]: ") or 'UTF8'
            url = f"firebird+fdb://{user}:{password}@{db_path}?charset={charset}"

    except (KeyboardInterrupt):
        print("\nOperação cancelada pelo usuário.")
        return None
        
    return url

def extract_and_write_metadata(url, output_file):
    """Conecta ao banco, extrai os metadados e escreve no arquivo de saída."""
    
    print("\nTentando conectar ao banco de dados...")
    
    try:
        engine = create_engine(url)
        with engine.connect() as connection:
            print("Conexão bem-sucedida!")
            inspector = inspect(engine)
            
            db_name = engine.url.database

            # NOVO: Coleta a versão do banco de dados
            dialect = engine.dialect
            db_version_info = dialect.server_version_info
            db_type_name = dialect.name.capitalize()
            db_version_string = '.'.join(map(str, db_version_info))
            full_db_info = f"{db_type_name} {db_version_string}"
            print(f"Versão do SGBD detectada: {full_db_info}")


            # Garante que o diretório de saída exista antes de tentar escrever
            output_dir = os.path.dirname(output_file)
            if output_dir: # Garante que não seja uma string vazia se o path for relativo
                os.makedirs(output_dir, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                # ATUALIZADO: Adiciona a versão do SGBD ao cabeçalho do arquivo
                f.write(f"--- METADADOS DO BANCO DE DADOS: {db_name} ---\n")
                f.write(f"--- VERSÃO DO SGBD: {full_db_info} ---\n\n")
                
                schemas_to_inspect = []
                # CORREÇÃO: Para MySQL, o "schema" é o próprio banco de dados.
                # Limitamos a busca para apenas o banco de dados especificado.
                if engine.dialect.name == 'mysql':
                    schemas_to_inspect.append(db_name)
                    print(f"Buscando tabelas no banco de dados (schema): {db_name}")
                else:
                    # Para outros bancos (PostgreSQL, SQL Server), o comportamento padrão está correto.
                    schemas_to_inspect = inspector.get_schema_names()
                    print(f"Buscando tabelas nos schemas: {', '.join(schemas_to_inspect)}")
                    # Caso especial para Firebird que pode não retornar schemas
                    if not schemas_to_inspect and engine.dialect.name == 'firebird':
                        schemas_to_inspect.append(None)
                
                table_count = 0
                for schema in schemas_to_inspect:
                    tables = inspector.get_table_names(schema=schema)
                    
                    for table_name in sorted(tables):
                        table_count += 1
                        full_table_name = f"{schema}.{table_name}" if schema else table_name
                        print(f"Processando tabela: {full_table_name}")

                        f.write(f"========================================\n")
                        f.write(f"TABELA: {full_table_name}\n")
                        f.write(f"========================================\n\n")

                        # Colunas
                        f.write("COLUNAS:\n")
                        columns = inspector.get_columns(table_name, schema=schema)
                        for col in columns:
                            col_type = str(col['type'])
                            nullable = "NULL" if col['nullable'] else "NOT NULL"
                            default = f" (DEFAULT: {col['default']})" if col['default'] is not None else ""
                            f.write(f"  - {col['name']}: {col_type} ({nullable}){default}\n")
                        f.write("\n")

                        # Chave Primária (PK)
                        pk_constraint = inspector.get_pk_constraint(table_name, schema=schema)
                        if pk_constraint and pk_constraint['constrained_columns']:
                            pk_cols = ', '.join(pk_constraint['constrained_columns'])
                            f.write(f"CHAVE PRIMÁRIA (PK):\n  - ({pk_cols})\n\n")

                        # Chaves Estrangeiras (FK)
                        fks = inspector.get_foreign_keys(table_name, schema=schema)
                        if fks:
                            f.write("CHAVES ESTRANGEIRAS (FK):\n")
                            for fk in fks:
                                local_cols = ', '.join(fk['constrained_columns'])
                                remote_table = fk['referred_table']
                                if fk['referred_schema']:
                                    remote_table = f"{fk['referred_schema']}.{remote_table}"
                                remote_cols = ', '.join(fk['referred_columns'])
                                f.write(f"  - A coluna(s) '{local_cols}' referencia -> {remote_table}({remote_cols})\n")
                        f.write("\n\n")

                print(f"\nExtração concluída! {table_count} tabelas processadas.")
                print(f"Os metadados foram salvos em '{output_file}'.")

    except SQLAlchemyError as e:
        print("\n--- ERRO ---")
        print("Ocorreu um erro ao conectar ou processar o banco de dados.")
        print("Verifique os seguintes pontos:")
        print("  - As credenciais (usuário/senha) estão corretas?")
        print("  - O nome do host/servidor e a porta estão acessíveis?")
        print("  - O nome do banco de dados ou caminho do arquivo existe?")
        print("  - O driver ODBC/biblioteca do banco está instalado e configurado corretamente?")
        print(f"\nMensagem de erro original: {e}")
    except IOError as e:
        print(f"\n--- ERRO DE ARQUIVO ---")
        print(f"Não foi possível escrever no arquivo '{output_file}'. Verifique as permissões.")
        print(f"Mensagem de erro original: {e}")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")


def main():
    """Função principal que orquestra a execução do script."""
    print("=" * 40)
    print("  Extrator de Metadados de Banco de Dados")
    print("=" * 40)
    print("Este script requer bibliotecas adicionais.")
    print("Certifique-se de instalá-las com: pip install SQLAlchemy psycopg2-binary mysql-connector-python pyodbc fdb\n")

    try:
        choice = get_db_driver_choice()

        if choice == '0':
            print("Saindo do programa.")
            sys.exit(0)

        connection_url = build_connection_url(choice)

        if connection_url:
            # Solicita o diretório e o nome do arquivo separadamente
            output_dir = input("\nDigite o diretório para salvar o arquivo (deixe em branco para o atual): ") or '.'
            file_name = input("Digite o nome do arquivo de saída [metadata]: ") or 'metadata'

            # Garante que o arquivo tenha a extensão .txt
            if not file_name.lower().endswith('.txt'):
                file_name += '.txt'
            
            # Monta o caminho completo do arquivo
            full_output_path = os.path.join(output_dir, file_name)

            extract_and_write_metadata(connection_url, full_output_path)

    except (KeyboardInterrupt):
        print("\n\nOperação cancelada pelo usuário. Saindo.")
        sys.exit(0)


if __name__ == '__main__':
    main()