<#
.SYNOPSIS
    Bump version, commit, tag and push to trigger GitHub release
.DESCRIPTION
    Usage: .\release.ps1 <patch|minor|major>

    Examples:
        .\release.ps1 patch   # 1.1.1 -> 1.1.2
        .\release.ps1 minor   # 1.1.1 -> 1.2.0
        .\release.ps1 major   # 1.1.1 -> 2.0.0
#>

param(
    [Parameter(Mandatory)]
    [ValidateSet('patch', 'minor', 'major')]
    [string]$Bump
)

$ErrorActionPreference = 'Stop'

# --- helpers ---
function Get-CurrentVersion {
    $path = Join-Path $PSScriptRoot 'src' 'ytdlp_gui' '__init__.py'
    $content = Get-Content -LiteralPath $path -Raw
    if ($content -match '__version__\s*=\s*"([^"]+)"') {
        return $matches[1]
    }
    throw "Could not parse version from __init__.py"
}

function Split-SemVer {
    param([string]$v)
    $parts = $v.Split('.')
    return @{
        major = [int]$parts[0]
        minor = [int]$parts[1]
        patch = [int]$parts[2]
    }
}

function Update-File {
    param([string]$Path, [string]$Pattern, [string]$NewValue)
    $content = Get-Content -LiteralPath $Path -Raw
    $content = $content -replace $Pattern, $NewValue
    Set-Content -LiteralPath $Path -Value $content -NoNewline
    Write-Host "  Updated: $Path"
}

# --- main ---
$root = $PSScriptRoot
$current = Get-CurrentVersion
$parts = Split-SemVer $current

switch ($Bump) {
    'patch' { $parts.patch += 1 }
    'minor' { $parts.minor += 1; $parts.patch = 0 }
    'major' { $parts.major += 1; $parts.minor = 0; $parts.patch = 0 }
}

$new = "$($parts.major).$($parts.minor).$($parts.patch)"
$tag = "v$new"

Write-Host "`nRelease $current -> $new ($Bump)" -ForegroundColor Cyan
Write-Host "Tag: $tag`n" -ForegroundColor Cyan

# 1. Update version in __init__.py
$initPy = Join-Path $root 'src' 'ytdlp_gui' '__init__.py'
Update-File -Path $initPy -Pattern '__version__\s*=\s*"[^"]*"' -Value "__version__ = `"$new`""

# 2. Update version in pyproject.toml
$toml = Join-Path $root 'pyproject.toml'
Update-File -Path $toml -Pattern '(?<=^version\s*=\s*")[^"]*' -Value $new

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
