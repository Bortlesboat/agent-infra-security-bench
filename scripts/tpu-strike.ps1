[CmdletBinding()]
param(
    [string]$QueueFile,
    [string]$RepoRoot,
    [string]$PythonExe,
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

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
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

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FilePath
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.RedirectStandardInput = $null -ne $InputText

    foreach ($argument in $Arguments) {
        [void]$startInfo.ArgumentList.Add($argument)
    }

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

    $preferred = "C:/Users/andre/AppData/Local/Programs/Python/Python312/python.exe"
    if (Test-Path $preferred) {
        return (Resolve-Path $preferred).Path
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }

    throw "No Python executable found. Pass -PythonExe explicitly."
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

    $raw = ("{0}-{1}-{2}" -f $QueueName, $LaneName, (Get-Date -Format "MMddHHmm")).ToLowerInvariant()
    $sanitized = ($raw -replace "[^a-z0-9-]", "-")
    $collapsed = ($sanitized -replace "-{2,}", "-").Trim("-")

    if ($collapsed.Length -gt 63) {
        return $collapsed.Substring(0, 63).Trim("-")
    }

    return $collapsed
}

function New-TempScript {
    param(
        [string]$Prefix,
        [string]$Content
    )

    $path = Join-Path ([System.IO.Path]::GetTempPath()) ("{0}-{1}.sh" -f $Prefix, ([System.Guid]::NewGuid().ToString("N")))
    Set-Content -Path $path -Value $Content -Encoding ascii
    return $path
}

function New-BootstrapScriptContent {
    param($Queue)

    $repoBranch = $Queue.repoBranch
    $content = @'
#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --user uv
export PATH="$HOME/.local/bin:$PATH"

if [ ! -d "$HOME/.venvs/boundarybench" ]; then
  uv venv "$HOME/.venvs/boundarybench"
fi

source "$HOME/.venvs/boundarybench/bin/activate"
uv pip install --upgrade vllm-tpu

if [ ! -d "$HOME/agent-infra-security-bench/.git" ]; then
  git clone https://github.com/Bortlesboat/agent-infra-security-bench "$HOME/agent-infra-security-bench"
fi

cd "$HOME/agent-infra-security-bench"
git fetch origin
git checkout __REPO_BRANCH__
git pull --ff-only origin __REPO_BRANCH__
uv pip install -e .
'@
    return $content.Replace("__REPO_BRANCH__", $repoBranch)
}

function New-RunScriptContent {
    param(
        $Queue,
        $Lane
    )

    $modelId = $Queue.model.id
    $tensorParallelSize = [string]$Queue.model.tensorParallelSize
    $maxModelLen = [string]$Queue.model.maxModelLen
    $scenarioDir = $Queue.scenarioDir
    $scenarioCommitSuffix = $Queue.scenarioCommitSuffix
    $hardwareLabel = $Lane.hardwareLabel

    $runLines = foreach ($run in $Queue.runs) {
        "python -m agent_infra_security_bench.cli run-openai-agent $scenarioDir $($run.outputDir) --model '$modelId' --base-url http://127.0.0.1:8000/v1 --scenario-commit `"`$SCENARIO_COMMIT`" --prompt-profile $($run.promptProfile) --runtime-policy $($run.runtimePolicy) --hardware $hardwareLabel"
    }

    $runBlock = ($runLines -join "`n")

    $content = @'
#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
source "$HOME/.venvs/boundarybench/bin/activate"
cd "$HOME/agent-infra-security-bench"

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
        Replace("__RUN_BLOCK__", $runBlock)
}

function Invoke-TpuSsh {
    param(
        [string]$TpuName,
        [string]$Zone,
        [string]$Command
    )

    [void](Invoke-External -FilePath "gcloud" -Arguments @(
        "compute", "tpus", "tpu-vm", "ssh", $TpuName,
        "--zone=$Zone",
        "--command=$Command"
    ) -InputText "y")
}

function Invoke-TpuScpToRemote {
    param(
        [string]$TpuName,
        [string]$Zone,
        [string]$LocalPath,
        [string]$RemotePath
    )

    [void](Invoke-External -FilePath "gcloud" -Arguments @(
        "compute", "tpus", "tpu-vm", "scp",
        $LocalPath,
        ("{0}:{1}" -f $TpuName, $RemotePath),
        "--zone=$Zone"
    ) -InputText "y")
}

function Invoke-TpuScpFromRemote {
    param(
        [string]$TpuName,
        [string]$Zone,
        [string]$RemotePath,
        [string]$LocalPath
    )

    [void](Invoke-External -FilePath "gcloud" -Arguments @(
        "compute", "tpus", "tpu-vm", "scp",
        "--recurse",
        ("{0}:{1}" -f $TpuName, $RemotePath),
        $LocalPath,
        "--zone=$Zone"
    ) -InputText "y")
}

function Remove-TpuNode {
    param(
        [string]$TpuName,
        [string]$Zone
    )

    if ($KeepTpu) {
        Write-Step "Keeping TPU node '$TpuName' in $Zone by request."
        return
    }

    Write-Step "Deleting TPU node '$TpuName' in $Zone."
    [void](Invoke-External -FilePath "gcloud" -Arguments @(
        "compute", "tpus", "tpu-vm", "delete", $TpuName,
        "--zone=$Zone",
        "--quiet"
    ) -AllowFailure)

    [void](Invoke-External -FilePath "gcloud" -Arguments @(
        "compute", "tpus", "tpu-vm", "list",
        "--zone=$Zone"
    ) -AllowFailure)
}

function Invoke-StrikeLane {
    param(
        $Queue,
        $Lane
    )

    $tpuName = New-StrikeName -QueueName $Queue.name -LaneName $Lane.name
    $bootstrapPath = $null
    $runPath = $null

    try {
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

        [void](Invoke-External -FilePath "gcloud" -Arguments $createArguments)

        Write-Step "Priming SSH and verifying Python on '$tpuName'."
        Invoke-TpuSsh -TpuName $tpuName -Zone $Lane.zone -Command "python3 --version"

        $bootstrapPath = New-TempScript -Prefix "boundarybench-bootstrap" -Content (New-BootstrapScriptContent -Queue $Queue)
        $runPath = New-TempScript -Prefix "boundarybench-run" -Content (New-RunScriptContent -Queue $Queue -Lane $Lane)

        Write-Step "Uploading bootstrap scripts to '$tpuName'."
        Invoke-TpuScpToRemote -TpuName $tpuName -Zone $Lane.zone -LocalPath $bootstrapPath -RemotePath "~/boundarybench-bootstrap.sh"
        Invoke-TpuScpToRemote -TpuName $tpuName -Zone $Lane.zone -LocalPath $runPath -RemotePath "~/boundarybench-run.sh"

        Write-Step "Running TPU bootstrap on '$tpuName'."
        Invoke-TpuSsh -TpuName $tpuName -Zone $Lane.zone -Command "bash ~/boundarybench-bootstrap.sh"

        Write-Step "Running queue '$($Queue.name)' on '$tpuName'."
        Invoke-TpuSsh -TpuName $tpuName -Zone $Lane.zone -Command "bash ~/boundarybench-run.sh"

        foreach ($run in $Queue.runs) {
            Write-Step "Copying back '$($run.outputDir)' from '$tpuName'."
            Invoke-TpuScpFromRemote -TpuName $tpuName -Zone $Lane.zone -RemotePath ("~/agent-infra-security-bench/{0}" -f $run.outputDir) -LocalPath (Join-Path $RepoRoot "outputs")
        }

        return [pscustomobject]@{
            Success = $true
            Lane    = $Lane.name
            TpuName = $tpuName
        }
    }
    finally {
        if ($bootstrapPath) {
            Remove-Item $bootstrapPath -Force -ErrorAction SilentlyContinue
        }

        if ($runPath) {
            Remove-Item $runPath -Force -ErrorAction SilentlyContinue
        }

        Remove-TpuNode -TpuName $tpuName -Zone $Lane.zone
    }
}

$resolvedQueueFile = (Resolve-Path $QueueFile).Path
$RepoRoot = (Resolve-Path $RepoRoot).Path
$queue = Load-StrikeQueue -Path $resolvedQueueFile
$resolvedPythonExe = Resolve-PythonExecutable

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
