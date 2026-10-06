"""Shared fixtures: small vaults in tmp_path, a copy of the shipped vault, and a fake model.

No test talks to a model: `quicklearn.llm.client` fails every test that reaches it, and tests that
need replies use `fake_llm`, which stands in for llm.stream_text and llm.complete.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from quicklearn import llm
from quicklearn.agents.adapter import load_prompt
from quicklearn.chapter.state import ChapterState
from quicklearn.reader.store import PERSONAL_DIR, ReaderStore

REPO = Path(__file__).parent.parent


def write(root: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def words(word: str, n: int) -> str:
    return " ".join([word] * n) + "\n"


QUIZ = "# Prior\n\n1. Pick one\n   - [ ] no\n   - [x] yes\n\n# Learned\n"

CHAPTER = """---
title: Small Chapter
---

# Small Chapter

*By the author*

# Welcome

Fixed text that links [[beta]], [[page|a page]] and [[nowhere]].

_TEXT_INPUT_: About you
Tell us about yourself.

![[alpha]]

![[beta]]

# Symbols

| a | b |
"""

# A chapter with two sections of 100 words each, a text input, and fixed text around them
SMALL_VAULT = {
    "outline.md": "# Book\n\n- [[ch/chapter|Small Chapter]]\n- [[page|A Page]]\n- Not written yet\n",
    "page.md": "# A Page\n\nBack to [[ch/chapter|the chapter]].\n",
    "ch/chapter.md": CHAPTER,
    "ch/agent.md": "Hints for the rewrites.\n",
    "ch/alpha.md": "---\ntopics: [first topic, second topic]\n---\n\n# Alpha\n\n" + words("alpha", 100),
    "ch/alpha.quiz.md": QUIZ,
    "ch/beta.md": "---\ntopics: third topic\n---\n\n# Beta\n\n" + words("beta", 100),
    "ch/beta.quiz.md": QUIZ,
}


@pytest.fixture
def make_vault(tmp_path: Path):
    """Write a vault from {path: text} into tmp_path/vault."""
    return lambda files: write(tmp_path / "vault", files)


@pytest.fixture
def small_vault(make_vault) -> Path:
    return make_vault(SMALL_VAULT)


@pytest.fixture
def store(small_vault: Path) -> ReaderStore:
    return ReaderStore(small_vault, "tester")


@pytest.fixture
def chapter(small_vault: Path, store: ReaderStore) -> ChapterState:
    return ChapterState(small_vault / "ch" / "chapter.md", small_vault, store)


@pytest.fixture
def shipped_vault(tmp_path: Path) -> Path:
    """A copy of content/ without the reader folders."""
    vault = tmp_path / "content"
    shutil.copytree(REPO / "content", vault, ignore=shutil.ignore_patterns(PERSONAL_DIR))
    return vault


def _no_client():
    raise AssertionError("A test reached the model; use the fake_llm fixture")


@pytest.fixture(autouse=True)
def no_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "client", _no_client)


class FakeLLM:
    """Stands in for llm.stream_text and llm.complete. Replies by prompt name, and records each call.

    A reply is a string, or a list of chunks to stream. A chunk that is a callable runs between
    chunks instead of being streamed, e.g. to wait on an event or look at a half-written file.
    """

    def __init__(self) -> None:
        self.prompts = {name: load_prompt(name) for name in ("rewrite", "learned_quiz", "feedback", "memory")}
        self.replies: dict[str, str | list] = {
            "rewrite": ["New text.\n\n", "More text."],
            "learned_quiz": "1. A new question\n   - [x] right\n   - [ ] wrong\n",
            "feedback": "Well done.",
            "memory": "<rewrite>no</rewrite><reason>Nothing new.</reason>",
        }
        self.calls: list[tuple[str, str]] = []  # (prompt name, request)

    def requests(self, name: str) -> list[str]:
        return [request for prompt, request in self.calls if prompt == name]

    def stream_text(self, system, request, max_tokens, should_stop=None, config=None):
        name = next(n for n, p in self.prompts.items() if p == system)
        self.calls.append((name, request))
        reply = self.replies[name]
        for chunk in [reply] if isinstance(reply, str) else reply:
            if callable(chunk):
                chunk()
                continue
            if should_stop is not None and should_stop():
                raise llm.Stopped
            yield chunk

    def complete(self, system, request, max_tokens, config=None) -> str:
        return "".join(self.stream_text(system, request, max_tokens))


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> FakeLLM:
    fake = FakeLLM()
    monkeypatch.setattr(llm, "stream_text", fake.stream_text)
    monkeypatch.setattr(llm, "complete", fake.complete)
    return fake
