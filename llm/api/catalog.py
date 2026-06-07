"""Metric Catalog 只读 API —— 指标、实体、维度、度量目录查询。"""

from fastapi import APIRouter

from llm.repositories.metric_layer_repository import MetricLayerRepository

router = APIRouter(prefix="/api", tags=["catalog"])

_repo = MetricLayerRepository()


@router.get("/metrics")
def list_metrics():
    return _repo.list_active_metrics()


@router.get("/metrics/{metric_code}")
def get_metric(metric_code: str):
    metric = _repo.get_active_metric(metric_code)
    if metric is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"指标 {metric_code} 不存在")
    return metric


@router.get("/entities")
def list_entities():
    from sqlalchemy import text

    from llm.repositories.db import get_engine

    with get_engine().connect() as conn:
        rows = conn.execute(
            text(
                "SELECT entity_code, entity_name, base_table, description, status "
                "FROM entity_definitions WHERE status = 'active'"
            )
        ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/entities/{entity_code}/dimensions")
def list_dimensions(entity_code: str):
    dims = _repo.get_dimensions(entity_code)
    return dims


@router.get("/metrics/{metric_code}/value")
def get_metric_value(metric_code: str):
    """查询某个指标的当月数值。"""
    from datetime import date

    from llm.schemas.metric_query import MetricQuery, TimeRange
    from llm.services.metric_engine import MetricEngine, MetricEngineError

    metric = _repo.get_active_metric(metric_code)
    if metric is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"指标 {metric_code} 不存在")

    engine = MetricEngine()
    month_start = date.today().replace(day=1)
    try:
        results, sql = engine.execute(
            MetricQuery(
                metric_codes=[metric_code],
                time_range=TimeRange(start_date=month_start, end_date=date.today()),
                filters={},
                group_by=[],
            )
        )
        if results:
            r = results[0]
            return {
                "metric_code": r.metric_code,
                "metric_name": r.metric_name,
                "value": r.value,
                "unit": r.unit,
                "measures": r.measures,
                "description": r.description,
                "period": f"{month_start.isoformat()} ~ {date.today().isoformat()}",
            }
    except MetricEngineError:
        pass
    return {"metric_code": metric_code, "value": None}


@router.get("/suggestions")
def get_suggestions():
    """返回基于当前指标的动态建议问题列表。"""
    metrics = _repo.list_active_metrics()
    suggestions: list[str] = []
    for m in metrics:
        code = m["metric_code"]
        name = m["metric_name"]
        if "close_rate" in code:
            suggestions.append(f"本月 {name} 是多少？")
            suggestions.append(f"按模块统计本月 {name}")
        elif "open_rate" in code:
            suggestions.append(f"当前 {name} 是多少？")
        elif "reopen_rate" in code:
            suggestions.append(f"哪个模块的 {name} 最高？")
        elif "delay_rate" in code:
            suggestions.append(f"近三个月 {name} 趋势如何？")
        elif "count" in code:
            suggestions.append(f"最近一个月创建了多少 {name.split()[0]}？")
    if not suggestions:
        suggestions = [
            "最近一个月创建了多少 Bug？",
            "本月 Bug 关闭率是多少？",
            "查看当前组织架构",
        ]
    return suggestions[:6]


@router.get("/entities/{entity_code}/measures")
def list_measures(entity_code: str):
    from sqlalchemy import text

    from llm.repositories.db import get_engine

    with get_engine().connect() as conn:
        rows = conn.execute(
            text(
                "SELECT measure_code, measure_name, entity_code, aggregation, "
                "expression, description, status "
                "FROM measure_definitions "
                "WHERE entity_code = :code AND status = 'active'"
            ),
            {"code": entity_code},
        ).mappings().all()
    return [dict(r) for r in rows]
