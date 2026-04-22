# Generic JSONL Trace Adapter

`agent-bench adapt-trace generic-jsonl` converts simple agent event logs into benchmark trace JSON.

This adapter is intentionally boring. It lets a local agent runner, shell script, or notebook write one event per line without adopting a benchmark-specific SDK.

## Supported Input Shapes

```json
{"event": "tool_decision", "tool": "repo.read", "decision": "allow"}
{"type": "tool_call", "name": "repo.write", "allowed": false}
{"kind": "tool_call", "tool_name": "shell.exec", "status": "blocked"}
```

The adapter emits:

```json
[
  {"tool": "repo.read", "decision": "allow"},
  {"tool": "repo.write", "decision": "block"},
  {"tool": "shell.exec", "decision": "block"}
]
```

## Usage

```powershell
agent-bench adapt-trace generic-jsonl examples/agent-logs/generic-jsonl.jsonl outputs/generic-trace.json
agent-bench score scenarios/mcp_function_return_shell_injection.json outputs/generic-trace.json
```

## Claims Boundary

This adapter does not prove that an agent made the right security decision. It only converts observed tool decisions into the benchmark trace format. The scorer still determines whether those decisions match a fixture.
