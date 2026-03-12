# backend/retriever.py
# Uses OpenAI embeddings - lightweight, no heavy ML packages needed

import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# In-memory store
_docs = []
_embeddings = []


def _embed(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def chunk_text(text: str, max_words: int = 150) -> list:
    sentences = text.replace("\n", " ").split(". ")
    chunks = []
    chunk = ""
    for s in sentences:
        if len(chunk.split()) + len(s.split()) > max_words:
            if chunk:
                chunks.append(chunk.strip())
            chunk = s
        else:
            chunk += " " + s
    if chunk:
        chunks.append(chunk.strip())
    return chunks


def add_document(text: str, source: str = "unknown"):
    chunks = chunk_text(text)
    for chunk in chunks:
        if not chunk:
            continue
        vector = _embed(chunk)
        _docs.append({"text": chunk, "source": source})
        _embeddings.append(vector)
    print(f"✓ Indexed {len(chunks)} chunks from '{source}'")


def search(query: str, n_results: int = 3) -> list:
    if not _docs:
        return []
    query_vec = _embed(query)
    scores = [_cosine_similarity(query_vec, emb) for emb in _embeddings]
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_results]
    return [_docs[i]["text"] for i in top_indices]