import pytest
from fastapi.testclient import TestClient

def test_root_and_health(client: TestClient):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "running"

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

def test_ingest_note_and_query_flow(client: TestClient):
    # 1. Ingest Note
    payload = {
        "type": "note",
        "title": "Quantum Computing Fundamentals",
        "content": "Quantum computers use qubits that can exist in superposition states of 0 and 1 simultaneously.",
        "tags": ["quantum", "physics"]
    }
    ingest_res = client.post("/api/v1/items/ingest", json=payload)
    assert ingest_res.status_code == 201
    item_data = ingest_res.json()
    assert item_data["title"] == "Quantum Computing Fundamentals"
    assert item_data["type"] == "note"
    assert item_data["chunk_count"] >= 1
    item_id = item_data["id"]

    # 2. List Items
    list_res = client.get("/api/v1/items")
    assert list_res.status_code == 200
    items_list = list_res.json()["items"]
    assert any(i["id"] == item_id for i in items_list)

    # 3. Get Item Details with Chunks
    detail_res = client.get(f"/api/v1/items/{item_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == item_id
    assert len(detail_data["chunks"]) >= 1

    # 4. Query RAG
    query_payload = {
        "question": "What is a qubit in quantum computing?",
        "top_k": 3
    }
    query_res = client.post("/api/v1/query", json=query_payload)
    assert query_res.status_code == 200
    q_data = query_res.json()
    assert len(q_data["answer"]) > 0
    assert len(q_data["citations"]) >= 1
    assert q_data["citations"][0]["item_id"] == item_id

    # 5. Query SSE Stream
    stream_res = client.post("/api/v1/query/stream", json=query_payload)
    assert stream_res.status_code == 200
    assert "event: sources" in stream_res.text
    assert "event: token" in stream_res.text
    assert "event: done" in stream_res.text

    # 6. Delete Item
    del_res = client.delete(f"/api/v1/items/{item_id}")
    assert del_res.status_code == 200

    # Verify 404 on deleted item
    get_del = client.get(f"/api/v1/items/{item_id}")
    assert get_del.status_code == 404

def test_validation_errors(client: TestClient):
    # Missing content for note
    bad_note = {"type": "note", "content": ""}
    res = client.post("/api/v1/items/ingest", json=bad_note)
    assert res.status_code == 422

    # Query with too short question
    bad_query = {"question": "a"}
    res2 = client.post("/api/v1/query", json=bad_query)
    assert res2.status_code == 422
