"""Agent Eval —— 指标查询意图分类 + 指标匹配正确率。

运行方式：pytest tests/test_agent_eval.py -v -m llm
"""

import json
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage

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


class TestIntentClassification:
    """意图分类 —— 20 题。"""

    @pytest.mark.asyncio
    async def test_metric_intent(self, graph, questions):
        correct = 0
        total = 0
        errors = []
        for q in questions:
            state = {
                "messages": [HumanMessage(content=q["question"])],
                "session_id": "eval",
            }
            result = await graph._classify_intent(state)
            actual = result["intent"]
            expected = q["expected_intent"]
            total += 1
            if actual == expected:
                correct += 1
            else:
                errors.append(f"  Q{q['id']}: \"{q['question']}\" → {actual} (expected {expected})")

        accuracy = correct / total * 100 if total > 0 else 0
        print(f"\n意图分类准确率: {correct}/{total} = {accuracy:.1f}%")
        if errors:
            print("错误:")
            for e in errors:
                print(e)

        assert accuracy >= 75, f"意图分类准确率 {accuracy:.1f}% < 75%"


class TestMetricMatching:
    """指标匹配 —— 有明确 expects 的题。"""

    @pytest.mark.asyncio
    async def test_metric_matching(self, graph, questions):
        correct = 0
        total = 0
        errors = []
        for q in questions:
            if not q.get("expected_metric_codes"):
                continue
            state = {
                "messages": [HumanMessage(content=q["question"])],
                "session_id": "eval",
                "metric_codes": [],
            }
            result = await graph._match_metric(state)
            actual = set(result.get("metric_codes", []))
            expected = set(q["expected_metric_codes"])
            total += 1
            if actual & expected:
                correct += 1
            else:
                errors.append(
                    f"  Q{q['id']}: \"{q['question']}\" → {actual} (expected {expected})"
                )

        accuracy = correct / total * 100 if total > 0 else 0
        print(f"\n指标匹配准确率: {correct}/{total} = {accuracy:.1f}%")
        if errors:
            print("错误:")
            for e in errors:
                print(e)

        assert accuracy >= 60, f"指标匹配准确率 {accuracy:.1f}% < 60%"
