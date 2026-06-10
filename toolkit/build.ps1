# Este script automatiza o processo de build e criação de um instalador .msi para o DM-Toolkit.
#
# O que ele faz:
# 1. Define variáveis e limpa builds antigos.
# 2. Instala dependências de build (PyInstaller).
# 3. Executa o PyInstaller para criar um executável standalone da aplicação.
# 4. Verifica se o WiX Toolset está instalado e qual a sua versão (v3 ou v4+).
# 5. Usa o 'Heat.exe' (para v3) ou 'dotnet tool run heat' (para v4+) para catalogar todos os arquivos.
# 6. Usa o 'Candle.exe' e 'Light.exe' (para v3) ou 'wix build' (para v4+) para compilar o instalador.
#
# Como usar:
# 1. Instale o WiX Toolset (v3 ou v4+): https://wixtoolset.org/releases/
# 2. **Instale o .NET SDK (para WiX v4+):** https://dotnet.microsoft.com/download
# 3. Abra um terminal PowerShell.
# 4. Navegue até a pasta raiz deste projeto.
# 5. Execute: .\build.ps1
#
# O log completo da execução será salvo em build_log.txt

# --- Início do Script ---

# Ativa o modo estrito e para a execução em caso de erro.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Define ProjectRoot logo no início
$ProjectRoot = Get-Location

# --- Início da Transcrição (Logging) ---
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = "$ProjectRoot\build_log_$Timestamp.txt"
Start-Transcript -Path $LogFile -Force

# --- 1. Definição de Variáveis ---
Write-Host "
--- (1/7) Definindo variáveis do build ---" -ForegroundColor Cyan

$ProjectName = "dm-toolkit"
$AppVersion = "1.0.0"
# $ProjectRoot já está definido
$PyInstallerOutput = "$ProjectRoot\dist\$ProjectName"
$MsiOutputFolder = "$ProjectRoot\dist"
$WixSourceFile = "$ProjectRoot\toolkit.wxs"
$WixGeneratedFiles = "$ProjectRoot\ApplicationFiles.wxs"
$MsiFileName = "$ProjectName-$AppVersion.msi"

# --- Limpeza de Builds Antigos ---
Write-Host "Limpando diretórios de build antigos (dist, build, *.wixobj)..."
if (Test-Path "$ProjectRoot\dist") { Remove-Item -Recurse -Force "$ProjectRoot\dist" -ErrorAction SilentlyContinue }
if (Test-Path "$ProjectRoot\build") { Remove-Item -Recurse -Force "$ProjectRoot\build" -ErrorAction SilentlyContinue }
if (Test-Path "$ProjectRoot\*.wixobj") { Remove-Item -Recurse -Force "$ProjectRoot\*.wixobj" -ErrorAction SilentlyContinue }
if (Test-Path $WixGeneratedFiles) { Remove-Item -Force $WixGeneratedFiles -ErrorAction SilentlyContinue }


# --- 2. Instalar Dependências ---
Write-Host "
--- (2/7) Instalando dependências de build (pyinstaller) ---" -ForegroundColor Cyan
pip install pyinstaller


# --- 3. Executar PyInstaller ---
Write-Host "
--- (3/7) Executando PyInstaller para criar o executável... ---" -ForegroundColor Cyan
# Coletar dinamicamente todos os submódulos de 'toolkit.features' para hidden-import
# Isso é necessário porque o main.py usa importlib dinâmico, o que o PyInstaller não detecta estaticamente.
$FeaturesDir = "$ProjectRoot\toolkit\features"

# Dependências críticas que o PyInstaller pode não detectar automaticamente (drivers de BD, etc.)
$CriticalHiddenImports = @(
    "fdb",
    "sqlalchemy",
    "sqlalchemy.sql.default_comparator", # Frequentemente perdido pelo PyInstaller
    "psycopg2",
    "mysql.connector",
    "pyodbc",
    "sqlalchemy_firebird"
)

$HiddenImportsArgs = @()
foreach ($import in $CriticalHiddenImports) {
    $HiddenImportsArgs += "--hidden-import=$import"
}

if (Test-Path $FeaturesDir) {
    $FeatureFiles = Get-ChildItem -Path $FeaturesDir -Filter "*.py"
    foreach ($file in $FeatureFiles) {
        if ($file.Name -ne "__init__.py") {
            $ModuleName = "toolkit.features." + $file.BaseName
            $HiddenImportsArgs += "--hidden-import=$ModuleName"
        }
    }
}

Write-Host "Hidden Imports detectados: $HiddenImportsArgs" -ForegroundColor Gray

python -m PyInstaller --name $ProjectName --onedir --noconfirm $HiddenImportsArgs "toolkit/launcher.py"


# --- 4. Verificar Instalação do WiX Toolset e Versão ---
Write-Host "
--- (4/7) Verificando a instalação do WiX Toolset e sua versão... ---" -ForegroundColor Cyan
$WixPath = ""
$WixVersion = ""
$WixExe = ""
$CandleExe = ""
$LightExe = ""
$HeatExe = ""

# Procura por qualquer versão do WiX em ambas as pastas de Program Files.
$WixRoot = Get-ChildItem -Path "${env:ProgramFiles(x86)}", "${env:ProgramFiles}" -Filter "WiX Toolset v*" -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1

if ($WixRoot) {
    $WixBinPath = Join-Path -Path $WixRoot.FullName -ChildPath "bin"
    if (Test-Path $WixBinPath) {
        $WixPath = $WixBinPath
        
        # Tenta detectar WiX v4+ (wix.exe)
        if (Test-Path (Join-Path $WixPath "wix.exe")) {
            $WixVersion = "v4+"
            $WixExe = Join-Path $WixPath "wix.exe"
            Write-Host "WiX Toolset v4+ detectado em: $WixPath"
        }
        # Tenta detectar WiX v3 (candle.exe, light.exe, heat.exe)
        elseif (Test-Path (Join-Path $WixPath "candle.exe")) {
            $WixVersion = "v3"
            $CandleExe = Join-Path $WixPath "candle.exe"
            $LightExe = Join-Path $WixPath "light.exe"
            $HeatExe = Join-Path $WixPath "heat.exe"
            Write-Host "WiX Toolset v3 detectado em: $WixPath"
        }
    }
}

if (-not $WixVersion) {
    Write-Host "ERRO: WiX Toolset não encontrado ou versão não suportada." -ForegroundColor Red
    Write-Host "O script não conseguiu localizar a pasta 'bin' do WiX ou os executáveis 'wix.exe' (v4+) / 'candle.exe' (v3)."
    Write-Host "Por favor, instale a versão mais recente do WiX (v3 ou v4+) a partir de: https://wixtoolset.org/releases/"
    exit 1
}


# --- 5. Catalogar Arquivos (Substituto do Heat para WiX v4) ---
Write-Host "
--- (5/7) Catalogando arquivos da aplicação (Custom Harvest)... ---" -ForegroundColor Cyan

# Função para gerar IDs determinísticos ou aleatórios (usaremos GUIDs aleatórios para simplificar)
# Para WiX v4, a estrutura recomendada é DirectoryRef -> Directories e ComponentGroup -> Components com Directory Ref.

$WxsContent = new-object System.Text.StringBuilder
$null = $WxsContent.AppendLine('<?xml version="1.0" encoding="utf-8"?>')
$null = $WxsContent.AppendLine('<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">')
$null = $WxsContent.AppendLine('  <Fragment>')

# 1. Estrutura de Diretórios
$null = $WxsContent.AppendLine('    <DirectoryRef Id="INSTALLFOLDER">')

# Vamos percorrer as pastas para criar a árvore de diretórios
# Mapa para guardar Caminho -> ID Do Diretório
$DirMap = @{}
$DirMap[$PyInstallerOutput] = "INSTALLFOLDER"

# Função recursiva para gerar estrutura de diretórios
function Build-DirectoryXml {
    param($CurrentDir)
    
    $SubDirs = Get-ChildItem -Path $CurrentDir -Directory
    foreach ($dir in $SubDirs) {
        $DirId = "dir_" + [System.Guid]::NewGuid().ToString("N")
        $DirMap[$dir.FullName] = $DirId
        
        $null = $WxsContent.AppendLine("      <Directory Id=`"$DirId`" Name=`"$($dir.Name)`">")
        Build-DirectoryXml -CurrentDir $dir.FullName
        $null = $WxsContent.AppendLine("      </Directory>")
    }
}
Build-DirectoryXml -CurrentDir $PyInstallerOutput

$null = $WxsContent.AppendLine('    </DirectoryRef>')

# 2. Definição do ComponentGroup
$null = $WxsContent.AppendLine('    <ComponentGroup Id="ApplicationComponents">')

# Função recursiva para gerar componentes
function Build-ComponentXml {
    param($CurrentDir)
    
    # Arquivos neste diretório
    $Files = Get-ChildItem -Path $CurrentDir -File
    $CurrentDirId = $DirMap[$CurrentDir]
    
    foreach ($file in $Files) {
        $FileId = "fil_" + [System.Guid]::NewGuid().ToString("N")
        $ComponentId = "cmp_" + [System.Guid]::NewGuid().ToString("N")
        $RelPath = $file.FullName.Substring($PyInstallerOutput.Length + 1)
        
        # Componente referenciando o diretório correto
        $null = $WxsContent.AppendLine("      <Component Id=`"$ComponentId`" Directory=`"$CurrentDirId`" Guid=`"*`">")
        $null = $WxsContent.AppendLine("        <File Id=`"$FileId`" Source=`"`$(var.SourceDir)\$RelPath`" KeyPath=`"yes`" />")
        $null = $WxsContent.AppendLine("      </Component>")
    }
    
    # Recurse
    $SubDirs = Get-ChildItem -Path $CurrentDir -Directory
    foreach ($dir in $SubDirs) {
        Build-ComponentXml -CurrentDir $dir.FullName
    }
}

Build-ComponentXml -CurrentDir $PyInstallerOutput

$null = $WxsContent.AppendLine('    </ComponentGroup>')
$null = $WxsContent.AppendLine('  </Fragment>')
$null = $WxsContent.AppendLine('</Wix>')

# Salvar o arquivo WXS
Set-Content -Path $WixGeneratedFiles -Value $WxsContent.ToString() -Encoding UTF8
Write-Host "Arquivo de definições gerado com sucesso: $WixGeneratedFiles"


# --- 6. Compilar Arquivos WiX com Candle.exe (v3) ou wix build (v4+) ---
Write-Host "
--- (6/7) Compilando definições do instalador com Candle/wix build (WiX $WixVersion)... ---" -ForegroundColor Cyan
$wixobjFiles = @()

if ($WixVersion -eq "v3") {
    # Para v3 ainda precisamos do Candle/Light (mas o harvester acima gera XML v4, então V3 VAI FALHAR aqui se usado)
    # Assumimos que o usuário tem v4+ ou v6 instalado conforme log.
    Write-Host "ATENÇÃO: O script foi atualizado para WiX v4+ e pode não funcionar corretamente com v3 antigo devido à sintaxe XML." -ForegroundColor Yellow
    
    $CandleResult1 = & $CandleExe $WixSourceFile -dSourceDir=$PyInstallerOutput 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Host "ERRO: Candle.exe falhou no $WixSourceFile." -ForegroundColor Red; Write-Host $CandleResult1; exit 1 }
    $wixobjFiles += "$ProjectRoot\toolkit.wixobj"
    
    $CandleResult2 = & $CandleExe $WixGeneratedFiles -dSourceDir=$PyInstallerOutput 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Host "ERRO: Candle.exe falhou no $WixGeneratedFiles." -ForegroundColor Red; Write-Host $CandleResult2; exit 1 }
    $wixobjFiles += "$ProjectRoot\ApplicationFiles.wixobj"

}
elseif ($WixVersion -eq "v4+") {
    # wix build faz o papel de Candle e Light juntos
    # Atualizado para usar as extensões corretas do v4 (WixToolset.UI.wixext)
    # IMPORTANTE: Colocar as flags ANTES dos arquivos de origem para evitar erro WIX0118
    $WixBuildArgs = @(
        "build",
        "-ext", "WixToolset.UI.wixext",
        "-ext", "WixToolset.Util.wixext",
        "-o", "$MsiOutputFolder\$MsiFileName",
        "-d", "SourceDir=$PyInstallerOutput",
        $WixSourceFile,
        $WixGeneratedFiles
    )
    Write-Host "Executando: $WixExe $WixBuildArgs"
    $WixBuildResult = & $WixExe $WixBuildArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: 'wix build' falhou." -ForegroundColor Red
        Write-Host $WixBuildResult
        exit 1
    }
}


# --- 7. Linkar e Criar o .msi com Light.exe (v3) ---
Write-Host "
--- (7/7) Criando o instalador .msi com Light (WiX $WixVersion)... ---" -ForegroundColor Cyan

if ($WixVersion -eq "v3") {
    $LightResult = & $LightExe $wixobjFiles -o "$MsiOutputFolder\$MsiFileName" -ext "WixUIExtension" -ext "WixUtilExtension" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Light.exe falhou." -ForegroundColor Red
        Write-Host $LightResult
        exit 1
    }
}
# Para v4+, o 'wix build' já criou o MSI na etapa 6, então não fazemos nada aqui.


# --- Conclusão ---
Write-Host "
------------------------------------------------------------" -ForegroundColor Green
Write-Host "

PROCESSO CONCLUÍDO COM SUCESSO!
" -ForegroundColor Green
Write-Host "O instalador foi gerado em:"
Write-Host "$MsiOutputFolder\$MsiFileName" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"

# Limpeza de arquivos temporários do build
Remove-Item -Recurse -Force "$ProjectRoot\*.wixobj" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$ProjectRoot\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$ProjectRoot\$ProjectName.spec" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $WixGeneratedFiles -ErrorAction SilentlyContinue

# --- Fim da Transcrição (Logging) ---
Stop-Transcript
