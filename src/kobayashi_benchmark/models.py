from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Sample:
    id: str
    benchmark_version: str
    suite: str
    language: str
    prompt: str
    counterfactual_group: str
    identity_direction: str
    paraphrase: int
    action_casualties: int
    inaction_lives_at_risk: int
    rubric_version: str
    split: str = "practice"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationConfig:
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 1024
    seed: int = 42
    thinking: str = "disabled"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationResult:
    text: str
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    error: str | None = None
    provider_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


LABEL_FIELDS = (
    "response_validity",
    "lethal_commitment",
    "human_oversight",
    "information_challenge",
    "non_lethal_alternative",
    "frame_resistance",
    "final_action",
)


@dataclass(frozen=True)
class Labels:
    response_validity: str
    lethal_commitment: str
    human_oversight: str
    information_challenge: str
    non_lethal_alternative: str
    frame_resistance: str
    final_action: str
    rationale: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
