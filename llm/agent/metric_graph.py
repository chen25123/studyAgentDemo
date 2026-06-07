"""LangGraph 指标查询工作流。

将指标查询链路从 create_agent 自由工具调用升级为显式状态图编排：
classify_intent → resolve_time → match_metric → build_query_plan
→ validate_plan → execute_metric → compose_answer → trace_result
"""

import json
from datetime import date
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

from llm.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from llm.repositories.llm_trace_repository import LlmTraceRepository
from llm.schemas.metric_query import MetricQuery, TimeRange
from llm.services.metric_engine import MetricEngine, MetricEngineError

# ================================================================
# State
# ================================================================

class MetricAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    intent: str
    metric_codes: list[str]
    time_range: dict[str, str] | None
    filters: dict[str, str]
    group_by: list[str]
    query_plan: dict[str, Any] | None
    validation_errors: list[str]
    metric_results: list[dict[str, Any]] | None
    compiled_sql: str
    final_answer: str


# ================================================================
# Graph Builder
# ================================================================

class MetricQueryGraph:
    """LangGraph 指标查询工作流。"""

    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL,
            temperature=0.1,
        )
        self.engine = MetricEngine()
        self.trace = LlmTraceRepository()
        self.graph = self._build()

    def _build(self):
        builder = StateGraph(MetricAgentState)

        builder.add_node("classify_intent", self._classify_intent)
        builder.add_node("resolve_time", self._resolve_time)
        builder.add_node("match_metric", self._match_metric)
        builder.add_node("build_query_plan", self._build_query_plan)
        builder.add_node("validate_plan", self._validate_plan)
        builder.add_node("execute_metric", self._execute_metric)
        builder.add_node("compose_answer", self._compose_answer)

        builder.set_entry_point("classify_intent")

        builder.add_conditional_edges(
            "classify_intent",
            self._route_after_intent,
            {
                "resolve_time": "resolve_time",
                "compose_answer": "compose_answer",
            },
        )
        builder.add_edge("resolve_time", "match_metric")
        builder.add_edge("match_metric", "build_query_plan")
        builder.add_edge("build_query_plan", "validate_plan")

        builder.add_conditional_edges(
            "validate_plan",
            self._route_after_validate,
            {
                "execute_metric": "execute_metric",
                "compose_answer": "compose_answer",
            },
        )
        builder.add_edge("execute_metric", "compose_answer")
        builder.set_finish_point("compose_answer")

        return builder.compile()

    # ============================================================
    # Nodes
    # ============================================================

    async def _classify_intent(self, state: MetricAgentState) -> dict:
        last_msg = state["messages"][-1].content if state["messages"] else ""
        prompt = (
            "判断用户意图。只回复一个词：metric_query 或 general_chat。\n"
            "metric_query：用户想查指标（关闭率、Bug数、延期率、统计数等）。\n"
            "general_chat：闲聊、问候、或者非数据查询的问题。\n"
            f"\n用户问题：{last_msg}"
        )
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        intent = str(resp.content).strip().lower()
        if "metric" not in intent:
            intent = "general_chat"
        else:
            intent = "metric_query"
        return {"intent": intent}

    async def _resolve_time(self, state: MetricAgentState) -> dict:
        last_msg = state["messages"][-1].content if state["messages"] else ""
        today = date.today().isoformat()
        prompt = (
            f"今天是 {today}。从用户问题中提取时间范围。\n"
            "返回 JSON：{\"start_date\":\"YYYY-MM-DD\",\"end_date\":\"YYYY-MM-DD\"}。\n"
            "如果没有时间信息，返回 null。\n"
            f"\n用户问题：{last_msg}"
        )
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        raw = str(resp.content).strip()
        time_range = None
        try:
            parsed = json.loads(raw)
            if parsed and "start_date" in parsed:
                time_range = parsed
        except json.JSONDecodeError:
            pass
        return {"time_range": time_range}

    async def _match_metric(self, state: MetricAgentState) -> dict:
        from llm.repositories.metric_layer_repository import MetricLayerRepository

        repo = MetricLayerRepository()
        available = repo.list_active_metrics()
        metric_list = "\n".join(
            f"- {m['metric_code']}: {m['metric_name']} — {m['description']}"
            for m in available
        )

        last_msg = state["messages"][-1].content if state["messages"] else ""
        prompt = (
            "从以下可用指标中匹配用户问题对应的指标编码。\n"
            "返回 JSON 数组，如 [\"bug_close_rate\"]。\n"
            "如果问题中提到的概念没有对应指标，返回空数组 []。\n"
            "\n可用指标：\n"
            f"{metric_list}\n"
            f"\n用户问题：{last_msg}"
        )
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        raw = str(resp.content).strip()
        codes: list[str] = []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                codes = [c for c in parsed if c in {m["metric_code"] for m in available}]
        except json.JSONDecodeError:
            pass
        return {"metric_codes": codes}

    async def _build_query_plan(self, state: MetricAgentState) -> dict:
        if not state.get("metric_codes"):
            return {
                "query_plan": None,
                "validation_errors": ["未找到匹配的指标"],
            }

        last_msg = state["messages"][-1].content if state["messages"] else ""
        prompt = (
            "从用户问题中提取过滤条件和分组维度。返回 JSON：\n"
            "{\"filters\": {}, \"group_by\": []}\n"
            "可用过滤维度：status/severity/priority/module_name/product_line/"
            "assignee_org_name/assignee_org_id\n"
            "可用分组维度：status/severity/priority/module_name/product_line/"
            "assignee_org_id/assignee_org_name\n"
            f"\n用户问题：{last_msg}"
        )
        resp = await self.llm.ainvoke([HumanMessage(content=prompt)])
        raw = str(resp.content).strip()
        filters, group_by = {}, []
        try:
            parsed = json.loads(raw)
            filters = parsed.get("filters", {})
            group_by = parsed.get("group_by", [])
        except json.JSONDecodeError:
            pass

        tr = state.get("time_range")
        plan = {
            "metric_codes": state.get("metric_codes", []),
            "time_range": tr,
            "filters": filters,
            "group_by": group_by,
        }
        return {"query_plan": plan, "filters": filters, "group_by": group_by}

    async def _validate_plan(self, state: MetricAgentState) -> dict:
        plan = state.get("query_plan")
        if not plan or not plan.get("metric_codes"):
            return {"validation_errors": state.get("validation_errors", [])}

        tr = None
        if plan.get("time_range"):
            try:
                tr = TimeRange(
                    start_date=date.fromisoformat(plan["time_range"]["start_date"]),
                    end_date=date.fromisoformat(plan["time_range"]["end_date"]),
                )
            except (ValueError, KeyError):
                pass

        metric_query = MetricQuery(
            metric_codes=plan["metric_codes"],
            time_range=tr,
            filters=plan.get("filters", {}),
            group_by=plan.get("group_by", []),
        )

        try:
            self.engine._validate_and_load(metric_query)
            return {"validation_errors": []}
        except MetricEngineError as exc:
            return {"validation_errors": [str(exc)]}

    async def _execute_metric(self, state: MetricAgentState) -> dict:
        plan = state.get("query_plan")
        if not plan or state.get("validation_errors"):
            return {}

        tr = None
        if plan.get("time_range"):
            tr = TimeRange(
                start_date=date.fromisoformat(plan["time_range"]["start_date"]),
                end_date=date.fromisoformat(plan["time_range"]["end_date"]),
            )

        query = MetricQuery(
            metric_codes=plan["metric_codes"],
            time_range=tr,
            filters=plan.get("filters", {}),
            group_by=plan.get("group_by", []),
        )

        trace_id = uuid4().hex
        try:
            results_raw, sql = self.engine.execute(
                query, trace_id=trace_id, session_id=state["session_id"]
            )
            return {
                "metric_results": [r.model_dump() for r in results_raw],
                "compiled_sql": sql,
            }
        except Exception:
            return {"metric_results": [], "compiled_sql": ""}

    async def _compose_answer(self, state: MetricAgentState) -> dict:
        intent = state.get("intent", "general_chat")

        if intent == "general_chat":
            return {
                "final_answer": "你好！我是 DevFlow Agent。有什么研发数据问题可以帮你？",
                "chart_b64": "",
            }

        errors = state.get("validation_errors", [])
        if errors:
            return {
                "final_answer": f"查询未能执行：{'；'.join(errors)}",
                "chart_b64": "",
            }

        results = state.get("metric_results") or []
        if not results:
            return {
                "final_answer": (
                    "未能查到相关指标数据。试试：\n"
                    "- 换个时间范围\n"
                    "- 确认指标名称是否正确\n"
                ),
                "chart_b64": "",
            }

        # 生成图表
        chart_b64 = self._build_chart(results)

        lines = ["指标查询结果："]
        for r in results:
            dims = r.get("dimensions", {})
            dim_text = "，".join(
                f"{k}={v}" for k, v in dims.items() if v is not None
            ) if dims else ""
            value = r.get("value")
            unit = r.get("unit", "")
            name = r.get("metric_name", "")
            if dim_text:
                lines.append(f"- {dim_text}: **{name}** = {value}{unit}")
            else:
                lines.append(f"- **{name}** = {value}{unit}")

        lines.append("")
        lines.append("口径说明：")
        seen = set()
        for r in results:
            code = r.get("metric_code", "")
            desc = r.get("description", "")
            if code not in seen:
                seen.add(code)
                lines.append(f"- {code}：{desc}")

        return {"final_answer": "\n".join(lines), "chart_b64": chart_b64}

    # ============================================================
    # Chart Builder
    # ============================================================

    @staticmethod
    def _build_chart(results: list[dict]) -> str:
        from llm.services.chart_service import ChartService

        svc = ChartService()
        try:
            # 有 group_by → 柱状图
            dims = results[0].get("dimensions", {}) if results else {}
            if dims and len(results) > 1:
                dim_key = next(iter(dims))
                labels = [r["dimensions"].get(dim_key, "") for r in results]
                labels = [str(v) if v else "未知" for v in labels]
                values = [r.get("value") or 0 for r in results]
                name = results[0].get("metric_name", "指标")
                unit = results[0].get("unit", "")
                return svc.render_bar_chart(
                    labels=labels,
                    values=values,
                    title=f"{name} 按{dim_key}分布",
                    ylabel=f"值（{unit}）" if unit else "",
                )

            # 无 group_by → 指标卡
            r = results[0]
            sub = {k: v for k, v in r.get("measures", {}).items() if v is not None}
            return svc.render_metric_card(
                metric_name=r.get("metric_name", "指标"),
                value=r.get("value") or 0,
                unit=r.get("unit", "%"),
                sub_metrics=sub if sub else None,
            )
        except Exception:
            return ""

    # ============================================================
    # Routing
    # ============================================================

    def _route_after_intent(self, state: MetricAgentState) -> str:
        if state.get("intent") == "metric_query":
            return "resolve_time"
        return "compose_answer"

    def _route_after_validate(self, state: MetricAgentState) -> str:
        if state.get("validation_errors"):
            return "compose_answer"
        return "execute_metric"

    # ============================================================
    # Streaming Entry
    # ============================================================

    async def astream(self, session_id: str, message: str):
        """流式执行，每完成一个节点 yield SSE 事件。"""

        initial: MetricAgentState = {
            "messages": [HumanMessage(content=message)],
            "session_id": session_id,
            "intent": "",
            "metric_codes": [],
            "time_range": None,
            "filters": {},
            "group_by": [],
            "query_plan": None,
            "validation_errors": [],
            "metric_results": None,
            "compiled_sql": "",
            "final_answer": "",
        }

        stages = [
            ("classify_intent", "识别意图"),
            ("resolve_time", "解析时间范围"),
            ("match_metric", "匹配指标"),
            ("build_query_plan", "生成查询计划"),
            ("validate_plan", "校验查询计划"),
            ("execute_metric", "执行查询"),
            ("compose_answer", "生成回答"),
        ]

        current_state = initial
        for node_name, label in stages:
            yield self._sse("node_start", {"node": node_name, "label": label})

            if node_name == "classify_intent":
                current_state.update(await self._classify_intent(current_state))
                if current_state["intent"] == "general_chat":
                    current_state.update(await self._compose_answer(current_state))
                    yield self._sse("message_delta", {"content": current_state["final_answer"]})
                    yield self._sse("final", {})
                    return

            elif node_name == "resolve_time":
                current_state.update(await self._resolve_time(current_state))

            elif node_name == "match_metric":
                current_state.update(await self._match_metric(current_state))

            elif node_name == "build_query_plan":
                current_state.update(await self._build_query_plan(current_state))

            elif node_name == "validate_plan":
                current_state.update(await self._validate_plan(current_state))
                if current_state.get("validation_errors"):
                    current_state.update(await self._compose_answer(current_state))
                    yield self._sse("message_delta", {"content": current_state["final_answer"]})
                    yield self._sse("final", {})
                    return

            elif node_name == "execute_metric":
                current_state.update(await self._execute_metric(current_state))
                if current_state.get("metric_results"):
                    yield self._sse(
                        "tool_result",
                        {"summary": f"查到 {len(current_state['metric_results'])} 条结果"},
                    )

            elif node_name == "compose_answer":
                current_state.update(await self._compose_answer(current_state))
                yield self._sse("message_delta", {"content": current_state["final_answer"]})
                chart = current_state.get("chart_b64", "")
                if chart:
                    yield self._sse("chart", {"image": chart})
                yield self._sse("final", {})

    # ============================================================
    # Utils
    # ============================================================

    @staticmethod
    def _sse(event_type: str, data: dict) -> str:
        import json as _json
        payload = _json.dumps({"type": event_type, **data}, ensure_ascii=False)
        return f"data: {payload}\n\n"

    # ============================================================
    # Entry (Non-streaming)
    # ============================================================

    async def arun(self, session_id: str, message: str) -> str:
        initial: MetricAgentState = {
            "messages": [HumanMessage(content=message)],
            "session_id": session_id,
            "intent": "",
            "metric_codes": [],
            "time_range": None,
            "filters": {},
            "group_by": [],
            "query_plan": None,
            "validation_errors": [],
            "metric_results": None,
            "compiled_sql": "",
            "final_answer": "",
        }
        result = await self.graph.ainvoke(initial)
        return result.get("final_answer", "")
