# backend/app/groq_client.py
import os
import json
import httpx
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "compound-beta")
GROQ_BASE = "https://api.groq.com/openai/v1"  # OpenAI-compatible endpoint

if not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY in environment")

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

async def stream_chat_completion(prompt: str) -> AsyncGenerator[str, None]:
    """
    Calls the Groq chat completions endpoint with stream: true and yields
    token deltas as they arrive (strings). The endpoint returns SSE lines like:
      data: {"id": "...", "choices":[{"delta": {"content": "..."} }]}
    and ends with: data: [DONE]
    """
    url = f"{GROQ_BASE}/chat/completions"
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": True
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, headers=HEADERS, json=payload) as resp:
            resp.raise_for_status()
            async for raw_line in resp.aiter_lines():
                line = raw_line.strip()
                if not line:
                    continue
                # SSE lines start with "data: "
                if line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data_str)
                        # OpenAI-compatible format: choices[].delta.content
                        choices = parsed.get("choices", [])
                        for choice in choices:
                            delta = choice.get("delta", {})
                            # there could be 'content' or other fields
                            content = delta.get("content")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        # ignore non-json lines
                        continue
