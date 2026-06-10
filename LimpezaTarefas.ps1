# --- INÍCIO DO SCRIPT ---

# Carrega configurações do arquivo user_config.json, se existir
$configFile = Join-Path $PSScriptRoot "toolkit\user_config.json"
$config = @{}
if (Test-Path $configFile) {
    try {
        $config = Get-Content $configFile | ConvertFrom-Json
    } catch {
        $config = @{}
    }
}

# 1. CONFIGURE A PASTA RAIZ AQUI
if ($config.limpeza_tarefas_dir) {
    $pastaRaiz = $config.limpeza_tarefas_dir
} else {
    $pastaRaiz = Read-Host "Por favor, digite o caminho completo da pasta de tarefas para limpar"
    $config | Add-Member -MemberType NoteProperty -Name "limpeza_tarefas_dir" -Value $pastaRaiz -Force
    $config | ConvertTo-Json | Set-Content $configFile
}

# 2. CONFIGURE A PASTA PARA SALVAR OS ARQUIVOS DE LOG
if ($config.limpeza_tarefas_logs) {
    $caminhoLogs = $config.limpeza_tarefas_logs
} else {
    $caminhoLogs = Join-Path $PSScriptRoot "logs_limpeza_tarefas"
}

# 3. DEFINA O LIMITE DE DIAS (1 ANO = 365 DIAS)
$diasLimite = 365

# --- LÓGICA DE EXECUÇÃO (NÃO PRECISA ALTERAR ABAIXO) ---

# Verifica se a pasta de logs existe. Se não, a cria.
if (-not (Test-Path $caminhoLogs)) {
    Write-Host "A pasta de logs '$caminhoLogs' não existe. Criando..."
    New-Item -ItemType Directory -Force -Path $caminhoLogs | Out-Null
}

# Cria o nome do arquivo de log com data e hora atuais (formato AAAA-MM-DD_HH-mm-ss)
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$arquivoLog = Join-Path -Path $caminhoLogs -ChildPath "log-$timestamp.log"

# --- FUNÇÃO DE LOG ---
# Esta função escreve a mensagem na tela (Host) e também a adiciona ao arquivo de log.
function Escrever-Log {
    param(
        [string]$Mensagem
    )
    # Adiciona a data e hora na frente de cada linha do log
    $mensagemComData = "[$(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')] - $Mensagem"
    Write-Host $mensagemComData
    Add-Content -Path $arquivoLog -Value $mensagemComData
}

# Calcula a data limite para exclusão
$dataLimite = (Get-Date).AddDays(-$diasLimite)

# Verifica se o caminho da pasta raiz realmente existe antes de continuar.
if (-not (Test-Path $pastaRaiz)) {
    Escrever-Log "ERRO: O caminho '$pastaRaiz' não foi encontrado. Verifique o caminho no script e tente novamente."
    # Pausa a execução para que a mensagem de erro seja lida.
    Read-Host "Pressione Enter para fechar."
    exit
}

Escrever-Log "============================================================"
Escrever-Log "Iniciando verificação de limpeza automática."
Escrever-Log "Pasta Raiz Alvo: $pastaRaiz"
Escrever-Log "Arquivo de Log: $arquivoLog"
Escrever-Log "Regra 1: Excluir pastas com data de criação anterior a $($dataLimite.ToString('dd/MM/yyyy HH:mm:ss')) (mais de $diasLimite dias)."
Escrever-Log "Regra 2: Ignorar pastas cujo nome comece com um ponto ('.')."
Escrever-Log "============================================================"

# Obtém a lista de todas as subpastas (diretórios) dentro da pasta raiz.
$subpastas = Get-ChildItem -Path $pastaRaiz -Directory

# Itera (passa por) cada uma das subpastas encontradas.
foreach ($pasta in $subpastas) {
    # --- NOVA MELHORIA ---
    # PRIMEIRO, verifica se o nome da pasta começa com um ponto.
    if ($pasta.Name.StartsWith(".")) {
        Escrever-Log "IGNORANDO: A pasta '$($pasta.Name)' está marcada para ser mantida (inicia com '.')."
        continue # O comando 'continue' pula para a próxima iteração do loop.
    }

    # SEGUNDO, compara a data de criação da pasta com a data limite calculada.
    if ($pasta.CreationTime -lt $dataLimite) {
        # Se a pasta for mais antiga que o limite, ela será excluída.
        $logExclusao = "EXCLUINDO: A pasta '$($pasta.Name)' (Data de Criação: $($pasta.CreationTime.ToString('dd/MM/yyyy')))"
        Escrever-Log $logExclusao

        # O comando abaixo deleta a pasta, seu conteúdo (-Recurse) e ignora avisos (-Force).
        # PARA TESTAR SEM DELETAR: Adicione o parâmetro -WhatIf no final da linha abaixo.
        # Exemplo de teste: 
        #Remove-Item -Path $pasta.FullName -Recurse -Force -WhatIf
        Remove-Item -Path $pasta.FullName -Recurse -Force

        Escrever-Log "-> A pasta '$($pasta.Name)' foi excluída com sucesso."
    } else {
        # Se a pasta for mais recente, ela será mantida.
        $logManutencao = "MANTENDO: A pasta '$($pasta.Name)' (Data de Criação: $($pasta.CreationTime.ToString('dd/MM/yyyy')))"
        Escrever-Log $logManutencao
    }
}

Escrever-Log "============================================================"
Escrever-Log "Verificação concluída."
Escrever-Log "============================================================"

# --- FIM DO SCRIPT ---
