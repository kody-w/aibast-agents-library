param(
    [Parameter(Mandatory = $true)][string]$NodePath,
    [Parameter(Mandatory = $true)][string]$Workspace,
    [Parameter(Mandatory = $true)][string]$Artifact,
    [Parameter(Mandatory = $true)][string]$AppDir,
    [Parameter(Mandatory = $true)][string]$ScratchDir,
    [Parameter(Mandatory = $true)][string]$PythonPath,
    [Parameter(Mandatory = $true)][string]$Mode,
    [Parameter(Mandatory = $true)][string]$Report,
    [string]$ExpectedPublisher = "",
    [string]$ReleaseTag = "",
    [string]$ReleaseCommit = "",
    [string]$RuntimeVersionUrl = ""
)

$ErrorActionPreference = "Stop"
if (-not [Environment]::Is64BitProcess) {
    throw "The Windows package gate launcher must run as x64."
}

$userName = "RappGate$PID"
$passwordText = "$([Guid]::NewGuid().ToString('N'))!Aa1"
$password = ConvertTo-SecureString $passwordText -AsPlainText -Force
$credential = [pscredential]::new("$env:COMPUTERNAME\$userName", $password)
$releaseDir = Join-Path $Workspace "beta\release"
$configPath = Join-Path $releaseDir "standard-user-gate-$PID.json"
$runnerPath = Join-Path $releaseDir "standard-user-gate-$PID.ps1"
$resultPath = Join-Path $releaseDir "standard-user-gate-$PID.exit"
$logPath = Join-Path $releaseDir "standard-user-gate-$PID.log"

try {
    New-LocalUser -Name $userName -Password $password `
        -AccountNeverExpires -PasswordNeverExpires | Out-Null
    $usersGroup = (([Security.Principal.SecurityIdentifier]"S-1-5-32-545").Translate([Security.Principal.NTAccount]).Value.Split("\"))[-1]
    Add-LocalGroupMember -Group $usersGroup -Member $userName
    & icacls.exe $releaseDir /grant "${userName}:(OI)(CI)M" /T /C /Q | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not grant the standard gate user access to the release directory."
    }

    $arguments = @(
        "--platform", "windows",
        "--arch", "x64",
        "--mode", $Mode,
        "--artifact", $Artifact,
        "--app-dir", $AppDir,
        "--scratch-dir", $ScratchDir,
        "--brainstem-python", $PythonPath,
        "--brainstem-source", (Join-Path $Workspace "rapp_brainstem"),
        "--report", $Report,
        "--require-standard-user", "true"
    )
    if ($ExpectedPublisher) {
        $arguments += @("--expected-publisher", $ExpectedPublisher)
    }
    if ($ReleaseTag) {
        $arguments += @("--release-tag", $ReleaseTag)
    }
    if ($ReleaseCommit) {
        $arguments += @("--release-commit", $ReleaseCommit)
    }
    if ($RuntimeVersionUrl) {
        $arguments += @("--runtime-version-url", $RuntimeVersionUrl)
    }

    @{
        NodePath = $NodePath
        GateScript = (Join-Path $Workspace "beta\scripts\package-gate.mjs")
        Arguments = $arguments
        ResultPath = $resultPath
        LogPath = $logPath
        Path = $env:PATH
        SigningEnvironment = @{
            WINDOWS_SIGNING_SUBJECT = $env:WINDOWS_SIGNING_SUBJECT
            AZURE_ARTIFACT_SIGNING_ENDPOINT = $env:AZURE_ARTIFACT_SIGNING_ENDPOINT
            AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME = $env:AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME
            AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME = $env:AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME
            AZURE_ARTIFACT_SIGNING_PROFILE_TYPE = $env:AZURE_ARTIFACT_SIGNING_PROFILE_TYPE
        }
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $configPath -Encoding utf8

    @'
$ErrorActionPreference = "Stop"
$config = Get-Content -LiteralPath $args[0] -Raw | ConvertFrom-Json
$env:PATH = $config.Path
foreach ($property in $config.SigningEnvironment.psobject.Properties) {
    if ($property.Value) {
        [Environment]::SetEnvironmentVariable(
            $property.Name,
            [string]$property.Value,
            "Process"
        )
    }
}
$gateArguments = @($config.Arguments | ForEach-Object { [string]$_ })
& $config.NodePath $config.GateScript @gateArguments *> $config.LogPath
$code = $LASTEXITCODE
Set-Content -LiteralPath $config.ResultPath -Value $code -Encoding ascii
exit $code
'@ | Set-Content -LiteralPath $runnerPath -Encoding utf8

    $process = Start-Process -FilePath powershell.exe `
        -Credential $credential `
        -ArgumentList @(
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-File", "`"$runnerPath`"",
            "`"$configPath`""
        ) `
        -LoadUserProfile `
        -Wait `
        -PassThru

    if (Test-Path $logPath) {
        Get-Content -LiteralPath $logPath | Write-Host
    }
    if (-not (Test-Path $resultPath)) {
        throw "The standard-user package gate did not record an exit code."
    }
    $gateExit = [int](Get-Content -LiteralPath $resultPath -Raw)
    if ($process.ExitCode -ne 0 -or $gateExit -ne 0) {
        throw "The standard-user package gate failed with exit $gateExit."
    }
} finally {
    Remove-Item $configPath, $runnerPath, $resultPath, $logPath `
        -Force -ErrorAction SilentlyContinue
    & icacls.exe $releaseDir /remove $userName /T /C /Q | Out-Null
    Remove-LocalUser -Name $userName -ErrorAction SilentlyContinue
}
