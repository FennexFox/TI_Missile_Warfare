<#
.SYNOPSIS
Build and deploy the MissileWarfare Unity Mod Manager mod.

.DESCRIPTION
The script builds the mod project, stages the UMM mod folder under dist, and
copies it into the Terra Invicta Mods directory for in-game testing.

Local paths can come from Directory.Build.props, environment variables, or
explicit parameters. Explicit parameters win.

.EXAMPLE
.\build.ps1

.EXAMPLE
.\build.ps1 -GameDir "C:\Program Files (x86)\Steam\steamapps\common\Terra Invicta" -UnityModManagerDir "C:\Tools\UnityModManager"

.EXAMPLE
.\build.ps1 -Configuration Release -NoDeploy
#>

[CmdletBinding()]
param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug",

    [string]$TargetFramework = "net48",

    [string]$GameDir,

    [string]$ModsDir,

    [string]$TerraInvictaManagedDir,

    [string]$UnityModManagerDir,

    [string]$OutputDir,

    [switch]$NoDeploy,

    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ModProject = Join-Path $Root "src\MissileFireControl.Mod\MissileFireControl.Mod.csproj"
$ModInfoFile = Join-Path $Root "ModInfo.json"
$PropsFile = Join-Path $Root "Directory.Build.props"

function ConvertTo-FullPath {
    param(
        [AllowNull()]
        [string]$PathValue
    )

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $null
    }

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $Root $PathValue))
}

function Get-LocalBuildProperty {
    param([string]$Name)

    if (-not (Test-Path -LiteralPath $PropsFile)) {
        return $null
    }

    [xml]$props = Get-Content -LiteralPath $PropsFile -Raw
    $node = $props.SelectSingleNode("//$Name")
    if ($null -eq $node) {
        return $null
    }

    $value = $node.InnerText.Trim()
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $null
    }

    return $value
}

function Find-DefaultGameDir {
    $candidates = @(
        $env:TERRA_INVICTA_DIR,
        "C:\Program Files (x86)\Steam\steamapps\common\Terra Invicta",
        "C:\Program Files\Steam\steamapps\common\Terra Invicta"
    )

    foreach ($candidate in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Get-GameDirFromManagedDir {
    param([string]$ManagedDir)

    if ([string]::IsNullOrWhiteSpace($ManagedDir)) {
        return $null
    }

    $fullManagedDir = ConvertTo-FullPath $ManagedDir
    $managedLeaf = Split-Path -Leaf $fullManagedDir
    $dataDir = Split-Path -Parent $fullManagedDir
    $dataLeaf = Split-Path -Leaf $dataDir

    if ($managedLeaf -eq "Managed" -and $dataLeaf -eq "TerraInvicta_Data") {
        return Split-Path -Parent $dataDir
    }

    return $null
}

function Stop-Build {
    param([string]$Message)

    [Console]::Error.WriteLine($Message.Trim())
    exit 1
}

function Assert-FileExists {
    param(
        [string]$PathValue,
        [string]$Description
    )

    if (-not (Test-Path -LiteralPath $PathValue -PathType Leaf)) {
        Stop-Build "$Description not found: $PathValue"
    }
}

function Invoke-DotNet {
    param([string[]]$Arguments)

    & dotnet @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet failed with exit code $LASTEXITCODE"
    }
}

$modMetadata = Get-Content -LiteralPath $ModInfoFile -Raw | ConvertFrom-Json
$modId = $modMetadata.Id
if ([string]::IsNullOrWhiteSpace($modId)) {
    Stop-Build "ModInfo.json must contain an Id."
}

$propTerraInvictaManagedDir = Get-LocalBuildProperty "TerraInvictaManagedDir"
$propUnityModManagerDir = Get-LocalBuildProperty "UnityModManagerDir"

if ([string]::IsNullOrWhiteSpace($GameDir)) {
    $GameDir = Find-DefaultGameDir
}

if ([string]::IsNullOrWhiteSpace($TerraInvictaManagedDir) -and -not [string]::IsNullOrWhiteSpace($env:TERRA_INVICTA_MANAGED_DIR)) {
    $TerraInvictaManagedDir = $env:TERRA_INVICTA_MANAGED_DIR
}

if ([string]::IsNullOrWhiteSpace($TerraInvictaManagedDir) -and -not [string]::IsNullOrWhiteSpace($propTerraInvictaManagedDir)) {
    $TerraInvictaManagedDir = $propTerraInvictaManagedDir
}

if ([string]::IsNullOrWhiteSpace($TerraInvictaManagedDir) -and -not [string]::IsNullOrWhiteSpace($GameDir)) {
    $TerraInvictaManagedDir = Join-Path $GameDir "TerraInvicta_Data\Managed"
}

if ([string]::IsNullOrWhiteSpace($GameDir) -and -not [string]::IsNullOrWhiteSpace($TerraInvictaManagedDir)) {
    $GameDir = Get-GameDirFromManagedDir $TerraInvictaManagedDir
}

if ([string]::IsNullOrWhiteSpace($UnityModManagerDir) -and -not [string]::IsNullOrWhiteSpace($env:UNITY_MOD_MANAGER_DIR)) {
    $UnityModManagerDir = $env:UNITY_MOD_MANAGER_DIR
}

if ([string]::IsNullOrWhiteSpace($UnityModManagerDir) -and -not [string]::IsNullOrWhiteSpace($propUnityModManagerDir)) {
    $UnityModManagerDir = $propUnityModManagerDir
}

$GameDir = ConvertTo-FullPath $GameDir
$ModsDir = ConvertTo-FullPath $ModsDir
$TerraInvictaManagedDir = ConvertTo-FullPath $TerraInvictaManagedDir
$UnityModManagerDir = ConvertTo-FullPath $UnityModManagerDir

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $Root "dist\$modId"
}
$OutputDir = ConvertTo-FullPath $OutputDir

if ([string]::IsNullOrWhiteSpace($TerraInvictaManagedDir) -or [string]::IsNullOrWhiteSpace($UnityModManagerDir)) {
    Stop-Build @"
Missing build reference paths.

Either create Directory.Build.props from Directory.Build.props.example, or pass:
  .\build.ps1 -GameDir "C:\Path\To\Terra Invicta" -UnityModManagerDir "C:\Path\To\UnityModManager"

You can also set TERRA_INVICTA_MANAGED_DIR and UNITY_MOD_MANAGER_DIR.
"@
}

Assert-FileExists (Join-Path $TerraInvictaManagedDir "Assembly-CSharp.dll") "Terra Invicta Assembly-CSharp.dll"
Assert-FileExists (Join-Path $TerraInvictaManagedDir "UnityEngine.CoreModule.dll") "UnityEngine.CoreModule.dll"
Assert-FileExists (Join-Path $UnityModManagerDir "UnityModManager.dll") "UnityModManager.dll"
Assert-FileExists (Join-Path $UnityModManagerDir "0Harmony.dll") "0Harmony.dll"

$msbuildProperties = @(
    "/p:TerraInvictaManagedDir=$TerraInvictaManagedDir",
    "/p:UnityModManagerDir=$UnityModManagerDir"
)

if ($Clean) {
    Write-Host "Cleaning $Configuration $TargetFramework..."
    Invoke-DotNet (@(
        "clean",
        $ModProject,
        "--configuration",
        $Configuration,
        "--framework",
        $TargetFramework,
        "--nologo"
    ) + $msbuildProperties)
}

Write-Host "Building $Configuration $TargetFramework..."
try {
    Invoke-DotNet (@(
        "build",
        $ModProject,
        "--configuration",
        $Configuration,
        "--framework",
        $TargetFramework,
        "--nologo"
    ) + $msbuildProperties)
}
catch {
    Stop-Build "$($_.Exception.Message). Check that the .NET Framework 4.8 targeting pack is installed and the local reference paths are correct."
}

$buildOutputDir = Join-Path $Root "src\MissileFireControl.Mod\bin\$Configuration\$TargetFramework"
$modDll = Join-Path $buildOutputDir "MissileFireControl.Mod.dll"
Assert-FileExists $modDll "Built mod DLL"

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$legacyModFile = Join-Path $OutputDir "ModFile.json"
Remove-Item -LiteralPath $legacyModFile -Force -ErrorAction SilentlyContinue

Copy-Item -LiteralPath $ModInfoFile -Destination (Join-Path $OutputDir "ModInfo.json") -Force

$artifactPatterns = @("MissileFireControl.*.dll", "MissileFireControl.*.pdb")
foreach ($pattern in $artifactPatterns) {
    Get-ChildItem -LiteralPath $buildOutputDir -Filter $pattern -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $OutputDir $_.Name) -Force
    }
}

Write-Host "Packaged: $OutputDir"

if (-not $NoDeploy) {
    if ([string]::IsNullOrWhiteSpace($ModsDir)) {
        if ([string]::IsNullOrWhiteSpace($GameDir)) {
            Stop-Build "Packaged successfully, but no Terra Invicta game directory was found. Re-run with -GameDir, -ModsDir, or -NoDeploy."
        }

        $ModsDir = Join-Path $GameDir "Mods\Enabled"
    }

    $deployDir = Join-Path $ModsDir $modId
    New-Item -ItemType Directory -Force -Path $deployDir | Out-Null

    $legacyDeployedModFile = Join-Path $deployDir "ModFile.json"
    Remove-Item -LiteralPath $legacyDeployedModFile -Force -ErrorAction SilentlyContinue

    Get-ChildItem -LiteralPath $OutputDir -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $deployDir $_.Name) -Force
    }

    Write-Host "Deployed: $deployDir"
}

Write-Host "Done."
