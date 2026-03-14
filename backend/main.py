# backend/main.py
import os
import uuid
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

from .ingest import load_pdf, load_text
from .retriever import add_document, search
from .llm import generate_answer, stream_answer, clear_session, get_history

# ── Config ──────────────────────────────────────────────────
TWIN_NAME    = os.getenv("TWIN_NAME", "Precious")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "..", "data")
HTML_FILE = os.path.join(BASE_DIR, "..", "portfolio.html")
LINKEDIN  = os.path.join(DATA_DIR, "linkedin.pdf")
SUMMARY   = os.path.join(DATA_DIR, "summary.txt")

# ── App ──────────────────────────────────────────────────────
app = FastAPI(title=f"{TWIN_NAME} — AI Digital Twin")

app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/imagescerts", StaticFiles(directory="imagescerts"), name="imagescerts")
app.mount("/imagescv", StaticFiles(directory="imagescv"), name="imagescv")
app.mount("/imagesemb", StaticFiles(directory="imagesemb"), name="imagesemb")
app.mount("/imageswebapp", StaticFiles(directory="imageswebapp"), name="imageswebapp")
app.mount("/gifs", StaticFiles(directory="gifs"), name="gifs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load documents ───────────────────────────────────────────
_indexed = False

def _ensure_indexed():
    global _indexed
    if _indexed:
        return
    try:
        linkedin_text = load_pdf(LINKEDIN)
        add_document(linkedin_text, "linkedin")
        print("✓ linkedin.pdf indexed")
    except FileNotFoundError as e:
        print(f"⚠ {e} — skipping")

    try:
        summary_text = load_text(SUMMARY)
        add_document(summary_text, "summary")
        print("✓ summary.txt indexed")
    except FileNotFoundError as e:
        print(f"⚠ {e} — skipping")

    print(f"✓ AI Digital Twin ready — {TWIN_NAME}")
    _indexed = True

_ensure_indexed()


# ── Schemas ──────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    n_results: int = 3


class AskResponse(BaseModel):
    answer: str
    session_id: str
    context: List[str]


# ── Routes ───────────────────────────────────────────────────
@app.get("/")
def root():
    """Serve the portfolio HTML."""
    if os.path.exists(HTML_FILE):
        return FileResponse(HTML_FILE, media_type="text/html")
    return {"message": f"{TWIN_NAME}'s AI Digital Twin is running. POST to /ask"}


@app.get("/health")
def health():
    return {"status": "ok", "twin": TWIN_NAME}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, stream: bool = Query(default=False)):
    session_id = request.session_id or str(uuid.uuid4())
    context_chunks = search(request.question, n_results=request.n_results)

    if not context_chunks:
        context = "No specific context found — answer based on general knowledge about the person."
    else:
        context = "\n\n".join(context_chunks)

    if stream:
        def _gen():
            for token in stream_answer(context, request.question, TWIN_NAME, session_id):
                yield token
        return StreamingResponse(_gen(), media_type="text/plain",
                                  headers={"X-Session-Id": session_id})

    answer = generate_answer(context, request.question, TWIN_NAME, session_id)
    return AskResponse(answer=answer, session_id=session_id, context=context_chunks)


@app.get("/session/{session_id}")
def get_session(session_id: str):
    return {"session_id": session_id, "messages": get_history(session_id)}


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    clear_session(session_id)
    return {"status": "cleared"}
#-----------------------------------------------------------
# # backend/main.py
# import os
# import uuid
# from fastapi import FastAPI, HTTPException, Query
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel
# from typing import List, Optional

# from .ingest import load_pdf, load_text
# from .retriever import add_document, search
# from .llm import generate_answer, stream_answer, clear_session, get_history

# # ── Config ──────────────────────────────────────────────────
# TWIN_NAME    = os.getenv("TWIN_NAME", "Precious")
# CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# # Works both locally and on Vercel
# BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR  = os.path.join(BASE_DIR, "..", "data")
# LINKEDIN  = os.path.join(DATA_DIR, "linkedin.pdf")
# SUMMARY   = os.path.join(DATA_DIR, "summary.txt")

# # ── App ──────────────────────────────────────────────────────
# app = FastAPI(title=f"{TWIN_NAME} — AI Digital Twin")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ── Load documents at module level ───────────────────────────
# # Vercel is serverless — each cold start re-imports this module,
# # so we index here (not just in startup) to ensure it always runs.
# _indexed = False

# def _ensure_indexed():
#     global _indexed
#     if _indexed:
#         return
#     try:
#         linkedin_text = load_pdf(LINKEDIN)
#         add_document(linkedin_text, "linkedin")
#         print("✓ linkedin.pdf indexed")
#     except FileNotFoundError as e:
#         print(f"⚠ {e} — skipping")

#     try:
#         summary_text = load_text(SUMMARY)
#         add_document(summary_text, "summary")
#         print("✓ summary.txt indexed")
#     except FileNotFoundError as e:
#         print(f"⚠ {e} — skipping")

#     print(f"✓ AI Digital Twin ready — {TWIN_NAME}")
#     _indexed = True

# _ensure_indexed()


# # ── Schemas ──────────────────────────────────────────────────
# class AskRequest(BaseModel):
#     question: str
#     session_id: Optional[str] = None
#     n_results: int = 3


# class AskResponse(BaseModel):
#     answer: str
#     session_id: str
#     context: List[str]


# # ── Routes ───────────────────────────────────────────────────
# @app.get("/")
# def root():
#     return {"message": f"{TWIN_NAME}'s AI Digital Twin is running. POST to /ask"}


# @app.get("/health")
# def health():
#     return {"status": "ok", "twin": TWIN_NAME}


# @app.post("/ask", response_model=AskResponse)
# def ask(request: AskRequest, stream: bool = Query(default=False)):
#     """
#     Ask the digital twin a question.
#     - Pass session_id to maintain conversation memory.
#     - Add ?stream=true for token-by-token streaming (returns text/plain).
#     """
#     session_id = request.session_id or str(uuid.uuid4())
#     context_chunks = search(request.question, n_results=request.n_results)

#     if not context_chunks:
#         context = "No specific context found — answer based on general knowledge about the person."
#     else:
#         context = "\n\n".join(context_chunks)

#     if stream:
#         def _gen():
#             for token in stream_answer(context, request.question, TWIN_NAME, session_id):
#                 yield token
#         return StreamingResponse(_gen(), media_type="text/plain",
#                                   headers={"X-Session-Id": session_id})

#     answer = generate_answer(context, request.question, TWIN_NAME, session_id)
#     return AskResponse(answer=answer, session_id=session_id, context=context_chunks)


# @app.get("/session/{session_id}")
# def get_session(session_id: str):
#     return {"session_id": session_id, "messages": get_history(session_id)}


# @app.delete("/session/{session_id}")
# def delete_session(session_id: str):
#     clear_session(session_id)
#     return {"status": "cleared"}