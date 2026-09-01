# -*- coding: utf-8 -*-

import os
import getpass
from urllib.parse import quote_plus
from toolkit.utils import selecionar_diretorio

try:
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    SQLAlchemyError = None
    create_engine = None
    inspect = None
    text = None

try:
    from access_parser import AccessParser
except ImportError:
    AccessParser = None

class DbExtractor:
    def __init__(self):
        print("\n--- Extrator de Metadados de Banco de Dados ---")
        if not SQLAlchemyError:
            print("ERRO: Bibliotecas de banco de dados não instaladas.")
            print('Para usar esta função, instale: pip install SQLAlchemy "psycopg2-binary" "mysql-connector-python" "pyodbc" "fdb" "sqlalchemy-access" "access-parser"')

    def _get_db_driver_choice(self):
        print("\nSelecione o tipo de banco de dados:")
        print("  1. PostgreSQL")
        print("  2. MySQL")
        print("  3. SQL Server")
        print("  4. Firebird")
        print("  5. MS Access (.mdb, .accdb) [Recomendado para arquivos antigos]")
        print("  0. Voltar ao menu principal")
        while True:
            choice = input("Digite o número da sua opção: ")
            if choice in ['1', '2', '3', '4', '5', '0']: return choice
            print("Opção inválida. Tente novamente.")

    def _build_connection_url(self, choice):
        url, dbname = None, None
        try:
            if choice == '1': # PostgreSQL
                user, host, port = input("Usuário [postgres]: ") or 'postgres', input("Host [localhost]: ") or 'localhost', input("Porta [5432]: ") or '5432'
                password = getpass.getpass("Senha: ")
                dbname = input("Nome do banco de dados: ")
                if not dbname: raise ValueError("Nome do banco de dados é obrigatório.")
                url = f"postgresql+psycopg2://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{dbname}"
            elif choice == '2': # MySQL
                user, host, port = input("Usuário [root]: ") or 'root', input("Host [localhost]: ") or 'localhost', input("Porta [3306]: ") or '3306'
                password = getpass.getpass("Senha: ")
                dbname = input("Nome do banco de dados: ")
                if not dbname: raise ValueError("Nome do banco de dados é obrigatório.")
                url = f"mysql+mysqlconnector://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{dbname}?charset=utf8"
            elif choice == '3': # SQL Server
                server = input("Servidor (IP ou Hostname) [localhost]: ") or 'localhost'
                port_instance = input("Porta (ex: 1433) ou Instância (ex: SQLEXPRESS) [Opcional - Enter para pular]: ")
                
                if port_instance:
                    # Verifica se é uma porta (apenas dígitos)
                    if port_instance.isdigit():
                        # Para ODBC Driver, porta é separada por vírgula
                        host = f"{server},{port_instance}"
                    else:
                        # Assume que é uma instância. Trata se o usuário digitou '\SQLEXPRESS' ou apenas 'SQLEXPRESS'
                        if port_instance.startswith('\\'):
                            host = f"{server}{port_instance}"
                        else:
                            host = f"{server}\\{port_instance}"
                else:
                    host = server

                dbname = input("Nome do banco de dados: ")
                if not dbname: raise ValueError("Nome do banco de dados é obrigatório.")
                auth_choice = input("Usar Autenticação do Windows (S/N)? [S]: ").upper() or 'S'
                driver = "ODBC Driver 17 for SQL Server"
                if auth_choice == 'S':
                    url = f"mssql+pyodbc://{host}/{dbname}?driver={driver}&Trusted_Connection=yes"
                else:
                    user = input("Usuário: ")
                    password = getpass.getpass("Senha: ")
                    url = f"mssql+pyodbc://{quote_plus(user)}:{quote_plus(password)}@{host}/{dbname}?driver={driver}"
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
                
                url = f"firebird+fdb://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{db_path}?charset={charset}"
            elif choice == '5': # MS Access
                db_path = input("Caminho COMPLETO do arquivo .mdb ou .accdb: ")
                if not db_path:
                    raise ValueError("O caminho do arquivo é obrigatório.")
                if not os.path.exists(db_path):
                    raise ValueError(f"Arquivo não encontrado: {db_path}")
                
                dbname = os.path.splitext(os.path.basename(db_path))[0]
                # Para Access, retornamos o caminho do arquivo como a "URL"
                url = f"access_file://{db_path}"
        except (KeyboardInterrupt, ValueError) as e:
            print(f"\nOperação cancelada ou entrada inválida: {e}")
            return None, None
        return url, dbname

    def _get_charset(self, engine, db_name):
        charset = "Não foi possível determinar"
        dialect_name = engine.dialect.name
        try:
            with engine.connect() as connection:
                if dialect_name == 'postgresql':
                    stmt = text("SELECT pg_encoding_to_char(encoding) FROM pg_database WHERE datname = :db_name")
                    result = connection.execute(stmt, {'db_name': db_name})
                    charset = result.scalar()
                elif dialect_name == 'mysql':
                    result = connection.execute(text("SELECT @@character_set_database"))
                    charset = result.scalar()
                elif dialect_name == 'mssql':
                    stmt = text("SELECT DATABASEPROPERTYEX(:db_name, 'Collation')")
                    result = connection.execute(stmt, {'db_name': db_name})
                    charset = result.scalar()
                elif dialect_name == 'firebird':
                    result = connection.execute(text("SELECT RDB$CHARACTER_SET_NAME FROM RDB$DATABASE"))
                    charset = result.scalar().strip()
        except Exception as e:
            print(f"AVISO: Não foi possível determinar o charset do banco de dados: {e}")
        return charset

    def _extract_access_native(self, db_path, db_name, diretorio_saida):
        """Extrai metadados de arquivos Access (.mdb, .accdb) usando access-parser (sem drivers)"""
        if not AccessParser:
            print("ERRO: Biblioteca 'access-parser' não instalada. Execute: pip install access-parser")
            return

        nome_arquivo = f"{db_name}-metadata.txt"
        caminho_completo_saida = os.path.join(diretorio_saida, nome_arquivo)
        
        print(f"\nLendo arquivo Access: {db_path}...")
        try:
            db = AccessParser(db_path)
            # Tenta obter as tabelas do catálogo. O access-parser mudou em versões recentes.
            tables = []
            if hasattr(db, 'catalog'):
                if isinstance(db.catalog, dict):
                    tables = sorted(db.catalog.keys())
                else:
                    tables = sorted(db.catalog)
            
            with open(caminho_completo_saida, 'w', encoding='utf-8') as f:
                f.write(f"--- METADADOS DO BANCO DE DADOS: {db_name} ---\n")
                f.write(f"--- SGBD: MS Access (via access-parser) ---\n")
                f.write(f"--- ARQUIVO: {db_path} ---\n\n")
                
                table_count = 0
                error_count = 0
                for table_name in tables:
                    # Pula tabelas de sistema e temporárias
                    if table_name.startswith('MSys') or table_name.startswith('~'):
                        continue
                        
                    table_count += 1
                    print(f"Processando tabela: {table_name}...", end=" ", flush=True)
                    
                    try:
                        f.write(f"{ '='*40}\nTABELA: {table_name}\n{ '='*40}\n\n")
                        f.write("COLUNAS:\n")
                        
                        try:
                            # No access-parser, a estrutura (metadados) está no catálogo
                            table_def = db.catalog.get(table_name)
                            
                            if table_def and hasattr(table_def, 'columns'):
                                for col in table_def.columns:
                                    f.write(f"  - {col.name}: {col.type}\n")
                                print("OK")
                            elif table_def and isinstance(table_def, dict) and 'columns' in table_def:
                                # Caso o catálogo seja um dicionário de dicionários em algumas versões
                                for col_name, col_info in table_def['columns'].items():
                                    f.write(f"  - {col_name}: {col_info}\n")
                                print("OK (via dict)")
                            else:
                                print(f"FALHA (Tipo: {type(table_def)})")
                                f.write(f"  AVISO: Estrutura não reconhecida para esta tabela.\n")
                                f.write(f"  Tipo do objeto: {type(table_def)}\n")
                        except Exception as inner_e:
                            error_count += 1
                            print(f"FALHA")
                            f.write(f"  AVISO: Falha ao ler estrutura detalhada desta tabela.\n")
                            f.write(f"  Erro técnico: {str(inner_e)}\n")
                        
                        f.write("\n\n")
                    except Exception as e:
                        error_count += 1
                        print(f"ERRO CRÍTICO")
                        f.write(f"ERRO CRÍTICO ao processar tabela {table_name}: {e}\n\n")

                print(f"\nExtração concluída!")
                print(f"- {table_count} tabelas processadas.")
                if error_count > 0:
                    print(f"- {error_count} tabelas apresentaram falhas (detalhes no TXT).")
                print(f"Metadados salvos em '{caminho_completo_saida}'.")
        except Exception as e:
            print(f"\n--- ERRO CRÍTICO ---\nNão foi possível abrir o arquivo Access: {e}")
            print("DICA: Certifique-se de que o arquivo não está aberto em outro programa.")

    def _extract(self, url, db_name, diretorio_saida):
        # Se for um arquivo Access usando a nova lógica
        if url.startswith("access_file://"):
            db_path = url.replace("access_file://", "")
            self._extract_access_native(db_path, db_name, diretorio_saida)
            return

        nome_arquivo = f"{db_name}-metadata.txt"
        caminho_completo_saida = os.path.join(diretorio_saida, nome_arquivo)
        
        print("\nTentando conectar ao banco de dados...")
        try:
            engine = create_engine(url)
            with engine.connect():
                print("Conexão bem-sucedida!")
                inspector = inspect(engine)
                charset = self._get_charset(engine, db_name)
                with open(caminho_completo_saida, 'w', encoding='utf-8') as f:
                    f.write(f"--- METADADOS DO BANCO DE DADOS: {db_name} ---\n")
                    f.write(f"--- SGBD: {engine.dialect.name.capitalize()} ---\n")
                    f.write(f"--- CHARSET: {charset} ---\n\n")
                    
                    # A obtenção de esquemas varia entre SGBDs
                    schemas = []
                    if engine.dialect.name == 'firebird':
                        # Firebird não tem um conceito de schema forte, então usamos None
                        schemas.append(None)
                    elif engine.dialect.name == 'mysql':
                        # MySQL usa o nome do banco como schema
                        schemas = [db_name]
                    else:
                        # Para outros SGBDs, tentamos obter os schemas
                        try:
                            schemas = inspector.get_schema_names()
                        except NotImplementedError:
                            print("AVISO: O SGBD não suporta listagem de schemas. Continuando com schema padrão.")
                            schemas.append(None)
                    
                    # Garantia para o caso de a lista de schemas vir vazia (ex: Firebird inicial)
                    if not schemas:
                         schemas.append(None)
                    
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
        except UnicodeDecodeError as e:
            print(f"\n--- ERRO ---\nFalha de decodificação ao tentar conectar ou ler o banco de dados.")
            print(f"DICA: Verifique se a senha, usuário e nome do banco de dados estão absolutamente corretos.")
            print(f"Muitas vezes isso acontece quando a conexão falha (senha errada, etc.) e o PostgreSQL retorna uma mensagem de erro com acentuação que causa falha no driver.")
            print(f"Detalhe técnico: {e}")

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
