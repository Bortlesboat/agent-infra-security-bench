import json

from agent_infra_security_bench.adapters import convert_generic_events, load_generic_events


def test_convert_generic_events_extracts_tool_decisions():
    events = [
        {"event": "message", "content": "Checking the repo."},
        {"event": "tool_decision", "tool": "repo.read", "decision": "allow"},
        {"type": "tool_call", "name": "repo.write", "allowed": False},
        {"kind": "tool_call", "tool_name": "shell.exec", "status": "blocked"},
    ]

    assert convert_generic_events(events) == [
        {"tool": "repo.read", "decision": "allow"},
        {"tool": "repo.write", "decision": "block"},
        {"tool": "shell.exec", "decision": "block"},
    ]


def test_load_generic_events_supports_jsonl_and_json_array(tmp_path):
    jsonl = tmp_path / "events.jsonl"
    jsonl.write_text(
        "\n".join(
            [
                json.dumps({"event": "tool_decision", "tool": "repo.read", "decision": "allow"}),
                json.dumps({"type": "tool_call", "name": "repo.write", "allowed": False}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    array = tmp_path / "events.json"
    array.write_text(
        json.dumps([{"kind": "tool_call", "tool_name": "shell.exec", "status": "blocked"}]),
        encoding="utf-8",
    )

    assert load_generic_events(jsonl) == [
        {"event": "tool_decision", "tool": "repo.read", "decision": "allow"},
        {"type": "tool_call", "name": "repo.write", "allowed": False},
    ]
    assert load_generic_events(array) == [
        {"kind": "tool_call", "tool_name": "shell.exec", "status": "blocked"}
    ]
