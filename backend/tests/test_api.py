import json

import httpx
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.rag import rag_pipeline

IN_DOMAIN = "How is high blood pressure treated?"
OFF_TOPIC = "What is the capital of France?"


class ExplodingLLM(FakeListChatModel):
    """Fails like an Ollama call that times out."""

    def _call(self, *args, **kwargs):
        raise httpx.ReadTimeout("timed out")

    def _stream(self, *args, **kwargs):
        raise httpx.ReadTimeout("timed out")


def ask(client, auth, message):
    resp = client.post("/api/chat", json={"message": message}, headers=auth)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_health_reports_degraded_when_ollama_is_down(client):
    body = client.get("/api/health").json()
    assert body["knowledge_base"]["ready"] is True
    assert body["knowledge_base"]["qa_pairs"] == 52
    assert body["llm"]["ready"] is False
    assert body["status"] == "degraded"
    assert "not reachable" in body["llm"]["detail"]


def test_chat_requires_login(client):
    assert client.post("/api/chat", json={"message": IN_DOMAIN}).status_code == 401


def test_answer_cites_sources(client, auth, fake_llm):
    fake_llm("Treatment includes lifestyle changes [1] and medicines [2].")
    body = ask(client, auth, IN_DOMAIN)
    assert body["status"] == "answered"
    assert body["disclaimer"]
    ids = [s["id"] for s in body["sources"]]
    assert ids == list(range(1, len(ids) + 1))
    assert body["sources"][0]["question"] == "What is hypertension?"
    cited = {s["id"] for s in body["sources"] if s["cited"]}
    assert cited == {1, 2} & set(ids)


def test_off_topic_question_is_declined_without_calling_the_llm(client, auth, fake_llm):
    fake_llm(model=ExplodingLLM(responses=["unused"]))  # would fail if called
    body = ask(client, auth, OFF_TOPIC)
    assert body["status"] == "declined"
    assert body["sources"] == []
    assert "don't have enough information" in body["answer"]


def test_model_refusal_counts_as_decline(client, auth, fake_llm):
    fake_llm("I don't have enough information in my sources to answer that.")
    body = ask(client, auth, IN_DOMAIN)
    assert body["status"] == "declined"
    assert body["sources"] == []


def test_ollama_down_gives_clearly_labelled_fallback(client, auth, fake_llm):
    fake_llm(healthy=False)
    body = ask(client, auth, IN_DOMAIN)
    assert body["status"] == "fallback"
    assert body["answer"].startswith("> ⚠️ The answer generator is unavailable")
    assert body["sources"] and all(s["cited"] for s in body["sources"])


def test_llm_timeout_falls_back_instead_of_500(client, auth, fake_llm):
    fake_llm(model=ExplodingLLM(responses=["unused"]))
    body = ask(client, auth, IN_DOMAIN)
    assert body["status"] == "fallback"
    assert "ReadTimeout" in body["answer"]


def test_missing_knowledge_base_returns_503(client, auth):
    retriever, error = rag_pipeline.retriever, rag_pipeline.error
    rag_pipeline.retriever, rag_pipeline.error = None, "Dataset not found at dataset/x.json"
    try:
        resp = client.post("/api/chat", json={"message": IN_DOMAIN}, headers=auth)
        stream = client.post("/api/chat/stream", json={"message": IN_DOMAIN}, headers=auth)
    finally:
        rag_pipeline.retriever, rag_pipeline.error = retriever, error
    assert resp.status_code == 503
    assert "Dataset not found" in resp.json()["detail"]
    assert stream.status_code == 503
    assert client.get("/api/history", headers=auth).json() == []  # nothing was saved


def test_emergency_short_circuits(client, auth, fake_llm):
    fake_llm(model=ExplodingLLM(responses=["unused"]))
    body = ask(client, auth, "I have chest pain right now")
    assert body["is_emergency"] is True
    assert body["status"] == "emergency"
    assert "EMERGENCY" in body["answer"]


def test_stream_sends_meta_tokens_then_done(client, auth, fake_llm):
    fake_llm("Lifestyle changes help [1].")
    resp = client.post("/api/chat/stream", json={"message": IN_DOMAIN}, headers=auth)
    assert resp.status_code == 200
    events = [json.loads(line[6:]) for line in resp.text.split("\n\n") if line.startswith("data: ")]
    assert events[0]["type"] == "meta" and events[0]["status"] == "generating"
    assert events[-1]["type"] == "done" and events[-1]["status"] == "answered"
    text = "".join(e["content"] for e in events if e["type"] == "token")
    assert text == "Lifestyle changes help [1]."
    assert [s["cited"] for s in events[-1]["sources"]][0] is True


def test_history_is_private_to_each_user(client, auth, fake_llm):
    fake_llm("Lifestyle changes help [1].")
    chat_id = ask(client, auth, IN_DOMAIN)["chat_id"]

    history = client.get("/api/history", headers=auth).json()
    assert [c["id"] for c in history] == [chat_id]
    detail = client.get(f"/api/history/{chat_id}", headers=auth).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]

    other = client.post(
        "/api/auth/register",
        json={"name": "Other", "email": "other@example.com", "password": "Passw0rdX"},
    ).json()["access_token"]
    other_auth = {"Authorization": f"Bearer {other}"}
    assert client.get(f"/api/history/{chat_id}", headers=other_auth).status_code == 404
    assert client.delete(f"/api/history/{chat_id}", headers=other_auth).status_code == 404

    renamed = client.put(f"/api/history/{chat_id}", json={"title": "BP"}, headers=auth)
    assert renamed.json()["title"] == "BP"
    assert client.delete(f"/api/history/{chat_id}", headers=auth).status_code == 200
    assert client.get("/api/history", headers=auth).json() == []
