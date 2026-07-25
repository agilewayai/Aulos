"""Static-host rate gate rules."""

from rate_gate import RateGate, rule_for


def test_version_rule_is_tight() -> None:
    name, limit, window = rule_for("/version.json")
    assert name == "version"
    assert limit <= 30
    assert window == 60.0


def test_gate_blocks() -> None:
    gate = RateGate()
    for _ in range(3):
        ok, _ = gate.allow("t:ip", limit=3, window_sec=60)
        assert ok
    ok, retry = gate.allow("t:ip", limit=3, window_sec=60)
    assert not ok
    assert retry > 0
