# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from pathlib import Path
import time
from toolkit.utils import selecionar_arquivo

class FirebirdMigrator:
    """
    Ferramenta para migrar bancos de dados Firebird 2.5 para 4.0.
    Utiliza containers Docker para isolar as versões da engine do banco.
    """
    
    def __init__(self):
        self.image_fb25 = "jacobalberty/firebird:2.5-sc"
        self.image_fb40 = "firebirdsql/firebird:4"

    def check_docker(self):
        """Verifica se o Docker está instalado e rodando."""
        try:
            subprocess.check_call(
                ["docker", "ps"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def pull_images(self):
        """Garante que as imagens necessárias estejam presentes."""
        print(f"\n[INFO] Verificando imagens Docker necessárias...")
        for img in [self.image_fb25, self.image_fb40]:
            print(f"       Verificando {img}...")
            try:
                subprocess.check_call(["docker", "pull", img], stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print(f"[ERRO CRÍTICO] Não foi possível baixar a imagem: {img}")
                print("               Verifique sua conexão ou se o nome da imagem está correto.")
                raise Exception("Falha no download da imagem Docker.")
        print("[OK] Imagens verificadas.")

    def start_container(self, image, volume_map, env_vars, container_name):
        """Inicia um container em background."""
        print(f"       Iniciando container {container_name}...")
        cmd = [
            "docker", "run", "-d", "--rm",
            "--name", container_name,
            "-v", volume_map,
        ]
        for k, v in env_vars.items():
            cmd.extend(["-e", f"{k}={v}"])
        cmd.append(image)
        
        try:
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
            time.sleep(20) # Aguarda inicialização do serviço Firebird (margem de segurança)
            return True
        except subprocess.CalledProcessError:
            print(f"[ERRO] Falha ao iniciar container {container_name}")
            return False

    def stop_container(self, container_name):
        """Para e remove o container."""
        print(f"       Parando container {container_name}...")
        subprocess.call(["docker", "stop", container_name], stdout=subprocess.DEVNULL)

    def run_docker_exec(self, container_name, cmd_list, description):
        """Executa um comando dentro de um container rodando e captura saída."""
        print(f"\n--> {description}...")
        full_cmd = ["docker", "exec", container_name] + cmd_list
        try:
            # Captura stdout e stderr para análise
            process = subprocess.run(full_cmd, capture_output=True, text=True)
            
            if process.returncode == 0:
                print("    [SUCESSO]")
                return True, process.stdout
            else:
                print(f"    [ERRO] Código: {process.returncode}")
                # Imprime as últimas linhas do erro para o usuário ver
                print(f"    Detalhes: {process.stderr.strip()}")
                return False, process.stderr
        except Exception as e:
            print(f"    [ERRO CRÍTICO] Falha na chamada do Docker: {e}")
            return False, str(e)

    def run(self):
        print("\n=== MIGRADOR FIREBIRD (2.5 -> 4.0) ===")
        print("Esta ferramenta usa Docker para converter backups antigos ou arquivos .fdb")
        print("para o formato compatível com Firebird 4.0.\n")

        # 1. Verifica Docker
        if not self.check_docker():
            print("[ERRO CRÍTICO] O Docker não foi detectado ou não está rodando.")
            print("               Por favor, inicie o Docker Desktop e tente novamente.")
            input("\nPressione ENTER para voltar ao menu...")
            return

        # 2. Solicita Arquivo
        print("Selecione o arquivo .fdb ou .fbk na janela que será aberta...")
        file_path = selecionar_arquivo("Selecione o banco de dados Firebird", [("Arquivos Firebird", "*.fdb *.fbk"), ("Todos os arquivos", "*.*")])
        
        if not file_path:
            print("[INFO] Nenhum arquivo selecionado. Operação cancelada.")
            return
        
        if not os.path.exists(file_path):
            print(f"[ERRO] Arquivo não encontrado: {file_path}")
            return

        input_path = Path(file_path).resolve()
        work_dir = input_path.parent
        filename = input_path.name
        
        # Mapeamento de volume
        volume_map = f"{work_dir}:/db"

        # Garante imagens
        try:
            self.pull_images()
        except Exception:
            return

        # Variáveis de fluxo
        bkp_file = None
        use_fb4_directly = False # Flag para caso detectemos que o banco já é novo
        
        # --- PASSO 1: BACKUP (FB 2.5) ---
        if input_path.suffix.lower() == '.fdb':
            print(f"\n[FASE 1] Arquivo .fdb detectado. Tentando backup com engine 2.5...")
            
            bkp_filename = input_path.stem + "_migrated.fbk"
            bkp_path = work_dir / bkp_filename
            
            if bkp_path.exists():
                try:
                    os.remove(bkp_path)
                except OSError:
                    pass

            container_name = "fb25_migrator"
            if self.start_container(self.image_fb25, volume_map, {"ISC_PASSWORD": "masterkey"}, container_name):
                
                cmd_bkp = [
                    "/usr/local/firebird/bin/gbak", "-b", "-v", "-t",
                    "-user", "SYSDBA", "-password", "masterkey",
                    f"/db/{filename}",
                    f"/db/{bkp_filename}"
                ]
                
                success, output = self.run_docker_exec(container_name, cmd_bkp, "Gerando backup (GBK) versão 2.5")
                self.stop_container(container_name)
                
                if success:
                    bkp_file = bkp_filename
                else:
                    # Análise de erro de versão ODS
                    if "unsupported on-disk structure" in output and "found 13.0" in output:
                        print("\n[ALERTA] Este banco de dados já parece ser Firebird 4.0 (ODS 13.0).")
                        print("         A engine 2.5 não consegue lê-lo.")
                        if input("         Deseja processar usando a engine 4.0 direto? (s/n): ").lower() == 's':
                            use_fb4_directly = True
                        else:
                            return
                    elif "unsupported on-disk structure" in output:
                         print("\n[ALERTA] Versão de ODS incompatível detectada.")
                         print("         O arquivo é mais novo que o suportado pelo Firebird 2.5.")
                         if input("         Deseja tentar processar com a engine 4.0? (s/n): ").lower() == 's':
                            use_fb4_directly = True
                         else:
                            return
                    else:
                        return
            else:
                return
        
        elif input_path.suffix.lower() == '.fbk':
            print(f"\n[FASE 1] Arquivo .fbk detectado. Pulando para restauração...")
            bkp_file = filename
        else:
            print("[ERRO] Formato não suportado. Use .fdb ou .fbk")
            return

        # --- FLUXO ALTERNATIVO: BANCO JÁ É 4.0 ---
        if use_fb4_directly:
            print(f"\n[FASE EXTRA] Realizando Backup/Restore via Engine 4.0 para manutenção...")
            
            bkp_filename = input_path.stem + "_v4_maintenance.fbk"
            bkp_file = bkp_filename # Para o restore usar este arquivo
            
            container_name = "fb40_maintenance"
            if self.start_container(self.image_fb40, volume_map, {"FIREBIRD_PASSWORD": "masterkey"}, container_name):
                 cmd_bkp_v4 = [
                    "/opt/firebird/bin/gbak", "-b", "-v", "-t",
                    "-user", "SYSDBA", "-password", "masterkey",
                    f"/db/{filename}",
                    f"/db/{bkp_filename}"
                ]
                 success, _ = self.run_docker_exec(container_name, cmd_bkp_v4, "Gerando Backup (GBK) com Engine 4.0")
                 self.stop_container(container_name)
                 
                 if not success:
                     return
            else:
                return

        # --- PASSO 2: RESTORE (FB 4.0) ---
        print(f"\n[FASE 2] Restaurando backup para engine 4.0...")
        
        target_fdb_name = input_path.stem + "_v4.fdb"
        target_path = work_dir / target_fdb_name
        
        if target_path.exists():
             print(f"[AVISO] O arquivo de destino já existe: {target_fdb_name}")
             if input("        Deseja sobrescrever? (s/n): ").lower() != 's':
                 print("Operação cancelada pelo usuário.")
                 return
             try:
                os.remove(target_path)
             except OSError as e:
                print(f"[ERRO] Não foi possível remover o arquivo: {e}")
                return

        container_name = "fb40_migrator"
        if self.start_container(self.image_fb40, volume_map, {"FIREBIRD_PASSWORD": "masterkey"}, container_name):
            
            cmd_restore = [
                "/opt/firebird/bin/gbak", "-c", "-v", 
                "-user", "SYSDBA", "-password", "masterkey",
                f"/db/{bkp_file}",
                f"/db/{target_fdb_name}"
            ]

            success, _ = self.run_docker_exec(container_name, cmd_restore, "Restaurando (GBK) para versão 4.0")
            self.stop_container(container_name)

            if success:
                print("\n" + "="*50)
                print("CONCLUÍDO COM SUCESSO!")
                print("="*50)
                print(f"Arquivo final: {target_path}")
                
                # Limpeza
                if bkp_file and (input_path.suffix.lower() == '.fdb' or use_fb4_directly):
                    if input("\nDeseja excluir o arquivo de backup intermediário (.fbk)? (s/n): ").lower() == 's':
                        try:
                            os.remove(work_dir / bkp_file)
                            print("Backup intermediário removido.")
                        except:
                            pass
        
        input("\nPressione ENTER para voltar ao menu...")
