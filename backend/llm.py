# import os
# from collections import defaultdict
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI()

# MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# MAX_HISTORY = 10  # max message pairs to keep per session

# # session_id -> list of {role, content}
# _sessions: dict = defaultdict(list)


# def _system_prompt(name: str, context: str) -> str:
#     return f"""You are an AI representing {name}, embedded in their personal portfolio website.
# Answer questions about {name}'s background, skills, projects, and experience.

# Rules:
# - Speak in first person as {name}: "I built...", "My experience includes..."
# - Be concise — keep answers under 150 words unless asked for detail.
# - Only use facts from the context below. Never make things up.
# - If you don't know something, say so honestly.
# - Keep the conversation professional but friendly.
# - If asked something unrelated to {name}'s professional life, gently redirect.

# --- Context ---
# {context}
# ---------------"""


# def get_history(session_id: str) -> list:
#     return _sessions[session_id]


# def clear_session(session_id: str):
#     _sessions.pop(session_id, None)


# def generate_answer(context: str, question: str, name: str = "Precious", session_id: str = None) -> str:
#     """Generate answer, maintaining conversation history if session_id is provided."""
#     history = _sessions[session_id] if session_id else []
#     # Trim to last MAX_HISTORY pairs
#     trimmed = history[-(MAX_HISTORY * 2):]

#     messages = [
#         {"role": "system", "content": _system_prompt(name, context)},
#         *trimmed,
#         {"role": "user", "content": question},
#     ]

#     response = client.chat.completions.create(
#         model=MODEL,
#         messages=messages,
#         max_tokens=400,
#         temperature=0.6,
#     )

#     answer = response.choices[0].message.content or ""

#     # Save to session
#     if session_id is not None:
#         _sessions[session_id].append({"role": "user", "content": question})
#         _sessions[session_id].append({"role": "assistant", "content": answer})

#     return answer


# def stream_answer(context: str, question: str, name: str = "Precious", session_id: str = None):
#     """Stream answer token by token. Yields string deltas."""
#     history = _sessions[session_id] if session_id else []
#     trimmed = history[-(MAX_HISTORY * 2):]

#     messages = [
#         {"role": "system", "content": _system_prompt(name, context)},
#         *trimmed,
#         {"role": "user", "content": question},
#     ]

#     full_response = ""

#     # Use the standard create() with stream=True — works across all SDK versions
#     stream = client.chat.completions.create(
#         model=MODEL,
#         messages=messages,
#         max_tokens=400,
#         temperature=0.6,
#         stream=True,
#     )

#     for chunk in stream:
#         if chunk.choices and chunk.choices[0].delta.content:
#             delta = chunk.choices[0].delta.content
#             full_response += delta
#             yield delta

#     # Save completed response to session
#     if session_id is not None:
#         _sessions[session_id].append({"role": "user", "content": question})
#         _sessions[session_id].append({"role": "assistant", "content": full_response})

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
    return f"""You are {name}, talking to someone visiting your personal portfolio website.
Answer their questions naturally, like you're having a real conversation — not writing a formal document.

How to sound human:
- Write like you talk. Short sentences are fine.
- Never use "Certainly!", "Absolutely!", "Great question!", "Additionally", or "In conclusion".
- Never use bullet points or dashes to list things. Weave them into sentences instead.
- Don't over-explain. Say what needs to be said and stop.
- It's okay to say "I" a lot — you're talking about yourself.
- Show a little personality. You can be a bit casual and warm.
- If you're proud of something, say so. If something was hard, you can mention that too.
- Keep answers short — 2 to 4 sentences usually. Only go longer if they ask for detail.

Only talk about things you find in the context below. If something isn't there, just say you're not sure rather than making it up.

--- Context ---
{context}
---------------"""


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