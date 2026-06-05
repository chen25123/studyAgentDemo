from langchain_core.tools import tool

from llm.repositories.org_metric_repository import OrgMetricRepository
from llm.schemas.org_metric import OrgMetricQuery

_repo = OrgMetricRepository()


@tool
def query_org_structure(query: OrgMetricQuery) -> str:
    """查询组织架构数据。

    适用问题：
    - 公司组织架构是什么样子的？
    - XX 部门/中心下面有哪些子部门？
    - 公司有哪些事业部/部门/小组？
    - 某个部门的上级部门是谁？
    - 各部门的层级关系？

    参数说明：
    - metrics: org_unit_count / direct_children_count
    - filters: org_name / org_type / parent_id / level
      注意：查某个部门的下级时，先将 list_mode 置为 True 找出 org_id，
      再用 parent_id 过滤查其子部门
    - group_by: org_type / level / parent_id
    - list_mode: True = 列出部门清单（含 id、name、path、parent_id），
      False = 仅统计数字

    示例：
    - "组织架构" → list_mode=True, metrics=["org_unit_count"]
    - "研发中心下面有什么" → list_mode=True, filters={"org_name":"研发中心"}
      拿到 id 后 → filters={"parent_id": 那个id}
    - "各个事业部的部门数" → metrics=["org_unit_count"], group_by=["org_type"]
    """
    try:
        rows = _repo.query_metrics(query)
    except ValueError as exc:
        return str(exc)

    if not rows:
        return "没有查询到符合条件的组织数据。"

    if query.list_mode:
        return _build_tree_output(rows)

    lines = ["组织架构查询结果："]
    for row in rows:
        dimension_text = _format_dimensions(row.dimensions)
        metric_text = _format_metrics(row.metrics)
        if dimension_text:
            lines.append(f"- {dimension_text}: {metric_text}")
        else:
            lines.append(f"- {metric_text}")

    return "\n".join(lines)


def _build_tree_output(rows: list) -> str:
    """把平铺的组织节点列表转成树形缩进字符串。

    利用 path 字段（如 /1/2/301/）确定层级和父子关系，
    前端 <pre> 标签或 white-space: pre-wrap 会保留缩进。
    """
    # 1. 按 path 排序，保证兄弟节点按 sort_order 排列
    sorted_rows = sorted(rows, key=lambda r: (
        r.dimensions.get("path", ""),
    ))

    # 2. 构建 id → node 映射 + 按 parent_id 分组子节点
    nodes: dict[int, dict] = {}
    root_ids: list[int] = []

    for row in sorted_rows:
        dims = row.dimensions
        node_id = int(dims["org_id"])
        parent_id = dims.get("parent_id")
        nodes[node_id] = {
            "id": node_id,
            "name": str(dims.get("org_name", "")),
            "code": str(dims.get("org_code", "")),
            "level": int(dims.get("level", 0)),
            "parent_id": int(parent_id) if parent_id is not None else None,
            "children": [],
        }
        if parent_id is None:
            root_ids.append(node_id)

    for node in nodes.values():
        pid = node["parent_id"]
        if pid is not None and pid in nodes:
            nodes[pid]["children"].append(node)

    # 3. 递归渲染树形
    lines: list[str] = []
    _render_tree(nodes, root_ids, "", lines)
    return "组织架构：\n" + "\n".join(lines)


def _render_tree(
    nodes: dict[int, dict],
    sibling_ids: list[int],
    prefix: str,
    lines: list[str],
) -> None:
    for i, node_id in enumerate(sibling_ids):
        node = nodes[node_id]
        is_last = i == len(sibling_ids) - 1
        connector = "└── " if is_last else "├── "
        line = f"{prefix}{connector}{node['name']}（{node['code']}）"
        lines.append(line)

        if node["children"]:
            child_prefix = prefix + ("    " if is_last else "│   ")
            _render_tree(nodes, [c["id"] for c in node["children"]], child_prefix, lines)


def _format_dimensions(dimensions: dict[str, str | int | None]) -> str:
    if not dimensions:
        return ""
    return "，".join(
        f"{key}={value if value is not None else '未设置'}"
        for key, value in dimensions.items()
    )


def _format_metrics(metrics: dict[str, int | float | None]) -> str:
    return "，".join(
        f"{key}={value if value is not None else 0}"
        for key, value in metrics.items()
    )
