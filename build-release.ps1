# Bridge release bundle — zips a runnable no-git download (PRD M5 slice).
# Run from repo root:  powershell -ExecutionPolicy Bypass -File build-release.ps1
# Output: dist/bridge-<version>.zip (pages + backend + start-bridge.bat).
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root

$version = (Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw).Trim()
$dist = Join-Path $root 'dist'
New-Item -ItemType Directory -Path $dist -Force | Out-Null
$zip = Join-Path $dist "bridge-$version.zip"
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }

$stage = Join-Path $dist "stage-bridge-$version"
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage | Out-Null

# Pinned top-level files.
Copy-Item -LiteralPath (Join-Path $root 'VERSION') -Destination $stage
Copy-Item -LiteralPath (Join-Path $root 'README.md') -Destination $stage
Copy-Item -LiteralPath (Join-Path $root 'start-bridge.bat') -Destination $stage
Copy-Item -LiteralPath (Join-Path $root 'manifest.webmanifest') -Destination $stage
Copy-Item -LiteralPath (Join-Path $root 'sw.js') -Destination $stage
foreach ($p in @('index.html', 'send.html', 'history.html', 'pair.html', 'settings.html')) {
  Copy-Item -LiteralPath (Join-Path $root $p) -Destination $stage
}
foreach ($d in @('css', 'js', 'icons')) {
  Copy-Item -Path (Join-Path $root $d) -Destination (Join-Path $stage $d) -Recurse
}

# Backend: runtime only — no tests, caches, local DB, or uploaded files.
$backend = Join-Path $stage 'backend'
New-Item -ItemType Directory -Path $backend | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'backend/app.py') -Destination $backend
Copy-Item -LiteralPath (Join-Path $root 'backend/db.py') -Destination $backend
Copy-Item -LiteralPath (Join-Path $root 'backend/requirements.txt') -Destination $backend
$uploads = Join-Path $backend 'uploads'
New-Item -ItemType Directory -Path $uploads | Out-Null
New-Item -ItemType File -Path (Join-Path $uploads '.gitkeep') -Force | Out-Null

Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip
Remove-Item -LiteralPath $stage -Recurse -Force
Write-Output "bridge $version bundled -> $zip"
