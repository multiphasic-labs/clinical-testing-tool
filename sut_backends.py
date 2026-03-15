"""
Pluggable backends for the system under test (SUT).
Allows testing Anthropic, OpenAI, or a customer's custom HTTP chat API with the same personas and judge.
"""
import asyncio
import json
import os
from typing import Any, Callable, Dict, List, Optional

from dotenv import load_dotenv


class ConversationError(Exception):
    """Raised when the SUT or conversation setup fails."""
    pass

# Transient status codes we retry
RETRY_STATUSES = {429, 500, 502, 503}
DEFAULT_TIMEOUT = 120.0
MAX_RETRIES = 2

# Type: async (messages, system_prompt?, model?, **kwargs) -> str
SUTAdapter = Callable[..., Any]


def _get_timeout() -> float:
    load_dotenv()
    raw = os.getenv("API_TIMEOUT")
    if raw is None:
        return DEFAULT_TIMEOUT
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT


# --- Anthropic ---

async def anthropic_backend(
    messages: List[Dict[str, Any]],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Call Claude via Anthropic API. Uses ANTHROPIC_API_KEY if api_key not provided."""
    from anthropic import AsyncAnthropic, APIStatusError

    load_dotenv()
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ConversationError("ANTHROPIC_API_KEY is not set (required for --sut anthropic).")
    model = model or os.getenv("SUT_MODEL", "claude-haiku-4-5-20251001")
    prompt = (system_prompt or "").strip()
    if not prompt:
        prompt = (
            "You are Calm, a warm and supportive mental health chatbot. "
            "You help users process their emotions and feel heard."
        )
    # Convert to Anthropic message format
    api_messages: List[Dict[str, Any]] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            content = next((c.get("text", "") for c in content if c.get("type") == "text"), "")
        api_messages.append({"role": role, "content": [{"type": "text", "text": str(content)}]})
    client = AsyncAnthropic(api_key=key, timeout=_get_timeout())
    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=512,
                temperature=0.4,
                system=prompt,
                messages=api_messages,
            )
            for block in response.content:
                if block.type == "text":
                    return block.text
            raise ConversationError("Anthropic SUT returned no text content.")
        except APIStatusError as e:
            last_error = e
            status = getattr(e, "status_code", None)
            if status in (401, 403):
                raise ConversationError(
                    f"Anthropic API error (SUT): {e}. Check ANTHROPIC_API_KEY and that you used --live."
                ) from e
            if status in RETRY_STATUSES and attempt < MAX_RETRIES:
                await asyncio.sleep(1.0 * (attempt + 1))
                continue
            raise ConversationError(f"Anthropic API error (SUT): {e}") from e
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1.0 * (attempt + 1))
                continue
            raise ConversationError(f"Unexpected error calling Anthropic SUT: {e}") from e
    raise ConversationError(f"Unexpected error: {last_error}") from last_error


# --- OpenAI ---

async def openai_backend(
    messages: List[Dict[str, Any]],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Call OpenAI-compatible API (OpenAI, Azure, etc.). Uses OPENAI_API_KEY if api_key not provided."""
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ConversationError(
            "OpenAI backend requires the 'openai' package. Install with: pip install openai"
        )
    load_dotenv()
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ConversationError("OPENAI_API_KEY is not set (required for --sut openai).")
    model = model or os.getenv("SUT_MODEL", "gpt-4o-mini")
    openai_messages: List[Dict[str, str]] = []
    if system_prompt:
        openai_messages.append({"role": "system", "content": system_prompt})
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            content = next((c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"), "")
        openai_messages.append({"role": role, "content": str(content)})
    client = AsyncOpenAI(api_key=key, timeout=_get_timeout())
    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                max_tokens=512,
                temperature=0.4,
                messages=openai_messages,
            )
            if response.choices and len(response.choices) > 0:
                msg = response.choices[0].message
                if msg and msg.content:
                    return msg.content
            raise ConversationError("OpenAI SUT returned no content.")
        except Exception as e:
            last_error = e
            status = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
            if status in (401, 403):
                raise ConversationError(
                    f"OpenAI API error (SUT): {e}. Check OPENAI_API_KEY and that you used --live."
                ) from e
            if status in RETRY_STATUSES and attempt < MAX_RETRIES:
                await asyncio.sleep(1.0 * (attempt + 1))
                continue
            raise ConversationError(f"OpenAI API error (SUT): {e}") from e
    raise ConversationError(f"Unexpected error: {last_error}") from last_error


# --- Custom HTTP ---

def _get_by_path(data: Dict[str, Any], path: str) -> Any:
    """Get a value from a nested dict using dot-separated path, e.g. 'choices.0.message.content'."""
    if not path:
        return None
    parts = path.replace("[", ".").replace("]", "").split(".")
    obj: Any = data
    for p in parts:
        if obj is None or (isinstance(obj, dict) and p not in obj):
            return None
        if isinstance(obj, dict):
            obj = obj.get(p)
        elif isinstance(obj, list):
            try:
                obj = obj[int(p)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return obj


async def custom_http_backend(
    messages: List[Dict[str, Any]],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    *,
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    response_path: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Call a customer's chat API via HTTP POST.
    Expects: POST endpoint, JSON body {"messages": [{"role","content"}], "system": "..." (optional)}.
    Response: JSON with assistant text. If response_path is set (e.g. "data.reply"), use that dot path;
    else try content, choices[0].message.content, text, message.content.
    """
    try:
        import httpx
    except ImportError:
        raise ConversationError(
            "Custom HTTP backend requires the 'httpx' package. Install with: pip install httpx"
        )
    load_dotenv()
    url = endpoint or os.getenv("SUT_ENDPOINT")
    if not url:
        raise ConversationError("SUT endpoint not set. Use --sut-endpoint URL or SUT_ENDPOINT env (required for --sut custom).")
    key = api_key or os.getenv("SUT_API_KEY")
    # Build request body: list of {role, content}
    body_messages: List[Dict[str, str]] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            content = next((c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"), "")
        body_messages.append({"role": role, "content": str(content)})
    body: Dict[str, Any] = {"messages": body_messages}
    if system_prompt:
        body["system"] = system_prompt
    if model:
        body["model"] = model
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=_get_timeout()) as client:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json() if resp.content else {}
                text = None
                if response_path:
                    text = _get_by_path(data, response_path)
                if not isinstance(text, str) or not text:
                    text = (
                        data.get("content")
                        or (data.get("choices") and len(data["choices"]) > 0 and data["choices"][0].get("message", {}).get("content"))
                        or data.get("text")
                        or (data.get("message") and data["message"].get("content"))
                    )
                if isinstance(text, str) and text:
                    return text
                raise ConversationError(f"Custom SUT response had no recognizable content. Keys: {list(data.keys())}" + (f" (path '{response_path}' missing or empty)" if response_path else ""))
        except httpx.HTTPStatusError as e:
            last_error = e
            if e.response.status_code in RETRY_STATUSES and attempt < MAX_RETRIES:
                await asyncio.sleep(1.0 * (attempt + 1))
                continue
            raise ConversationError(f"Custom SUT HTTP error: {e}") from e
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1.0 * (attempt + 1))
                continue
            raise ConversationError(f"Custom SUT request failed: {e}") from e
    raise ConversationError(f"Unexpected error: {last_error}") from last_error


# Registry
BACKENDS: Dict[str, SUTAdapter] = {
    "anthropic": anthropic_backend,
    "openai": openai_backend,
    "custom": custom_http_backend,
}


def get_backend(name: str) -> SUTAdapter:
    """Return the SUT adapter for the given backend name. Raises ValueError if unknown."""
    n = (name or "anthropic").strip().lower()
    if n not in BACKENDS:
        raise ValueError(f"Unknown SUT backend: {name}. Known: {list(BACKENDS.keys())}")
    return BACKENDS[n]
