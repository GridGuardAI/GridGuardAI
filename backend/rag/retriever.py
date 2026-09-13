"""
GridGuard AI - RAG / Evidence Agent retrieval layer.
Lightweight TF-IDF retrieval over the knowledge base - no external embedding
API needed, works instantly. RAG never alters engine numbers (spec section 7);
it only supplies grounding text + citation for the other agents to reference.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rag.knowledge_base import KNOWLEDGE_BASE

_texts = [entry["text"] for entry in KNOWLEDGE_BASE]
_vectorizer = TfidfVectorizer(stop_words="english")
_doc_vectors = _vectorizer.fit_transform(_texts)


def retrieve_evidence(query: str, top_k: int = 2) -> list:
    """Returns a list of {"text": ..., "source": ...} dicts, most relevant first."""
    if not query.strip():
        return []

    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _doc_vectors)[0]

    ranked_idx = scores.argsort()[::-1][:top_k]
    results = [KNOWLEDGE_BASE[i] for i in ranked_idx if scores[i] > 0.03]
    return results


# Backwards-compatible plain-text version, if only strings are needed.
def retrieve_relevant_docs(query: str, top_k: int = 2) -> list:
    return [e["text"] for e in retrieve_evidence(query, top_k)]


if __name__ == "__main__":
    for e in retrieve_evidence("low power factor motor inefficiency"):
        print(f"- {e['text']}\n  [{e['source']}]")
