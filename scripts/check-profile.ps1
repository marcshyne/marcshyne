$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$snakePath = Join-Path $root "assets/contribution-game.svg"
$bannerPath = Join-Path $root "assets/trap-banner-v7.webp"
$readme = Get-Content -Raw -Encoding utf8 (Join-Path $root "README.md")
$snake = Get-Content -Raw -Encoding utf8 $snakePath

[xml]$snake | Out-Null
$foodCount = [regex]::Matches($snake, 'id="food-\d+"').Count
if ($snake -notmatch 'data-step-snake="true"' -or $snake -notmatch 'calcMode="discrete"' -or $foodCount -ne 14 -or $snake -notmatch 'SELF-BITE' -or $snake -notmatch 'dur="20s"') { throw "Cell snake cycle is incomplete" }
if ($readme -notmatch "trap-banner-v7\.webp" -or $readme -notmatch "contribution-game\.svg") { throw "README asset links are stale" }

$bytes = [IO.File]::ReadAllBytes($bannerPath)
$chunks = @()
$pos = 12
while ($pos + 8 -le $bytes.Length) {
    $id = [Text.Encoding]::ASCII.GetString($bytes, $pos, 4)
    $size = [BitConverter]::ToUInt32($bytes, $pos + 4)
    if ($id -eq "ANMF") { $chunks += $pos }
    $pos += 8 + $size + ($size % 2)
}
if ($chunks.Count -lt 2) { throw "Banner is not animated" }
foreach ($chunk in $chunks | Select-Object -Skip 1) {
    $p = $chunk + 8
    $x = 2 * (([int]$bytes[$p]) -bor (([int]$bytes[$p + 1]) -shl 8) -bor (([int]$bytes[$p + 2]) -shl 16))
    $y = 2 * (([int]$bytes[$p + 3]) -bor (([int]$bytes[$p + 4]) -shl 8) -bor (([int]$bytes[$p + 5]) -shl 16))
    $w = 1 + (([int]$bytes[$p + 6]) -bor (([int]$bytes[$p + 7]) -shl 8) -bor (([int]$bytes[$p + 8]) -shl 16))
    $h = 1 + (([int]$bytes[$p + 9]) -bor (([int]$bytes[$p + 10]) -shl 8) -bor (([int]$bytes[$p + 11]) -shl 16))
    if ($x -lt 760 -or $y -lt 70 -or $x + $w -gt 1080 -or $y + $h -gt 210) { throw "Banner motion escaped the MARC SHYNE heading" }
}

"Profile assets OK: $($chunks.Count) text-shimmer frames, discrete cell snake with sequential food"
