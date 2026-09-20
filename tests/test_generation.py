"""Offline checks for Tri's generation and integration work."""

from copy import deepcopy

import pytest

from src import task10_generation as generation
from src import task9_retrieval_pipeline as pipeline
from src.contracts import validate_generation_result


def chunks():
    return [{"id": f"chunk-{i}", "content": f"Evidence {i}", "score": 1 - i / 10,
             "metadata": {"source": "policy.md", "title": "Policy", "doc_type": "legal", "url": None, "chunk_index": i},
             "retrieval_method": "hybrid"} for i in range(5)]


def test_citations_keep_original_source_numbers_after_reorder(monkeypatch):
    sources = chunks()
    before = deepcopy(sources)
    monkeypatch.setattr(generation, "retrieve", lambda *a, **kw: sources)

    def fake_llm(system, message):
        assert message.index("Document 5") < message.index("Document 2")
        assert "[Document 2 | ID: chunk-1" in message
        return "Evidence 1 [2]. Evidence 4 [5]."

    monkeypatch.setattr(generation, "call_llm", fake_llm)
    output = generation.generate_with_citation("question")
    validate_generation_result(output)
    assert output["sources"] == before == sources
    assert output["answer"] == "Evidence 1 [2]. Evidence 4 [5]."


@pytest.mark.parametrize("answer", ["", "No citations", "Invented [6]", "Invalid [0]", generation.SAFE_REFUSAL])
def test_invalid_answers_are_refused(monkeypatch, answer):
    monkeypatch.setattr(generation, "retrieve", lambda *a, **kw: chunks())
    monkeypatch.setattr(generation, "call_llm", lambda *a: answer)
    output = generation.generate_with_citation("question")
    validate_generation_result(output)
    assert output["retrieval_source"] == "none"
    assert output["sources"] == []


@pytest.mark.parametrize("stage", ["retrieve", "call_llm"])
def test_failures_return_safe_refusal(monkeypatch, stage):
    monkeypatch.setattr(generation, "retrieve", lambda *a, **kw: chunks())

    def fail(*a, **kw):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(generation, stage, fail)
    assert generation.generate_with_citation("question")["answer"] == generation.SAFE_REFUSAL


def test_no_evidence_skips_llm(monkeypatch):
    monkeypatch.setattr(generation, "retrieve", lambda *a, **kw: [])
    monkeypatch.setattr(generation, "call_llm", lambda *a: pytest.fail("must not call LLM"))
    assert generation.generate_with_citation("question")["sources"] == []


def test_dense_only_skips_other_retrievers(monkeypatch):
    sources = [{**item, "retrieval_method": "dense"} for item in chunks()]
    monkeypatch.setattr(pipeline, "semantic_search", lambda *a, **kw: sources)
    for name in ("lexical_search", "rerank_rrf", "pageindex_search"):
        monkeypatch.setattr(pipeline, name, lambda *a, **kw: pytest.fail("dense-only baseline"))
    assert pipeline.retrieve("question", top_k=2, use_reranking=False) == sources[:2]


def test_empty_fallback_keeps_hybrid(monkeypatch):
    sources = chunks()
    monkeypatch.setattr(pipeline, "semantic_search", lambda *a, **kw: [])
    monkeypatch.setattr(pipeline, "lexical_search", lambda *a, **kw: [])
    monkeypatch.setattr(pipeline, "rerank_rrf", lambda lists, top_k: sources[:top_k])
    monkeypatch.setattr(pipeline, "pageindex_search", lambda *a, **kw: [])
    assert pipeline.retrieve("question", top_k=2) == sources[:2]


def test_chat_preserves_sources_on_rerun(monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(generation, "generate_with_citation", lambda query, top_k: {
        "answer": "Evidence [1]", "sources": chunks()[:1], "retrieval_source": "hybrid",
    })
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py")).run()
    app.chat_input[0].set_value("question").run()
    assert not app.exception
    assert len(app.session_state["messages"]) == 2
    assert app.session_state["messages"][1]["sources"][0]["id"] == "chunk-0"
    app.run()
    assert len(app.expander) == 1
    assert "[1]" in app.expander[0].label
    app.button[0].click().run()
    assert app.session_state["messages"] == []


def test_pageindex_generation_marks_source(monkeypatch):
    sources = [{**chunks()[0], "retrieval_method": "pageindex"}]
    monkeypatch.setattr(generation, "retrieve", lambda *a, **kw: sources)
    monkeypatch.setattr(generation, "call_llm", lambda *a: "Evidence [1]")
    output = generation.generate_with_citation("question")
    validate_generation_result(output)
    assert output["retrieval_source"] == "pageindex"


@pytest.mark.parametrize("provider", ["openai", "gemini", "anthropic"])
def test_provider_dispatch_offline(monkeypatch, provider):
    import sys
    from types import ModuleType, SimpleNamespace

    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text="answer", text="answer", content=[SimpleNamespace(type="text", text="answer")])

    class Client:
        def __init__(self, **kwargs):
            self.responses = SimpleNamespace(create=create)
            self.messages = SimpleNamespace(create=create)
            self.models = SimpleNamespace(generate_content=create)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    if provider == "gemini":
        google = ModuleType("google")
        genai = ModuleType("google.genai")
        genai.Client = Client
        genai.types = SimpleNamespace(HttpOptions=lambda **kw: kw, GenerateContentConfig=lambda **kw: kw)
        google.genai = genai
        monkeypatch.setitem(sys.modules, "google", google)
        monkeypatch.setitem(sys.modules, "google.genai", genai)
    else:
        module = ModuleType(provider)
        setattr(module, "OpenAI" if provider == "openai" else "Anthropic", Client)
        monkeypatch.setitem(sys.modules, provider, module)
    monkeypatch.setattr(generation, "LLM_PROVIDER", provider)
    monkeypatch.setattr(generation, "LLM_MODEL", "configured-model")
    monkeypatch.setenv({"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}[provider], "test-key")
    assert generation.call_llm("system", "question") == "answer"
    assert calls[0]["model"] == "configured-model"
