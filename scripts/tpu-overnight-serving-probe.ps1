[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BillingAccount,
    [string]$BillingProject = $env:GOOGLE_CLOUD_PROJECT,
    [string[]]$Zones = @("europe-west4-a", "us-east1-d"),
    [int]$MaxHours = 7,
    [string]$NamePrefix = "agent-bench-night",
    [string]$RemoteUser = $env:USERNAME,
    [string]$RepoUrl = "https://github.com/Bortlesboat/agent-infra-security-bench",
    [int]$BillingPropagationSeconds = 90
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $BillingProject) {
    throw "Pass -BillingProject or set GOOGLE_CLOUD_PROJECT before starting the TPU run."
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
$RunId = (Get-Date -Format "yyyyMMdd-HHmmss")
$RunRoot = Join-Path $RepoRoot "outputs/tpu-overnight/$RunId"
$LogPath = Join-Path $RunRoot "runner.log"
$DeadlineUtc = (Get-Date).ToUniversalTime().AddHours($MaxHours)
$TpuName = "$NamePrefix-$($RunId.Replace('-', ''))"
$CurrentZone = $null
$CreatedTpu = $false

function Write-Log {
    param([string]$Message)

    [void](New-Item -ItemType Directory -Path $RunRoot -Force)
    $safeMessage = $Message `
        -replace "billingAccounts/[A-Z0-9-]+", "billingAccounts/[redacted]" `
        -replace "--billing-account=[A-Z0-9-]+", "--billing-account=[redacted]" `
        -replace '("ssh-keys":\s*").*(")', '$1[redacted]$2' `
        -replace "ssh-rsa [A-Za-z0-9+/=]+ [^\s""]+", "ssh-rsa [redacted]"
    $line = "$(Get-Date -Format o) $safeMessage"
    Add-Content -Path $LogPath -Value $line -Encoding utf8
    Write-Host $line
}

function Invoke-Logged {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    Write-Log "> $FilePath $($Arguments -join ' ')"
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & $FilePath @Arguments 2>&1
        $exit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    foreach ($line in $output) {
        Write-Log $line
    }
    if (-not $AllowFailure -and $exit -ne 0) {
        throw "Command failed ($exit): $FilePath $($Arguments -join ' ')"
    }
    return [pscustomobject]@{ ExitCode = $exit; Output = $output }
}

function Read-GcloudJson {
    param([string[]]$Arguments)

    $result = Invoke-Logged -FilePath "gcloud" -Arguments ($Arguments + @("--format=json"))
    $text = ($result.Output -join "`n")
    if (-not $text.Trim()) {
        return $null
    }
    return $text | ConvertFrom-Json
}

function Enable-AwakeMode {
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class BoundaryBenchSleep {
  [DllImport("kernel32.dll")]
  public static extern uint SetThreadExecutionState(uint esFlags);
}
"@ -ErrorAction SilentlyContinue
    $flags = [uint32]2147483713
    [void][BoundaryBenchSleep]::SetThreadExecutionState($flags)
}

function Disable-AwakeMode {
    try {
        [void][BoundaryBenchSleep]::SetThreadExecutionState([uint32]2147483648)
    }
    catch {
    }
}

function Assert-CleanCloudState {
    $instances = Read-GcloudJson @("compute", "instances", "list")
    if ($instances -and $instances.Count -gt 0) {
        throw "Compute instances exist before run; refusing to continue."
    }
    $disks = Read-GcloudJson @("compute", "disks", "list")
    if ($disks -and $disks.Count -gt 0) {
        throw "Compute disks exist before run; refusing to continue."
    }
    $addresses = Read-GcloudJson @("compute", "addresses", "list")
    if ($addresses -and $addresses.Count -gt 0) {
        throw "Compute addresses exist before run; refusing to continue."
    }
    foreach ($zone in $Zones) {
        $nodes = Read-GcloudJson @("compute", "tpus", "tpu-vm", "list", "--zone=$zone")
        if ($nodes -and $nodes.Count -gt 0) {
            throw "TPU nodes exist in $zone before run; refusing to continue."
        }
    }
}

function Wait-ForBillingPropagation {
    Write-Log "waiting $BillingPropagationSeconds seconds for billing propagation"
    Start-Sleep -Seconds $BillingPropagationSeconds
    $billing = Read-GcloudJson @("billing", "projects", "describe", $BillingProject)
    if (-not $billing.billingEnabled) {
        throw "Billing did not become enabled after propagation wait."
    }
}

function New-SshFiles {
    $sshDir = Join-Path $RunRoot "ssh"
    [void](New-Item -ItemType Directory -Path $sshDir -Force)
    $sourceKey = Join-Path $env:USERPROFILE ".ssh/google_compute_engine"
    $sourcePub = "$sourceKey.pub"
    $key = Join-Path $sshDir "google_compute_engine"
    $known = Join-Path $sshDir "known_hosts"
    Copy-Item -Force $sourceKey $key
    Copy-Item -Force $sourcePub "$key.pub"
    Invoke-Logged -FilePath "icacls" -Arguments @($key, "/inheritance:r", "/grant:r", "$env:USERNAME`:(F)") | Out-Null
    if (Test-Path $known) {
        Remove-Item $known -Force
    }
    $pub = (Get-Content $sourcePub -Raw).Trim()
    $sshKeys = Join-Path $sshDir "ssh-keys.txt"
    "${RemoteUser}:$pub" | Set-Content -Path $sshKeys -Encoding ascii
    return [pscustomobject]@{ Dir = $sshDir; Key = $key; KnownHosts = $known; SshKeys = $sshKeys }
}

function Wait-ForTpuReady {
    param([string]$Zone)

    $stop = (Get-Date).AddMinutes(25)
    while ((Get-Date) -lt $stop) {
        $node = Read-GcloudJson @("compute", "tpus", "tpu-vm", "describe", $TpuName, "--zone=$Zone")
        if ($node.state -eq "READY") {
            return $node
        }
        if ($node.state -in @("PREEMPTED", "DELETING", "TERMINATED")) {
            throw "TPU entered state $($node.state) before READY."
        }
        Write-Log "waiting for $TpuName in ${Zone}: state=$($node.state)"
        Start-Sleep -Seconds 20
    }
    throw "Timed out waiting for TPU READY in $Zone."
}

function New-Tpu {
    param($SshFiles)

    foreach ($zone in $Zones) {
        if ((Get-Date).ToUniversalTime() -gt $DeadlineUtc.AddMinutes(-45)) {
            throw "Deadline too close for new TPU creation."
        }
        $script:CurrentZone = $zone
        Write-Log "creating Spot v6e-8 TPU $TpuName in $zone"
        $create = Invoke-Logged -FilePath "gcloud" -Arguments @(
            "compute", "tpus", "tpu-vm", "create", $TpuName,
            "--zone=$zone",
            "--accelerator-type=v6e-8",
            "--version=v2-alpha-tpuv6e",
            "--spot",
            "--labels=purpose=overnight-probe",
            "--metadata-from-file=ssh-keys=$($SshFiles.SshKeys)",
            "--async"
        ) -AllowFailure
        if ($create.ExitCode -ne 0) {
            Write-Log "create failed in $zone; trying next zone"
            continue
        }
        try {
            $node = Wait-ForTpuReady -Zone $zone
            $script:CreatedTpu = $true
            return $node
        }
        catch {
            Write-Log "TPU did not become usable in ${zone}: $($_.Exception.Message)"
            Remove-Tpu -Zone $zone
        }
    }
    throw "No TPU zone produced a usable node."
}

function Remove-Tpu {
    param([string]$Zone)

    if (-not $Zone) {
        return
    }
    Write-Log "deleting $TpuName in $Zone"
    Invoke-Logged -FilePath "gcloud" -Arguments @(
        "compute", "tpus", "tpu-vm", "delete", $TpuName,
        "--zone=$Zone",
        "--quiet"
    ) -AllowFailure | Out-Null
    $script:CreatedTpu = $false
}

function Invoke-Remote {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ip,
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        $SshFiles,
        [switch]$AllowFailure
    )

    $target = "$RemoteUser@$Ip"
    $args = @(
        "-i", $SshFiles.Key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=$($SshFiles.KnownHosts)",
        "-o", "IdentitiesOnly=yes",
        $target,
        $Command
    )
    return Invoke-Logged -FilePath "ssh.exe" -Arguments $args -AllowFailure:$AllowFailure
}

function Copy-RemoteFile {
    param(
        [string]$Ip,
        [string]$RemotePath,
        [string]$LocalPath,
        $SshFiles
    )

    $target = "$RemoteUser@$Ip`:$RemotePath"
    Invoke-Logged -FilePath "scp.exe" -Arguments @(
        "-i", $SshFiles.Key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=$($SshFiles.KnownHosts)",
        "-o", "IdentitiesOnly=yes",
        $target,
        $LocalPath
    ) -AllowFailure | Out-Null
}

function Write-RemoteScript {
    param([string]$Path)

    $deadlineEpoch = [int][double]::Parse((Get-Date $DeadlineUtc -UFormat %s))
    $content = @"
#!/usr/bin/env bash
set -euo pipefail
RUN_ID="$RunId"
REPO_URL="$RepoUrl"
DEADLINE_EPOCH="$deadlineEpoch"
ROOT="`$HOME/agent-infra-security-bench"
OUT="`$HOME/tpu-overnight-runs/`$RUN_ID"
mkdir -p "`$OUT/logs"
log() { printf '%s %s\n' "`$(date -u +%Y-%m-%dT%H:%M:%SZ)" "`$*" | tee -a "`$OUT/logs/overnight.log"; }
time_left() { now=`$(date +%s); echo `$((DEADLINE_EPOCH - now)); }
should_continue() { [ "`$(time_left)" -gt 2400 ]; }
cleanup_server() { pkill -f "vllm serve" || true; sleep 5; }
trap cleanup_server EXIT

log "bootstrap start"
export DEBIAN_FRONTEND=noninteractive
if ! command -v git >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y git curl ca-certificates
fi
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="`$HOME/.local/bin:`$PATH"
uv python install 3.11
if [ ! -d "`$HOME/.venvs/boundarybench" ]; then
  uv venv "`$HOME/.venvs/boundarybench" --python 3.11
fi
source "`$HOME/.venvs/boundarybench/bin/activate"
uv pip install --upgrade vllm-tpu
if [ ! -d "`$ROOT/.git" ]; then
  if [ -e "`$ROOT" ]; then
    STALE="`${ROOT}.stale.`${RUN_ID}.`$(date +%s)"
    log "moving stale non-git repo path to `$STALE"
    mv "`$ROOT" "`$STALE"
  fi
  git clone "`$REPO_URL" "`$ROOT"
fi
cd "`$ROOT"
git fetch origin main
git checkout main
git pull --ff-only
uv pip install -e .
python -m agent_infra_security_bench.cli probe-openai-serving --help >/dev/null
log "bootstrap done"

make_long_prompt() {
  local label="`$1"
  local prompt="`$OUT/`${label}-long-frontier-prompt.txt"
  rm -f "`$prompt"
  for i in 1 2 3 4 5 6 7 8; do
    cat docs/runbooks/tpu-probe-frontier-prompt.txt >> "`$prompt"
    printf '\n\n' >> "`$prompt"
  done
  printf 'Return one compact JSON decision object.\n' >> "`$prompt"
  echo "`$prompt"
}

wait_for_server() {
  local label="`$1"
  for attempt in `$(seq 1 90); do
    if curl -sf http://127.0.0.1:8000/v1/models > "`$OUT/logs/`${label}-models.json"; then
      log "`$label server ready attempt=`$attempt"
      return 0
    fi
    sleep 10
  done
  log "`$label server failed to become ready"
  return 1
}

run_probe_model() {
  local model="`$1"
  local label="`$2"
  local tp="`$3"
  local max_len="`$4"
  if ! should_continue; then
    log "deadline too close; skipping `$label"
    return 0
  fi
  log "starting model=`$model label=`$label tp=`$tp max_len=`$max_len time_left=`$(time_left)"
  cleanup_server
  nohup vllm serve "`$model" --download_dir /tmp --tensor_parallel_size "`$tp" --max-model-len "`$max_len" > "`$OUT/logs/`${label}-vllm.log" 2>&1 &
  echo `$! > "`$OUT/logs/`${label}-vllm.pid"
  if ! wait_for_server "`$label"; then
    cleanup_server
    return 0
  fi
  agent-bench probe-openai-serving --base-url http://127.0.0.1:8000/v1 --model "`$model" --prompt-file docs/runbooks/tpu-probe-frontier-prompt.txt --concurrency 1,8,64,128,256 --requests-per-level 128 --max-tokens 96 --timeout 300 --label "`${label}-short" --json "`$OUT/`${label}-short.json" --csv "`$OUT/`${label}-short.csv" --markdown "`$OUT/`${label}-short.md" || log "`$label short probe failed"
  agent-bench probe-openai-serving --base-url http://127.0.0.1:8000/v1 --model "`$model" --prompt-file docs/runbooks/tpu-probe-frontier-prompt.txt --concurrency 512 --requests-per-level 512 --max-tokens 96 --timeout 300 --label "`${label}-limit512" --json "`$OUT/`${label}-limit512.json" --csv "`$OUT/`${label}-limit512.csv" --markdown "`$OUT/`${label}-limit512.md" || log "`$label limit512 probe failed"
  local long_prompt
  long_prompt=`$(make_long_prompt "`$label")
  agent-bench probe-openai-serving --base-url http://127.0.0.1:8000/v1 --model "`$model" --prompt-file "`$long_prompt" --concurrency 1,8,64,256 --requests-per-level 128 --max-tokens 64 --timeout 300 --label "`${label}-long-repeated" --json "`$OUT/`${label}-long.json" --csv "`$OUT/`${label}-long.csv" --markdown "`$OUT/`${label}-long.md" || log "`$label long probe failed"
  cleanup_server
  log "finished `$label"
}

run_probe_model "Qwen/Qwen2.5-14B-Instruct" "qwen14b-v6e8" 4 4096
run_probe_model "mistralai/Mistral-7B-Instruct-v0.3" "mistral7b-v6e8" 1 4096
run_probe_model "Qwen/Qwen2.5-7B-Instruct" "qwen7b-v6e8-repeat" 1 4096

cd "`$HOME/tpu-overnight-runs"
tar -czf "`$HOME/tpu-overnight-`$RUN_ID.tgz" "`$RUN_ID"
log "artifact tarball `$HOME/tpu-overnight-`$RUN_ID.tgz"
"@
    $lf = $content.Replace("`r`n", "`n")
    [System.IO.File]::WriteAllText($Path, $lf, [System.Text.Encoding]::ASCII)
}

try {
    Enable-AwakeMode
    Write-Log "overnight TPU run $RunId starting; deadline=$($DeadlineUtc.ToString("o"))"
    Invoke-Logged -FilePath "gcloud" -Arguments @("billing", "projects", "link", $BillingProject, "--billing-account=$BillingAccount", "--format=json") | Out-Null
    Wait-ForBillingPropagation
    Assert-CleanCloudState
    $sshFiles = New-SshFiles
    $node = New-Tpu -SshFiles $sshFiles
    $ip = $node.networkEndpoints[0].accessConfig.externalIp
    Write-Log "TPU ready ip=$ip zone=$CurrentZone"
    for ($i = 1; $i -le 30; $i++) {
        $test = Invoke-Remote -Ip $ip -SshFiles $sshFiles -Command "python3 --version" -AllowFailure
        if ($test.ExitCode -eq 0) {
            break
        }
        Start-Sleep -Seconds 10
    }
    $remoteScript = Join-Path $RunRoot "remote-overnight.sh"
    Write-RemoteScript -Path $remoteScript
    Invoke-Logged -FilePath "scp.exe" -Arguments @(
        "-i", $sshFiles.Key,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=$($sshFiles.KnownHosts)",
        "-o", "IdentitiesOnly=yes",
        $remoteScript,
        "$RemoteUser@$ip`:~/remote-overnight.sh"
    ) | Out-Null
    Invoke-Remote -Ip $ip -SshFiles $sshFiles -Command "chmod +x ~/remote-overnight.sh && bash ~/remote-overnight.sh" -AllowFailure | Out-Null
    Copy-RemoteFile -Ip $ip -SshFiles $sshFiles -RemotePath "~/tpu-overnight-$RunId.tgz" -LocalPath (Join-Path $RunRoot "tpu-overnight-$RunId.tgz")
    Write-Log "remote run complete or stopped; artifacts copied if available"
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
}
finally {
    try {
        if ($CurrentZone) {
            Remove-Tpu -Zone $CurrentZone
        }
        foreach ($zone in $Zones) {
            Invoke-Logged -FilePath "gcloud" -Arguments @("compute", "tpus", "tpu-vm", "list", "--zone=$zone", "--format=json") -AllowFailure | Out-Null
        }
        Invoke-Logged -FilePath "gcloud" -Arguments @("compute", "instances", "list", "--format=json") -AllowFailure | Out-Null
        Invoke-Logged -FilePath "gcloud" -Arguments @("compute", "disks", "list", "--format=json") -AllowFailure | Out-Null
    }
    finally {
        Invoke-Logged -FilePath "gcloud" -Arguments @("billing", "projects", "unlink", $BillingProject, "--quiet", "--format=json") -AllowFailure | Out-Null
        Disable-AwakeMode
        Write-Log "overnight TPU run $RunId finished"
    }
}
