$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$snakePath = Join-Path $root "assets/contribution-game.svg"
$bannerPath = Join-Path $root "assets/trap-banner-v5.webp"
$readme = Get-Content -Raw -Encoding utf8 (Join-Path $root "README.md")
$snake = Get-Content -Raw -Encoding utf8 $snakePath

[xml]$snake | Out-Null
$foodCount = [regex]::Matches($snake, 'id="food-\d+"').Count
if ($snake -notmatch 'data-step-snake="true"' -or $snake -notmatch 'calcMode="discrete"' -or $foodCount -ne 14 -or $snake -notmatch 'SELF-BITE' -or $snake -notmatch 'dur="20s"') { throw "Cell snake cycle is incomplete" }
if ($readme -notmatch "trap-banner-v5\.webp" -or $readme -notmatch "contribution-game\.svg") { throw "README asset links are stale" }

$bytes = [IO.File]::ReadAllBytes($bannerPath)
$chunks = [regex]::Matches([Text.Encoding]::ASCII.GetString($bytes), "ANMF")
$frames = $chunks.Count
if ($frames -lt 2) { throw "Banner is not animated" }
foreach ($chunk in $chunks | Select-Object -Skip 1) {
    $p = $chunk.Index + 8
    $x = 2 * ($bytes[$p] -bor ($bytes[$p + 1] -shl 8) -bor ($bytes[$p + 2] -shl 16))
    $w = 1 + ($bytes[$p + 6] -bor ($bytes[$p + 7] -shl 8) -bor ($bytes[$p + 8] -shl 16))
    if ($x -lt 200 -or $x + $w -gt 520) { throw "Banner motion escaped the syrup area" }
}

"Profile assets OK: $frames banner frames, discrete cell snake with sequential food"
