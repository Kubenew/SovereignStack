<#
.SYNOPSIS
    Build SovereignStack Windows release — Rust binaries + Python services + MSI installer.
.DESCRIPTION
    Produces a full Windows distribution under .\dist\SovereignStack-v<version>\:
      - ss-node.exe         (reference node HTTP server)
      - ss-cli.exe          (command-line client)
      - services/*.exe      (Python microservices bundled via PyInstaller)
      - config/             (default YAML/JSON configs)
      - README.html
    And optionally an MSI installer if WiX (candle.exe/light.exe) is on PATH.
.PARAMETER Version
    Release version string (default: reads from RELEASE-v*.md or VERSION file).
.PARAMETER SkipPyInstaller
    Skip bundling Python services (faster, for dev builds).
.PARAMETER SkipMsi
    Skip MSI generation even if WiX is available.
.EXAMPLE
    .\scripts\build-release.ps1
.EXAMPLE
    .\scripts\build-release.ps1 -Version "0.3.0" -SkipPyInstaller
#>

param(
    [string]$Version,
    [switch]$SkipPyInstaller,
    [switch]$SkipMsi
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $RepoRoot

# ── Detect version ──────────────────────────────────────────────────────────
if (-not $Version) {
    if (Test-Path "RELEASE-v*.md") {
        $Version = (Get-ChildItem "RELEASE-v*.md").Name -replace 'RELEASE-v|\.md'
    } else {
        $Version = "0.0.0-dev"
    }
}
Write-Host "Building SovereignStack v$Version for Windows..." -ForegroundColor Cyan

$DistDir = Join-Path $RepoRoot "dist\SovereignStack-v$Version"
if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
New-Item -ItemType Directory -Path "$DistDir\bin" -Force | Out-Null
New-Item -ItemType Directory -Path "$DistDir\services" -Force | Out-Null
New-Item -ItemType Directory -Path "$DistDir\config" -Force | Out-Null
New-Item -ItemType Directory -Path "$DistDir\docs" -Force | Out-Null

# ── 1. Build Rust binaries ─────────────────────────────────────────────────
Write-Host "`n[1/4] Building Rust binaries (release)..." -ForegroundColor Yellow
cargo build --release --bin ss-node --bin ss-cli
if (-not $?) { throw "Rust build failed" }

Copy-Item "target\release\ss-node.exe" "$DistDir\bin\"
Copy-Item "target\release\ss-cli.exe" "$DistDir\bin\"
Write-Host "  ✓ ss-node.exe, ss-cli.exe" -ForegroundColor Green

# ── 2. Bundle Python services via PyInstaller ───────────────────────────────
if (-not $SkipPyInstaller) {
    Write-Host "`n[2/4] Bundling Python services with PyInstaller..." -ForegroundColor Yellow
    $PythonServices = @(
        @{Name="gateway-service"; Entry="services/gateway_service.py"},
        @{Name="federation-service"; Entry="services/federation_service.py"},
        @{Name="merkle-audit"; Entry="services/merkle_audit.py"},
        @{Name="memory-service"; Entry="services/memory_service.py"},
        @{Name="logging-service"; Entry="services/logging_config.py"}
    )
    foreach ($svc in $PythonServices) {
        Write-Host "  Packaging $($svc.Name)..."
        $outDir = "dist\pyinstaller\$($svc.Name)"
        pyinstaller --onefile --distpath $outDir --noconsole $svc.Entry 2>&1 | Out-Null
        if (Test-Path "$outDir\$($svc.Name).exe") {
            Copy-Item "$outDir\$($svc.Name).exe" "$DistDir\services\"
            Write-Host "    ✓ $($svc.Name).exe" -ForegroundColor Green
        } else {
            Write-Host "    ⚠ $($svc.Name) — PyInstaller failed, skipping" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "`n[2/4] Skipping PyInstaller ( -SkipPyInstaller )" -ForegroundColor Yellow
}

# ── 3. Copy configs + docs ──────────────────────────────────────────────────
Write-Host "`n[3/4] Copying configs and docs..." -ForegroundColor Yellow
@("config", "*.yaml", "*.yml", "*.json", "*.toml") | ForEach-Object {
    $configs = Get-ChildItem -Path $RepoRoot -Filter $_ -File -Depth 2
    foreach ($cfg in $configs) { Copy-Item $cfg.FullName "$DistDir\config\" -ErrorAction SilentlyContinue }
}

@("README.md", "CERTIFICATION.md", "CONFORMANCE.md", "SECURITY.md", "URI_STANDARD.md") | ForEach-Object {
    if (Test-Path $_) { Copy-Item $_ "$DistDir\docs\" }
}

# Copy playground config if exists
if (Test-Path "playground\.env.example") { Copy-Item "playground\.env.example" "$DistDir\config\env.example" }

# ── 4. Generate MSI (WiX) ───────────────────────────────────────────────────
if (-not $SkipMsi) {
    $candle = Get-Command "candle.exe" -ErrorAction SilentlyContinue
    $light  = Get-Command "light.exe" -ErrorAction SilentlyContinue
    if ($candle -and $light) {
        Write-Host "`n[4/4] Generating MSI installer..." -ForegroundColor Yellow
        $WixObj = "dist\sovereignstack.wixobj"
        & $candle.Source -arch x64 -dVersion=$Version -out $WixObj "installer\sovereignstack.wxs"
        if ($?) {
            & $light.Source -out "dist\SovereignStack-v$Version.msi" $WixObj
            if ($?) { Write-Host "  ✓ SovereignStack-v$Version.msi" -ForegroundColor Green }
        }
    } else {
        Write-Host "`n[4/4] WiX not found — skipping MSI. Install WiX Toolset v4 from https://wixtoolset.org" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[4/4] Skipping MSI ( -SkipMsi )" -ForegroundColor Yellow
}

# ── Done ────────────────────────────────────────────────────────────────────
Write-Host "`n✅ SovereignStack v$Version Windows distribution ready:" -ForegroundColor Cyan
Write-Host "   $DistDir"
if (Test-Path "dist\SovereignStack-v$Version.msi") {
    Write-Host "   dist\SovereignStack-v$Version.msi"
}
Write-Host "`nBinaries:" -ForegroundColor White
Get-ChildItem "$DistDir\bin\*.exe" | ForEach-Object { Write-Host "   $($_.Name)  ($([math]::Round($_.Length/1KB)) KB)" }
