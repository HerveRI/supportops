import httpx

from app.config import settings


class LLMError(RuntimeError):
    """Raised when the local LLM cannot produce a valid response."""


def generate_chat_response(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Generate one non-streaming response from the configured Ollama model."""

    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

    payload = {
        "model": settings.ollama_model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "think": False,
        "stream": False,
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise LLMError("Failed to communicate with ollama") from e

    try:
        data = response.json()
        content = data["message"]["content"]
    except (ValueError, KeyError, TypeError) as e:
        raise LLMError("Ollama returned an invalid response") from e

    if not isinstance(content, str) or not content.strip():
        raise LLMError("Ollama returned an empty response")

    return content.strip()
