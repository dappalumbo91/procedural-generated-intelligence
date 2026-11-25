Set-StrictMode -Version Latest
Set-Location $PSScriptRoot
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pgi --demo
exit $LASTEXITCODE
