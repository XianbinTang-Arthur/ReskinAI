[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$UseExistingServer,
    [switch]$KeepServer,
    [int]$StartupTimeoutSec = 60,
    [string]$PythonPath = ".\.venv\Scripts\python.exe",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([string]$Message)
    Write-Host "[verify-openai] $Message"
}

function Assert-Env {
    if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
        throw "OPENAI_API_KEY is empty in current shell. Please set it first."
    }
}

function Invoke-JsonApi {
    param(
        [string]$Method,
        [string]$Url,
        [object]$Body = $null,
        [string]$Token = ""
    )

    $headers = @{}
    if (-not [string]::IsNullOrWhiteSpace($Token)) {
        $headers["Authorization"] = "Bearer $Token"
    }

    if ($null -eq $Body) {
        return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers
    }

    $json = $Body | ConvertTo-Json -Depth 10
    return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers -ContentType "application/json" -Body $json
}

function Invoke-UploadApi {
    param(
        [string]$Url,
        [string]$Token,
        [string]$ConsentId,
        [byte[]]$FileBytes,
        [string]$FileName,
        [string]$ContentType
    )

    Add-Type -AssemblyName System.Net.Http | Out-Null

    $client = [System.Net.Http.HttpClient]::new()
    $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Post, $Url)
    $request.Headers.Authorization = [System.Net.Http.Headers.AuthenticationHeaderValue]::new("Bearer", $Token)

    $multipart = [System.Net.Http.MultipartFormDataContent]::new()
    $multipart.Add([System.Net.Http.StringContent]::new($ConsentId), "consent_id")

    $fileContent = [System.Net.Http.ByteArrayContent]::new($FileBytes)
    $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse($ContentType)
    $multipart.Add($fileContent, "file", $FileName)
    $request.Content = $multipart

    try {
        $response = $client.SendAsync($request).GetAwaiter().GetResult()
        $raw = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            throw "Upload API failed ($([int]$response.StatusCode)): $raw"
        }
        return $raw | ConvertFrom-Json
    }
    finally {
        $multipart.Dispose()
        $request.Dispose()
        $client.Dispose()
    }
}

function Wait-ForHealth {
    param(
        [string]$HealthUrl,
        [int]$TimeoutSec
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $health = Invoke-RestMethod -Method Get -Uri $HealthUrl -TimeoutSec 5
            if ($health.status -eq "ok") {
                return $health
            }
        }
        catch {
            Start-Sleep -Milliseconds 700
        }
    }
    throw "Health check timed out after ${TimeoutSec}s: $HealthUrl"
}

function Stop-UvicornProcesses {
    $targets = Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and
        $_.CommandLine -match "uvicorn" -and
        $_.CommandLine -match "reskin_ai\.main:app"
    }

    foreach ($proc in $targets) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
            Write-Step "Stopped old uvicorn process PID=$($proc.ProcessId)"
        }
        catch {
            Write-Step "Skip stopping PID=$($proc.ProcessId): $($_.Exception.Message)"
        }
    }
}

function Resolve-PythonExe {
    param(
        [string]$RepoRoot,
        [string]$PathHint
    )

    if ([System.IO.Path]::IsPathRooted($PathHint)) {
        return $PathHint
    }
    return (Join-Path $RepoRoot $PathHint)
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$baseUri = [Uri]$BaseUrl
$healthUrl = "$($baseUri.Scheme)://$($baseUri.Host):$($baseUri.Port)/healthz"
$pythonExe = Resolve-PythonExe -RepoRoot $repoRoot -PathHint $PythonPath
$stdoutLog = Join-Path $repoRoot "storage\verify-openai-uvicorn.out.log"
$stderrLog = Join-Path $repoRoot "storage\verify-openai-uvicorn.err.log"

if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found: $pythonExe"
}

if ($DryRun) {
    Write-Step "DryRun enabled."
    Write-Step "BaseUrl=$BaseUrl"
    Write-Step "UseExistingServer=$UseExistingServer"
    Write-Step "KeepServer=$KeepServer"
    Write-Step "PythonExe=$pythonExe"
    Write-Step "HealthUrl=$healthUrl"
    exit 0
}

Assert-Env

$startedServer = $false
$serverProcess = $null

try {
    if (-not $UseExistingServer) {
        Stop-UvicornProcesses

        $escapedRepo = $repoRoot.Replace("'", "''")
        $escapedPy = $pythonExe.Replace("'", "''")
        $escapedHost = $baseUri.Host.Replace("'", "''")
        $port = $baseUri.Port
        $escapedKey = $env:OPENAI_API_KEY.Replace("'", "''")

        $launchScript = @"
`$env:MODEL_PROVIDER='openai'
`$env:MODEL_FALLBACK_ENABLED='false'
`$env:OPENAI_API_KEY='$escapedKey'
Set-Location '$escapedRepo'
& '$escapedPy' -m uvicorn reskin_ai.main:app --host $escapedHost --port $port
"@

        Write-Step "Starting uvicorn with MODEL_PROVIDER=openai and MODEL_FALLBACK_ENABLED=false"
        $serverProcess = Start-Process `
            -FilePath "powershell" `
            -ArgumentList "-NoProfile", "-Command", $launchScript `
            -PassThru `
            -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutLog `
            -RedirectStandardError $stderrLog
        $startedServer = $true
        Write-Step "Started uvicorn PID=$($serverProcess.Id)"
    }

    Write-Step "Waiting for health endpoint..."
    $health = Wait-ForHealth -HealthUrl $healthUrl -TimeoutSec $StartupTimeoutSec
    Write-Step "Health ready: env=$($health.env), model_provider=$($health.model_provider), fallback_enabled=$($health.fallback_enabled)"

    $sessionUser = Invoke-JsonApi -Method "POST" -Url "$BaseUrl/api/v1/auth/session" -Body @{ role = "user" }
    $userToken = [string]$sessionUser.token

    $consent = Invoke-JsonApi `
        -Method "POST" `
        -Url "$BaseUrl/api/v1/consents" `
        -Token $userToken `
        -Body @{
            policy_version = "consent-v1"
            disclaimer_accepted = $true
        }

    $preference = Invoke-JsonApi `
        -Method "POST" `
        -Url "$BaseUrl/api/v1/preferences" `
        -Token $userToken `
        -Body @{
            style = "floral"
            motifs = @("lotus", "line-art")
            meaning_keywords = @("healing", "growth")
            avoid_list = @("text-overlay")
            mood = "calm"
        }

    $tinyPngB64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO6sN7sAAAAASUVORK5CYII="
    $imageBytes = [Convert]::FromBase64String($tinyPngB64)
    $upload = Invoke-UploadApi `
        -Url "$BaseUrl/api/v1/uploads/file" `
        -Token $userToken `
        -ConsentId ([string]$consent.id) `
        -FileBytes $imageBytes `
        -FileName "scar.png" `
        -ContentType "image/png"

    $generation = Invoke-JsonApi `
        -Method "POST" `
        -Url "$BaseUrl/api/v1/generations" `
        -Token $userToken `
        -Body @{
            upload_id = [string]$upload.id
            preference_id = [string]$preference.id
            variant_count = 1
        }

    if ([string]$generation.status -ne "completed") {
        throw "Generation status is not completed: $($generation.status)"
    }
    if (-not $generation.concepts -or $generation.concepts.Count -lt 1) {
        throw "No concepts returned from generation."
    }
    $conceptUri = [string]$generation.concepts[0].storage_uri
    if ($conceptUri -match "\.svg($|\?)") {
        throw "Concept URI is SVG fallback: $conceptUri"
    }

    $sessionAdmin = Invoke-JsonApi -Method "POST" -Url "$BaseUrl/api/v1/auth/session" -Body @{ role = "admin" }
    $metrics = Invoke-JsonApi -Method "GET" -Url "$BaseUrl/api/v1/admin/metrics" -Token ([string]$sessionAdmin.token)
    $provider = [string]$metrics.diagnostics.last_generation_provider
    if ($provider -ne "openai") {
        throw "last_generation_provider is '$provider' (expected 'openai')."
    }

    Write-Step "PASS"
    Write-Step "generation_id=$($generation.id)"
    Write-Step "concept_uri=$conceptUri"
    Write-Step "last_generation_provider=$provider"
    exit 0
}
catch {
    Write-Error "[verify-openai] FAILED: $($_.Exception.Message)"
    if (-not $UseExistingServer) {
        Write-Step "Logs: $stdoutLog"
        Write-Step "Logs: $stderrLog"
    }
    exit 1
}
finally {
    if ($startedServer -and -not $KeepServer -and $null -ne $serverProcess) {
        try {
            Stop-Process -Id $serverProcess.Id -Force -ErrorAction Stop
            Write-Step "Stopped uvicorn PID=$($serverProcess.Id)"
        }
        catch {
            Write-Step "Failed to stop uvicorn PID=$($serverProcess.Id): $($_.Exception.Message)"
        }
    }
}
