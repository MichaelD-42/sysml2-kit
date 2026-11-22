# Start the model explorer: build a kit project's docs, load it, serve http://127.0.0.1:8000.
# Usage: demo\start.ps1 [-Project <path>]   (default: the seat-switch RFQ example)
# The project's Makefile runs sh, find, sed and sort: put Git for Windows' usr\bin on PATH ahead of
# C:\Windows\System32, whose find.exe is another program.
param([string]$Project = (Join-Path $PSScriptRoot '..\examples\seat-switch-rfq'))
$ErrorActionPreference = 'Stop'
# a project given relative to where the script is called from, resolved before moving to demo\
$Project = (Resolve-Path $Project).Path
Set-Location $PSScriptRoot

foreach ($tool in 'uv', 'make', 'sysml', 'sysml2kit', 'sphinx-build') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Error "start.ps1: $tool is not on PATH (uv: https://docs.astral.sh/uv/; the kit's tools: make tools in the project)"
        exit 1
    }
}

uv sync --quiet
if ($LASTEXITCODE) { exit $LASTEXITCODE }
# rule violations are reported, not fatal, as with `make -C demo demo`
make -C $Project docs STRICT=
if ($LASTEXITCODE) { exit $LASTEXITCODE }
uv run python -m explorer.server $Project
exit $LASTEXITCODE
