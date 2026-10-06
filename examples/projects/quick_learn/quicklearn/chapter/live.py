"""Live sections: each block of a chapter page watches its file and tells the page when it changes.

A rewrite streams into the section's file in the reader folder, and the app's poller calls
LiveMaterial.poll_all() every two seconds. A section whose file changed updates its Section in
place and fires the callbacks of every open page, which update just that section on screen.
Edits to the vault, e.g. in Obsidian while the app runs, show up the same way.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from quicklearn.core.material import Section, Snapshot
from quicklearn.core.quiz import Quiz, QuizQuestion, QuizState

if TYPE_CHECKING:
    from quicklearn.chapter.state import ChapterState

log = logging.getLogger(__name__)


def _mtime(path: Path) -> float | None:
    return path.stat().st_mtime if path.exists() else None


class LiveSection:
    """A block of the page with its Section, and the callbacks of the pages that show it."""

    def __init__(self, section: Section) -> None:
        self.section = section
        # One callback per open page, so every browser tab sees the change
        self._on_change: list[Callable[[LiveSection], None]] = []

    def bind(self, callback: Callable[[LiveSection], None]) -> None:
        self._on_change.append(callback)

    def unbind(self, callback: Callable[[LiveSection], None]) -> None:
        self._on_change.remove(callback)

    def _notify(self) -> None:
        for callback in list(self._on_change):
            callback(self)

    def poll(self) -> bool:
        """Check the file on disk. If it changed, update the section and notify. True if it changed."""
        return False


class ContentLive(LiveSection):
    """A section: its rewritten text in the current version, or else the vault file."""

    def __init__(self, section: Section, chapter: ChapterState, name: str) -> None:
        super().__init__(section)
        self.chapter = chapter
        self.name = name
        self._seen = self._stamp()

    def _stamp(self) -> tuple[Path, float | None]:
        path = self.chapter.section_path(self.name)
        return path, _mtime(path)

    def poll(self) -> bool:
        stamp = self._stamp()
        if stamp == self._seen:
            return False
        self._seen = stamp
        content = self.chapter.section_text(self.name)
        if content == self.section.content:
            return False
        self.section.content = content
        log.info("%s: section %s changed on disk", self.chapter.key, self.name)
        self._notify()
        return True


class QuizLive(LiveSection):
    """A quiz: the part of `<name>.quiz.md` from the current version, or else from the vault.

    New questions reset the reader's answers, so a new learned quiz shows fresh.
    """

    def __init__(self, section: Section, chapter: ChapterState, name: str, part: str, quiz: Quiz) -> None:
        super().__init__(section)
        self.chapter = chapter
        self.name = name
        self.part = part
        self.quiz = quiz
        self._seen = self._stamp()

    def _stamp(self) -> tuple:
        return tuple((path, _mtime(path)) for path in self.chapter.quiz_paths(self.name))

    def poll(self) -> bool:
        stamp = self._stamp()
        if stamp == self._seen:
            return False
        self._seen = stamp
        questions = self.chapter.quiz_questions(self.name, self.part)
        if fingerprint(questions) == fingerprint(self.quiz.questions):
            return False
        self.quiz.questions = questions
        self.quiz.answers = {}
        self.quiz.state = QuizState.ACTIVE
        self.chapter.save_answers()
        log.info("%s: quiz %s has %d new questions", self.chapter.key, self.quiz.id, len(questions))
        self._notify()
        return True


def fingerprint(questions: list[QuizQuestion]) -> str:
    """Identity of a quiz: its question texts and options."""
    import hashlib

    raw = repr([(q.text, tuple(q.options or []), q.correct_answer) for q in questions])
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


class LiveMaterial:
    """The chapter's Material and quizzes, with one LiveSection per block and the version stack."""

    def __init__(self, chapter: ChapterState, live_sections: list[LiveSection]) -> None:
        self.chapter = chapter
        self.material = chapter.material
        self.quizzes = chapter.quizzes
        self.live_sections = live_sections

    def poll_all(self) -> set[str]:
        """Poll every section and return the ids of those that changed. New versions on disk
        join the version stack, so the version bar shows them without a reload."""
        self.chapter.sync_version_stack()
        return {ls.section.id for ls in self.live_sections if ls.poll()}

    @property
    def by_id(self) -> dict[str, LiveSection]:
        return {ls.section.id: ls for ls in self.live_sections}


__all__ = ["ContentLive", "LiveMaterial", "LiveSection", "QuizLive", "Snapshot", "fingerprint"]
