"""Agent Eval —— 指标查询意图分类 + 指标匹配正确率。

运行方式：pytest tests/test_agent_eval.py -v -m llm

注意：此测试需要 LLM API 可用，非纯单元测试。标记为 @pytest.mark.llm。
"""

import json
from pathlib import Path

import pytest

from llm.agent.metric_graph import MetricQueryGraph

pytestmark = pytest.mark.llm


@pytest.fixture(scope="module")
def graph():
    return MetricQueryGraph()


@pytest.fixture(scope="module")
def questions():
    path = Path(__file__).parent / "evals" / "metric_questions.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["questions"]


@pytest.mark.parametrize("q", range(20), ids=lambda i: f"Q{i+1}")
@pytest.mark.asyncio
async def test_intent_classification(graph, questions, q):
    item = questions[q]
    state = {
        "messages": [{"content": item["question"], "type": "human"}],
        "session_id": "eval",
    }
    result = await graph._classify_intent(state)
    actual = result["intent"]
    expected = item["expected_intent"]
    assert actual == expected, f"意图错误: 期望={expected}, 实际={actual}"


_MATCH_QUESTIONS = [
    (1, "最近一个月创建了多少 Bug？", ["bug_count"]),
    (2, "本月 Bug 关闭率是多少？", ["bug_close_rate"]),
    (3, "研发一部上个月 Bug 未关闭率", ["bug_open_rate"]),
    (4, "Bug 重开率多高？", ["bug_reopen_rate"]),
    (5, "按模块统计本月 Bug 关闭率", ["bug_close_rate"]),
    (6, "需求延期率是多少？", ["requirement_delay_rate"]),
]


@pytest.mark.parametrize(
    "qid,question,expected_codes", _MATCH_QUESTIONS, ids=lambda x: f"Q{x[0]}"
)
@pytest.mark.asyncio
async def test_metric_matching(graph, qid, question, expected_codes):
    """只测有明确预期指标的问题。"""
    item = {"question": question, "expected_metric_codes": expected_codes}

    state = {
        "messages": [{"content": item["question"], "type": "human"}],
        "session_id": "eval",
        "metric_codes": [],
    }
    result = await graph._match_metric(state)
    actual = set(result.get("metric_codes", []))
    expected = set(item.get("expected_metric_codes", []))

    common = actual & expected
    assert len(common) > 0, (
        f"指标匹配失败: 期望含 {expected}, 实际={actual}"
    )
