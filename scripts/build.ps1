# Runs only on a Windows GitHub-hosted runner. Official SFX is EXTRACTED, never executed.
# All command exit codes checked immediately. SourceForge source archive is version-matched.
param(
  [Parameter(Mandatory=$false)][string]$Version = 'latest'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$work = Join-Path $root 'work'
$dist = Join-Path $root 'dist'
if (Test-Path -LiteralPath $work) { throw 'Refusing to reuse work/ staging. Clean git checkout required.' }
New-Item -ItemType Directory -Path $work -Force | Out-Null
python -m pip install --disable-pip-version-check --no-input 'PyYAML==6.0.2' 'Pillow==11.3.0'
if ($LASTEXITCODE -ne 0) { throw 'Python tool dependency installation failed' }
python -m unittest discover -s (Join-Path $root 'tests') -v
if ($LASTEXITCODE -ne 0) { throw 'Local static unit tests failed; refusing build' }
python (Join-Path $root 'scripts\verify_actions.py') (Join-Path $work 'shared-actions.json')
if ($LASTEXITCODE -ne 0) { throw 'Shared action verification failed' }
python (Join-Path $root 'scripts\resolve.py') --version $Version --out $work --builder-revision b1r3
if ($LASTEXITCODE -ne 0) { throw 'Official SourceForge release resolution/download/hash verification failed' }
$seven = Get-Command 7z.exe -ErrorAction SilentlyContinue | Select-Object -First 1
$sevenPath = $null
if ($seven) { $sevenPath = $seven.Source }
foreach($candidate in @('C:\Program Files\7-Zip\7z.exe','C:\Program Files (x86)\7-Zip\7z.exe')) {
  if (-not $sevenPath -and (Test-Path -LiteralPath $candidate)) { $sevenPath = $candidate }
}
if (-not $sevenPath) {
  choco install 7zip --yes --no-progress --limit-output
  if ($LASTEXITCODE -ne 0) { throw '7-Zip setup failed' }
  $sevenPath = 'C:\Program Files\7-Zip\7z.exe'
}
if (-not (Test-Path -LiteralPath $sevenPath)) { throw '7-Zip not found' }
$rawFull = Join-Path $work 'vendor-extracted'
$rawSource = Join-Path $work 'source-extracted'
New-Item -ItemType Directory -Path $rawFull, $rawSource | Out-Null
& $sevenPath x (Join-Path $work 'downloads\FileOptimizerFull.7z.exe') ('-o'+$rawFull) '-y' '-bd'
if ($LASTEXITCODE -ne 0) { throw 'Official self-extracting archive extraction failed' }
& $sevenPath x (Join-Path $work 'downloads\FileOptimizerSource.7z') ('-o'+$rawSource) '-y' '-bd'
if ($LASTEXITCODE -ne 0) { throw 'Official source archive extraction failed' }
python (Join-Path $root 'scripts\stage.py') --full $rawFull --source $rawSource --work $work --kit $root
if ($LASTEXITCODE -ne 0) { throw 'Application-specific source audit/staging failed' }
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path -LiteralPath $vswhere)) { throw 'Visual Studio vswhere missing on Windows runner' }
$vs = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if ($LASTEXITCODE -ne 0 -or -not $vs) { throw 'MSVC x64 compiler workload missing' }
$dev = Join-Path $vs 'Common7\Tools\VsDevCmd.bat'
if (-not (Test-Path -LiteralPath $dev)) { throw 'VsDevCmd.bat missing' }
$source = Join-Path $root 'launcher\FileOptimizerPortable.cpp'
$target = Join-Path $work 'stage\FileOptimizerCommunityPortable\FileOptimizerPortable.exe'
$commandFile = Join-Path $work 'compile-launcher.cmd'
# cmd environment setup must be in the same process as cl.exe. Disable echo and check codes.
$lines = @(
  '@echo off',
  'chcp 65001 >nul',
  'setlocal',
  "call `"$dev`" -arch=x64 -host_arch=x64 >nul",
  'if errorlevel 1 exit /b 10',
  "cl.exe /nologo /std:c++17 /EHsc /O2 /W4 /MT /DUNICODE /D_UNICODE `"$source`" /Fe:`"$target`" /link /SUBSYSTEM:WINDOWS advapi32.lib shell32.lib user32.lib bcrypt.lib",
  'if errorlevel 1 exit /b 11',
  'exit /b 0'
)
[System.IO.File]::WriteAllLines($commandFile, $lines, [System.Text.UTF8Encoding]::new($false))
& cmd.exe /d /c "`"$commandFile`""
if ($LASTEXITCODE -ne 0) { throw "Native PE root launcher compilation failed (exit $LASTEXITCODE)" }
python (Join-Path $root 'scripts\package.py') --work $work --dist $dist
if ($LASTEXITCODE -ne 0) { throw 'Independent ZIP validation failed' }
Write-Host 'PORTABLEAPPS ZIP VALIDATED; shared custom-nsis package builder can run next.'
