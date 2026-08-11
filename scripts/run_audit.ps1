$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $projectRoot
$vendorPath = Join-Path $workspaceRoot 'gateB_poc\vendor'
$pythonExe = 'C:\Users\MarynaShapoval\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Bundled Python runtime not found: $pythonExe"
}

$env:PYTHONPATH = $vendorPath
& $pythonExe (Join-Path $PSScriptRoot 'audit_formalisation.py') @args
exit $LASTEXITCODE

