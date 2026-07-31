<#
.SYNOPSIS
    Bump version, commit, tag and push to trigger GitHub release
.DESCRIPTION
    Usage: .\release.ps1
    Increments version: 2026.07.31 -> 2026.08.01 ...
#>

param()

$ErrorActionPreference = 'Stop'

# --- root directory (PSScriptRoot is empty when invoked via some hosts) ---
$root = $PSScriptRoot
if (-not $root) {
    $root = (Get-Location).Path
}

# --- helpers ---
function Get-CurrentVersion {
    $path = Join-Path $root 'src\ytdlp_gui\__init__.py'
    $content = Get-Content -LiteralPath $path -Raw
    if ($content -match '__version__\s*=\s*"([^"]+)"') {
        return $matches[1]
    }
    throw "Could not parse version from __init__.py"
}

function Update-File {
    param([string]$Path, [string]$Pattern, [string]$NewValue)
    $content = Get-Content -LiteralPath $Path -Raw
    $content = $content -replace $Pattern, $NewValue
    Set-Content -LiteralPath $Path -Value $content -NoNewline
    Write-Host "  Updated: $Path"
}

# --- main ---
$current = Get-CurrentVersion
$currentDate = [datetime]::ParseExact($current, 'yyyy.MM.dd', [Globalization.CultureInfo]::InvariantCulture)
$new = $currentDate.AddDays(1).ToString('yyyy.MM.dd')
$tag = "v$new"

Write-Host "`nRelease $current -> $new" -ForegroundColor Cyan
Write-Host "Tag: $tag`n" -ForegroundColor Cyan

# 1. Update version in __init__.py
$initPy = Join-Path $root 'src\ytdlp_gui\__init__.py'
Update-File -Path $initPy -Pattern '__version__\s*=\s*"[^"]*"' -Value "__version__ = `"$new`""

# 2. Update version in pyproject.toml
$toml = Join-Path $root 'pyproject.toml'
Update-File -Path $toml -Pattern '(?m)^version\s*=\s*"[^"]*"' -Value $new

# 3. Commit
Write-Host "`n  Committing..." -NoNewline
git -C $root add "$initPy" "$toml"
git -C $root commit -m "v$new"
Write-Host " done" -ForegroundColor Green

# 4. Tag
Write-Host "  Tagging..." -NoNewline
git -C $root tag $tag
Write-Host " done ($tag)" -ForegroundColor Green

# 5. Push
Write-Host "`n  Pushing commits..." -NoNewline
git -C $root push origin main
Write-Host " done" -ForegroundColor Green

Write-Host "  Pushing tag..." -NoNewline
git -C $root push origin $tag
Write-Host " done" -ForegroundColor Green

Write-Host "`n✓ Release $tag created!" -ForegroundColor Green
Write-Host "  CI is building on: https://github.com/vokrob/yt-dlp-gui/actions" -ForegroundColor Cyan
Write-Host "  Release will appear at: https://github.com/vokrob/yt-dlp-gui/releases`n" -ForegroundColor Cyan
