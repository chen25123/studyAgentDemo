"""Metric Engine 核心测试。

验证语义层引擎的校验、编译、执行全链路。
"""

from datetime import date

import pytest
from sqlalchemy import text

from llm.repositories.db import get_engine
from llm.schemas.metric_query import MetricQuery, TimeRange
from llm.services.metric_engine import MetricEngine, MetricEngineError


@pytest.fixture
def engine() -> MetricEngine:
    return MetricEngine()


def _bug_query(**kwargs) -> MetricQuery:
    return MetricQuery(
        metric_codes=kwargs.pop("metric_codes", ["bug_close_rate"]),
        time_range=kwargs.pop(
            "time_range",
            TimeRange(start_date=date(2026, 6, 1), end_date=date(2026, 6, 30)),
        ),
        **kwargs,
    )


class TestBasicMetrics:
    def test_bug_close_rate_returns_value(self, engine):
        results, _ = engine.execute(_bug_query())
        assert len(results) == 1
        assert results[0].metric_code == "bug_close_rate"
        assert results[0].value is not None
        assert results[0].unit == "%"

    def test_bug_open_rate_returns_value(self, engine):
        results, _ = engine.execute(
            _bug_query(metric_codes=["bug_open_rate"])
        )
        assert len(results) == 1
        assert results[0].value is not None

    def test_description_present(self, engine):
        results, _ = engine.execute(_bug_query())
        assert len(results[0].description) > 0

    def test_measures_present(self, engine):
        results, _ = engine.execute(_bug_query())
        assert "closed_bug_count" in results[0].measures
        assert "bug_count" in results[0].measures


class TestTimeRange:
    def test_with_time_range(self, engine):
        results, _ = engine.execute(_bug_query())
        assert results[0].measures.get("bug_count", 0) > 0

    def test_future_range_returns_zero(self, engine):
        results, _ = engine.execute(
            _bug_query(
                time_range=TimeRange(
                    start_date=date(2030, 1, 1), end_date=date(2030, 1, 31)
                )
            )
        )
        assert results[0].measures.get("bug_count", 0) == 0


class TestGroupBy:
    def test_group_by_module(self, engine):
        results, _ = engine.execute(_bug_query(group_by=["module_name"]))
        assert len(results) > 1
        for r in results:
            assert "module_name" in r.dimensions

    def test_group_by_severity(self, engine):
        results, _ = engine.execute(
            _bug_query(group_by=["severity"])
        )
        # 种子数据可能只产生一种 severity，至少验证分组生效
        assert len(results) >= 1
        for r in results:
            assert "severity" in r.dimensions


class TestValidation:
    def test_invalid_metric_rejected(self, engine):
        with pytest.raises(MetricEngineError, match="不存在或未激活"):
            engine.execute(_bug_query(metric_codes=["nonexistent_metric"]))

    def test_invalid_filter_rejected(self, engine):
        with pytest.raises(MetricEngineError, match="不支持过滤"):
            engine.execute(
                _bug_query(filters={"nonexistent_field": "value"})
            )

    def test_empty_metrics_rejected(self, engine):
        with pytest.raises(MetricEngineError, match="至少需要一个"):
            engine.execute(
                MetricQuery(
                    metric_codes=[], time_range=None, filters={}, group_by=[]
                )
            )

    def test_mixed_entity_rejected(self, engine):
        """跨实体查询应在阶段一被拒绝。"""
        with pytest.raises(MetricEngineError, match="单实体"):
            engine.execute(
                MetricQuery(
                    metric_codes=["bug_close_rate", "requirement_delay_rate"],
                    time_range=None,
                    filters={},
                    group_by=[],
                )
            )


class TestOrgFilter:
    def test_filter_by_org_name(self, engine):
        """组织名称过滤应正确 JOIN 并返回结果。"""
        results, _ = engine.execute(
            _bug_query(filters={"assignee_org_name": "研发"})
        )
        assert len(results) == 1


class TestQueryLog:
    def test_query_log_written(self, engine):
        """执行查询后 metric_query_logs 应有新记录。"""
        db = get_engine()
        with db.connect() as conn:
            before = conn.execute(
                text("SELECT COUNT(*) FROM metric_query_logs")
            ).scalar()

        engine.execute(_bug_query())

        with db.connect() as conn:
            after = conn.execute(
                text("SELECT COUNT(*) FROM metric_query_logs")
            ).scalar()
        assert after > before
