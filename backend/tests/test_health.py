"""第一阶段验收测试：/health 健康检查。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["service"] == "Lost-and-Found Intelligent Platform"


def test_health_contains_version_and_time():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"]
    assert data["time"]
    assert data["environment"] == "development"
