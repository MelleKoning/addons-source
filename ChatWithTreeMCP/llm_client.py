#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2025 Melle Koning
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
llm_client.py — minimal, dependency-free OpenAI-compatible LLM client.

Replaces the external ``litellm`` dependency with a small stdlib-only
implementation. It speaks the OpenAI Chat Completions HTTP API
(https://platform.openai.com/docs/api-reference/chat) so it works against any
OpenAI-compatible endpoint (Ollama, LM Studio, vLLM, OpenAI itself, …).

The response objects returned by :meth:`LLMClient.completion` deliberately
mimic the subset of the ``litellm``/OpenAI ``ModelResponse`` surface that the
rest of ChatWithTreeMCP relies on:

    response.choices[0].message.content
    response.choices[0].message.tool_calls
    response.choices[0].message.reasoning_content
    response.choices[0].message.to_dict()
    response.choices[0].message["tool_calls"]
    response.choices[0].message["tool_calls"][i]["function"]["name"]
    response.choices[0].message["tool_calls"][i]["function"]["arguments"]
    response.choices[0].message["tool_calls"][i]["id"]

Both attribute and item access are supported, and missing fields return
``None`` (matching litellm) rather than raising, so the existing tool-loop
code keeps working unchanged.
"""
import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

# Default base URL of an OpenAI-compatible endpoint. Mirrors the previous
# litellm default for the ``ollama/`` provider (Ollama's OpenAI shim lives at
# http://localhost:11434/v1).
DEFAULT_MODEL_URL = "http://localhost:11434"

PROVIDER_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ollama": {
        "url": "http://localhost:11434/v1/chat/completions",
        "key_env": None,
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
    },
    "moonshotai": {
        "url": "https://api.moonshot.ai/v1/chat/completions",
        "key_env": "MOONSHOT_API_KEY",
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "key_env": "OPENAI_API_KEY",
    },
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "key_env": "DEEPSEEK_API_KEY",
    },
    "opencode": {
        "url": "https://opencode.ai/zen/v1/chat/completions",
        "key_env": "OPENCODE_API_KEY",
    },
}


def _strip_provider_prefix(model_name: str) -> str:
    """Drop a leading ``provider/`` segment (e.g. ``ollama/foo`` -> ``foo``).

    litellm routes by provider and strips this prefix before sending the
    model name to the actual endpoint. We keep that behaviour so the
    documented ``ollama/…`` / ``openai/…`` / ``gemini/…`` names remain valid
    against a single, explicitly-configured OpenAI-compatible base URL.
    """
    if "/" in model_name:
        return model_name.split("/", 1)[1]
    return model_name


def resolve_provider(model_name: str) -> tuple:
    """Resolve provider prefix to (url, api_key, stripped_model_name)."""
    if "/" in model_name:
        provider = model_name.split("/", 1)[0]
        stripped = _strip_provider_prefix(model_name)
    else:
        provider = None
        stripped = model_name
    if provider and provider in PROVIDER_REGISTRY:
        entry = PROVIDER_REGISTRY[provider]
        url = entry["url"]
        key = os.environ.get(entry["key_env"]) if entry["key_env"] else None
        return url, key, stripped
    # Fallback: no prefix or unknown provider
    base = os.environ.get("GRAMPS_AI_MODEL_URL", DEFAULT_MODEL_URL)
    return base, os.environ.get("OPENAI_API_KEY"), model_name


def _endpoint_url(model_url: str) -> str:
    """Build the chat/completions URL from a base URL.

    - A full ``…/chat/completions`` URL is used verbatim.
    - A ``…/v1`` base gets ``/chat/completions`` appended.
    - Any other base gets ``/v1/chat/completions`` appended.
    """
    base = (model_url or DEFAULT_MODEL_URL).rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


class Message:
    """Dict-backed message supporting both attribute and item access."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        # Only called for names not found via normal attribute lookup.
        # Return None for missing fields to mirror litellm/OpenAI behaviour.
        return self._data.get(name)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise back to the raw dict (echoed into chat history)."""
        return self._data


class Choice:
    """Wraps a single ``choices[]`` entry."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def message(self) -> Message:
        return Message(self._data.get("message", {}))

    def __getattr__(self, name: str) -> Any:
        return self._data.get(name)


class CompletionResponse:
    """Wraps the full chat/completions JSON response."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def choices(self) -> List[Choice]:
        return [Choice(c) for c in self._data.get("choices", [])]

    def __getattr__(self, name: str) -> Any:
        return self._data.get(name)


class LLMClient:
    """Stdlib-only client for an OpenAI-compatible Chat Completions API."""

    def __init__(
        self,
        model_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ):
        # The base URL of an OpenAI-compatible endpoint. Honours
        # GRAMPS_AI_MODEL_URL; falls back to the local Ollama default.
        self.model_url = model_url or os.environ.get(
            "GRAMPS_AI_MODEL_URL", DEFAULT_MODEL_URL
        )
        # Only attach an Authorization header when a key is present
        # (e.g. for OpenAI/LM Studio gateways; local Ollama needs none).
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.timeout = timeout

    def completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        seed: Optional[int] = None,
        stream: bool = False,
        model_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> CompletionResponse:
        """POST a chat-completion request and return a ``CompletionResponse``.

        ``model`` is taken per-call (not captured) so the ``/setmodel`` command
        can switch models at runtime, as the previous litellm path did.
        """
        url = _endpoint_url(model_url if model_url is not None else self.model_url)
        payload: Dict[str, Any] = {
            "model": _strip_provider_prefix(model),
            "messages": messages,
            "stream": stream,
        }
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if seed is not None:
            payload["seed"] = seed

        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header(
            "User-Agent",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        )
        request.add_header(
            "Accept",
            "text/event-stream" if stream else "application/json",
        )
        key = api_key if api_key is not None else self.api_key
        if key:
            request.add_header("Authorization", f"Bearer {key}")

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace") if exc.fp else ""
            key = api_key if api_key is not None else self.api_key
            # Diagnostic context for auth/debug errors (404/401/etc.)
            diag = (
                f"[url={url}; key_present={key is not None}; "
                f"model={_strip_provider_prefix(model)}]"
            )
            raise RuntimeError(
                f"LLM endpoint returned HTTP {exc.code}: "
                f"{detail or exc.reason} {diag}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Could not reach LLM endpoint {url}: {exc.reason}"
            ) from exc

        data = self._accumulate_sse(raw) if stream else json.loads(raw)
        return CompletionResponse(data)

    # -- streaming helpers -------------------------------------------------
    @staticmethod
    def _accumulate_sse(raw: str) -> Dict[str, Any]:
        """Reconstruct one response dict from an SSE ``text/event-stream``.

        Accumulates ``content`` deltas and merges incremental ``tool_calls``
        deltas (OpenAI streams them indexed by ``index`` with partial
        ``function.arguments`` fragments). Returns a Chat-Completions-shaped
        dict whose first choice message carries the full content/tool_calls.
        """
        content_parts: List[str] = []
        # index -> {"index", "id", "type", "function": {"name", "arguments"}}
        tool_calls: Dict[int, Dict[str, Any]] = {}
        finish_reason: Optional[str] = None
        model_name: Optional[str] = None
        role: str = "assistant"

        for line in raw.splitlines():
            line = line.strip()
            if not line or not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if payload == "[DONE]":
                break
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue

            model_name = event.get("model", model_name)
            choices = event.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            if "role" in delta:
                role = delta["role"]
            if delta.get("content") is not None:
                content_parts.append(delta["content"])
            for tc in delta.get("tool_calls", []) or []:
                idx = tc.get("index", 0)
                slot = tool_calls.setdefault(
                    idx,
                    {
                        "index": idx,
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    },
                )
                if tc.get("id"):
                    slot["id"] = tc["id"]
                if tc.get("type"):
                    slot["type"] = tc["type"]
                func = tc.get("function", {})
                if func.get("name"):
                    slot["function"]["name"] += func["name"]
                if func.get("arguments"):
                    slot["function"]["arguments"] += func["arguments"]
            if choices[0].get("finish_reason") is not None:
                finish_reason = choices[0]["finish_reason"]

        message: Dict[str, Any] = {
            "role": role,
            "content": "".join(content_parts),
        }
        if tool_calls:
            ordered = [tool_calls[i] for i in sorted(tool_calls)]
            for slot in ordered:
                slot.pop("index", None)
            message["tool_calls"] = ordered

        return {
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": message,
                    "finish_reason": finish_reason,
                }
            ],
        }
