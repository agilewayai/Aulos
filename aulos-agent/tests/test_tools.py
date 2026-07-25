"""Tool unit tests."""

from aulos_agent.tools.builtin import echo_text, get_current_utc_time
from aulos_agent.tools.registry import get_tools


def test_echo_tool():
    assert echo_text.invoke({"text": "ping"}) == "ping"


def test_utc_tool_returns_iso_like_string():
    value = get_current_utc_time.invoke({})
    assert "T" in value
    assert value.endswith("+00:00") or value.endswith("Z") or "+" in value[10:]


def test_default_registry_includes_builtins():
    names = {t.name for t in get_tools()}
    assert "echo_text" in names
    assert "get_current_utc_time" in names
