$ErrorActionPreference = "Stop"

$Repo = "git+https://github.com/GuidanceStudio/aisk.git"
$InstallTarget = $Repo
$InstallSource = "GitHub"

if ($PSScriptRoot) {
    $ProjectFile = Join-Path $PSScriptRoot "pyproject.toml"
    $PackageDir = Join-Path $PSScriptRoot "src\aisk"
    if ((Test-Path -LiteralPath $ProjectFile) -and (Test-Path -LiteralPath $PackageDir)) {
        $InstallTarget = $PSScriptRoot
        $InstallSource = "local checkout"
    }
}

function Write-Step {
    param([string]$Text)
    Write-Host ""
    Write-Host $Text -ForegroundColor Cyan
}

function Add-UserBinToPath {
    $Candidates = @()
    if ($env:USERPROFILE) {
        $Candidates += Join-Path $env:USERPROFILE ".local\bin"
    }
    if ($HOME) {
        $Candidates += Join-Path $HOME ".local\bin"
    }

    foreach ($Path in ($Candidates | Select-Object -Unique)) {
        if ((Test-Path -LiteralPath $Path) -and -not ($env:Path -split [IO.Path]::PathSeparator | Where-Object { $_ -eq $Path })) {
            $env:Path = "$Path$([IO.Path]::PathSeparator)$env:Path"
        }
    }
}

Write-Host ""
Write-Host "--------------------------------------------------------------------------------"
Write-Host "  aisk - installer"
Write-Host "--------------------------------------------------------------------------------"

Add-UserBinToPath

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Step "uv not found - installing..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    Add-UserBinToPath
}

$Installed = $false
try {
    $ToolList = & uv tool list 2>$null
    if ($LASTEXITCODE -eq 0 -and ($ToolList -match "(?m)^aisk\s")) {
        $Installed = $true
    }
} catch {
    $Installed = $false
}

if ($Installed) {
    Write-Step "[1/3] Upgrading aisk"
    Write-Host "source: $InstallSource ($InstallTarget)"
    & uv tool install --force --upgrade $InstallTarget
} else {
    Write-Step "[1/3] Installing aisk"
    Write-Host "source: $InstallSource ($InstallTarget)"
    & uv tool install $InstallTarget
}

Add-UserBinToPath

Write-Step "[2/3] Setup"
& aisk init

Write-Step "[3/3] Done"
Write-Host "Open a new PowerShell window if 'aisk' is not on PATH yet."
Write-Host "Then run: aisk --version"
Write-Host "--------------------------------------------------------------------------------"
Write-Host ""
