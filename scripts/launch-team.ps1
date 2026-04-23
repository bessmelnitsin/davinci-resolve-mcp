# Launch a DaVinci Resolve MCP agent team.
#
# Spins up one server process per role, each on its own port, all sharing
# the local DaVinci Resolve instance. Concurrent page switches are
# coordinated by a two-level lock:
#   - PageLock (in-process)       — serializes tool calls within one server
#   - ProcessFileLock (OS file)   — serializes page switches across servers
#
# Health probe: GET http://127.0.0.1:<port>/health  (no auth required)
#
# Usage:
#   # Per-role tokens (recommended — each agent gets its own credential)
#   $env:MCP_AUTH_TOKENS = "color:ctok,deliver:dtok,edit:etok,director:drtok"
#   .\scripts\launch-team.ps1
#
#   # Shared token (simpler)
#   $env:MCP_AUTH_TOKEN = "s3cret"
#   .\scripts\launch-team.ps1
#
# Stop all servers: close this window, or Ctrl+C each child.

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot "venv\Scripts\python.exe"
$main = Join-Path $projectRoot "src\main.py"

if (-not (Test-Path $python)) {
    Write-Error "Python venv not found at $python. Run: python -m venv venv; venv\Scripts\activate; pip install -r requirements.txt"
    exit 1
}

if (-not $env:MCP_AUTH_TOKEN -and -not $env:MCP_AUTH_TOKENS) {
    Write-Error "Set MCP_AUTH_TOKEN=<t> or MCP_AUTH_TOKENS=role:tok,role:tok before launching."
    exit 2
}

# role -> port
$team = @{
    "media"     = 8100
    "edit"      = 8101
    "color"     = 8102
    "fusion"    = 8103
    "fairlight" = 8104
    "deliver"   = 8105
    "director"  = 8106
}

$jobs = @()
foreach ($entry in $team.GetEnumerator()) {
    $role = $entry.Key
    $port = $entry.Value
    Write-Host "-> Starting $role on port $port"
    $p = Start-Process -FilePath $python `
        -ArgumentList $main, "--role", $role, "--transport", "http", "--port", $port `
        -PassThru -NoNewWindow
    $jobs += [pscustomobject]@{ Role = $role; Port = $port; Pid = $p.Id }
}

Write-Host ""
Write-Host "Agent team running:"
$jobs | Format-Table -AutoSize

Write-Host "Press Ctrl+C to stop all servers..."
try {
    while ($true) { Start-Sleep -Seconds 60 }
} finally {
    foreach ($j in $jobs) {
        try { Stop-Process -Id $j.Pid -Force -ErrorAction SilentlyContinue } catch {}
    }
}
