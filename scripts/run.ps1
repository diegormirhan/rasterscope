$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot\..
try {
    if (-not (Test-Path frontend\dist)) {
        Push-Location frontend
        try {
            npm run build
        }
        finally {
            Pop-Location
        }
    }
    uv run fastapi run --host 127.0.0.1 --port 8000
}
finally {
    Pop-Location
}
