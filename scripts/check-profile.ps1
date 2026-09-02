$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$snakePath = Join-Path $root "assets/contribution-game.svg"
$bannerPath = Join-Path $root "assets/trap-banner-v4.webp"
$readme = Get-Content -Raw -Encoding utf8 (Join-Path $root "README.md")
$snake = Get-Content -Raw -Encoding utf8 $snakePath

[xml]$snake | Out-Null
$foodCount = [regex]::Matches($snake, 'id="food-\d+"').Count
if ($snake -notmatch 'data-step-snake="true"' -or $snake -notmatch 'calcMode="discrete"' -or $foodCount -ne 14 -or $snake -notmatch 'SELF-BITE' -or $snake -notmatch 'dur="20s"') { throw "Cell snake cycle is incomplete" }
if ($readme -notmatch "trap-banner-v4\.webp" -or $readme -notmatch "contribution-game\.svg") { throw "README asset links are stale" }

$bytes = [IO.File]::ReadAllBytes($bannerPath)
$frames = [regex]::Matches([Text.Encoding]::ASCII.GetString($bytes), "ANMF").Count
if ($frames -lt 2) { throw "Banner is not animated" }

"Profile assets OK: $frames banner frames, discrete cell snake with sequential food"
