# backend/retriever.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

dimension = 384
index = faiss.IndexFlatL2(dimension)
docs = []


def embed(text):
    return model.encode(text).astype(np.float32)


def chunk_text(text, max_tokens=600):
    """Split text into overlapping chunks."""
    sentences = text.split(". ")
    chunks = []
    chunk = ""
    for s in sentences:
        if len(chunk.split()) + len(s.split()) > max_tokens:
            chunks.append(chunk.strip())
            chunk = s
        else:
            chunk += " " + s
    if chunk:
        chunks.append(chunk.strip())
    return chunks


def add_document(text, doc_id=None):
    chunks = chunk_text(text)
    for chunk in chunks:
        vector = embed(chunk)
        index.add(np.array([vector]))
        docs.append(chunk)


def search(query, n_results=3):
    if index.ntotal == 0:
        return []
    vector = embed(query)
    distances, indices = index.search(np.array([vector]), n_results)
    results = [docs[i] for i in indices[0] if i < len(docs)]
    return results