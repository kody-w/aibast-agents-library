# AIBAST Brainstem one-liner (Windows PowerShell):
#   irm https://microsoft.github.io/aibast-agents-library/aibast-install.ps1 | iex
#
# 1. Runs this site's Brainstem installer (install.ps1) unchanged, without launching.
# 2. Adds the AIBAST Registry agent, checked byte for byte against this site's registry,
#    so AIBAST agents, offline mode and Send to Copilot Studio are one chat message away.
# 3. Runs the installer again, which finds everything up to date and launches as usual.
$SITE = "https://microsoft.github.io/aibast-agents-library/"
$RAW = "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/"
$KERNEL = "$env:USERPROFILE\.brainstem\src\rapp_brainstem"
$passThrough = @($args)
$launch = -not ($passThrough -contains "--no-launch")

$installer = [scriptblock]::Create((Invoke-RestMethod "${SITE}install.ps1"))
& $installer --no-launch @passThrough
$ErrorActionPreference = "Stop"  # set after the installer so it runs exactly as it does on its own
if (-not (Test-Path (Join-Path $KERNEL "brainstem.py"))) {
    throw "The Brainstem installer did not finish, so the AIBAST Registry agent was not added."
}

Write-Host "  Adding the AIBAST Registry agent..."
$registry = Invoke-RestMethod "${SITE}registry.json"
$entry = $registry.agents | Where-Object { $_.name -eq "@aibast-agents-library/aibast-registry" } | Select-Object -First 1
$part = Join-Path $KERNEL "agents\.aibast_registry_agent.py.part"
Invoke-WebRequest "$RAW$($entry._file)" -OutFile $part -UseBasicParsing
$digest = (Get-FileHash $part -Algorithm SHA256).Hash.ToLower()
if ($digest -ne $entry._sha256) {
    Remove-Item $part -Force
    throw "The AIBAST Registry agent did not match the registry, so it was not added."
}
Move-Item $part (Join-Path $KERNEL "agents\aibast_registry_agent.py") -Force
$envFile = Join-Path $KERNEL ".env"
$text = if (Test-Path $envFile) { Get-Content $envFile -Raw } else { "" }
if ($text -notmatch "AIBAST_REGISTRY_URL=") {  # every AIBAST organ follows this one setting
    Add-Content $envFile "AIBAST_REGISTRY_URL=${SITE}registry.json"
}
Write-Host "  Done: AIBAST Registry agent added (checked against ${SITE}registry.json)" -ForegroundColor Green

if ($launch) {
    & $installer @passThrough
}
