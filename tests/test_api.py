"""API 集成测试 —— 用 FastAPI TestClient 验证 HTTP 接口。

不依赖外部 LLM（mock Agent.invoke）。
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from llm.api.app import app

client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestDashboard:
    def test_summary_ok(self):
        r = client.get("/api/dashboard/summary")
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data
        assert "risks" in data
        assert len(data["metrics"]) == 4
        assert len(data["risks"]) == 3


class TestCatalog:
    def test_entities(self):
        r = client.get("/api/entities")
        assert r.status_code == 200
        entities = r.json()
        assert len(entities) >= 2  # bug + requirement

    def test_metrics(self):
        r = client.get("/api/metrics")
        assert r.status_code == 200
        metrics = r.json()
        assert len(metrics) >= 4

    def test_metric_detail(self):
        r = client.get("/api/metrics/bug_close_rate")
        assert r.status_code == 200
        assert r.json()["metric_code"] == "bug_close_rate"

    def test_metric_detail_not_found(self):
        r = client.get("/api/metrics/nonexistent")
        assert r.status_code == 404

    def test_dimensions(self):
        r = client.get("/api/entities/bug/dimensions")
        assert r.status_code == 200
        dims = r.json()
        assert len(dims) >= 9


class TestChat:
    @patch("llm.services.chat_service.DevFlowAgent.ask")
    def test_chat_ok(self, mock_ask):
        mock_ask.return_value = "回复内容"
        r = client.post(
            "/api/chat",
            json={"message": "测试消息", "session_id": "test-session"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["reply"] == "回复内容"
        assert data["session_id"] == "test-session"


class TestChatStream:
    @patch("llm.services.chat_service.MetricQueryGraph.astream")
    def test_stream_ok(self, mock_stream):
        async def fake_stream(session_id, message):
            yield 'data: {"type":"final"}\n\n'

        mock_stream.return_value = fake_stream("x", "y")

        with client.stream(
            "POST",
            "/api/chat/stream",
            json={"message": "测试", "session_id": "test"},
        ) as r:
            assert r.status_code == 200
            r.read()
            assert "final" in r.text


class TestSuggestions:
    def test_suggestions_ok(self):
        r = client.get("/api/suggestions")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0


class TestMetricValue:
    def test_bug_count_value(self):
        r = client.get("/api/metrics/bug_count/value")
        assert r.status_code == 200
        data = r.json()
        assert data["metric_code"] == "bug_count"
        assert data["value"] is not None

    def test_metric_value_not_found(self):
        r = client.get("/api/metrics/nonexistent/value")
        assert r.status_code == 404


class TestAdminAuth:
    def test_no_token_returns_403(self):
        r = client.get("/api/admin/llm-traces")
        assert r.status_code == 403
        assert r.json()["error_code"] == "PERMISSION_DENIED"

    def test_wrong_token_returns_403(self):
        r = client.get(
            "/api/admin/llm-traces",
            headers={"X-Admin-Token": "wrong"},
        )
        assert r.status_code == 403
