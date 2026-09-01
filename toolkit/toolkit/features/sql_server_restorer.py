# -*- coding: utf-8 -*-
import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from toolkit.utils import limpar_tela, aguardar_enter

class RestauradorSqlServer:
    """
    Ferramenta para restaurar múltiplos arquivos .bak do SQL Server em lote,
    utilizando o módulo dbatools (Restore-DbaDatabase) via PowerShell.
    """

    def run(self):
        limpar_tela()
        print("=== Restaurador de Banco de Dados SQL Server em Lote ===")
        print("Esta ferramenta utiliza o dbatools para restaurar múltiplos arquivos .bak")
        print("de um diretório selecionado para uma instância SQL Server.")
        print("-" * 60)

        instancias = self._obter_instancias_locais()
        instancia_alvo = self._selecionar_instancia(instancias)

        if not instancia_alvo:
            print("\n[AVISO] Nenhuma instância selecionada.")
            aguardar_enter()
            return

        print(f"\n[INFO] Instância selecionada: {instancia_alvo}")
        print("[INFO] Selecione a pasta com os arquivos .bak na janela que se abrirá...")
        
        pasta_arquivos = self._selecionar_pasta()
        
        if not pasta_arquivos or not os.path.isdir(pasta_arquivos):
            print("\n[AVISO] Pasta não selecionada ou inválida. Operação cancelada.")
            aguardar_enter()
            return
            
        print(f"[INFO] Pasta selecionada: {pasta_arquivos}")
        
        sobrescrever_input = input("\nDeseja sobrescrever bancos de dados existentes se houver conflito (WithReplace)? (S/N): ").strip().lower()
        sobrescrever = sobrescrever_input == 's'
        
        print("\nIniciando processo de restauração...")
        self._executar_restauracao(instancia_alvo, pasta_arquivos, sobrescrever)
        aguardar_enter()

    def _obter_instancias_locais(self):
        """Busca instâncias do SQL Server instaladas localmente usando o registro do Windows para obter nome e porta."""
        import winreg
        instancias_encontradas = []
        try:
            chave_instancias = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Microsoft SQL Server')
            instancias, _ = winreg.QueryValueEx(chave_instancias, 'InstalledInstances')
            winreg.CloseKey(chave_instancias)
            
            chave_nomes = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL')
            
            for inst in instancias:
                porta = ""
                try:
                    int_id, _ = winreg.QueryValueEx(chave_nomes, inst)
                    chave_tcp = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, fr'SOFTWARE\Microsoft\Microsoft SQL Server\{int_id}\MSSQLServer\SuperSocketNetLib\Tcp\IPAll')
                    
                    try:
                        porta, _ = winreg.QueryValueEx(chave_tcp, 'TcpPort')
                    except FileNotFoundError:
                        pass
                        
                    if not porta:
                        try:
                            porta, _ = winreg.QueryValueEx(chave_tcp, 'TcpDynamicPorts')
                        except FileNotFoundError:
                            pass
                    winreg.CloseKey(chave_tcp)
                except Exception:
                    pass
                    
                # Formata a string de exibição/conexão
                nome_exibicao = "localhost" if inst.upper() == "MSSQLSERVER" else f"localhost\\{inst}"
                if porta:
                    nome_exibicao += f",{porta}"
                    
                instancias_encontradas.append(nome_exibicao)
                
            winreg.CloseKey(chave_nomes)
        except Exception as e:
            print(f"[ERRO] Falha ao buscar instâncias locais no registro: {e}")
            
        return instancias_encontradas

    def _selecionar_instancia(self, opcoes):
        """Menu interativo para escolha ou inserção manual da instância do banco de dados."""
        if opcoes:
            print("\nInstâncias locais detectadas:")
            for i, op in enumerate(opcoes, 1):
                print(f"  {i}. {op}")
        
        print(f"  {len(opcoes) + 1}. Digitar manualmente (outra instância/porta)")
        
        escolha = input("\nEscolha a instância (número) ou pressione Enter para cancelar: ").strip()
        
        if not escolha.isdigit():
            return None
            
        indice = int(escolha) - 1
        
        if 0 <= indice < len(opcoes):
            return opcoes[indice]
        elif indice == len(opcoes):
            return input("Digite o nome da instância (ex: localhost,1433 ou Servidor\\Instancia): ").strip()
            
        return None

    def _selecionar_pasta(self):
        """Abre uma caixa de diálogo nativa do Windows para escolher o diretório com os backups."""
        raiz = tk.Tk()
        raiz.withdraw() # Oculta a janela principal do tkinter
        raiz.attributes('-topmost', True) # Força a janela de diálogo para frente
        raiz.lift()
        raiz.focus_force()
        caminho_pasta = filedialog.askdirectory(parent=raiz, title="Selecione a pasta com os arquivos .bak")
        raiz.destroy()
        # Corrige as barras para o formato do Windows
        if caminho_pasta:
            caminho_pasta = caminho_pasta.replace("/", "\\")
        return caminho_pasta

    def _executar_restauracao(self, instancia, pasta, sobrescrever):
        """Executa a restauração através do comando Restore-DbaDatabase do PowerShell."""
        replace_flag = "-WithReplace" if sobrescrever else ""
        
        script_ps = f'''
        Write-Host "Conectando ao servidor SQL Server: {instancia}..." -ForegroundColor Cyan
        try {{
            $server = Connect-DbaInstance -SqlInstance "{instancia}" -TrustServerCertificate -ErrorAction Stop
            Write-Host "Conexão estabelecida. Iniciando restauração da pasta: {pasta}" -ForegroundColor Cyan
            Restore-DbaDatabase -SqlInstance $server -Path "{pasta}" {replace_flag}
            Write-Host "Processo concluído com sucesso." -ForegroundColor Green
        }} catch {{
            Write-Host "ERRO DURANTE A EXECUÇÃO:" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
            exit 1
        }}
        '''
        
        processo = subprocess.run(["powershell", "-NoProfile", "-Command", script_ps])
        if processo.returncode != 0:
            print("\n[ERRO] O script de restauração falhou ou encontrou erros.")
