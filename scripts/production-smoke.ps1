param(
    [string]$FrontendUrl,
    [string]$BackendUrl,
    [int]$TimeoutSeconds = 10,
    [switch]$AllowUnconfiguredAI,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[smoke] $Message"
}

function Stop-Smoke {
    param([string]$Message)
    Write-Error "[smoke] $Message"
    exit 1
}

function Show-Usage {
    Write-Host "Usage:"
    Write-Host "  .\scripts\production-smoke.ps1 -FrontendUrl https://your-app.vercel.app -BackendUrl https://your-api.onrender.com"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -TimeoutSeconds 10        Request timeout for each check."
    Write-Host "  -AllowUnconfiguredAI      Do not fail if the AI provider reports configuration issues."
}

function Normalize-Url {
    param([string]$Url)
    return $Url.Trim().TrimEnd("/")
}

function Invoke-SmokeJson {
    param([string]$Url)
    return Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec $TimeoutSeconds -Headers @{ Accept = "application/json" }
}

if ($Help) {
    Show-Usage
    exit 0
}

if ([string]::IsNullOrWhiteSpace($FrontendUrl) -or [string]::IsNullOrWhiteSpace($BackendUrl)) {
    Show-Usage
    exit 64
}

$frontend = Normalize-Url -Url $FrontendUrl
$backend = Normalize-Url -Url $BackendUrl

Write-Step "Checking frontend: $frontend"
$frontendResponse = Invoke-WebRequest -Uri $frontend -Method Get -TimeoutSec $TimeoutSeconds -UseBasicParsing
if ($frontendResponse.StatusCode -lt 200 -or $frontendResponse.StatusCode -ge 400) {
    Stop-Smoke "Frontend returned HTTP $($frontendResponse.StatusCode)."
}
if ($frontendResponse.Content -notmatch "Snipe" -and $frontendResponse.Content -notmatch "<html") {
    Stop-Smoke "Frontend response did not look like the Snipe app shell."
}
Write-Step "Frontend OK: HTTP $($frontendResponse.StatusCode)"

$healthUrl = "$backend/api/v1/health"
Write-Step "Checking backend health: $healthUrl"
$health = Invoke-SmokeJson -Url $healthUrl
if ($health.status -ne "ok") {
    Stop-Smoke "Backend health status was '$($health.status)', expected 'ok'."
}
Write-Step "Backend OK: $($health.service) $($health.version) [$($health.environment)]"

$aiProviderUrl = "$backend/api/v1/health/ai-provider"
Write-Step "Checking AI provider configuration: $aiProviderUrl"
$aiProvider = Invoke-SmokeJson -Url $aiProviderUrl
Write-Step "AI provider: provider=$($aiProvider.provider), model=$($aiProvider.model_name), mode=$($aiProvider.mode)"
if (-not $aiProvider.configured -and -not $AllowUnconfiguredAI) {
    $issues = ($aiProvider.issues -join "; ")
    Stop-Smoke "AI provider is not configured: $issues"
}
if ($aiProvider.PSObject.Properties.Name -contains "ai_api_key") {
    Stop-Smoke "AI provider status exposed an API key field."
}
if ($aiProvider.PSObject.Properties.Name -contains "api_key") {
    Stop-Smoke "AI provider status exposed an API key value field."
}
Write-Step "AI provider OK: configured=$($aiProvider.configured), key-present=$($aiProvider.api_key_configured)"

Write-Host ""
Write-Host "Production smoke checks passed."
