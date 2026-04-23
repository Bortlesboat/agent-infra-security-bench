# TPU Frontier Sprint Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first generic OpenAI-compatible serving lane, refresh the TPU runbook to the grant-safe `v6e-8` path, and prepare BoundaryBench for the first TPU baseline plus the later TPU Frontier Pack.

**Architecture:** Extend the existing `llm_agent` abstraction instead of adding a TPU-specific fork. TPU serving should look like just another OpenAI-compatible backend, so the existing raw-event, trace, coverage, manifest, and sweep flow stays unchanged. In parallel, refresh the TPU documentation to encode the billing protocol and first-run sequence before any billed resources are created.

**Tech Stack:** Python 3.12, `urllib.request`, existing `agent_infra_security_bench` CLI and runner modules, pytest, Google Cloud TPU docs, vLLM TPU serving assumptions.

---

## File Structure

- Create: `docs/superpowers/plans/2026-04-23-tpu-frontier-sprint.md`
- Modify: `src/agent_infra_security_bench/llm_agent.py`
- Modify: `src/agent_infra_security_bench/cli.py`
- Modify: `tests/test_llm_agent.py`
- Modify: `tests/test_cli.py`
- Modify: `docs/runbooks/cloud-tpu-first-run.md`
- Optional later modify: `README.md`
- Optional later create: `scenarios/*` for the TPU Frontier Pack

The first implementation slice should stay tightly focused on the runner and runbook. Do not start adding the frontier fixtures until the generic runner and safe TPU runbook are both in place.

## Chunk 1: Generic OpenAI-Compatible Runner

### Task 1: Add the failing runner tests first

**Files:**
- Modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/tests/test_llm_agent.py`
- Modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/tests/test_cli.py`

- [ ] **Step 1: Write the failing client tests**

Add tests for:

- a new `OpenAICompatibleModelClient`
- env-file and env-var API key loading
- optional no-auth mode for local TPU endpoints
- chat-completions request payload shape
- bounded retry for transient `502/503/504`
- `write_llm_agent_run(...)` with the new client
- CLI summary output for `run-openai-agent`

Example test skeleton:

```python
def test_openai_compatible_client_calls_chat_completions(tmp_path, monkeypatch):
    client = OpenAICompatibleModelClient(
        model="meta-llama/Llama-3.1-8B-Instruct",
        base_url="http://127.0.0.1:8000/v1",
        api_key="local-token",
    )
    response = client.generate_decisions(fixture)
    assert json.loads(response)["decisions"][0]["tool"] == "repo.read_public_issue"
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_llm_agent.py tests/test_cli.py -k "openai_compatible or run_openai_agent" -v
```

Expected:

- FAIL with missing import, missing class, or missing CLI command

- [ ] **Step 3: Commit the red state only if you need a checkpoint**

```powershell
git status --short
```

No commit is required if the red-state checkpoint is too noisy.

### Task 2: Implement the generic client and CLI

**Files:**
- Modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/src/agent_infra_security_bench/llm_agent.py`
- Modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/src/agent_infra_security_bench/cli.py`

- [ ] **Step 1: Add `OpenAICompatibleModelClient`**

Implement a new client in `llm_agent.py` with:

- `provider = "openai-compatible"`
- `model`
- `base_url`
- optional `api_key`
- optional `env_file`
- `prompt_profile`
- `timeout`
- bounded retry behavior matching the hosted NVIDIA path

Minimal request pattern:

```python
payload = {
    "model": self.model,
    "messages": [{"role": "user", "content": render_decision_prompt(...)}],
    "temperature": 0,
    "max_tokens": 800,
    "stream": False,
}
```

Use the existing `_extract_chat_completion_text(...)` helper so parsing stays shared.

- [ ] **Step 2: Add a small wrapper like `write_openai_agent_run(...)`**

Keep it parallel to `write_ollama_agent_run(...)` and `write_nvidia_nim_agent_run(...)`:

```python
def write_openai_agent_run(...):
    return write_llm_agent_run(... client=OpenAICompatibleModelClient(...))
```

- [ ] **Step 3: Add CLI wiring**

Add a new command to `cli.py`:

```text
agent-bench run-openai-agent
```

Recommended flags:

- `scenario_dir`
- `output_dir`
- `--model`
- `--base-url`
- `--api-key`
- `--api-key-env`
- `--env-file`
- `--timeout`
- `--scenario-commit`
- `--prompt-profile`
- `--runtime-policy`
- `--hardware`

The CLI output should match the current Ollama and NVIDIA summary format.

- [ ] **Step 4: Run focused tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_llm_agent.py tests/test_cli.py -k "openai_compatible or run_openai_agent" -v
```

Expected:

- PASS

- [ ] **Step 5: Run the broader agent test surface**

Run:

```powershell
python -m pytest tests/test_llm_agent.py tests/test_cli.py -v
```

Expected:

- PASS

- [ ] **Step 6: Commit the runner slice**

```powershell
git add src/agent_infra_security_bench/llm_agent.py src/agent_infra_security_bench/cli.py tests/test_llm_agent.py tests/test_cli.py
git commit -m "feat: add openai-compatible model runner"
```

## Chunk 2: Grant-Safe TPU Runbook Refresh

### Task 3: Rewrite the TPU runbook around the actual grant-safe path

**Files:**
- Modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/docs/runbooks/cloud-tpu-first-run.md`

- [ ] **Step 1: Update the first-run target**

Replace the outdated `v5litepod-8` / `us-east5-a` path with:

- primary: `spot v6e-8` in `us-east1-d`
- fallback: `spot v5e-8` in `us-central1-a`

- [ ] **Step 2: Add explicit no-billing-surprises protocol**

Document:

- approved-zone-only rule
- single-host-only first run
- no GKE / Vertex for the first lane
- explicit stop/delete verification
- reminder that non-TPU GCP services can still bill

- [ ] **Step 3: Add the first TPU serving sequence**

Document the exact shape:

1. enable APIs
2. create TPU VM
3. SSH into VM
4. install `vllm-tpu`
5. serve one instruct model
6. hit one completion endpoint
7. run benchmark smoke and full 34-fixture checklist baseline
8. copy artifacts back
9. stop/delete TPU

- [ ] **Step 4: Add artifact expectations**

The runbook should explicitly say the first run must emit:

- raw events
- traces
- results CSV/Markdown
- coverage JSON/Markdown
- manifest

- [ ] **Step 5: Run a quick doc sanity check**

Run:

```powershell
Get-Content docs/runbooks/cloud-tpu-first-run.md
git diff -- docs/runbooks/cloud-tpu-first-run.md
```

Expected:

- updated zone, accelerator, and cleanup path are visibly correct

- [ ] **Step 6: Commit the runbook slice**

```powershell
git add docs/runbooks/cloud-tpu-first-run.md
git commit -m "docs: refresh TPU first-run protocol"
```

## Chunk 3: Local Preflight And First TPU Execution Prep

### Task 4: Prepare the zero-billing local preflight

**Files:**
- Modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/docs/runbooks/cloud-tpu-first-run.md`
- Optional create: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/docs/reports/2026-04-tpu-smoke-template.md`

- [ ] **Step 1: Run local non-billed checks**

Run:

```powershell
gcloud --version
gcloud auth list
gcloud config list
gcloud config set project <your-grant-approved-project-id>
gcloud services list --enabled --filter="NAME:tpu.googleapis.com"
```

Expected:

- local environment points at the correct project before any TPU create

- [ ] **Step 2: Save the exact first-run command block in the runbook**

Document the precise command that will be used for the first create.

- [ ] **Step 3: Do not create the TPU until the runner slice is merged locally and reviewed**

This step is a gate, not code:

- no TPU VM before the generic runner and runbook are done

## Chunk 4: TPU Frontier Pack Implementation

### Task 5: Add the first 6-8 frontier fixtures only after the TPU baseline row exists

**Files:**
- Create: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/scenarios/*.json`
- Modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/tests/` as needed
- Modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/docs/reports/*.md`

- [ ] **Step 1: Add 2 long-menu controls**
- [ ] **Step 2: Add 2 stateful controls**
- [ ] **Step 3: Add 3-4 marquee hybrid fixtures**
- [ ] **Step 4: Validate fixtures with targeted tests and benchmark commands**
- [ ] **Step 5: Commit the frontier-pack slice**

Use the existing fixture schema and keep all cases public-safe.

## Chunk 5: Reporting And Publication

### Task 6: Publish the first TPU comparison story

**Files:**
- Create or modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/docs/reports/*.md`
- Modify: `C:/Users/andre/OneDrive/Documents/Playground/agent-infra-security-bench/commons/index.json`

- [ ] **Step 1: Write the first TPU baseline report**
- [ ] **Step 2: Add the TPU row to the sweep surfaces**
- [ ] **Step 3: Update Commons metadata**
- [ ] **Step 4: Run full verification**

Run:

```powershell
python -m pytest
python -m agent_infra_security_bench.cli validate-commons commons/index.json --root .
python -m agent_infra_security_bench.cli validate-candidates candidates
git diff --check
```

Expected:

- PASS

- [ ] **Step 5: Commit the reporting slice**

```powershell
git add docs/reports commons/index.json
git commit -m "docs: publish TPU baseline comparison"
```

## Execution Notes

- Keep secrets and account-specific values out of the repo at all times.
- Do not commit `.env` files, tokens, project credentials, or TPU IPs.
- Prefer local shell preflight before any TPU create command.
- The first meaningful execution target is Chunk 1 plus Chunk 2. Do not jump to frontier fixtures first.
