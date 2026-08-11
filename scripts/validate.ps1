param(
    [switch]$UpdateHierarchy
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $projectRoot

$javaCandidates = @(@(
    (Get-Command java -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    'C:\Program Files\AnyLogic 8.9 Personal Learning Edition\jre\bin\java.exe',
    'C:\Program Files\PDF24\jre\bin\java.exe'
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
if (-not $javaCandidates) { throw 'Java 8+ is required for OWLAPI/HermiT validation.' }
$javaExe = $javaCandidates[0]

$pythonCandidates = @(@(
    $env:RSSO_PYTHON,
    'C:\Users\MarynaShapoval\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
    (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
if (-not $pythonCandidates) { throw 'Python 3.11+ is required for the test harness.' }
$pythonExe = $pythonCandidates[0]

$robot = Join-Path $projectRoot 'tools\robot.jar'
$catalog = Join-Path $projectRoot 'catalog-v001.xml'
$validationRoot = Join-Path $projectRoot 'ontology\validation.ttl'
$build = Join-Path $projectRoot 'build'
New-Item -ItemType Directory -Force -Path $build | Out-Null

$vendor = Join-Path $workspaceRoot 'gateB_poc\vendor'
if (Test-Path -LiteralPath $vendor) { $env:PYTHONPATH = $vendor }

& $javaExe -jar $robot validate-profile --catalog $catalog --input $validationRoot --profile DL --output (Join-Path $build 'owl2-dl-profile.txt')
if ($LASTEXITCODE -ne 0) { throw 'OWL 2 DL profile validation failed.' }

& $javaExe -jar $robot reason --catalog $catalog --input $validationRoot --reasoner HermiT --equivalent-classes-allowed none --output (Join-Path $build 'reasoned.owl')
if ($LASTEXITCODE -ne 0) { throw 'HermiT consistency/classification failed.' }

$etcsCase = Join-Path $projectRoot 'cases\etcs\abox.ttl'
& $javaExe -jar $robot validate-profile --catalog $catalog --input $etcsCase --profile DL --output (Join-Path $build 'etcs-owl2-dl-profile.txt')
if ($LASTEXITCODE -ne 0) { throw 'ETCS case OWL 2 DL profile validation failed.' }
& $javaExe -jar $robot reason --catalog $catalog --input $etcsCase --reasoner HermiT --equivalent-classes-allowed none --output (Join-Path $build 'etcs-reasoned.owl')
if ($LASTEXITCODE -ne 0) { throw 'ETCS case HermiT consistency/classification failed.' }

$currentHierarchy = Join-Path $build 'inferred-class-hierarchy.tsv'
& $pythonExe (Join-Path $PSScriptRoot 'write_inferred_hierarchy.py') (Join-Path $build 'reasoned.owl') $currentHierarchy
if ($LASTEXITCODE -ne 0) { throw 'Inferred hierarchy generation failed.' }
$committedHierarchy = Join-Path $projectRoot 'reports\inferred-class-hierarchy.tsv'
if ($UpdateHierarchy) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $committedHierarchy) | Out-Null
    Copy-Item -LiteralPath $currentHierarchy -Destination $committedHierarchy -Force
} elseif (-not (Test-Path -LiteralPath $committedHierarchy)) {
    throw 'Committed inferred hierarchy is missing. Run scripts\validate.ps1 -UpdateHierarchy after review.'
} elseif ((Get-FileHash $currentHierarchy).Hash -ne (Get-FileHash $committedHierarchy).Hash) {
    throw 'Inferred hierarchy changed. Inspect build\inferred-class-hierarchy.tsv and update deliberately.'
}

$currentMatrix = Join-Path $build 'entity-formalisation-matrix.tsv'
& $pythonExe (Join-Path $PSScriptRoot 'write_entity_matrix.py') $currentMatrix
if ($LASTEXITCODE -ne 0) { throw 'Entity formalisation matrix generation failed.' }
$committedMatrix = Join-Path $projectRoot 'reports\entity-formalisation-matrix.tsv'
if ($UpdateHierarchy) {
    Copy-Item -LiteralPath $currentMatrix -Destination $committedMatrix -Force
} elseif (-not (Test-Path -LiteralPath $committedMatrix)) {
    throw 'Committed entity formalisation matrix is missing.'
} elseif ((Get-FileHash $currentMatrix).Hash -ne (Get-FileHash $committedMatrix).Hash) {
    throw 'Entity formalisation matrix changed. Inspect the generated report and update deliberately.'
}

& $pythonExe (Join-Path $PSScriptRoot 'audit_formalisation.py')
if ($LASTEXITCODE -ne 0) { throw 'Frozen Gate B catalogue audit failed.' }

& $pythonExe (Join-Path $PSScriptRoot 'publication_lint.py') --root $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Module isolation/publication lint failed.' }

Push-Location $projectRoot
try {
    & $pythonExe -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Semantic/SHACL/CQ tests failed.' }
} finally {
    Pop-Location
}

$negativeLog = Join-Path $build 'expected-inconsistency.txt'
& $javaExe -jar $robot reason --catalog $catalog --input (Join-Path $projectRoot 'fixtures\reasoner\inconsistent.ttl') --reasoner HermiT --output (Join-Path $build 'must-not-exist.owl') 2>&1 | Set-Content -LiteralPath $negativeLog
if ($LASTEXITCODE -eq 0) { throw 'The deliberately inconsistent fixture was not rejected.' }

$categoryConflictLog = Join-Path $build 'expected-category-conflict.txt'
& $javaExe -jar $robot reason --catalog $catalog --input (Join-Path $projectRoot 'fixtures\reasoner\category-conflict.ttl') --reasoner HermiT --output (Join-Path $build 'category-conflict-must-not-exist.owl') 2>&1 | Set-Content -LiteralPath $categoryConflictLog
if ($LASTEXITCODE -eq 0) { throw 'A flow assigned to two disjoint transmission categories was not rejected.' }

Write-Output 'VALIDATION PASSED: OWL 2 DL, HermiT, hierarchy/matrix regression, Gate B audit, K-constraints, CQ suite and ETCS case.'
