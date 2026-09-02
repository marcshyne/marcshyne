$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$snakePath = Join-Path $root "assets/contribution-game.svg"
$bannerPath = Join-Path $root "assets/trap-banner-v9.webp"
$readme = Get-Content -Raw -Encoding utf8 (Join-Path $root "README.md")
$snake = Get-Content -Raw -Encoding utf8 $snakePath

[xml]$snake | Out-Null
$foodCount = [regex]::Matches($snake, 'id="food-\d+"').Count
if ($snake -notmatch 'data-step-snake="true"' -or $snake -notmatch 'calcMode="discrete"' -or $foodCount -ne 14 -or $snake -notmatch 'SELF-BITE' -or $snake -notmatch 'dur="20s"') { throw "Cell snake cycle is incomplete" }
if ($readme -notmatch "trap-banner-v9\.webp" -or $readme -notmatch "contribution-game\.svg") { throw "README asset links are stale" }

$bytes = [IO.File]::ReadAllBytes($bannerPath)
$chunks = @()
$pos = 12
while ($pos + 8 -le $bytes.Length) {
    $id = [Text.Encoding]::ASCII.GetString($bytes, $pos, 4)
    $size = [BitConverter]::ToUInt32($bytes, $pos + 4)
    if ($id -eq "ANMF") { $chunks += $pos }
    $pos += 8 + $size + ($size % 2)
}
if ($chunks.Count -lt 100) { throw "Banner loop is incomplete" }
if ($bytes.Length -gt 5MB) { throw "Banner is too large for the profile" }

"Profile assets OK: $($chunks.Count)-frame banner loop, discrete cell snake with sequential food"
