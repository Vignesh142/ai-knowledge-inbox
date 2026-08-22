import pytest
from backend.app.services.chunker_service import ChunkerService
from backend.app.models.domain import ItemRecord, ItemType

def test_chunker_small_text():
    chunker = ChunkerService(chunk_size=500, chunk_overlap=50)
    text = "Short note about machine learning."
    chunks = chunker.chunk_text(text, "item-123", {"title": "ML Note"})

    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].item_id == "item-123"
    assert chunks[0].chunk_index == 0
    assert chunks[0].char_count == len(text)

def test_chunker_large_text_splits():
    chunker = ChunkerService(chunk_size=100, chunk_overlap=20)
    paragraphs = [
        "Paragraph one is discussing retrieval augmented generation techniques in modern artificial intelligence systems.",
        "Paragraph two is discussing vector databases, cosine similarity, embeddings, and nearest neighbor search indexing.",
        "Paragraph three covers prompt engineering, few-shot examples, chain of thought reasoning, and output validation.",
    ]
    full_text = "\n\n".join(paragraphs)
    chunks = chunker.chunk_text(full_text, "item-large", {"title": "Large Doc"})

    assert len(chunks) >= 3
    for idx, c in enumerate(chunks):
        assert c.chunk_index == idx
        assert c.item_id == "item-large"
        assert len(c.text) > 0

def test_chunker_item_record():
    chunker = ChunkerService(chunk_size=300, chunk_overlap=50)
    item = ItemRecord(
        id="item-test-1",
        type=ItemType.NOTE,
        title="Test Title",
        content="First sentence here. Second sentence with details. Third sentence providing context.",
        tags=["ai", "test"]
    )
    chunks = chunker.chunk_item(item)
    assert len(chunks) >= 1
    assert chunks[0].metadata["title"] == "Test Title"
    assert chunks[0].metadata["type"] == "note"
