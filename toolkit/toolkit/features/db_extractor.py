# -*- coding: utf-8 -*-

import os
import getpass
from toolkit.utils import selecionar_diretorio

try:
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    SQLAlchemyError = None
    create_engine = None
    inspect = None

class DbExtractor:
    def __init__(self):
        print("\n--- Extrator de Metadados de Banco de Dados ---")
        if not SQLAlchemyError:
            print("ERRO: Bibliotecas de banco de dados não instaladas.")
            print('Para usar esta função, instale: pip install SQLAlchemy "psycopg2-binary" "mysql-connector-python" "pyodbc" "fdb"')

    def _get_db_driver_choice(self):
        print("\nSelecione o tipo de banco de dados:")
        print("  1. PostgreSQL")
        print("  2. MySQL")
        print("  3. SQL Server")
        print("  4. Firebird")
        print("  0. Voltar ao menu principal")
        while True:
            choice = input("Digite o número da sua opção: ")
            if choice in ['1', '2', '3', '4', '0']: return choice
            print("Opção inválida. Tente novamente.")

    def _build_connection_url(self, choice):
        url, dbname = None, None
        try:
            if choice == '1': # PostgreSQL
                user, host, port = input("Usuário [postgres]: ") or 'postgres', input("Host [localhost]: ") or 'localhost', input("Porta [5432]: ") or '5432'
                password = getpass.getpass("Senha: ")
                dbname = input("Nome do banco de dados: ")
                if not dbname: raise ValueError("Nome do banco de dados é obrigatório.")
                url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
            elif choice == '2': # MySQL
                user, host, port = input("Usuário [root]: ") or 'root', input("Host [localhost]: ") or 'localhost', input("Porta [3306]: ") or '3306'
                password = getpass.getpass("Senha: ")
                dbname = input("Nome do banco de dados: ")
                if not dbname: raise ValueError("Nome do banco de dados é obrigatório.")
                url = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}?charset=utf8"
            elif choice == '3': # SQL Server
                host = input(r"Host (servidor ou instância, ex: localhost\SQLEXPRESS): ")
                dbname = input("Nome do banco de dados: ")
                if not dbname: raise ValueError("Nome do banco de dados é obrigatório.")
                auth_choice = input("Usar Autenticação do Windows (S/N)? [S]: ").upper() or 'S'
                driver = "ODBC Driver 17 for SQL Server"
                if auth_choice == 'S':
                    url = f"mssql+pyodbc://{host}/{dbname}?driver={driver}&Trusted_Connection=yes"
                else:
                    user = input("Usuário: ")
                    password = getpass.getpass("Senha: ")
                    url = f"mssql+pyodbc://{user}:{password}@{host}/{dbname}?driver={driver}"
            elif choice == '4': # Firebird
                user = input("Usuário [SYSDBA]: ") or 'SYSDBA'
                password = getpass.getpass("Senha [masterkey]: ") or 'masterkey'
                host = input("Host [localhost]: ") or 'localhost'
                port = input("Porta [3050]: ") or '3050'
                db_path = input("Caminho COMPLETO do arquivo .fdb: ")
                if not db_path:
                    raise ValueError("O caminho do arquivo .fdb é obrigatório.")
                
                dbname = os.path.splitext(os.path.basename(db_path))[0]
                charset = input("Charset [UTF8]: ") or 'UTF8'
                
                url = f"firebird+fdb://{user}:{password}@{host}:{port}/{db_path}?charset={charset}"
        except (KeyboardInterrupt, ValueError) as e:
            print(f"\nOperação cancelada ou entrada inválida: {e}")
            return None, None
        return url, dbname

    def _extract(self, url, db_name, diretorio_saida):
        nome_arquivo = f"{db_name}-metadata.txt"
        caminho_completo_saida = os.path.join(diretorio_saida, nome_arquivo)
        
        print("\nTentando conectar ao banco de dados...")
        try:
            engine = create_engine(url)
            with engine.connect():
                print("Conexão bem-sucedida!")
                inspector = inspect(engine)
                with open(caminho_completo_saida, 'w', encoding='utf-8') as f:
                    f.write(f"--- METADADOS DO BANCO DE DADOS: {db_name} ---\n")
                    f.write(f"--- SGBD: {engine.dialect.name.capitalize()} ---\n\n")
                    
                    schemas = [db_name] if engine.dialect.name == 'mysql' else inspector.get_schema_names()
                    if not schemas and engine.dialect.name == 'firebird': schemas.append(None)
                    
                    table_count = 0
                    for schema in schemas:
                        for table_name in sorted(inspector.get_table_names(schema=schema)):
                            table_count += 1
                            full_table_name = f"{schema}.{table_name}" if schema else table_name
                            print(f"Processando tabela: {full_table_name}")

                            f.write(f"{ '='*40}\nTABELA: {full_table_name}\n{ '='*40}\n\n")
                            f.write("COLUNAS:\n")
                            for col in inspector.get_columns(table_name, schema=schema):
                                f.write(f"  - {col['name']}: {col['type']} {'NULL' if col['nullable'] else 'NOT NULL'}\n")
                            
                            pk = inspector.get_pk_constraint(table_name, schema=schema)
                            if pk and pk['constrained_columns']:
                                f.write(f"\nCHAVE PRIMÁRIA (PK): ({', '.join(pk['constrained_columns'])})\n")
                            
                            fks = inspector.get_foreign_keys(table_name, schema=schema)
                            if fks:
                                f.write("\nCHAVES ESTRANGEIRAS (FK):\n")
                                for fk in fks:
                                    ref_table = f"{fk['referred_schema']}.{fk['referred_table']}" if fk['referred_schema'] else fk['referred_table']
                                    f.write(f"  - ({', '.join(fk['constrained_columns'])}) -> {ref_table}({', '.join(fk['referred_columns'])})\n")
                            f.write("\n\n")
                    print(f"\nExtração concluída! {table_count} tabelas processadas.")
                    print(f"Metadados salvos em '{caminho_completo_saida}'.")
        except (SQLAlchemyError, IOError) as e:
            print(f"\n--- ERRO ---\nOcorreu um problema: {e}")

    def run(self):
        if not SQLAlchemyError:
            return

        choice = self._get_db_driver_choice()
        if choice == '0': return

        connection_url, db_name = self._build_connection_url(choice)
        if not connection_url: return

        diretorio_saida = selecionar_diretorio(f"Selecione a pasta para SALVAR o arquivo de metadados do banco '{db_name}'")
        if not diretorio_saida:
            print("Operação cancelada. Nenhum diretório de saída selecionado.")
            return
            
        self._extract(connection_url, db_name, diretorio_saida)
        print("\n" + "="*30 + "\nProcesso de extração de metadados do BD concluído!\n" + "="*30)
