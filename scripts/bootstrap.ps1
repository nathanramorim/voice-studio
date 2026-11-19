# bootstrap.ps1 — Windows (PowerShell 5.1+): confere o uv; sem ele, mostra e (com o seu ok ou -Sim/--sim)
# instala pelo winget ou pelo instalador OFICIAL do uv; atualiza o PATH desta sessão e roda
# `uv run requisitos.py checar` (ou os argumentos que você passar).
# Nunca exige Homebrew nem administrador; nunca aceita licença por você. Contrato: sdd/spec/contrato-requisitos.md.
# Uso: powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1 [-Sim] [-Oficial] [argumentos do requisitos.py]
#   -Oficial usa o instalador oficial mesmo com winget (o winget sem terminal espera o aceite da pessoa).
# Códigos: os do requisitos.py; 4 = falta o uv e não houve ok; 5 = a instalação do uv falhou.
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$UrlUv = 'https://astral.sh/uv/install.ps1'
$Aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$Sim = $false
$Oficial = $false
$Resto = @($args)
# Só as opções do começo são do bootstrap (como no bootstrap.sh); o resto vai inteiro para o motor.
while ($Resto.Count -gt 0 -and ($Resto[0] -in @('-Sim', '--sim', '-Oficial', '--oficial'))) {
    if ($Resto[0] -in @('-Sim', '--sim')) { $Sim = $true } else { $Oficial = $true }
    $Resto = @($Resto | Select-Object -Skip 1)
}
if ($Resto.Count -eq 0) { $Resto = @('checar') }

function Atualizar-Path {
    $maquina = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $usuario = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = (@($env:Path, $usuario, $maquina, (Join-Path $HOME '.local\bin')) | Where-Object { $_ }) -join ';'
}

function Achar-Uv {
    if (Get-Command uv -ErrorAction SilentlyContinue) { return $true }
    $local = Join-Path $HOME '.local\bin\uv.exe'
    if (Test-Path $local) { $env:Path = (Join-Path $HOME '.local\bin') + ';' + $env:Path; return $true }
    return $false
}

if (-not (Achar-Uv)) {
    $temWinget = (-not $Oficial) -and [bool](Get-Command winget -ErrorAction SilentlyContinue)
    Write-Output 'O uv não está instalado. Ele roda o requisitos.py e gerencia o Python (sem pip).'
    if ($temWinget) {
        Write-Output 'Vou usar: winget install --id=astral-sh.uv -e (o winget pergunta a você o aceite dos termos).'
    } else {
        Write-Output "Sem winget: vou baixar e rodar o instalador oficial $UrlUv (instala em ~\.local\bin, sem administrador)."
    }
    if (-not $Sim -and [Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
        $resp = Read-Host 'Instalar o uv agora? [s/N]'
        if ($resp -match '^(s|sim|y)$') { $Sim = $true }
    }
    if (-not $Sim) {
        Write-Output "Nada foi instalado. Com o seu ok, rode: powershell -ExecutionPolicy Bypass -File $($MyInvocation.MyCommand.Path) -Sim"
        exit 4
    }
    try {
        if ($temWinget) {
            & winget install --id=astral-sh.uv -e
            if ($LASTEXITCODE -ne 0) { throw "winget saiu com $LASTEXITCODE" }
        } else {
            $tmp = Join-Path ([IO.Path]::GetTempPath()) ("uv-install-" + [Guid]::NewGuid().ToString() + '.ps1')
            Invoke-WebRequest -UseBasicParsing -Uri $UrlUv -OutFile $tmp
            try {
                & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp
                if ($LASTEXITCODE -ne 0) { throw "instalador saiu com $LASTEXITCODE" }
            } finally { Remove-Item -Force $tmp -ErrorAction SilentlyContinue }
        }
    } catch {
        Write-Output "A instalação do uv falhou: $_"
        exit 5
    }
    Atualizar-Path
    if (-not (Achar-Uv)) { Write-Output 'O uv foi instalado, mas não está no PATH: abra outro terminal.'; exit 5 }
    Write-Output 'uv instalado e já no PATH desta sessão.'
}

& uv run (Join-Path $Aqui 'requisitos.py') @Resto
exit $LASTEXITCODE
