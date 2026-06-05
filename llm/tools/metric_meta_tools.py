from langchain_core.tools import tool

from llm.repositories.metric_layer_repository import MetricLayerRepository

_repo = MetricLayerRepository()


@tool
def list_available_metrics() -> str:
    """列出当前所有可用的业务指标及其口径说明。

    当用户问"有哪些指标""能查什么指标"时调用。
    当你不确定某个业务概念对应哪个指标编码时也先调用此工具。
    """
    metrics = _repo.list_active_metrics()

    if not metrics:
        return "当前没有可用的业务指标。"

    lines = ["当前可用业务指标："]
    for m in metrics:
        unit_label = "%" if m["format_type"] == "percent" else "个"
        lines.append(
            f"- **{m['metric_code']}**：{m['metric_name']} "
            f"（实体={m['entity_code']}，格式={unit_label}）"
        )
        lines.append(f"  {m['description']}")

    return "\n".join(lines)
