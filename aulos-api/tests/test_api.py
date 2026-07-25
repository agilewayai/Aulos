from fastapi.testclient import TestClient

from aulos_api.app import create_app


def test_health() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "aulos-api"


def test_chat_fake() -> None:
    client = TestClient(create_app())
    response = client.post("/v1/chat", json={"message": "hello", "thread_id": "t1"})
    assert response.status_code == 200
    body = response.json()
    assert "hello" in body["reply"]
    assert body["thread_id"] == "t1"
    assert body["source"] == "fake"
