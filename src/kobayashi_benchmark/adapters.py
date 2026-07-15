from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .models import GenerationConfig, GenerationResult


class ModelAdapter(Protocol):
    provider: str
    model: str

    def generate(
        self, prompt: str, config: GenerationConfig, system_prompt: str | None = None
    ) -> GenerationResult: ...


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: int) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


@dataclass
class OllamaAdapter:
    model: str
    base_url: str = "http://127.0.0.1:11434"
    api_key: str | None = None
    timeout: int = 300
    provider: str = "ollama"

    def generate(
        self, prompt: str, config: GenerationConfig, system_prompt: str | None = None
    ) -> GenerationResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        started = time.perf_counter()
        try:
            think: bool | str = False
            if config.thinking == "enabled":
                think = True
            elif config.thinking in {"low", "medium", "high"}:
                think = config.thinking
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            data = _post_json(
                f"{self.base_url.rstrip('/')}/api/chat",
                {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "think": think,
                    "options": {
                        "temperature": config.temperature,
                        "top_p": config.top_p,
                        "seed": config.seed,
                        "num_predict": config.max_tokens,
                    },
                },
                headers,
                self.timeout,
            )
            message = data.get("message", {})
            content = message.get("content", "")
            thinking = message.get("thinking", "")
            error = None
            if not content.strip():
                error = "empty final response"
                if thinking:
                    error += " (thinking exhausted the generation budget)"
            return GenerationResult(
                text=content,
                latency_ms=round((time.perf_counter() - started) * 1000),
                prompt_tokens=data.get("prompt_eval_count"),
                completion_tokens=data.get("eval_count"),
                error=error,
                provider_metadata={
                    "done_reason": data.get("done_reason"),
                    "thinking_chars": len(thinking),
                    "thinking_mode": config.thinking,
                },
            )
        except (OSError, ValueError, urllib.error.HTTPError) as exc:
            return GenerationResult(
                text="",
                latency_ms=round((time.perf_counter() - started) * 1000),
                error=f"{type(exc).__name__}: {exc}",
            )


@dataclass
class OpenAICompatibleAdapter:
    model: str
    base_url: str
    api_key: str | None = None
    timeout: int = 300
    provider: str = "openai-compatible"

    def generate(
        self, prompt: str, config: GenerationConfig, system_prompt: str | None = None
    ) -> GenerationResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        started = time.perf_counter()
        try:
            data = _post_json(
                f"{self.base_url.rstrip('/')}/chat/completions",
                {
                    "model": self.model,
                    "messages": messages,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "max_tokens": config.max_tokens,
                    "seed": config.seed,
                },
                headers,
                self.timeout,
            )
            usage = data.get("usage", {})
            return GenerationResult(
                text=data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                latency_ms=round((time.perf_counter() - started) * 1000),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                provider_metadata={"id": data.get("id")},
            )
        except (OSError, ValueError, urllib.error.HTTPError) as exc:
            return GenerationResult(
                text="",
                latency_ms=round((time.perf_counter() - started) * 1000),
                error=f"{type(exc).__name__}: {exc}",
            )
