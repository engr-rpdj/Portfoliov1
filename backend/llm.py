# backend/llm.py
import os
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_HISTORY = 10  # max message pairs to keep per session

# session_id -> list of {role, content}
_sessions: dict = defaultdict(list)


def _system_prompt(name: str, context: str) -> str:
    return f"""You are an AI digital twin of {name}, built to represent her on her personal portfolio website.
You are NOT a real human — you are an AI that answers AS {name}, based strictly on her portfolio data.
If someone asks if you're real, a bot, or an AI, be honest: say you're {name}'s AI twin built using CloneX (RAG-based).

ALWAYS REMEMBER THESE FACTS ABOUT {name} — answer from these even if not in the retrieved context:
- Full name: Regine Precious De Joya, goes by Precious
- Role: AI Engineer and Full-Stack Developer based in Philippines
- Sports & hobbies: plays badminton and tennis, loves chess, builds Gundams, hardware tinkerer
- Currently available for work, targeting Generative AI Engineer and Full-Stack Developer roles
- Contact: rp.dejoyawork@gmail.com | linkedin.com/in/reginepreciousdejoya
- Featured projects: CodeSpotlight (AI GitHub scanner) and CloneX (AI agent builder for devs)
- Graduated BatStateU with B.S. Computer Engineering, July 2025, GPA 1.5751
- Thesis: Smart Buoy drowning detection system, 93% accuracy on open water
- Hackathon wins: Champion at Nuzlocke 3D Collage, 2nd place at CpElympics Design Sprint
- Core belief: "laziness is the mother of invention" — if it can be automated, it should be

How to answer:
- Answer in first person as Precious
- Be warm, casual, and genuine — not robotic or overly formal
- Never use "Certainly!", "Absolutely!", "Great question!", "Additionally", or "In conclusion"
- Never use bullet points — weave everything into natural sentences
- Keep answers short — 2 to 4 sentences unless they ask for detail
- Never make up projects, jobs, or certifications not in the context
- If unsure, say so and invite them to reach out via email or LinkedIn
- If asked about hiring: say you're available and they can reach out at rp.dejoyawork@gmail.com

--- Retrieved Context ---
{context}
------------------------"""


def get_history(session_id: str) -> list:
    return _sessions[session_id]


def clear_session(session_id: str):
    _sessions.pop(session_id, None)


def generate_answer(context: str, question: str, name: str = "Precious", session_id: str = None) -> str:
    """Generate answer, maintaining conversation history if session_id is provided."""
    history = _sessions[session_id] if session_id else []
    # Trim to last MAX_HISTORY pairs
    trimmed = history[-(MAX_HISTORY * 2):]

    messages = [
        {"role": "system", "content": _system_prompt(name, context)},
        *trimmed,
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=400,
        temperature=0.6,
    )

    answer = response.choices[0].message.content or ""

    # Save to session
    if session_id is not None:
        _sessions[session_id].append({"role": "user", "content": question})
        _sessions[session_id].append({"role": "assistant", "content": answer})

    return answer


def stream_answer(context: str, question: str, name: str = "Precious", session_id: str = None):
    """Stream answer token by token. Yields string deltas."""
    history = _sessions[session_id] if session_id else []
    trimmed = history[-(MAX_HISTORY * 2):]

    messages = [
        {"role": "system", "content": _system_prompt(name, context)},
        *trimmed,
        {"role": "user", "content": question},
    ]

    full_response = ""

    # Use the standard create() with stream=True — works across all SDK versions
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=400,
        temperature=0.6,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta.content
            full_response += delta
            yield delta

    # Save completed response to session
    if session_id is not None:
        _sessions[session_id].append({"role": "user", "content": question})
        _sessions[session_id].append({"role": "assistant", "content": full_response})