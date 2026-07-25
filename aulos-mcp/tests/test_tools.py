from aulos_mcp.tools import aulos_status, echo_message, utc_now


def test_echo_message() -> None:
    assert echo_message("hi") == "echo: hi"


def test_utc_now_iso() -> None:
    value = utc_now()
    assert "T" in value
    assert value.endswith("+00:00") or value.endswith("Z") or "+" in value


def test_aulos_status() -> None:
    status = aulos_status()
    assert status["project"] == "aulos-mcp"
    assert status["status"] == "ready"


def test_create_server() -> None:
    from aulos_mcp.server import create_server

    server = create_server()
    assert server is not None
    assert server.name == "aulos-mcp"
