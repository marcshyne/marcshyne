$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$snakePath = Join-Path $root "assets/contribution-game.svg"
$bannerPath = Join-Path $root "assets/trap-banner-v2.webp"
$readme = Get-Content -Raw -Encoding utf8 (Join-Path $root "README.md")
$snake = Get-Content -Raw -Encoding utf8 $snakePath

[xml]$snake | Out-Null
if ($snake -match "indefinite") { throw "Snake must stop after Game Over" }
if ($readme -notmatch "trap-banner-v2\.webp" -or $readme -notmatch "contribution-game\.svg") { throw "README asset links are stale" }

$bytes = [IO.File]::ReadAllBytes($bannerPath)
$frames = [regex]::Matches([Text.Encoding]::ASCII.GetString($bytes), "ANMF").Count
if ($frames -lt 2) { throw "Banner is not animated" }

"Profile assets OK: $frames banner frames, finite snake"
