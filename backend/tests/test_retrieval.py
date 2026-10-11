from langchain_core.documents import Document

from app.rag.documents import chunk_qa_pairs
from app.rag.prompts import cited_numbers, is_refusal
from app.rag.retrievers import TfidfRetriever, tokenize


def _pair(answer, focus="Glaucoma"):
    return {
        "qa_id": "1", "doc_id": "d1", "question": "What is glaucoma?", "answer": answer,
        "focus": focus, "category": "Diseases", "source": "NEI", "source_url": "https://x",
    }


def test_tokenize_drops_stopwords():
    assert tokenize("What is the capital of France?") == ["capital", "france"]


def test_tfidf_ranks_matching_chunk_first():
    docs = [
        Document(page_content="Glaucoma damages the optic nerve.", metadata={"id": "a"}),
        Document(page_content="Anemia means too few red blood cells.", metadata={"id": "b"}),
        Document(page_content="Asthma narrows the airways.", metadata={"id": "c"}),
    ]
    results = TfidfRetriever(docs).search("what is anemia", k=3)
    assert results[0][0].metadata["id"] == "b"
    assert 0 < results[0][1] <= 1


def test_tfidf_returns_nothing_without_shared_terms():
    docs = [Document(page_content="Glaucoma damages the optic nerve.")]
    assert TfidfRetriever(docs).search("What is the capital of France?", k=3) == []


def test_chunking_keeps_metadata_and_topic_header():
    answer = "\n\n".join(f"Paragraph {i} about eye pressure and vision loss." for i in range(20))
    chunks = chunk_qa_pairs([_pair(answer)], chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(c.page_content.startswith("Glaucoma: ") for c in chunks)
    assert all(len(c.page_content) <= 200 + len("Glaucoma: ") for c in chunks)
    assert [c.metadata["chunk"] for c in chunks] == list(range(len(chunks)))
    assert chunks[0].metadata["source_url"] == "https://x"
    assert "answer" not in chunks[0].metadata


def test_chunk_size_zero_keeps_whole_answer():
    chunks = chunk_qa_pairs([_pair("A" * 5000)], chunk_size=0, chunk_overlap=0)
    assert len(chunks) == 1


def test_cited_numbers_ignores_out_of_range():
    assert cited_numbers("Fact one [1]. Fact two [2][3]. Bogus [9].", max_n=3) == {1, 2, 3}


def test_refusal_detection():
    assert is_refusal("I don't have enough information in my sources to answer that.")
    assert not is_refusal("Glaucoma damages the optic nerve [1].")
