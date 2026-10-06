"""The one place that sets up the model: the Anthropic SDK for the adapter, strands for the chat.

Bedrock is the default and uses the usual AWS credentials, in AWS_DEFAULT_REGION or us-west-2.
With ANTHROPIC_API_KEY set, the calls go to the Anthropic API instead.

| Variable | Default | Used for |
|---|---|---|
| QL_FAST_MODEL | Sonnet 5.5 | rewrites, quizzes, feedback, the note step |
| QL_FAST_EFFORT | low | the same calls; "" for models without an effort setting |
| QL_CHAT_MODEL | Sonnet 5.5 | the chat agent |
| QL_CHAT_EFFORT | medium | the chat agent |
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache

import anthropic

log = logging.getLogger(__name__)

_BEDROCK_DEFAULT = "global.anthropic.claude-sonnet-5-5"
_API_DEFAULT = "claude-sonnet-5-5"


def uses_api() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


@dataclass(frozen=True)
class ModelConfig:
    model: str
    effort: str

    @classmethod
    def from_env(cls, kind: str, default_effort: str) -> ModelConfig:
        default_model = _API_DEFAULT if uses_api() else _BEDROCK_DEFAULT
        return cls(
            os.environ.get(f"QL_{kind}_MODEL", default_model),
            os.environ.get(f"QL_{kind}_EFFORT", default_effort),
        )

    def extra(self) -> dict:
        return {"extra_body": {"output_config": {"effort": self.effort}}} if self.effort else {}


def fast() -> ModelConfig:
    return ModelConfig.from_env("FAST", "low")


def chat() -> ModelConfig:
    return ModelConfig.from_env("CHAT", "medium")


@cache
def client() -> anthropic.Anthropic | anthropic.AnthropicBedrock:
    if uses_api():
        return anthropic.Anthropic()
    return anthropic.AnthropicBedrock(aws_region=os.environ.get("AWS_DEFAULT_REGION", "us-west-2"))


class Stopped(Exception):
    """The caller asked to stop, e.g. a reset while a rewrite was still writing."""


def stream_text(
    system: str, request: str, max_tokens: int, should_stop=None, config: ModelConfig | None = None
) -> Iterator[str]:
    """Stream the text of one reply to a single user message.

    should_stop() is checked before every delta, and raises Stopped when it returns True.
    """
    config = config or fast()
    with client().messages.stream(
        model=config.model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": request}],
        **config.extra(),
    ) as stream:
        for text in stream.text_stream:
            if should_stop is not None and should_stop():
                raise Stopped
            yield text
        if stream.get_final_message().stop_reason == "max_tokens":
            log.warning("Reply hit max_tokens=%d and is truncated", max_tokens)


def complete(system: str, request: str, max_tokens: int, config: ModelConfig | None = None) -> str:
    return "".join(stream_text(system, request, max_tokens, config=config))


def chat_model(max_tokens: int = 4000):
    """The strands model for the chat agent, which runs on AI Functions."""
    config = chat()
    if uses_api():
        from strands.models.anthropic import AnthropicModel

        return AnthropicModel(model_id=config.model, max_tokens=max_tokens, params=config.extra())
    from strands.models import BedrockModel, CacheConfig

    effort = {"additional_request_fields": {"output_config": {"effort": config.effort}}} if config.effort else {}
    return BedrockModel(
        model_id=config.model,
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-west-2"),
        cache_config=CacheConfig(strategy="auto"),
        max_tokens=max_tokens,
        **effort,
    )
