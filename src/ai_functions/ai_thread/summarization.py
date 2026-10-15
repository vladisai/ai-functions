"""Pluggable conversation-summarization strategies."""

from __future__ import annotations

import dataclasses
import re
from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry
from strands.types.content import Message, Messages

from ..types import (
    ContextSummarizedEvent,
    Event,
    MessageAssistantCompleteEvent,
    MessageUserEvent,
    RenderableEvent,
    ThreadContext,
    ToolResultEvent,
    is_renderable_event,
)
from .config import AgentKwargs, ThreadConfig
from .errors import AIFunctionError
from .reconstruction import reconstruct_messages

if TYPE_CHECKING:
    from .ai_function import AIFunction

# Rough chars-per-token estimate. Conservative — we
# under-estimate tokens slightly (i.e. over-estimate each message's token cost
# when comparing against bounds) which biases the strategy toward summarizing
# a bit more aggressively. That is the safer direction: oversized tails are
# what trigger runaway overflow.
_CHARS_PER_TOKEN: float = 3.5

# Hard cap on summarization attempts per invocation (proactive + reactive
# combined). Bounds the worst case when every strategy configuration still
# overflows.
_MAX_SUMMARIZATION_ATTEMPTS: int = 3

# System prompt used by the dedicated-summarizer path (when forking is
# incompatible with the parent's structured-output shape).
_DEDICATED_SUMMARIZER_SYSTEM_PROMPT: str = (
    "You are a conversation summarization assistant. You receive a full "
    "conversation history (possibly including tool calls and their results) "
    "and must produce a summary of everything that happened, faithfully capturing "
    "the user's goals, the assistant's actions and findings, and any "
    "unresolved threads or pending work.\n"
    "\n"
    "Output the summary inside <summary>...</summary> XML tags, and nothing "
    "else. Do not answer any question the user may have asked; your job is "
    "exclusively to summarize so the conversation can be continued with a "
    "shorter history."
)

# User turn appended to the reconstructed history to request the summary.
# Shared by the forking and dedicated paths so the messages the summarizer
# sees are identical modulo system prompt and tool specs.
_SUMMARIZE_REQUEST_TEXT: str = (
    "Context-management task: the conversation above has grown too long. "
    "Produce a summary of everything that "
    "happened, emphasising the user's goals, the assistant's actions and "
    "findings, and any unresolved threads. Output ONLY the summary inside "
    "<summary>...</summary> XML tags. Do not attempt to answer any "
    "question from the user; this output is for internal compaction."
)

_SUMMARY_RE: re.Pattern[str] = re.compile(r"<summary>(.*?)</summary>", re.DOTALL | re.IGNORECASE)


def _extract_summary_text(raw: str) -> str:
    """Pull the ``<summary>...</summary>`` body out of the model's output.

    Falls back to the raw string (stripped) when the tags are absent.
    """
    match = _SUMMARY_RE.search(raw)
    if match is not None:
        return match.group(1).strip()
    return raw.strip()


@runtime_checkable
class SummarizationStrategy(Protocol):
    """Produce a compacted history for a thread whose context is too long.

    Strategies are the pluggable decision layer for context management: they choose
    which model to call, what to preserve verbatim, and what to fold into a synthetic
    summary. Built-in implementations live in :mod:`ai_functions.summarization`; user code
    may supply its own. A thread selects its strategy via
    :attr:`ThreadConfig.summarization_strategy`.
    """

    async def summarize(
        self,
        events: list[Event],
        ctx: ThreadContext,
        cycle_config: ThreadConfig,
    ) -> list[RenderableEvent]:
        """Compact ``events`` into a shorter synthetic history.

        Invoked by the thread when its accumulated event log exceeds the configured
        context bounds. The returned list is appended as the ``new_history`` payload
        of a :class:`ContextSummarizedEvent`; on the next reconstruction every event
        before that marker is dropped and the returned list is rendered in its place.

        Args:
            events: Full event log at the moment summarization was triggered.
            ctx: Per-cycle context of the thread requesting summarization.
            cycle_config: Resolved cycle config the parent thread was using when the
                overflow occurred.

        Returns:
            A synthetic sequence of renderable events representing the
            compacted history.

        Requires:
            ``events`` is sorted by append order (oldest first).

        Ensures: - The first event in the returned list (when present) has user-turn
        semantics on render. - Every ``toolUse`` block reachable through the returned
        events has a matching ``toolResult`` event later in the list, or will be
        healed by :func:`reconstruct_messages` (I10).

        Raises:
            SummarizationFailedError: No useful compaction could be produced.

        Concurrency:
            May perform I/O (model calls, runtime spawns). Must not emit events
            on the parent thread directly: the runtime is the sole emitter of the outer
            `ContextSummarizedEvent` tied to this summarization.
        """
        ...


class DefaultSummarizationStrategy:
    """Summarize a prefix via a model call, preserve a bounded tail.

    The built-in strategy. It chooses a tail of recent messages to keep verbatim (
    bounded below by ``preserve_min_messages`` / ``preserve_min_tokens`` and above by
    ``preserve_max_tokens``), advances the split to a legal tool-pair boundary (I10),
    and replaces everything before the split with a single synthetic user turn
    carrying a narrative summary produced by a helper thread.

    The helper-thread path is governed by ``summarize_by_forking``:

    - ``True`` — the helper inherits the parent's resolved cycle config (same model,
      system prompt, tools; tool execution denied via an internal hook).
      Requires ``cycle_config.structured_output is False``.
    - ``False`` — the helper uses a minimal dedicated config: parent's
      model only, no tools, a hard-coded summarization system prompt.
    - ``None`` — resolves to ``True`` iff ``cycle_config.structured_output is False``,
      else ``False``. Resolved per call, so one instance is reusable across threads with
      different output shapes.

    Args:
        summarize_by_forking: Fork policy (see above). ``None`` resolves lazily per call
            based on ``cycle_config``.
        preserve_min_messages: Floor on the number of tail messages kept verbatim.
        preserve_min_tokens: Floor on the number of tokens (estimated) kept verbatim.
        preserve_max_tokens: Ceiling on the number of tokens (estimated) kept verbatim.
            Messages that push the tail past this bound are summarized instead.

    Requires:
        - ``preserve_min_messages >= 1``.
        - ``preserve_min_tokens <= preserve_max_tokens``.

    Raises:
        ValueError: A ``Requires`` clause is violated.
    """

    __slots__ = (
        "_summarize_by_forking",
        "_preserve_min_messages",
        "_preserve_min_tokens",
        "_preserve_max_tokens",
    )

    _summarize_by_forking: bool | None
    _preserve_min_messages: int
    _preserve_min_tokens: int
    _preserve_max_tokens: int

    def __init__(
        self,
        *,
        summarize_by_forking: bool | None = None,
        preserve_min_messages: int = 6,
        preserve_min_tokens: int = 4_000,
        preserve_max_tokens: int = 40_000,
    ) -> None:
        if preserve_min_messages < 1:
            raise ValueError(f"preserve_min_messages must be >= 1, got {preserve_min_messages}")
        if preserve_min_tokens > preserve_max_tokens:
            raise ValueError(
                f"preserve_min_tokens ({preserve_min_tokens}) must be <= preserve_max_tokens ({preserve_max_tokens})"
            )
        self._summarize_by_forking = summarize_by_forking
        self._preserve_min_messages = preserve_min_messages
        self._preserve_min_tokens = preserve_min_tokens
        self._preserve_max_tokens = preserve_max_tokens

    async def summarize(
        self,
        events: list[Event],
        ctx: ThreadContext,
        cycle_config: ThreadConfig,
    ) -> list[RenderableEvent]:
        """Produce the compacted history per the class docstring algorithm.

        See :meth:`SummarizationStrategy.summarize` for the full protocol contract (
        ordering requirement on ``events``, rendering guarantees on the returned
        list, concurrency rules). This implementation additionally guarantees the
        shape below.

        Args:
            events: Parent thread's full event log at summarization time.
            ctx: Parent thread's per-cycle context.
            cycle_config: Parent thread's resolved cycle config.

        Returns:
            ``[MessageUserEvent(summary_text), *preserved_events]``.

        Raises:
            SummarizationFailedError: The history cannot be compacted at the  configured
                bounds, the helper thread failed, or ``summarize_by_forking=True`` was
                requested against a structured-output parent with a non-``str`` output.
        """
        # Resolve the fork flag. An explicit True against a structured-output
        # parent with a non-``str`` schema is a hard error: the fork would
        # inherit the parent's FinalAnswer schema and reject a plain summary.
        if self._summarize_by_forking is True and cycle_config.structured_output:
            raise SummarizationFailedError(
                function_name="",
                reason=(
                    "summarize_by_forking=True is incompatible with "
                    "structured_output=True: the forked summarizer would "
                    "inherit the parent's structured-output schema and could "
                    "not return a plain text summary. Either disable "
                    "structured_output on the parent, or set "
                    "summarize_by_forking=False (or None to auto-resolve)."
                ),
            )
        use_forking = (
            self._summarize_by_forking
            if self._summarize_by_forking is not None
            else (not cycle_config.structured_output)
        )

        # 1. Decide what to summarize vs preserve (pure function over events).
        to_summarize, preserved_events = self._split(events)

        # 2. Run the summarization cycle to produce the summary text.
        summary_text = await self._produce_summary_text(
            ctx=ctx,
            cycle_config=cycle_config,
            to_summarize=to_summarize,
            use_forking=use_forking,
        )

        # 3. Build the synthetic new history. The first event is the summary
        # carried as a user turn — ensures the rendered message sequence
        # starts with a user role. Preserved events follow verbatim.
        return [
            cast("RenderableEvent", MessageUserEvent(text=summary_text)),
            *preserved_events,
        ]

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _split(self, events: list[Event]) -> tuple[list[RenderableEvent], list[RenderableEvent]]:
        """Split events into ``(to_summarize, preserved_tail)``.

        The split is computed over the effective timeline that
        ``reconstruct_messages`` renders: the last ``ContextSummarizedEvent``'s
        ``new_history`` followed by the events after it, or the raw log when
        there is no summary yet. Both returned lists hold the renderable
        events of that timeline, before and after the split.
        """
        if not events:
            raise SummarizationFailedError(
                function_name="",
                reason="cannot summarize an empty event log",
            )

        # Build the *effective* renderable timeline: the last
        # ContextSummarizedEvent (if any) replaces every earlier event with its
        # ``new_history``, exactly as ``reconstruct_messages`` does. The
        # message-index → event mapping below MUST walk this effective list,
        # not the raw log — walking the raw log would count already-dropped
        # pre-summary events against ``split_idx``, placing the cut near the
        # start of the log and "preserving" nearly the entire history (the
        # tail would then never shrink across compaction passes).
        summary_idx: int | None = None
        for i in range(len(events) - 1, -1, -1):
            if isinstance(events[i], ContextSummarizedEvent):
                summary_idx = i
                break
        if summary_idx is None:
            effective_events: list[Event] = list(events)
        else:
            summary_event = events[summary_idx]
            assert isinstance(summary_event, ContextSummarizedEvent)
            effective_events = [*summary_event.new_history, *events[summary_idx + 1 :]]

        # Reconstruct the full message list so tail-sizing and tool-pair
        # adjustment share the same representation.
        all_messages = reconstruct_messages(events)
        n_messages = len(all_messages)

        preserved_token_estimate = 0
        preserved_count = 0
        split_idx = n_messages
        for i in range(n_messages - 1, -1, -1):
            msg_tokens = _estimate_message_tokens(all_messages[i])
            # Always keep the most-recent message, even if it alone exceeds
            # ``preserve_max_tokens``: an empty tail would hand the whole history
            # to the summarizer and could never shrink below its own input.
            # Keeping >=1 message makes the summarized prefix strictly smaller,
            # so the history shrinks monotonically; the ceiling governs the rest.
            if preserved_count >= 1 and preserved_token_estimate + msg_tokens > self._preserve_max_tokens:
                break
            preserved_token_estimate += msg_tokens
            preserved_count += 1
            split_idx = i
            if preserved_count >= self._preserve_min_messages and preserved_token_estimate >= self._preserve_min_tokens:
                break

        # Degenerate case: a single most-recent message larger than the
        # preserved-tail budget. No split helps — it must sit in either the tail
        # or the summarizer's input, and neither fits — so fail immediately
        # rather than burning the attempt budget on an ever-shrinking prefix.
        if preserved_token_estimate > self._preserve_max_tokens:
            raise SummarizationFailedError(
                function_name="",
                reason=(
                    f"the most recent message alone (~{preserved_token_estimate} estimated "
                    f"tokens) exceeds the preserved-tail budget ({self._preserve_max_tokens} "
                    "tokens); summarization cannot compact a single oversized message. "
                    "Reduce individual message / tool-output size, or raise "
                    "preserve_max_tokens."
                ),
            )

        split_idx = _adjust_split_point_for_tool_pairs(all_messages, split_idx)

        # Map the message-level split back to an event-level split over the
        # *effective* timeline, so message indices and event indices agree.
        summarize_prefix_events = _events_producing_prefix(effective_events, split_idx)
        if not summarize_prefix_events:
            raise SummarizationFailedError(
                function_name="",
                reason=(
                    "no events can be summarized at the configured "
                    "preservation bounds; the preserved tail already covers "
                    "the entire history"
                ),
            )

        # Both sides keep only renderable events: lifecycle, token usage, etc.
        # contribute nothing to the rendered history. The prefix is the exact
        # input the summarizer is seeded with (see ``_produce_summary_text``);
        # the preserved tail is every effective event after it
        # (``_events_producing_prefix`` returns a contiguous prefix of its input).
        to_summarize = [ev for ev in summarize_prefix_events if is_renderable_event(ev)]
        preserved: list[RenderableEvent] = [
            ev for ev in effective_events[len(summarize_prefix_events) :] if is_renderable_event(ev)
        ]

        return to_summarize, preserved

    async def _produce_summary_text(
        self,
        ctx: ThreadContext,
        cycle_config: ThreadConfig,
        to_summarize: list[RenderableEvent],
        use_forking: bool,
    ) -> str:
        """Spawn a summarizer helper seeded with ``to_summarize`` and return the ``<summary>`` text."""
        coordinator = ctx.coordinator

        if use_forking:
            summarizer_template = _build_fork_summarizer_template(cycle_config)
        else:
            summarizer_template = _build_dedicated_summarizer_template(cycle_config)

        try:
            # Spawn the helper seeded with exactly the events to summarize
            # (fresh ids, rewritten thread id). Seeding from the prefix rather
            # than copying the parent's raw log up to some event matters after
            # an earlier compaction: the prefix may end inside that summary's
            # ``new_history``, which no raw-log cut point reproduces, and the
            # raw log still holds every event the summary replaced. We rely on
            # the same worker hosting the parent (default worker selection in
            # spawn).
            child_handle = await coordinator.spawn(
                summarizer_template,
                seed_events=[*to_summarize],
                thread_name=f"summarize:{ctx.thread_id}",
                parent_id=ctx.thread_id,
            )
            try:
                raw = await child_handle.run()
            finally:
                # Always tear the helper down, even if the cycle raises —
                # otherwise a spawned-but-failed summarizer leaks on the
                # coordinator for the life of the session.
                try:
                    await child_handle.terminate_now()
                except Exception:
                    pass
        except SummarizationFailedError:
            raise
        except Exception as exc:
            raise SummarizationFailedError(
                function_name="",
                reason=f"summarization cycle raised: {exc!r}",
            ) from exc

        return _extract_summary_text(raw)


class ContextFitter:
    """Drive one invocation's summarization loop: fit history to the context budget.

    Runs a :class:`SummarizationStrategy` on both the proactive threshold check
    and the reactive post-overflow path, emitting a ``ContextSummarizedEvent``
    boundary for each compaction.

    One instance serves one ``invoke`` call. A shared attempt counter bounds
    total summarizations per invocation so a strategy that fails to shrink the
    history cannot loop forever. Do not reuse an instance across invocations:
    a long-lived counter would starve later cycles of their summarization budget.

    Args:
        strategy: The pluggable compaction strategy to run.
        function_name: Owning ``AIFunction`` name, for error attribution.
        max_attempts: Cap on summarizations per invocation (proactive +
            reactive combined).
    """

    __slots__ = ("_strategy", "_function_name", "_max_attempts", "_attempts")

    def __init__(
        self,
        strategy: SummarizationStrategy,
        function_name: str,
        max_attempts: int = _MAX_SUMMARIZATION_ATTEMPTS,
    ) -> None:
        self._strategy = strategy
        self._function_name = function_name
        self._max_attempts = max_attempts
        self._attempts = 0

    async def fit(self, ctx: ThreadContext, cycle_config: ThreadConfig) -> Messages:
        """Fetch the event log and return a message history under the threshold.

        Proactively compacts (possibly repeatedly, up to the attempt cap) while
        the estimated token count of the reconstructed history exceeds
        ``cycle_config.summarization_threshold``. With no threshold configured,
        this is a plain fetch-and-reconstruct.

        Returns:
            The reconstructed (possibly compacted) message history.
        """
        while True:
            events = await ctx.coordinator.get_events(ctx.thread_id)
            messages: Messages = reconstruct_messages(events)
            threshold = cycle_config.summarization_threshold
            if (
                cycle_config.summarization_enabled
                and threshold is not None
                and self._attempts < self._max_attempts
                and sum(_estimate_message_tokens(m) for m in messages) > threshold
            ):
                self._attempts += 1
                await self._summarize_and_emit(ctx, cycle_config, events)
                continue
            return messages

    async def compact_after_overflow(
        self,
        ctx: ThreadContext,
        cycle_config: ThreadConfig,
        exc: Exception,
    ) -> None:
        """Compact reactively after a ``ContextWindowOverflowException``.

        Re-fetches the event log so the compaction includes the user turns the
        failed model call had already appended.

        With ``summarization_enabled=False`` the overflow is not compacted: the
        original ``exc`` is re-raised unchanged so the thread fails loudly. This
        also keeps summarizer helper threads non-recursive, since their template
        sets the flag ``False``.

        Raises:
            ContextWindowOverflowException: ``summarization_enabled`` is
                ``False``; the original ``exc`` propagates unchanged.
            SummarizationFailedError: The attempt cap was already exhausted;
                chained to ``exc``.
        """
        if not cycle_config.summarization_enabled:
            raise exc
        if self._attempts >= self._max_attempts:
            raise SummarizationFailedError(
                function_name=self._function_name,
                reason=(f"Context window still overflowed after {self._max_attempts} summarization attempts: {exc}"),
            ) from exc
        self._attempts += 1
        fresh_events = await ctx.coordinator.get_events(ctx.thread_id)
        await self._summarize_and_emit(ctx, cycle_config, fresh_events)

    async def _summarize_and_emit(
        self,
        ctx: ThreadContext,
        cycle_config: ThreadConfig,
        events: list[Event],
    ) -> None:
        """Run the strategy over ``events`` and emit the boundary event.

        Wraps strategy failures in ``SummarizationFailedError`` and appends a
        ``ContextSummarizedEvent`` whose ``new_history`` replaces the
        summarized prefix on the next reconstruction (the I9
        cache-invalidation point).
        """
        try:
            new_history = await self._strategy.summarize(events, ctx, cycle_config)
        except SummarizationFailedError:
            raise
        except Exception as strategy_exc:
            raise SummarizationFailedError(
                function_name=self._function_name,
                reason=f"summarization strategy raised: {strategy_exc!r}",
            ) from strategy_exc
        ctx.on_event(ContextSummarizedEvent(new_history=new_history))


class SummarizationFailedError(AIFunctionError):
    """Summarization could not produce a usable compaction.

    Raised when every available strategy attempt fails to fit within the model's
    context window, or when no legal split point exists (for instance, a single
    preserved message is itself larger than the context limit). Unrecoverable by
    retry; callers must intervene (reset session, change config, shrink tool outputs).

    Args:
        function_name: Name of the ``AIFunction`` whose thread attempted summarization.
        reason: Short explanation of why summarization could not succeed.
    """

    def __init__(self, function_name: str, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Summarization failed: {reason}", function_name=function_name)


# ── Tool-denial hook used by the fork path ────────────────────────────────────


_SUMMARIZER_TOOL_DENIED_MESSAGE: str = (
    "Tool execution is disabled in summarization mode. Write the summary as text in your response instead."
)


class _DenyToolsHook(HookProvider):
    """Block tool execution during a summarization cycle."""

    def register_hooks(self, registry: HookRegistry, **kwargs: object) -> None:
        """Register a ``BeforeToolCallEvent`` callback that cancels the call."""
        del kwargs
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)

    def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        """Cancel the tool call; the model gets the message as an error tool result.

        ``cancel_tool`` is the field Strands lets hooks write to skip a tool.
        ``BeforeToolCallEvent`` has no writable ``result``.
        """
        event.cancel_tool = _SUMMARIZER_TOOL_DENIED_MESSAGE


# ── Template builders ─────────────────────────────────────────────────────────


def _summarizer_prompt_fn() -> str:
    """Prompt-function body for every summarizer template."""
    return _SUMMARIZE_REQUEST_TEXT


def _build_fork_summarizer_template(cycle_config: ThreadConfig) -> AIFunction[[], str]:
    """Build a summarizer template that inherits the parent's resolved cycle config."""
    from .ai_function import AIFunction

    deny_hook: HookProvider = _DenyToolsHook()
    existing_hooks = list(cycle_config.agent_kwargs.get("hooks") or [])
    merged_hooks: list[HookProvider] = [*existing_hooks, deny_hook]
    new_agent_kwargs = dict(cycle_config.agent_kwargs)
    new_agent_kwargs["hooks"] = merged_hooks
    new_agent_kwargs.pop("conversation_manager", None)
    new_agent_kwargs.pop("messages", None)
    new_agent_kwargs.pop("state", None)

    summarizer_config = dataclasses.replace(
        cycle_config,
        structured_output=False,
        post_conditions=(),
        config_hook=None,
        summarization_strategy=None,
        # The summarizer must never summarize itself: disabling context
        # management here makes an overflow inside the summarization cycle
        # propagate instead of recursively spawning another summarizer.
        summarization_enabled=False,
        summarization_threshold=None,
        agent_kwargs=cast("AgentKwargs", new_agent_kwargs),
        thread_name="summarize:fork",
    )
    return AIFunction(
        prompt_fn=_summarizer_prompt_fn,
        output_type=str,
        config=summarizer_config,
    )


def _build_dedicated_summarizer_template(cycle_config: ThreadConfig) -> AIFunction[[], str]:
    """Build a standalone summarizer with no tools and a minimal system prompt."""
    from .ai_function import AIFunction

    summarizer_config = ThreadConfig(
        model=cycle_config.model,
        system_prompt=_DEDICATED_SUMMARIZER_SYSTEM_PROMPT,
        tools=(),
        post_conditions=(),
        max_attempts=1,
        structured_output=False,
        agent_kwargs=AgentKwargs(),
        config_hook=None,
        summarization_strategy=None,
        # See the fork builder: a summarizer must not summarize itself.
        summarization_enabled=False,
        thread_name="summarize:dedicated",
    )
    return AIFunction(
        prompt_fn=_summarizer_prompt_fn,
        output_type=str,
        config=summarizer_config,
    )


# ── Token estimation + tool-pair adjustment + prefix extraction ───────────────


def _estimate_message_tokens(message: Message) -> int:
    """Approximate token cost of a single ``Message``."""
    content = message.get("content", [])
    chars = 0
    for block in content:
        block_d = cast("dict[str, object]", block)
        text = block_d.get("text")
        if isinstance(text, str):
            chars += len(text)
            continue
        tool_use = block_d.get("toolUse")
        if isinstance(tool_use, dict):
            tool_use_d = cast("dict[str, object]", tool_use)
            name = tool_use_d.get("name")
            if isinstance(name, str):
                chars += len(name)
            tool_input = tool_use_d.get("input")
            chars += _approx_json_chars(tool_input)
            continue
        tool_result = block_d.get("toolResult")
        if isinstance(tool_result, dict):
            tool_result_d = cast("dict[str, object]", tool_result)
            inner = tool_result_d.get("content", [])
            if isinstance(inner, list):
                for item in cast("list[object]", inner):
                    if isinstance(item, dict):
                        item_d = cast("dict[str, object]", item)
                        inner_text = item_d.get("text")
                        if isinstance(inner_text, str):
                            chars += len(inner_text)
                        elif "image" in item_d:
                            chars += 256
            continue
        reasoning = block_d.get("reasoningContent")
        if isinstance(reasoning, dict):
            reasoning_d = cast("dict[str, object]", reasoning)
            reasoning_text = reasoning_d.get("reasoningText")
            if isinstance(reasoning_text, dict):
                rt_d = cast("dict[str, object]", reasoning_text)
                rt = rt_d.get("text")
                if isinstance(rt, str):
                    chars += len(rt)
    framing = 8
    return max(1, int(chars / _CHARS_PER_TOKEN) + framing)


def _approx_json_chars(value: object) -> int:
    """Rough char count for a JSON-like value without importing ``json``."""
    if value is None:
        return 4
    if isinstance(value, str):
        return len(value) + 2
    if isinstance(value, bool):
        return 4
    if isinstance(value, (int, float)):
        return len(str(value))
    if isinstance(value, list):
        total = 2
        for item in cast("list[object]", value):
            total += _approx_json_chars(item) + 1
        return total
    if isinstance(value, dict):
        total = 2
        for k, v in cast("dict[object, object]", value).items():
            total += _approx_json_chars(k) + _approx_json_chars(v) + 2
        return total
    return len(str(value))


def _adjust_split_point_for_tool_pairs(messages: list[Message], split_idx: int) -> int:
    """Advance ``split_idx`` forward to a legal tool-pair boundary."""
    n = len(messages)
    if split_idx >= n:
        return n

    idx = split_idx
    while idx < n:
        content = messages[idx].get("content", [])
        has_tool_result = any("toolResult" in cast("dict[str, object]", b) for b in content)
        if has_tool_result:
            idx += 1
            continue
        has_tool_use = any("toolUse" in cast("dict[str, object]", b) for b in content)
        if has_tool_use:
            if idx + 1 < n:
                next_content = messages[idx + 1].get("content", [])
                next_has_result = any("toolResult" in cast("dict[str, object]", b) for b in next_content)
                if next_has_result:
                    return idx
            idx += 1
            continue
        return idx
    return n


def _events_producing_prefix(events: list[Event], split_idx: int) -> list[Event]:
    """Return the events whose reconstruction produces ``messages[:split_idx]``."""
    if split_idx <= 0:
        return []
    produced = 0
    pending_tool_group_open = False
    out: list[Event] = []
    for event in events:
        if isinstance(event, MessageUserEvent):
            if pending_tool_group_open:
                produced += 1
                pending_tool_group_open = False
            if produced >= split_idx:
                break
            out.append(event)
            produced += 1
        elif isinstance(event, MessageAssistantCompleteEvent):
            if pending_tool_group_open:
                produced += 1
                pending_tool_group_open = False
            if produced >= split_idx:
                break
            out.append(event)
            produced += 1
        elif isinstance(event, ToolResultEvent):
            if produced >= split_idx:
                break
            out.append(event)
            pending_tool_group_open = True
        else:
            if produced >= split_idx:
                break
            out.append(event)
    return out
