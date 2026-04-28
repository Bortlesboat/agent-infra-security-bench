[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BillingProject,
    [string]$NamePrefix = "agent-bench-night",
    [string[]]$Zones = @("europe-west4-a", "us-east1-d"),
    [int]$SleepSeconds = 28800,
    [string]$LogPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

function Write-WatchdogLog {
    param([string]$Message)

    $line = "$(Get-Date -Format o) $Message"
    if ($LogPath) {
        $parent = Split-Path -Parent $LogPath
        if ($parent) {
            [void](New-Item -ItemType Directory -Path $parent -Force)
        }
        Add-Content -Path $LogPath -Value $line -Encoding utf8
    }
    Write-Host $line
}

Write-WatchdogLog "watchdog sleeping for $SleepSeconds seconds"
Start-Sleep -Seconds $SleepSeconds

foreach ($zone in $Zones) {
    Write-WatchdogLog "checking TPU VMs in $zone"
    $json = & gcloud compute tpus tpu-vm list --zone=$zone --format=json 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-WatchdogLog "list failed in ${zone}: $json"
        continue
    }

    $nodes = @()
    try {
        $nodes = $json | ConvertFrom-Json
    }
    catch {
        Write-WatchdogLog "could not parse list JSON in ${zone}: $($_.Exception.Message)"
        continue
    }

    foreach ($node in $nodes) {
        $shortName = ($node.name -split "/")[-1]
        if ($shortName -like "$NamePrefix*") {
            Write-WatchdogLog "deleting $shortName in $zone"
            & gcloud compute tpus tpu-vm delete $shortName --zone=$zone --quiet 2>&1 | ForEach-Object {
                Write-WatchdogLog $_
            }
        }
    }
}

Write-WatchdogLog "unlinking billing for $BillingProject"
& gcloud billing projects unlink $BillingProject --quiet --format=json 2>&1 | ForEach-Object {
    Write-WatchdogLog $_
}

Write-WatchdogLog "watchdog complete"
