from typing import Any

import httpx

from app.config import settings


class LLMError(RuntimeError):
    """Raised when the local LLM cannot produce a valid response."""


def chat_with_ollama(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    think: bool = False,
) -> dict[str, Any]:
    """Send one non-streaming chat request to Ollama."""

    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

    payload: dict[str, Any] = {
        "model": settings.ollama_model,
        "messages": messages,
        "think": think,
        "stream": False,
        "option": {
            "num_ctx": 8192,
            "temperature": 0.7,
        },
    }

    if tools is not None:
        payload["tools"] = tools

    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise LLMError("Failed to communicate with Ollama") from e

    try:
        data = response.json()
        message = data["message"]
    except (ValueError, KeyError, TypeError) as exc:
        raise LLMError("Ollama returned an invalid message") from exc

    return message


def generate_chat_response(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Generate one text response from the configured Ollama model."""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    message = chat_with_ollama(messages)
    content = message.get("content")

    if not isinstance(content, str) or not content.strip():
        raise LLMError("Ollama returned an empty response")

    return content.strip()
