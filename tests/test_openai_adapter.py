from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

from endurance_agent_lab.analytics import derive_metrics
from endurance_agent_lab.providers import OpenAIProvider, RuleBasedProvider


def test_openai_adapter_parses_versioned_audit_contract(
    benchmark, skill, monkeypatch
) -> None:
    case = benchmark.by_id("END-016")
    derived = derive_metrics(case.context)
    expected = RuleBasedProvider().audit(case, skill, derived).audit

    class FakeResponses:
        def parse(self, **kwargs):
            assert kwargs["model"] == "gpt-test"
            assert kwargs["text_format"].__name__ == "AuditOutput"
            return SimpleNamespace(
                id="resp_test",
                output_parsed=expected,
                usage=SimpleNamespace(input_tokens=100, output_tokens=50, total_tokens=150),
                model_dump=lambda mode="json": {"id": "resp_test"},
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

    fake_openai = ModuleType("openai")
    fake_openai.OpenAI = FakeClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    result = OpenAIProvider(model="gpt-test").audit(case, skill, derived)

    assert result.request_id == "resp_test"
    assert result.audit.case_id == "END-016"
    assert result.usage.total_tokens == 150
