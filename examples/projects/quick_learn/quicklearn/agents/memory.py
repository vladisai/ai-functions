"""The note step: after each text input, quiz and chat exchange, the book decides what to remember.

One fast model call gets the event, reader.md and the chapter's notes.md, and returns the new
"About the reader" part of reader.md, the new "Notes" part of notes.md, and whether the chapter's
sections should be rewritten. The model rewrites both parts whole, so they stay short. The facts,
the text input answers and quiz results, never depend on the model: the app appends them to
"Inputs" and "Quiz results" before the call.

Sonnet 5.5 on Bedrock takes neither a forced tool choice nor a JSON output format, so the reply
is tagged text.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from quicklearn import llm
from quicklearn.agents.adapter import load_prompt, reader_context

if TYPE_CHECKING:
    from quicklearn.chapter.state import ChapterState
    from quicklearn.reader.store import ReaderStore

log = logging.getLogger(__name__)


@dataclass
class NoteResult:
    rewrite: bool
    reason: str


def _tag(text: str, name: str) -> str | None:
    match = re.search(rf"<{name}>(.*?)</{name}>", text, re.DOTALL)
    return match.group(1).strip() if match else None


def parse_reply(reply: str) -> tuple[str | None, str | None, bool, str]:
    """(about, notes, rewrite, reason); a part the reply leaves out is None and stays as it was."""
    about = _tag(reply, "about_reader")
    notes = _tag(reply, "notes")
    rewrite = (_tag(reply, "rewrite") or "").lower().startswith("y")
    return about, notes, rewrite, _tag(reply, "reason") or ""


def note_step(store: ReaderStore, chapter: ChapterState, event: str) -> NoteResult:
    """Update reader.md and the chapter's notes.md from one event. Runs under the store's lock,
    so two note steps never overwrite each other's notes."""
    with store.lock:
        t0 = time.monotonic()
        request = (
            f"{reader_context(store, chapter)}\n\n"
            f"<chapter>\n{chapter.title}\n\n{chapter.section_list()}\n</chapter>\n\n"
            f"<event>\n{event.strip()}\n</event>"
        )
        reply = llm.complete(load_prompt("memory"), request, max_tokens=1500)
        about, notes, rewrite, reason = parse_reply(reply)
        if about is not None:
            store.set_about("" if about == "Nothing yet." else about)
        if notes is not None:
            store.set_notes_part(chapter.key, "Notes", "" if notes == "Nothing yet." else notes)
        log.info("Note step for %s in %.1fs: rewrite=%s (%s)", chapter.key, time.monotonic() - t0, rewrite, reason)
        return NoteResult(rewrite, reason)
