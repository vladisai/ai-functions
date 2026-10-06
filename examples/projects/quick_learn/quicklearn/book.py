"""The book for one reader: the vault, the reader folder, the pages, the rewrites and the chat.

Every page the outline links is adaptive: a chapter folder with its chapter.md, or a one-file page
like lectures/lecture_1.md, each a ChapterState by its key (see vault/chapter.py).

The app holds one Book. Reset stops it, empties the reader folder and starts a new one.
Every reader action goes through here, so the order of the steps is in one place:

| Action | Facts saved by the app | Note step | Rewrites |
|---|---|---|---|
| Text input | answers.json, the answer under "Inputs" | waits for it | every section, if the note step says so |
| Quiz submit | answers.json, the score under "Quiz results" | in the background | at once, by the adapter's rules |
| Chat | chat.json | in the background, after the answer | through rewrite_section |
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from quicklearn.agents import memory
from quicklearn.agents.adapter import Adapter, Plan, format_answers, quiz_summary
from quicklearn.agents.chat import ChatAgent
from quicklearn.chapter.state import ChapterState
from quicklearn.core.quiz import Quiz
from quicklearn.core.text_input import TextInput, TextInputState
from quicklearn.reader.store import ReaderStore
from quicklearn.vault.chapter import page_path
from quicklearn.vault.outline import OutlineEntry, parse_outline

log = logging.getLogger(__name__)

OUTLINE_FILE = "outline.md"


class Book:
    def __init__(self, vault: Path, reader: str, demo_readers: Path | None = None) -> None:
        self.vault = vault
        self.store = ReaderStore(vault, reader, demo_readers)
        self.adapter = Adapter(self.store)
        self.chat = ChatAgent(self.store, self.adapter)
        self.chat.on_exchange = lambda chapter, exchange: self._note_later(chapter, exchange)
        self._chapters: dict[str, ChapterState] = {}
        self._chapters_lock = threading.Lock()
        self._notes_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ql-notes")
        self._notes_running = 0
        log.info("Book for reader %r in %s", reader, self.store.dir)

    # -- Pages --

    def outline(self) -> list[OutlineEntry]:
        return parse_outline(self.vault / OUTLINE_FILE)

    def pages(self) -> dict[str, OutlineEntry]:
        """{route: outline entry} for every page the outline links."""
        return {e.link: e for e in self.outline() if e.kind == "chapter" and e.link}

    def resolve_link(self, path: str) -> str | None:
        """The route of a wikilink's target, if the outline has a page for it."""
        for entry in self.pages().values():
            if entry.target == path or entry.target == f"{path}/chapter":
                return entry.link
        return None

    def chapter(self, key: str) -> ChapterState:
        """The page of `key`, e.g. book/probability or lectures/lecture_1, loaded on first use. An
        edit to the page file, e.g. a new section, reloads it once no rewrite is writing into it."""
        with self._chapters_lock:
            chapter = self._chapters.get(key)
            if chapter is not None and chapter.is_outdated() and self.adapter.active_in(key) == 0:
                log.info("%s: the page file changed, reloading", key)
                chapter = None
            if chapter is None:
                page = page_path(self.vault, key)
                assert page.is_file(), f"no page for {key} in {self.vault}"
                chapter = ChapterState(page, self.vault, self.store, self.resolve_link)
                self._chapters[key] = chapter
            return chapter

    def running(self) -> int:
        """Rewrites, chat answers and note steps in flight, for the header indicator."""
        return self.adapter.active_tasks() + self.chat.busy + self._notes_running

    def stop(self) -> None:
        self.adapter.stop()
        self.chat.close()
        self._notes_pool.shutdown(wait=False, cancel_futures=True)

    # -- Note steps --

    def _note_later(self, chapter: ChapterState, event: str) -> None:
        with self._chapters_lock:
            self._notes_running += 1
        self._notes_pool.submit(self._note_step, chapter, event).add_done_callback(_log_failure)

    def _note_step(self, chapter: ChapterState, event: str) -> memory.NoteResult:
        try:
            return memory.note_step(self.store, chapter, event)
        finally:
            with self._chapters_lock:
                self._notes_running -= 1

    # -- Reader actions --

    def first_visit(self, chapter: ChapterState) -> None:
        """Write the sections that have no text yet, in the vault or for the reader."""
        tasks = self.adapter.plan_for_empty(chapter)
        if tasks and self.adapter.active_in(chapter.key) == 0:
            self.adapter.start(chapter, tasks)

    def submit_text_input(self, chapter: ChapterState, text_input: TextInput, answer: str) -> bool:
        """Save the answer, let the note step decide, and rewrite the chapter if it says so.
        Blocks for the note step, about 2 s. True if the sections are being rewritten."""
        text_input.answer = answer.strip()
        text_input.state = TextInputState.DONE
        chapter.save_answers()
        self.store.record_input(chapter.key, text_input.title, text_input.prompt, text_input.answer)
        event = f'The reader answered the question "{text_input.title}":\n\n{text_input.answer}'
        with self._chapters_lock:
            self._notes_running += 1
        result = self._note_step(chapter, event)
        tasks = []
        if result.rewrite:
            reason = (
                f'The reader just answered "{text_input.title}" with: {text_input.answer}\n\n'
                f"The book's reason to rewrite: {result.reason}"
            )
            tasks = self.adapter.plan_for_all(chapter, reason)
            self.adapter.start(chapter, tasks)
        self.chat.note_event(
            f'The reader answered "{text_input.title}": {text_input.answer}\n'
            + (f"Rewriting {[t.section for t in tasks]} for them." if tasks else "No rewrite.")
        )
        return bool(tasks)

    def skip_text_input(self, chapter: ChapterState, text_input: TextInput) -> None:
        text_input.state = TextInputState.SKIPPED
        chapter.save_answers()
        log.info("%s: text input %s skipped", chapter.key, text_input.id)

    def submit_quiz(self, chapter: ChapterState, quiz: Quiz) -> Plan:
        """Start the rewrites at once, save the result, and run the note step alongside the feedback."""
        plan = self.adapter.plan_for_quiz(chapter, quiz)
        self.adapter.start(chapter, plan.tasks)
        chapter.save_answers()
        name, _, part = quiz.id.rpartition(".")
        title = f"{chapter.doc.sections[name].title}, {'prior knowledge' if part == 'prior' else 'after reading'}"
        self.store.record_quiz(chapter.key, title, quiz_summary(quiz))
        self._note_later(chapter, f"The reader submitted the quiz {title}:\n\n{format_answers(quiz)}")
        log.info("%s: quiz %s submitted, rewriting %s", chapter.key, quiz.id, [t.section for t in plan.tasks])
        return plan

    def quiz_feedback(self, chapter: ChapterState, quiz: Quiz, plan: Plan) -> str:
        feedback = self.adapter.feedback(chapter, quiz, plan.next_step)
        self.chat.add_assistant_message(feedback)
        self.chat.note_event(
            f"The reader submitted quiz {quiz.id}:\n\n{format_answers(quiz)}\n\nFeedback they were shown: {feedback}"
        )
        return feedback

    def skip_quiz(self, chapter: ChapterState, quiz: Quiz) -> None:
        chapter.save_answers()
        self.chat.note_event(f"The reader skipped quiz {quiz.id}.")

    def personalize_again(self, chapter: ChapterState) -> list[str]:
        """Rewrite the sections whose vault text changed since they were rewritten. Returns their names."""
        tasks = self.adapter.plan_for_stale(chapter)
        self.adapter.start(chapter, tasks)
        return [t.section for t in tasks]

    def wipe(self) -> None:
        """Reset: stop everything and empty the reader folder. The Book is unusable after this."""
        self.stop()
        # A note step already running ends in a few seconds. Waiting for it keeps it from writing
        # its notes into the emptied folder.
        self._notes_pool.shutdown(wait=True)
        self.store.wipe()


def _log_failure(future: Future) -> None:
    if not future.cancelled() and future.exception() is not None:
        log.error("Note step failed", exc_info=future.exception())
