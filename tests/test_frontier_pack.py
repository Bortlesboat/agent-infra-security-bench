from pathlib import Path

from agent_infra_security_bench.fixtures import load_fixture
from agent_infra_security_bench.policy_agent import write_policy_traces
from agent_infra_security_bench.results import score_suite


def test_frontier_pack_scenarios_load():
    scenario_dir = Path(__file__).resolve().parents[1] / "scenarios-frontier"

    fixtures = [load_fixture(path) for path in sorted(scenario_dir.glob("*.json"))]

    assert len(fixtures) == 7
    assert sum(len(fixture.tools) for fixture in fixtures) == 47
    assert {
        "frontier_long_menu_provenance_reply",
        "frontier_long_menu_payment_binding",
        "frontier_stateful_artifact_continuation",
        "frontier_stateful_memory_handoff",
        "frontier_hybrid_checkout_origin_and_payment",
        "frontier_hybrid_release_note_continuation",
        "frontier_hybrid_incident_handoff",
    } == {fixture.attack_type for fixture in fixtures}


def test_frontier_pack_distinguishes_payment_state_from_full_stateful_policy(tmp_path):
    scenario_dir = Path(__file__).resolve().parents[1] / "scenarios-frontier"

    payment_state_traces = tmp_path / "payment-state-traces"
    stateful_traces = tmp_path / "stateful-traces"

    write_policy_traces(scenario_dir, payment_state_traces, "deny-high-risk-payment-state")
    write_policy_traces(scenario_dir, stateful_traces, "deny-high-risk-stateful")

    payment_state_summary = score_suite(scenario_dir, payment_state_traces)
    stateful_summary = score_suite(scenario_dir, stateful_traces)

    assert payment_state_summary.total == 7
    assert payment_state_summary.passed == 1
    assert stateful_summary.total == 7
    assert stateful_summary.passed == 7
