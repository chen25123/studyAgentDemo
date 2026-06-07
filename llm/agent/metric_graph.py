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
                "final_answer": "你好！我是 DevFlow Agent。有什么研发数据问题可以帮你？"
            }

        errors = state.get("validation_errors", [])
        if errors:
            return {"final_answer": f"查询未能执行：{'；'.join(errors)}"}

        results = state.get("metric_results") or []
        if not results:
            return {
                "final_answer": (
                    "未能查到相关指标数据。试试：\n"
                    "- 换个时间范围\n"
                    "- 确认指标名称是否正确\n"
                )
            }

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

        return {"final_answer": "\n".join(lines)}

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
    # Entry
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
