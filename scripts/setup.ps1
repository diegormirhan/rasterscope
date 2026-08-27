$ErrorActionPreference = "Stop"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install it from https://docs.astral.sh/uv/."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js and npm are required. Install Node.js 22 or newer."
}

Push-Location $PSScriptRoot\..
try {
    uv sync --extra dev --extra ml
    Push-Location frontend
    try {
        npm ci
        npm run build
    }
    finally {
        Pop-Location
    }
}
finally {
    Pop-Location
}

Write-Host "RasterScope is ready. Run .\scripts\run.ps1 and open http://127.0.0.1:8000"
