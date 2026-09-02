$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$snakePath = Join-Path $root "assets/contribution-game.svg"
$bannerPath = Join-Path $root "assets/trap-banner-v3.webp"
$readme = Get-Content -Raw -Encoding utf8 (Join-Path $root "README.md")
$snake = Get-Content -Raw -Encoding utf8 $snakePath

[xml]$snake | Out-Null
if ($snake -notmatch 'repeatCount="indefinite"' -or $snake -notmatch 'GAME OVER' -or $snake -notmatch 'RESPAWN ENABLED' -or $snake -notmatch 'dur="15s"') { throw "Snake restart cycle is incomplete" }
if ($readme -notmatch "trap-banner-v3\.webp" -or $readme -notmatch "contribution-game\.svg") { throw "README asset links are stale" }

$bytes = [IO.File]::ReadAllBytes($bannerPath)
$frames = [regex]::Matches([Text.Encoding]::ASCII.GetString($bytes), "ANMF").Count
if ($frames -lt 2) { throw "Banner is not animated" }

"Profile assets OK: $frames banner frames, looping snake game"
