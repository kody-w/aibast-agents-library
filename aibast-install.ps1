# AIBAST RAPP one-liner (Windows PowerShell):
#   irm https://microsoft.github.io/aibast-agents-library/aibast-install.ps1 | iex
#
# AIBAST RAPP is the work twin of the Brainstem: it lives beside a personal Brainstem and never touches it.
# Its own folder (%USERPROFILE%\.aibast-rapp), its own sign-in, memory and agents, its own port (7272)
# and its own command (aibast-rapp). A personal Brainstem keeps .brainstem, port 7071 and brainstem.
#
# 1. Runs this site's Brainstem installer (install.ps1) unchanged, without launching, with
#    USERPROFILE pointed at the work twin's folder, so everything it writes lands there.
# 2. Adds the AIBAST Registry agent and FirstHour, each checked byte for byte against this site's registry,
#    so AIBAST agents, offline mode and Send to Copilot Studio are one chat message away.
# 3. Installs the aibast-rapp command and launches the work twin on its own port.
# AIBAST_HOME and AIBAST_PORT change the folder and the port.
$SITE = "https://microsoft.github.io/aibast-agents-library/"
$RAW = "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/"
$REAL_PROFILE = $env:USERPROFILE
$AIBAST_HOME = if ($env:AIBAST_HOME) { $env:AIBAST_HOME } else { "$REAL_PROFILE\.aibast-rapp" }
$AIBAST_PORT = if ($env:AIBAST_PORT) { $env:AIBAST_PORT } else { "7272" }
$KERNEL = "$AIBAST_HOME\.brainstem\src\rapp_brainstem"
$TWIN_BIN = "$AIBAST_HOME\.local\bin"
$REAL_BIN = "$REAL_PROFILE\.local\bin"
$passThrough = @($args)
$launch = -not ($passThrough -contains "--no-launch")

New-Item -ItemType Directory -Force -Path $AIBAST_HOME | Out-Null
$installer = [scriptblock]::Create((Invoke-RestMethod "${SITE}install.ps1"))
# The installer launches on 7071 itself, so it never launches here; the work twin starts below.
$env:USERPROFILE = $AIBAST_HOME
try { & $installer --no-launch @passThrough } finally { $env:USERPROFILE = $REAL_PROFILE }
$ErrorActionPreference = "Stop"  # set after the installer so it runs exactly as it does on its own
if (-not (Test-Path (Join-Path $KERNEL "brainstem.py"))) {
    throw "The Brainstem installer did not finish, so the AIBAST Registry agent was not added."
}

# The installer put the work twin's own launcher folder on the PATH; take it off again, or
# `brainstem` would open the work twin instead of a personal Brainstem.
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$kept = ($userPath -split ";") | Where-Object { $_ -and $_ -ne $TWIN_BIN }
[Environment]::SetEnvironmentVariable("Path", ($kept -join ";"), "User")
$env:Path = (($env:Path -split ";") | Where-Object { $_ -and $_ -ne $TWIN_BIN }) -join ";"

Write-Host "  Adding the AIBAST Registry and FirstHour agents..."
$registry = Invoke-RestMethod "${SITE}registry.json"
# The AIBAST Registry agent, and FirstHour, the guide to the first hour ("teach me my first hour").
foreach ($pick in @(@("@aibast-agents-library/aibast-registry", "aibast_registry_agent.py", "AIBAST Registry"),
                    @("@aibast-agents-library/first-hour", "first_hour_agent.py", "FirstHour"))) {
    $entry = $registry.agents | Where-Object { $_.name -eq $pick[0] } | Select-Object -First 1
    $part = Join-Path $KERNEL "agents\.$($pick[1]).part"
    Invoke-WebRequest "$RAW$($entry._file)" -OutFile $part -UseBasicParsing
    $digest = (Get-FileHash $part -Algorithm SHA256).Hash.ToLower()
    if ($digest -ne $entry._sha256) {
        Remove-Item $part -Force
        throw "The $($pick[2]) agent did not match the registry, so it was not added."
    }
    Move-Item $part (Join-Path $KERNEL "agents\$($pick[1])") -Force
}
$envFile = Join-Path $KERNEL ".env"
$text = if (Test-Path $envFile) { Get-Content $envFile -Raw } else { "" }
if ($text -notmatch "AIBAST_REGISTRY_URL=") {  # every AIBAST organ follows this one setting
    Add-Content $envFile "AIBAST_REGISTRY_URL=${SITE}registry.json"
}
# Never 7071, the personal Brainstem's port (the kernel's .env.example starts there); a port chosen
# by hand is kept.
$lines = @(Get-Content $envFile) | Where-Object { $_ -notmatch "^PORT=\s*(7071)?\s*$" }
if (-not ($lines -match "^PORT=")) { $lines += "PORT=$AIBAST_PORT" }
if (-not ($lines -match "^OFFLINE_PORT=")) { $lines += "OFFLINE_PORT=$([int]$AIBAST_PORT + 1)" }  # never 7072
Set-Content $envFile $lines
Write-Host "  Done: AIBAST Registry and FirstHour agents added (checked against ${SITE}registry.json)" -ForegroundColor Green

# The aibast-rapp command runs the installer's own launcher with USERPROFILE set to the work twin's folder.
New-Item -ItemType Directory -Force -Path $REAL_BIN | Out-Null
Set-Content -Path "$REAL_BIN\aibast-rapp.cmd" -Value @"
@echo off
rem AIBAST RAPP (work twin). Its folder: $AIBAST_HOME. Your personal Brainstem is untouched.
set "USERPROFILE=$AIBAST_HOME"
call "$TWIN_BIN\brainstem.cmd" %*
"@
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($userPath -split ";") -notcontains $REAL_BIN) {
    [Environment]::SetEnvironmentVariable("Path", "$REAL_BIN;$userPath", "User")
    $env:Path = "$REAL_BIN;$env:Path"
}
Write-Host "  Done: aibast-rapp command installed to $REAL_BIN\aibast-rapp.cmd" -ForegroundColor Green

if ($launch) {
    $port = ((Get-Content $envFile) -match "^PORT=" | Select-Object -Last 1) -replace "^PORT=", ""
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "  Port $port is in use. If that is AIBAST RAPP it is already running: http://localhost:$port"
        Write-Host "  Otherwise set AIBAST_PORT to a free port and run this again."
        return
    }
    Start-Job -ScriptBlock {
        param($p)
        for ($i = 0; $i -lt 60; $i++) {
            try { Invoke-WebRequest "http://localhost:$p/health" -UseBasicParsing -TimeoutSec 1 | Out-Null; break } catch { Start-Sleep 1 }
        }
        Start-Process "http://localhost:$p"
    } -ArgumentList $port | Out-Null
    Write-Host "  Starting AIBAST RAPP on http://localhost:$port ..."
    & "$REAL_BIN\aibast-rapp.cmd"
}
