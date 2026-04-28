[CmdletBinding()]
param(
    [string]$QueueFile,
    [string]$RepoRoot,
    [string]$PythonExe,
    [string]$GcloudExe,
    [string]$RemoteUser = $env:USERNAME,
    [switch]$SkipLocalValidation,
    [switch]$DryRun,
    [switch]$KeepTpu
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptRoot = if ($PSScriptRoot) {
    $PSScriptRoot
}
else {
    Split-Path -Parent $MyInvocation.MyCommand.Path
}

if (-not $RepoRoot) {
    $RepoRoot = Split-Path -Parent $ScriptRoot
}

if (-not $QueueFile) {
    $QueueFile = Join-Path $RepoRoot "docs/runbooks/tpu-frontier-v2-qwen7b-first-wave.json"
}

$script:RemoteHome = "/home/$RemoteUser"
$script:OpenSshTempDir = Join-Path ([System.IO.Path]::GetTempPath()) "boundarybench-openssh"

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Get-IsoUtcNow {
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Get-ElapsedSeconds {
    param(
        [string]$StartedAt,
        [string]$FinishedAt
    )

    if (-not $StartedAt -or -not $FinishedAt) {
        return $null
    }

    $started = [datetime]::Parse($StartedAt).ToUniversalTime()
    $finished = [datetime]::Parse($FinishedAt).ToUniversalTime()
    return [math]::Round(($finished - $started).TotalSeconds, 3)
}

function Write-JsonFile {
    param(
        [string]$Path,
        $Value
    )

    $parent = Split-Path -Parent $Path
    if ($parent) {
        [void](New-Item -ItemType Directory -Path $parent -Force)
    }

    $Value | ConvertTo-Json -Depth 12 | Set-Content -Path $Path -Encoding utf8
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $RepoRoot,
        [string]$InputText,
        [switch]$AllowFailure
    )

    if ($DryRun) {
        $joined = ($Arguments | ForEach-Object {
                if ($_ -match "\s") { '"' + $_ + '"' } else { $_ }
            }) -join " "
        Write-Host "[dry-run] $FilePath $joined"
        return [pscustomobject]@{
            ExitCode = 0
            StdOut   = ""
            StdErr   = ""
        }
    }

    $escapedArguments = $Arguments | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_.Replace('"', '\"')) + '"'
        }
        else {
            $_
        }
    }

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FilePath
    $startInfo.Arguments = ($escapedArguments -join " ")
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.RedirectStandardInput = $null -ne $InputText

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()

    if ($null -ne $InputText) {
        $process.StandardInput.WriteLine($InputText)
        $process.StandardInput.Close()
    }

    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    if ($stdout) {
        Write-Host ($stdout.TrimEnd())
    }

    if ($stderr) {
        Write-Host ($stderr.TrimEnd())
    }

    if (-not $AllowFailure -and $process.ExitCode -ne 0) {
        throw "Command failed ($($process.ExitCode)): $FilePath $($Arguments -join ' ')"
    }

    return [pscustomobject]@{
        ExitCode = $process.ExitCode
        StdOut   = $stdout
        StdErr   = $stderr
    }
}

function Resolve-PythonExecutable {
    if ($PythonExe) {
        if (Test-Path $PythonExe) {
            return (Resolve-Path $PythonExe).Path
        }

        return $PythonExe
    }

    if ($env:BOUNDARYBENCH_PYTHON) {
        if (Test-Path $env:BOUNDARYBENCH_PYTHON) {
            return (Resolve-Path $env:BOUNDARYBENCH_PYTHON).Path
        }

        return $env:BOUNDARYBENCH_PYTHON
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand -and $pythonCommand.Source -notmatch "\\WindowsApps\\") {
        return $pythonCommand.Source
    }

    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonLauncher) {
        return $pythonLauncher.Source
    }

    throw "No Python executable found. Pass -PythonExe or set BOUNDARYBENCH_PYTHON."
}

function Resolve-GcloudExecutable {
    if ($GcloudExe) {
        if (Test-Path $GcloudExe) {
            return (Resolve-Path $GcloudExe).Path
        }

        return $GcloudExe
    }

    if ($env:GCLOUD_EXE) {
        if (Test-Path $env:GCLOUD_EXE) {
            return (Resolve-Path $env:GCLOUD_EXE).Path
        }

        return $env:GCLOUD_EXE
    }

    foreach ($candidate in @("gcloud.cmd", "gcloud.ps1", "gcloud")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }

    throw "No gcloud executable found. Pass -GcloudExe explicitly."
}

function Resolve-OpenSshExecutable {
    param([string]$CommandName)

    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    throw "No OpenSSH executable found for '$CommandName'."
}

function Get-CanonicalGcloudSshKeyBasePath {
    $sourceKey = Join-Path $env:USERPROFILE ".ssh/google_compute_engine"
    if (-not (Test-Path $sourceKey)) {
        throw "Canonical Google Compute Engine private key not found at '$sourceKey'."
    }

    $sourcePublicKey = "$sourceKey.pub"
    if (-not (Test-Path $sourcePublicKey)) {
        throw "Canonical Google Compute Engine public key not found at '$sourcePublicKey'."
    }

    $sourcePpk = "$sourceKey.ppk"
    if (-not (Test-Path $sourcePpk)) {
        throw "Canonical Google Compute Engine PuTTY key not found at '$sourcePpk'."
    }

    return $sourceKey
}

function Protect-PrivateKeyFile {
    param([string]$Path)

    $grant = "{0}\{1}:(F)" -f $env:USERDOMAIN, $env:USERNAME
    $result = & icacls.exe $Path /inheritance:r /grant:r $grant 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Could not protect OpenSSH private key with icacls: $result"
    }
}

function Initialize-OpenSshIdentity {
    if (Test-Path $script:OpenSshTempDir) {
        Remove-Item $script:OpenSshTempDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    $sourceKey = Join-Path $env:USERPROFILE ".ssh/google_compute_engine"
    if (-not (Test-Path $sourceKey)) {
        throw "OpenSSH private key not found at '$sourceKey'."
    }

    $sourcePublicKey = "$sourceKey.pub"
    if (-not (Test-Path $sourcePublicKey)) {
        throw "OpenSSH public key not found at '$sourcePublicKey'."
    }

    [void](New-Item -ItemType Directory -Path $script:OpenSshTempDir -Force)

    $keyPath = Join-Path $script:OpenSshTempDir "google_compute_engine"
    $knownHostsPath = Join-Path $script:OpenSshTempDir "known_hosts"

    Copy-Item $sourceKey $keyPath -Force
    Copy-Item $sourcePublicKey "$keyPath.pub" -Force
    Protect-PrivateKeyFile -Path $keyPath

    if (Test-Path $knownHostsPath) {
        Remove-Item $knownHostsPath -Force
    }
    [void](New-Item -ItemType File -Path $knownHostsPath -Force)

    return [pscustomobject]@{
        KeyPath        = $keyPath
        KnownHostsPath = $knownHostsPath
    }
}

function Refresh-OpenSshIdentity {
    $sshIdentity = Initialize-OpenSshIdentity
    $script:ResolvedSshKeyFile = $sshIdentity.KeyPath
    $script:ResolvedKnownHostsFile = $sshIdentity.KnownHostsPath
}

function Load-StrikeQueue {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Queue file not found: $Path"
    }

    $queue = Get-Content $Path -Raw | ConvertFrom-Json

    foreach ($requiredProperty in @("name", "repoBranch", "scenarioDir", "scenarioCommitSuffix", "lanes", "model", "runs")) {
        if (-not $queue.PSObject.Properties.Name.Contains($requiredProperty)) {
            throw "Queue file missing required property '$requiredProperty'."
        }
    }

    return $queue
}

function Test-LocalQueueValidation {
    param(
        $Queue,
        [string]$ResolvedPythonExe
    )

    if ($SkipLocalValidation) {
        Write-Step "Skipping local validation by request."
        return
    }

    if ($Queue.scenarioDir -ne "scenarios-frontier-v2") {
        Write-Step "No built-in local validation rule for scenario dir '$($Queue.scenarioDir)'."
        return
    }

    Write-Step "Running local frontier-v2 validation before any TPU create."
    Invoke-External -FilePath $ResolvedPythonExe -Arguments @("-m", "pytest", "tests/test_frontier_pack_v2.py", "-v")
}

function New-StrikeName {
    param(
        [string]$QueueName,
        [string]$LaneName
    )

    $suffix = [System.Guid]::NewGuid().ToString("N").Substring(0, 8)
    $baseRaw = ("{0}-{1}" -f $QueueName, $LaneName).ToLowerInvariant()
    $baseSanitized = ($baseRaw -replace "[^a-z0-9-]", "-")
    $baseCollapsed = ($baseSanitized -replace "-{2,}", "-").Trim("-")
    $maxBaseLength = 63 - 1 - $suffix.Length

    if ($baseCollapsed.Length -gt $maxBaseLength) {
        $baseCollapsed = $baseCollapsed.Substring(0, $maxBaseLength).Trim("-")
    }

    return ("{0}-{1}" -f $baseCollapsed, $suffix).Trim("-")
}

function New-TempScript {
    param(
        [string]$Prefix,
        [string]$Content
    )

    $path = Join-Path ([System.IO.Path]::GetTempPath()) ("{0}-{1}.sh" -f $Prefix, ([System.Guid]::NewGuid().ToString("N")))
    $normalizedContent = $Content -replace "\r\n?", "`n"
    [System.IO.File]::WriteAllText($path, $normalizedContent, [System.Text.Encoding]::ASCII)
    return $path
}

function New-RemoteWrapperScriptContent {
    param(
        [string]$RemoteScriptPath,
        [string]$RemoteLogPath,
        [string]$RemoteExitPath
    )

    $content = @'
#!/usr/bin/env bash
set +e

{
  echo "[wrapper] starting __REMOTE_SCRIPT_PATH__"
  bash "__REMOTE_SCRIPT_PATH__"
  code=$?
  echo "[wrapper] finished __REMOTE_SCRIPT_PATH__ exit=${code}"
  printf '%s' "${code}" > "__REMOTE_EXIT_PATH__"
  exit 0
} > "__REMOTE_LOG_PATH__" 2>&1
'@

    return $content.
        Replace("__REMOTE_SCRIPT_PATH__", $RemoteScriptPath).
        Replace("__REMOTE_LOG_PATH__", $RemoteLogPath).
        Replace("__REMOTE_EXIT_PATH__", $RemoteExitPath)
}

function New-BootstrapScriptContent {
    param(
        $Queue,
        [string]$RemoteHome
    )

    $repoBranch = $Queue.repoBranch
    $content = @'
#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --user uv
export PATH="$HOME/.local/bin:$PATH"

uv python install 3.11

if [ -x "__REMOTE_HOME__/.venvs/boundarybench/bin/python" ]; then
  if ! "__REMOTE_HOME__/.venvs/boundarybench/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    rm -rf "__REMOTE_HOME__/.venvs/boundarybench"
  fi
fi

if [ ! -d "__REMOTE_HOME__/.venvs/boundarybench" ]; then
  uv venv --python 3.11 "__REMOTE_HOME__/.venvs/boundarybench"
fi

source "__REMOTE_HOME__/.venvs/boundarybench/bin/activate"
python --version
uv pip install --upgrade vllm-tpu

if [ ! -d "__REMOTE_HOME__/agent-infra-security-bench/.git" ]; then
  git clone https://github.com/Bortlesboat/agent-infra-security-bench "__REMOTE_HOME__/agent-infra-security-bench"
fi

cd "__REMOTE_HOME__/agent-infra-security-bench"
git fetch origin
git checkout __REPO_BRANCH__
git pull --ff-only origin __REPO_BRANCH__
uv pip install -e .
'@
    return $content.Replace("__REPO_BRANCH__", $repoBranch).Replace("__REMOTE_HOME__", $RemoteHome)
}

function New-RunScriptContent {
    param(
        $Queue,
        $Lane,
        [string]$RemoteHome
    )

    $modelId = $Queue.model.id
    $tensorParallelSize = [string]$Queue.model.tensorParallelSize
    $maxModelLen = [string]$Queue.model.maxModelLen
    $scenarioDir = $Queue.scenarioDir
    $scenarioCommitSuffix = $Queue.scenarioCommitSuffix
    $hardwareLabel = $Lane.hardwareLabel

    $runLines = foreach ($run in $Queue.runs) {
        "echo 'Running BoundaryBench row $($run.id) into $($run.outputDir)'"
        "python -m agent_infra_security_bench.cli run-openai-agent '$scenarioDir' '$($run.outputDir)' --model '$modelId' --base-url http://127.0.0.1:8000/v1 --scenario-commit `"`$SCENARIO_COMMIT`" --prompt-profile $($run.promptProfile) --runtime-policy $($run.runtimePolicy) --hardware $hardwareLabel"
        "echo 'Remote artifacts under $($run.outputDir):'"
        "find '$($run.outputDir)' -maxdepth 3 -type f -print | sort"
        "find '$($run.outputDir)' -name manifest.json -print -quit | grep -q ."
    }

    $runBlock = ($runLines -join "`n")

    $content = @'
#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
source "__REMOTE_HOME__/.venvs/boundarybench/bin/activate"
cd "__REMOTE_HOME__/agent-infra-security-bench"

pkill -f "vllm serve" || true
trap 'pkill -f "vllm serve" || true' EXIT

nohup vllm serve '__MODEL_ID__' --download_dir /tmp --tensor_parallel_size __TP_SIZE__ --max-model-len __MAX_MODEL_LEN__ > /tmp/vllm-tpu.log 2>&1 &

for attempt in $(seq 1 90); do
  if curl -sf http://127.0.0.1:8000/v1/models >/dev/null; then
    break
  fi
  sleep 5
done

curl -sf http://127.0.0.1:8000/v1/models >/dev/null

SCENARIO_COMMIT="$(git rev-parse HEAD)-__SCENARIO_COMMIT_SUFFIX__"

__RUN_BLOCK__
'@
    return $content.
        Replace("__MODEL_ID__", $modelId).
        Replace("__TP_SIZE__", $tensorParallelSize).
        Replace("__MAX_MODEL_LEN__", $maxModelLen).
        Replace("__SCENARIO_COMMIT_SUFFIX__", $scenarioCommitSuffix).
        Replace("__RUN_BLOCK__", $runBlock).
        Replace("__REMOTE_HOME__", $RemoteHome)
}

function Get-TpuExternalIp {
    param(
        [string]$TpuName,
        [string]$Zone
    )

    if ($DryRun) {
        return "203.0.113.10"
    }

    $result = Invoke-External -FilePath $script:ResolvedGcloudExe -Arguments @(
        "compute", "tpus", "tpu-vm", "describe", $TpuName,
        "--zone=$Zone",
        "--format=value(networkEndpoints[0].accessConfig.externalIp)"
    )

    $externalIp = $result.StdOut.Trim()
    if (-not $externalIp) {
        throw "Could not resolve external IP for TPU '$TpuName' in zone '$Zone'."
    }

    return $externalIp
}

function Wait-ForTpuSshReady {
    param(
        [string]$TpuName,
        [string]$Zone,
        [string]$ExternalIp,
        [int]$MaxAttempts = 24,
        [int]$SleepSeconds = 5
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $state = Get-TpuNodeState -TpuName $TpuName -Zone $Zone
        if ($state -in @("DELETING", "PREEMPTED", "STOPPING", "TERMINATED")) {
            throw "TPU '$TpuName' entered state '$state' before SSH became ready."
        }

        try {
            Refresh-OpenSshIdentity
            [void](Invoke-TpuGcloudSsh -TpuName $TpuName -Zone $Zone -Command "python3 --version")
            [void](Invoke-TpuSsh -ExternalIp $ExternalIp -Command "python3 --version")
            return
        }
        catch {
            if ($attempt -eq $MaxAttempts) {
                throw
            }

            Write-Warning "SSH not ready for '$ExternalIp' yet (attempt $attempt/$MaxAttempts): $($_.Exception.Message)"
            Start-Sleep -Seconds $SleepSeconds
        }
    }
}

function Get-TpuNodeState {
    param(
        [string]$TpuName,
        [string]$Zone
    )

    if ($DryRun) {
        return "READY"
    }

    $result = Invoke-External -FilePath $script:ResolvedGcloudExe -Arguments @(
        "compute", "tpus", "tpu-vm", "describe", $TpuName,
        "--zone=$Zone",
        "--format=value(state)"
    ) -AllowFailure

    return $result.StdOut.Trim()
}

function Invoke-TpuGcloudSsh {
    param(
        [string]$TpuName,
        [string]$Zone,
        [string]$Command
    )

    return Invoke-External -FilePath $script:ResolvedGcloudExe -Arguments @(
        "compute", "tpus", "tpu-vm", "ssh", $TpuName,
        "--zone=$Zone",
        "--command=$Command",
        "--ssh-key-file=$($script:ResolvedGcloudSshKeyFile)",
        "--ssh-key-expire-after=2h",
        "--strict-host-key-checking=no",
        "--quiet"
    )
}

function Invoke-TpuSsh {
    param(
        [string]$ExternalIp,
        [string]$Command
    )

    return Invoke-External -FilePath $script:ResolvedSshExe -Arguments @(
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "IdentitiesOnly=yes",
        "-o", "UserKnownHostsFile=$($script:ResolvedKnownHostsFile)",
        "-i", $script:ResolvedSshKeyFile,
        ("{0}@{1}" -f $RemoteUser, $ExternalIp),
        $Command
    )
}

function Invoke-TpuScpToRemote {
    param(
        [string]$ExternalIp,
        [string]$LocalPath,
        [string]$RemotePath
    )

    return Invoke-External -FilePath $script:ResolvedScpExe -Arguments @(
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "IdentitiesOnly=yes",
        "-o", "UserKnownHostsFile=$($script:ResolvedKnownHostsFile)",
        "-i", $script:ResolvedSshKeyFile,
        $LocalPath,
        ("{0}@{1}:{2}" -f $RemoteUser, $ExternalIp, $RemotePath)
    )
}

function Invoke-TpuScpFromRemote {
    param(
        [string]$ExternalIp,
        [string]$RemotePath,
        [string]$LocalPath
    )

    return Invoke-External -FilePath $script:ResolvedScpExe -Arguments @(
        "-r",
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "IdentitiesOnly=yes",
        "-o", "UserKnownHostsFile=$($script:ResolvedKnownHostsFile)",
        "-i", $script:ResolvedSshKeyFile,
        ("{0}@{1}:{2}" -f $RemoteUser, $ExternalIp, $RemotePath),
        $LocalPath
    )
}

function Invoke-TpuScpSingleFileFromRemote {
    param(
        [string]$ExternalIp,
        [string]$RemotePath,
        [string]$LocalPath
    )

    return Invoke-External -FilePath $script:ResolvedScpExe -Arguments @(
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "IdentitiesOnly=yes",
        "-o", "UserKnownHostsFile=$($script:ResolvedKnownHostsFile)",
        "-i", $script:ResolvedSshKeyFile,
        ("{0}@{1}:{2}" -f $RemoteUser, $ExternalIp, $RemotePath),
        $LocalPath
    )
}

function Copy-TpuRunArtifactsBack {
    param(
        [string]$ExternalIp,
        [string]$RemoteOutputDir,
        [string]$LocalOutputRoot
    )

    $manifestPathResult = Invoke-TpuSsh -ExternalIp $ExternalIp -Command "find '$RemoteOutputDir' -name manifest.json -print -quit"
    $remoteManifestPath = $manifestPathResult.StdOut.Trim()
    if (-not $remoteManifestPath) {
        throw "No remote manifest.json found under '$RemoteOutputDir'."
    }

    $remoteRunDirResult = Invoke-TpuSsh -ExternalIp $ExternalIp -Command "dirname '$remoteManifestPath'"
    $remoteRunDir = $remoteRunDirResult.StdOut.Trim()
    if (-not $remoteRunDir) {
        throw "Could not resolve remote run directory from '$remoteManifestPath'."
    }

    $localRunDir = Join-Path $LocalOutputRoot (Split-Path -Leaf $remoteRunDir)
    [void](New-Item -ItemType Directory -Path $localRunDir -Force)

    $summaryFiles = @(
        "manifest.json",
        "results.csv",
        "results.md",
        "coverage.json",
        "coverage.md"
    )

    foreach ($summaryFile in $summaryFiles) {
        $remoteFile = "$remoteRunDir/$summaryFile"
        $existsResult = Invoke-TpuSsh -ExternalIp $ExternalIp -Command "if [ -f '$remoteFile' ]; then printf 'yes'; fi"
        if ($existsResult.StdOut.Trim() -eq "yes") {
            [void](Invoke-TpuScpSingleFileFromRemote -ExternalIp $ExternalIp -RemotePath $remoteFile -LocalPath $localRunDir)
        }
    }

    foreach ($extraDir in @("raw-events", "traces")) {
        $remoteDir = "$remoteRunDir/$extraDir"
        $existsResult = Invoke-TpuSsh -ExternalIp $ExternalIp -Command "if [ -d '$remoteDir' ]; then printf 'yes'; fi"
        if ($existsResult.StdOut.Trim() -eq "yes") {
            try {
                [void](Invoke-TpuScpFromRemote -ExternalIp $ExternalIp -RemotePath $remoteDir -LocalPath $localRunDir)
            }
            catch {
                Write-Warning "Best-effort copy of '$remoteDir' failed after summary artifact copy: $($_.Exception.Message)"
            }
        }
    }

    return $localRunDir
}

function Wait-ForRemoteScriptCompletion {
    param(
        [string]$TpuName,
        [string]$Zone,
        [string]$ExternalIp,
        [string]$RemoteScriptPath,
        [string]$RemoteWrapperPath,
        [string]$RemoteLogPath,
        [string]$RemoteExitPath,
        [string]$RemotePidPath,
        [string]$Label = "remote script",
        [int]$MaxAttempts = 180,
        [int]$SleepSeconds = 10
    )

    $launchCommand = @(
        "rm -f '$RemoteExitPath' '$RemoteLogPath' '$RemotePidPath'",
        "chmod +x '$RemoteScriptPath' '$RemoteWrapperPath'",
        "nohup bash '$RemoteWrapperPath' >/dev/null 2>&1 & echo `$! > '$RemotePidPath'"
    ) -join "; "
    [void](Invoke-TpuSsh -ExternalIp $ExternalIp -Command $launchCommand)

    $statusCommand = @'
if [ -f '{0}' ]; then
  printf 'EXIT:'
  cat '{0}'
elif [ -f '{1}' ]; then
  pid="$(cat '{1}' 2>/dev/null)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    printf 'RUNNING'
  else
    printf 'NOEXIT'
  fi
elif [ -f '{2}' ]; then
  printf 'NOEXIT'
else
  printf 'STARTING'
fi
'@ -f $RemoteExitPath, $RemotePidPath, $RemoteLogPath

    if ($DryRun) {
        return
    }

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $state = Get-TpuNodeState -TpuName $TpuName -Zone $Zone
        if ($state -in @("DELETING", "PREEMPTED", "STOPPING", "TERMINATED")) {
            throw "TPU '$TpuName' entered state '$state' during $Label."
        }

        try {
            $statusResult = Invoke-TpuSsh -ExternalIp $ExternalIp -Command $statusCommand
            $status = $statusResult.StdOut.Trim()
        }
        catch {
            if ($attempt -eq $MaxAttempts) {
                throw
            }

            Write-Warning "$Label poll failed for '$ExternalIp' (attempt $attempt/$MaxAttempts): $($_.Exception.Message)"
            Start-Sleep -Seconds $SleepSeconds
            continue
        }

        if ($status -eq "RUNNING" -or $status -eq "STARTING") {
            Start-Sleep -Seconds $SleepSeconds
            continue
        }

        if ($status -like "EXIT:*") {
            $exitCodeText = $status.Substring(5).Trim()
            [int]$exitCode = 0
            if (-not [int]::TryParse($exitCodeText, [ref]$exitCode)) {
                throw "$Label wrote a non-numeric exit marker '$exitCodeText'."
            }
            if ($exitCode -eq 0) {
                return
            }

            $tailResult = Invoke-TpuSsh -ExternalIp $ExternalIp -Command "if [ -f '$RemoteLogPath' ]; then tail -n 80 '$RemoteLogPath'; fi"
            throw "$Label failed with exit code $exitCode. Tail:`n$($tailResult.StdOut.TrimEnd())"
        }

        if ($status -eq "NOEXIT") {
            $tailResult = Invoke-TpuSsh -ExternalIp $ExternalIp -Command "if [ -f '$RemoteLogPath' ]; then tail -n 80 '$RemoteLogPath'; fi"
            throw "$Label stopped without writing an exit code. Tail:`n$($tailResult.StdOut.TrimEnd())"
        }

        Start-Sleep -Seconds $SleepSeconds
    }

    $tailResult = Invoke-TpuSsh -ExternalIp $ExternalIp -Command "if [ -f '$RemoteLogPath' ]; then tail -n 80 '$RemoteLogPath'; fi"
    throw "$Label did not finish within the polling window. Tail:`n$($tailResult.StdOut.TrimEnd())"
}

function Remove-TpuNode {
    param(
        [string]$TpuName,
        [string]$Zone
    )

    if ($KeepTpu) {
        Write-Step "Keeping TPU node '$TpuName' in $Zone by request."
        return $false
    }

    if ($DryRun) {
        Write-Step "Deleting TPU node '$TpuName' in $Zone."
        [void](Invoke-External -FilePath $script:ResolvedGcloudExe -Arguments @(
            "compute", "tpus", "tpu-vm", "delete", $TpuName,
            "--zone=$Zone",
            "--quiet"
        ))
        [void](Invoke-External -FilePath $script:ResolvedGcloudExe -Arguments @(
            "compute", "tpus", "tpu-vm", "list",
            "--zone=$Zone",
            "--format=value(name)"
        ))
        return $true
    }

    $beforeNames = Get-TpuNodeNames -Zone $Zone
    if ($beforeNames -notcontains $TpuName) {
        Write-Step "No TPU node named '$TpuName' is present in $Zone."
        return $true
    }

    Write-Step "Deleting TPU node '$TpuName' in $Zone."
    [void](Invoke-External -FilePath $script:ResolvedGcloudExe -Arguments @(
        "compute", "tpus", "tpu-vm", "delete", $TpuName,
        "--zone=$Zone",
        "--quiet"
    ) -AllowFailure)

    $afterNames = Get-TpuNodeNames -Zone $Zone
    return ($afterNames -notcontains $TpuName)
}

function Get-TpuNodeNames {
    param([string]$Zone)

    $listResult = Invoke-External -FilePath $script:ResolvedGcloudExe -Arguments @(
        "compute", "tpus", "tpu-vm", "list",
        "--zone=$Zone",
        "--format=value(name)"
    ) -AllowFailure

    if (-not $listResult.StdOut) {
        return @()
    }

    return @($listResult.StdOut -split "\r?\n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Invoke-RunCostAnnotation {
    param(
        [string]$RunOutputDir,
        $Lane,
        $Timing,
        $Reliability,
        [string]$ResolvedPythonExe
    )

    if ($DryRun) {
        Write-Step "Dry run: skipping cost annotation for '$RunOutputDir'."
        return
    }

    if (-not $Lane.PSObject.Properties.Name.Contains("pricingSnapshot")) {
        Write-Warning "Lane '$($Lane.name)' has no pricingSnapshot; skipping cost annotation."
        return
    }

    if (-not (Test-Path $RunOutputDir)) {
        Write-Warning "Copied run output not found for cost annotation: $RunOutputDir"
        return
    }

    $manifest = Get-ChildItem -Path $RunOutputDir -Recurse -Filter "manifest.json" |
        Sort-Object FullName |
        Select-Object -First 1

    if (-not $manifest) {
        Write-Warning "No manifest.json found under '$RunOutputDir'; skipping cost annotation."
        return
    }

    $metadataDir = Join-Path $manifest.Directory.FullName "cost-metadata"
    $pricingPath = Join-Path $metadataDir "pricing.json"
    $timingPath = Join-Path $metadataDir "timing.json"
    $reliabilityPath = Join-Path $metadataDir "reliability.json"

    Write-JsonFile -Path $pricingPath -Value $Lane.pricingSnapshot
    Write-JsonFile -Path $timingPath -Value $Timing
    Write-JsonFile -Path $reliabilityPath -Value $Reliability

    Write-Step "Annotating run manifest with cost metadata: $($manifest.FullName)"
    $oldPythonPath = $env:PYTHONPATH
    try {
        $srcPath = Join-Path $RepoRoot "src"
        if ($oldPythonPath) {
            $env:PYTHONPATH = "$srcPath;$oldPythonPath"
        }
        else {
            $env:PYTHONPATH = $srcPath
        }

        Invoke-External -FilePath $ResolvedPythonExe -Arguments @(
            "-m", "agent_infra_security_bench.cli",
            "annotate-run-cost", $manifest.FullName,
            "--pricing-json", $pricingPath,
            "--timing-json", $timingPath,
            "--reliability-json", $reliabilityPath,
            "--output", $manifest.FullName,
            "--root", $RepoRoot
        )
    }
    finally {
        $env:PYTHONPATH = $oldPythonPath
    }
}

function Invoke-StrikeLane {
    param(
        $Queue,
        $Lane
    )

    $tpuName = New-StrikeName -QueueName $Queue.name -LaneName $Lane.name
    $bootstrapPath = $null
    $bootstrapWrapperPath = $null
    $runPath = $null
    $runWrapperPath = $null
    $success = $false
    $copiedRunDirs = New-Object System.Collections.Generic.List[string]
    $remoteBootstrapScript = "$($script:RemoteHome)/boundarybench-bootstrap.sh"
    $remoteBootstrapWrapper = "$($script:RemoteHome)/boundarybench-bootstrap-wrapper.sh"
    $remoteBootstrapLog = "$($script:RemoteHome)/boundarybench-bootstrap.log"
    $remoteBootstrapExit = "$($script:RemoteHome)/boundarybench-bootstrap.exitcode"
    $remoteBootstrapPid = "$($script:RemoteHome)/boundarybench-bootstrap.pid"
    $remoteRunScript = "$($script:RemoteHome)/boundarybench-run.sh"
    $remoteRunWrapper = "$($script:RemoteHome)/boundarybench-run-wrapper.sh"
    $remoteRunLog = "$($script:RemoteHome)/boundarybench-run.log"
    $remoteRunExit = "$($script:RemoteHome)/boundarybench-run.exitcode"
    $remoteRunPid = "$($script:RemoteHome)/boundarybench-run.pid"
    $timing = [ordered]@{
        lane                  = $Lane.name
        tpu_name              = $tpuName
        create_requested_at   = $null
        create_completed_at   = $null
        ready_at              = $null
        ssh_verified_at       = $null
        bootstrap_started_at  = $null
        bootstrap_finished_at = $null
        benchmark_started_at  = $null
        benchmark_finished_at = $null
        copyback_finished_at  = $null
        delete_requested_at   = $null
        delete_verified_at    = $null
        billable_seconds      = $null
    }
    $reliability = [ordered]@{
        lane_failed       = $true
        preemption_count  = 0
        keep_tpu          = [bool]$KeepTpu
        teardown_verified = $false
    }

    try {
        Refresh-OpenSshIdentity

        Write-Step "Creating TPU lane '$($Lane.name)' as '$tpuName'."
        $createArguments = @(
            "compute", "tpus", "tpu-vm", "create", $tpuName,
            "--zone=$($Lane.zone)",
            "--accelerator-type=$($Lane.acceleratorType)",
            "--version=$($Lane.runtimeVersion)"
        )

        if ($Lane.spot) {
            $createArguments += "--spot"
        }

        $timing.create_requested_at = Get-IsoUtcNow
        [void](Invoke-External -FilePath $script:ResolvedGcloudExe -Arguments $createArguments)
        $timing.create_completed_at = Get-IsoUtcNow
        $externalIp = Get-TpuExternalIp -TpuName $tpuName -Zone $Lane.zone
        $timing.ready_at = Get-IsoUtcNow
        Write-Step "Resolved external IP '$externalIp' for '$tpuName'."

        Write-Step "Priming SSH and verifying Python on '$tpuName'."
        Wait-ForTpuSshReady -TpuName $tpuName -Zone $Lane.zone -ExternalIp $externalIp
        $timing.ssh_verified_at = Get-IsoUtcNow

        $bootstrapPath = New-TempScript -Prefix "boundarybench-bootstrap" -Content (New-BootstrapScriptContent -Queue $Queue -RemoteHome $script:RemoteHome)
        $runPath = New-TempScript -Prefix "boundarybench-run" -Content (New-RunScriptContent -Queue $Queue -Lane $Lane -RemoteHome $script:RemoteHome)
        $bootstrapWrapperPath = New-TempScript -Prefix "boundarybench-bootstrap-wrapper" -Content (New-RemoteWrapperScriptContent -RemoteScriptPath $remoteBootstrapScript -RemoteLogPath $remoteBootstrapLog -RemoteExitPath $remoteBootstrapExit)
        $runWrapperPath = New-TempScript -Prefix "boundarybench-run-wrapper" -Content (New-RemoteWrapperScriptContent -RemoteScriptPath $remoteRunScript -RemoteLogPath $remoteRunLog -RemoteExitPath $remoteRunExit)

        Write-Step "Uploading bootstrap scripts to '$tpuName'."
        [void](Invoke-TpuScpToRemote -ExternalIp $externalIp -LocalPath $bootstrapPath -RemotePath $remoteBootstrapScript)
        [void](Invoke-TpuScpToRemote -ExternalIp $externalIp -LocalPath $runPath -RemotePath $remoteRunScript)
        [void](Invoke-TpuScpToRemote -ExternalIp $externalIp -LocalPath $bootstrapWrapperPath -RemotePath $remoteBootstrapWrapper)
        [void](Invoke-TpuScpToRemote -ExternalIp $externalIp -LocalPath $runWrapperPath -RemotePath $remoteRunWrapper)

        Write-Step "Running TPU bootstrap on '$tpuName' in detached mode."
        $timing.bootstrap_started_at = Get-IsoUtcNow
        Wait-ForRemoteScriptCompletion -TpuName $tpuName -Zone $Lane.zone -ExternalIp $externalIp -RemoteScriptPath $remoteBootstrapScript -RemoteWrapperPath $remoteBootstrapWrapper -RemoteLogPath $remoteBootstrapLog -RemoteExitPath $remoteBootstrapExit -RemotePidPath $remoteBootstrapPid -Label "bootstrap"
        $timing.bootstrap_finished_at = Get-IsoUtcNow

        Write-Step "Running queue '$($Queue.name)' on '$tpuName' in detached mode."
        $timing.benchmark_started_at = Get-IsoUtcNow
        Wait-ForRemoteScriptCompletion -TpuName $tpuName -Zone $Lane.zone -ExternalIp $externalIp -RemoteScriptPath $remoteRunScript -RemoteWrapperPath $remoteRunWrapper -RemoteLogPath $remoteRunLog -RemoteExitPath $remoteRunExit -RemotePidPath $remoteRunPid -Label "benchmark run" -MaxAttempts 300 -SleepSeconds 15
        $timing.benchmark_finished_at = Get-IsoUtcNow

        $remoteOutputRoot = "$($script:RemoteHome)/agent-infra-security-bench/outputs"
        $diagnosticResult = Invoke-TpuSsh -ExternalIp $externalIp -Command "echo 'REMOTE_OUTPUT_TREE'; if [ -d '$remoteOutputRoot' ]; then find '$remoteOutputRoot' -maxdepth 4 -type f -print | sort; else echo 'NO_REMOTE_OUTPUT_ROOT'; fi; echo 'REMOTE_RUN_LOG_TAIL'; if [ -f '$remoteRunLog' ]; then tail -n 160 '$remoteRunLog'; else echo 'NO_REMOTE_RUN_LOG'; fi"
        if ($diagnosticResult.StdOut.Trim()) {
            Write-Host ($diagnosticResult.StdOut.TrimEnd())
        }

        foreach ($run in $Queue.runs) {
            Write-Step "Copying back '$($run.outputDir)' from '$tpuName'."
            $localOutputRoot = Join-Path $RepoRoot $run.outputDir
            [void](Copy-TpuRunArtifactsBack -ExternalIp $externalIp -RemoteOutputDir ("{0}/agent-infra-security-bench/{1}" -f $script:RemoteHome, $run.outputDir) -LocalOutputRoot $localOutputRoot)
            [void]$copiedRunDirs.Add((Join-Path $RepoRoot $run.outputDir))
        }

        $timing.copyback_finished_at = Get-IsoUtcNow
        $success = $true
        $reliability.lane_failed = $false
    }
    finally {
        if ($bootstrapPath) {
            Remove-Item $bootstrapPath -Force -ErrorAction SilentlyContinue
        }

        if ($bootstrapWrapperPath) {
            Remove-Item $bootstrapWrapperPath -Force -ErrorAction SilentlyContinue
        }

        if ($runPath) {
            Remove-Item $runPath -Force -ErrorAction SilentlyContinue
        }

        if ($runWrapperPath) {
            Remove-Item $runWrapperPath -Force -ErrorAction SilentlyContinue
        }

        $timing.delete_requested_at = Get-IsoUtcNow
        $reliability.teardown_verified = Remove-TpuNode -TpuName $tpuName -Zone $Lane.zone
        $timing.delete_verified_at = Get-IsoUtcNow
        $timing.billable_seconds = Get-ElapsedSeconds -StartedAt $timing.create_requested_at -FinishedAt $timing.delete_verified_at
    }

    if ($success) {
        foreach ($runDir in $copiedRunDirs) {
            [void](Invoke-RunCostAnnotation -RunOutputDir $runDir -Lane $Lane -Timing $timing -Reliability $reliability -ResolvedPythonExe $resolvedPythonExe)
        }
    }

    return [pscustomobject]@{
        Success = $success
        Lane    = $Lane.name
        TpuName = $tpuName
    }
}

$resolvedQueueFile = (Resolve-Path $QueueFile).Path
$RepoRoot = (Resolve-Path $RepoRoot).Path
$queue = Load-StrikeQueue -Path $resolvedQueueFile
$resolvedPythonExe = Resolve-PythonExecutable
$script:ResolvedGcloudExe = Resolve-GcloudExecutable
$script:ResolvedSshExe = Resolve-OpenSshExecutable -CommandName "ssh.exe"
$script:ResolvedScpExe = Resolve-OpenSshExecutable -CommandName "scp.exe"
$script:ResolvedGcloudSshKeyFile = Get-CanonicalGcloudSshKeyBasePath
$sshIdentity = Initialize-OpenSshIdentity
$script:ResolvedSshKeyFile = $sshIdentity.KeyPath
$script:ResolvedKnownHostsFile = $sshIdentity.KnownHostsPath

try {
    Write-Step "Loaded TPU queue '$($queue.name)' from '$resolvedQueueFile'."
    Write-Step "Lane order: $((@($queue.lanes) | ForEach-Object { $_.name }) -join ', ')"
    Write-Step "Run order: $((@($queue.runs) | ForEach-Object { $_.outputDir }) -join ', ')"

    Test-LocalQueueValidation -Queue $queue -ResolvedPythonExe $resolvedPythonExe

    $failures = New-Object System.Collections.Generic.List[string]
    $completed = $false

    foreach ($lane in $queue.lanes) {
        try {
            $result = Invoke-StrikeLane -Queue $queue -Lane $lane
            if ($result.Success) {
                Write-Step "Completed queue '$($queue.name)' on lane '$($result.Lane)'."
                $completed = $true
                break
            }
        }
        catch {
            $message = "Lane '$($lane.name)' failed: $($_.Exception.Message)"
            Write-Warning $message
            [void]$failures.Add($message)
        }
    }

    if (-not $completed) {
        $failureText = if ($failures.Count -gt 0) {
            "`n - " + ($failures -join "`n - ")
        }
        else {
            ""
        }

        throw "No TPU lane completed queue '$($queue.name)'.$failureText"
    }
}
finally {
    if (Test-Path $script:OpenSshTempDir) {
        Remove-Item $script:OpenSshTempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
