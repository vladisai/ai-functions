"""Rewrites: Python picks what to rewrite, and one streamed model call writes each section.

The plan is a few rules over the page's sections and quizzes, the same for every section, embedded
or inline, of a chapter folder or a one-file page. A question's tags (see quiz_md) name the
sections it is about; a missed untagged question of the page's own quiz only goes to notes.md.
Each rewrite streams into the section's file in the current version folder, and the page's poller
shows the partial text, so the page starts changing seconds after a submit. Every request carries
what the book knows about the reader, reader.md and the chapter's notes.md, so a rewrite of
Expectation knows what the reader got wrong in Random Variables.

| Reader action | What is rewritten |
|---|---|
| Prior quiz with gaps | the section, around what they missed, and a learned quiz after it |
| Prior quiz all right | the section, condensed, unless it is already compact |
| Page prior with gaps | each section tagged on a missed question, around what was missed, in parallel; no quiz |
| Page prior all right | nothing |
| Learned quiz with gaps | the tagged sections of the missed questions (its own when untagged), then a fresh |
| | learned quiz in the same slot on all the sections it covers |
| Text input | every section, when the note step says the answer calls for it |
| Chat | the sections the chat agent names through rewrite_section |
| Chat, add_quiz | no text, only a prior or learned quiz for the section the chat agent names |
| Personalize again | the rewritten sections whose vault text changed since |
| First visit | the sections that have no text yet |
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from quicklearn import llm
from quicklearn.core.quiz import Quiz
from quicklearn.vault.chapter import QUIZ_SUFFIX
from quicklearn.vault.quiz_md import QuizFile, format_quiz_file, parse_quiz

if TYPE_CHECKING:
    from quicklearn.chapter.state import ChapterState
    from quicklearn.reader.store import ReaderStore

log = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_FLUSH_SECONDS = 1.0
WRITING_MARK = "\n\n*Rewriting this section for you…*\n"
_DEFAULT_QUIZ_QUESTIONS = 4


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


QUIZ_PARTS = ("prior", "learned")


@dataclass
class Task:
    """Rewrite one section, then optionally write a new quiz before or after it."""

    section: str  # the section's name, e.g. "random-variables"
    reason: str  # what the reader did, e.g. their quiz answers
    quiz: str = ""  # "prior" or "learned": also write this quiz of the section
    from_vault: bool = False  # start from the vault's text instead of the reader's current one
    rewrite: bool = True  # False writes only the quiz, from the section's current text
    # The sections the quiz is on, when more than its own: it waits for their rewrites in the same batch
    covers: list[str] = field(default_factory=list)


@dataclass
class Plan:
    """What a quiz submit triggers, and how the feedback describes it."""

    next_step: str
    tasks: list[Task] = field(default_factory=list)


def has_gaps(quiz: Quiz) -> bool:
    """True if any question is unanswered or answered wrong."""
    return any(quiz.check_answer(i) is not True for i in range(len(quiz.questions)))


def missed(quiz: Quiz) -> list[int]:
    """The questions answered wrong or not at all."""
    return [i for i in range(len(quiz.questions)) if quiz.check_answer(i) is not True]


def format_answers(quiz: Quiz, indices: list[int] | None = None) -> str:
    """Every question, or those at `indices`, with its options, the reader's answer and the correct answer."""
    blocks = []
    for idx, q in enumerate(quiz.questions):
        if indices is not None and idx not in indices:
            continue
        status = {True: "correct", False: "WRONG", None: "not graded"}[quiz.check_answer(idx)]
        if idx not in quiz.answers:
            status = "unanswered"
        lines = [f"Q{idx + 1} ({status}): {q.text}"]
        lines += [f"  {letter}) {opt}" for letter, opt in zip("abcdefghij", q.options or [], strict=False)]
        lines.append(f"  Reader answered: {quiz.answers.get(idx, '-')}")
        lines.append(f"  Correct answer: {q.correct_answer}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def quiz_summary(quiz: Quiz) -> str:
    """One line for notes.md, e.g. "3 of 4 right. Missed: Q4 Analyze these statements about independence…." """
    graded = [i for i in range(len(quiz.questions)) if quiz.check_answer(i) is not None]
    right = [i for i in graded if quiz.check_answer(i)]
    missed = [i for i in range(len(quiz.questions)) if quiz.check_answer(i) is not True]
    text = f"{len(right)} of {len(quiz.questions)} right."
    if missed:
        text += " Missed: " + "; ".join(
            f"Q{i + 1} {_short(quiz.questions[i].text)}" for i in missed
        ) + "."
    return text


def _short(text: str, words: int = 12) -> str:
    parts = text.split()
    return " ".join(parts[:words]) + ("…" if len(parts) > words else "")


def reader_context(store: ReaderStore, chapter: ChapterState) -> str:
    """What the book knows about the reader, for every request in this chapter."""
    return (
        f"<reader>\n{store.reader_md().strip()}\n</reader>\n\n"
        f"<chapter_notes>\n{store.notes_md(chapter.key).strip()}\n</chapter_notes>"
    )


class Adapter:
    """Runs rewrite tasks on a thread pool, streaming each one into its file."""

    def __init__(self, store: ReaderStore) -> None:
        self.store = store
        self._prompts = {name: load_prompt(name) for name in ("rewrite", "learned_quiz", "feedback")}
        self._pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ql-adapt")
        # Guards _active. A chapter opens a new version only when no task is writing into the current one.
        self._lock = threading.Lock()
        self._active: dict[str, int] = defaultdict(int)
        # Tasks for the same section run in order, so the second one rewrites the first one's result.
        self._section_locks: dict[tuple[str, str], threading.Lock] = defaultdict(threading.Lock)
        self._stopped = threading.Event()

    def active_tasks(self) -> int:
        return sum(self._active.values())

    def active_in(self, key: str) -> int:
        return self._active[key]

    def stop(self) -> None:
        """End every running task before its next write, so a reset starts from clean files."""
        self._stopped.set()
        self._pool.shutdown(wait=False, cancel_futures=True)

    # -- Plans --

    def plan_for_quiz(self, chapter: ChapterState, quiz: Quiz) -> Plan:
        name, _, part = quiz.id.rpartition(".")
        answers = format_answers(quiz)
        names = chapter.section_names
        page = chapter.is_page_quiz(quiz)
        if part == "prior" and page:
            return self._plan_for_background(chapter, quiz)
        if part == "prior":
            if not has_gaps(quiz) and chapter.is_compact(name):
                return Plan("The section stays a compact reference, since you know this already.")
            if not has_gaps(quiz):
                reason = f"The reader answered every question of the prior-knowledge quiz correctly:\n\n{answers}"
                return Plan("The section below is being condensed, since you know this already.", [Task(name, reason)])
            reason = f"The reader took the prior-knowledge quiz placed before this section:\n\n{answers}"
            return Plan(
                "The section below is being rewritten around what you missed, "
                "and a short quiz to check it will appear after it.",
                [Task(name, reason, quiz="learned")],
            )
        if part == "learned":
            if not has_gaps(quiz):
                if page:
                    return Plan("That completes the chapter.")
                # The chapter is done when no later section has a quiz, e.g. only a table of symbols is left
                later = names[names.index(name) + 1:]
                if any(chapter.quizzes[f"{n}.{p}"].questions for n in later for p in QUIZ_PARTS):
                    return Plan("You are ready for the next section.")
                end = chapter.quizzes.get(f"{chapter.doc.stem}.learned")
                if end is not None and chapter.is_page_quiz(end) and end.questions:
                    return Plan("You are ready for the check at the end of the page.")
                return Plan("That completes the chapter.")
            return self._plan_for_learned_gaps(chapter, quiz)
        return Plan("")

    @staticmethod
    def _plan_for_background(chapter: ChapterState, quiz: Quiz) -> Plan:
        """The page's prior: rewrite each section a missed question is tagged with, and write no quiz."""
        if not has_gaps(quiz):
            return Plan("The page stays as it is, since you have the background already.")
        about = chapter.question_sections(quiz)
        wrong = missed(quiz)
        targets = [n for n in chapter.section_names if any(n in about[i] for i in wrong)]
        if not targets:
            return Plan("The book notes what you missed, and the page stays as it is.")
        tasks = []
        for name in targets:
            mine = [i for i in range(len(quiz.questions)) if name in about[i]]
            reason = (
                "The reader took the background check at the start of the page. These of its questions are "
                f"about this section, and some went wrong. Rewrite it around what they missed:\n\n"
                f"{format_answers(quiz, mine)}"
            )
            tasks.append(Task(name, reason))
        return Plan(f"{_sections_phrase(chapter, targets)} rewritten around what you missed.", tasks)

    @staticmethod
    def _plan_for_learned_gaps(chapter: ChapterState, quiz: Quiz) -> Plan:
        """Rewrite the sections of the missed questions, then write a fresh quiz into the same slot."""
        name = quiz.id.rpartition(".")[0]
        page = chapter.is_page_quiz(quiz)
        # An untagged question of a section's quiz is about that section, of the page's quiz about none
        about = [tags or ([] if page else [name]) for tags in chapter.question_sections(quiz)]
        wrong = missed(quiz)
        targets = [n for n in chapter.section_names if any(n in about[i] for i in wrong)]
        covers = [n for n in chapter.section_names if any(n in tags for tags in about)]
        answers = format_answers(quiz)
        if not targets:
            return Plan("The book notes what you missed.")
        if targets == covers == [name]:
            reason = f"The reader read this section, then took the quiz after it:\n\n{answers}"
            return Plan(
                "The section is being rewritten around these mistakes, with a fresh quiz after it.",
                [Task(name, reason, quiz="learned")],
            )
        tasks = []
        for target in targets:
            mine = [i for i in range(len(quiz.questions)) if target in about[i]]
            reason = (
                "The reader read this section, then took a quiz on it and the sections around it. These of its "
                f"questions are about this section, and some went wrong:\n\n{format_answers(quiz, mine)}"
            )
            tasks.append(Task(target, reason))
        reason = (
            "The reader took the quiz on these sections, and the sections with mistakes were just rewritten "
            f"around them. Their answers:\n\n{answers}"
        )
        tasks.append(Task(name, reason, quiz="learned", rewrite=False, covers=covers))
        return Plan(
            f"{_sections_phrase(chapter, targets)} rewritten around these mistakes, with a fresh quiz after them.",
            tasks,
        )

    @staticmethod
    def plan_for_all(chapter: ChapterState, reason: str) -> list[Task]:
        return [Task(name, reason) for name in chapter.section_names]

    @staticmethod
    def plan_for_stale(chapter: ChapterState) -> list[Task]:
        reason = (
            "The author updated this section since it was last rewritten for the reader. The current "
            "text below is the author's new version. Rewrite it for the reader, as the earlier "
            "rewrites did, using what the book knows about them."
        )
        return [Task(name, reason, from_vault=True) for name in chapter.stale_sections()]

    @staticmethod
    def plan_for_empty(chapter: ChapterState) -> list[Task]:
        reason = "The section has no text yet. Write it for the reader from its topics."
        return [Task(name, reason) for name in chapter.empty_sections()]

    # -- Running --

    def start(self, chapter: ChapterState, tasks: list[Task]) -> None:
        """Run tasks in the background. Opens a new version unless tasks are still writing."""
        if not tasks:
            return
        with self._lock:
            if self._active[chapter.key] == 0:
                chapter.new_version()
            self._active[chapter.key] += len(tasks)
        version_dir = chapter.version_dir
        log.info("%s: rewriting %s in %s", chapter.key, [t.section for t in tasks], version_dir.name)
        # A quiz on several sections waits for their rewrites. They were submitted first, so no wait deadlocks
        futures: dict[str, Future] = {}
        for task in tasks:
            deps = [futures[name] for name in task.covers if name in futures]
            future = self._pool.submit(self._run, chapter, task, version_dir, deps)
            future.add_done_callback(_log_failure)
            if task.rewrite:
                futures[task.section] = future

    def feedback(self, chapter: ChapterState, quiz: Quiz, next_step: str) -> str:
        """A few sentences on the reader's answers, ending with what the book does next."""
        request = (
            f"{reader_context(self.store, chapter)}\n\nQuiz answers:\n\n{format_answers(quiz)}\n\n"
            f"What the book does next: {next_step}"
        )
        return llm.complete(self._prompts["feedback"], request, max_tokens=600).strip()

    def _run(self, chapter: ChapterState, task: Task, version_dir: Path, deps: list[Future] | None = None) -> None:
        try:
            wait(deps or [])
            if self._stopped.is_set():
                raise llm.Stopped
            with self._section_locks[(chapter.key, task.section)]:
                t0 = time.monotonic()
                if task.rewrite:
                    text = self._rewrite(chapter, task, version_dir)
                    log.info("Rewrote %s in %.1fs (%d words)", task.section, time.monotonic() - t0, len(text.split()))
                else:
                    # A quiz on several sections reads each of theirs, and the page's own quiz has no text
                    text = "" if task.covers else chapter.section_text(task.section, version_dir)
                if task.quiz:
                    t0 = time.monotonic()
                    self._write_quiz(chapter, task, version_dir, text)
                    log.info("Wrote the %s quiz of %s in %.1fs", task.quiz, task.section, time.monotonic() - t0)
        finally:
            with self._lock:
                self._active[chapter.key] -= 1

    def _rewrite(self, chapter: ChapterState, task: Task, version_dir: Path) -> str:
        section = chapter.doc.sections[task.section]
        path = chapter.override_path(task.section, version_dir)
        before = path.read_text() if path.exists() else None
        current = chapter.vault_body(task.section) if task.from_vault else (before or chapter.vault_body(task.section))
        request = (
            f"{reader_context(self.store, chapter)}\n\n"
            f"<chapter_guide>\n{chapter.doc.agent_notes.strip()}\n</chapter_guide>\n\n"
            f"{task.reason}\n\n"
            f'Section: "{section.title}". Subsection headers use {"#" * (section.level + 1)}.\n'
            f"Topics: {'; '.join(section.topics) or 'as in the current text'}\n\n"
            f"Current text of the section:\n\n{current.strip() or '(not written yet)'}"
        )
        text = ""
        flushed = time.monotonic()
        try:
            for delta in llm.stream_text(self._prompts["rewrite"], request, 4000, should_stop=self._stopped.is_set):
                text += delta
                if time.monotonic() - flushed > _FLUSH_SECONDS and "\n\n" in text:
                    write_atomic(path, text[: text.rindex("\n\n")] + WRITING_MARK)
                    flushed = time.monotonic()
        except llm.Stopped:
            # Leave the file as it was, so a restart does not show half a section.
            # After a reset the folder is gone.
            if path.parent.exists():
                if before is None:
                    path.unlink(missing_ok=True)
                else:
                    write_atomic(path, before)
            raise
        text = text.strip() + "\n"
        write_atomic(path, text)
        chapter.record_source(task.section, version_dir)
        return text

    def _write_quiz(self, chapter: ChapterState, task: Task, version_dir: Path, section_text: str) -> None:
        """Write the task's quiz part into `<name>.quiz.md` of the version, keeping its other part."""
        part = task.quiz
        assert part in QUIZ_PARTS, part
        vault_quiz = chapter.doc.quiz_file(task.section)
        vault_parts = (vault_quiz.questions(part), vault_quiz.learned, vault_quiz.prior) if vault_quiz else ()
        count = len(next((q for q in vault_parts if q), [])) or _DEFAULT_QUIZ_QUESTIONS
        page = chapter.doc.is_page(task.section)
        if page:
            placement = (
                "This quiz comes at the start of the page and checks the background the reader needs for it."
                if part == "prior" else "This quiz comes at the end of the page and checks what the reader understood."
            )
        else:
            placement = (
                "This quiz comes before the section and checks what the reader knows already, before reading it."
                if part == "prior" else "This quiz comes after the section and checks what the reader understood."
            )
        if task.covers:
            sections = "\n\n".join(
                f'<section title="{chapter.doc.sections[n].title}" tag="[[{chapter.doc.tag(n)}]]">\n'
                f"{chapter.section_text(n, version_dir).strip()}\n</section>"
                for n in task.covers
            )
            about = (
                f"Write {count} questions about these sections. End each question's text with the tags of the "
                f"sections it is about, as given, e.g. [[{chapter.doc.tag(task.covers[0])}]].\n\n{sections}"
            )
        else:
            about = f"Write {count} questions about this section:\n\n{section_text}"
        request = f"{reader_context(self.store, chapter)}\n\n{task.reason}\n\n{placement}\n\n{about}"
        raw = llm.complete(self._prompts["learned_quiz"], request, max_tokens=3000)
        questions = getattr(parse_quiz(f"# {part.title()}\n\n" + _strip_fences(raw)), part) or []
        if not questions:
            log.warning("The %s quiz of %s came back without questions:\n%s", part, task.section, raw[:500])
            return
        for parsed in questions:
            # A tag the page has no section for would fail the checker
            parsed.links = [link for link in parsed.links if chapter.doc.link_section(link)]
        path = version_dir / f"{task.section}{QUIZ_SUFFIX}"
        quiz = parse_quiz(path.read_text()) if path.exists() else QuizFile()
        setattr(quiz, part, questions)
        write_atomic(path, format_quiz_file(quiz))


def _sections_phrase(chapter: ChapterState, names: list[str]) -> str:
    """E.g. 'The section "Information" is being', 'The sections "A" and "B" are being' or '5 sections, from "A"
    to "E", are being'."""
    titles = [f'"{chapter.doc.sections[n].title}"' for n in names]
    if len(titles) == 1:
        return f"The section {titles[0]} is being"
    if len(titles) > 3:
        return f"{len(titles)} sections, from {titles[0]} to {titles[-1]}, are being"
    return f"The sections {', '.join(titles[:-1])} and {titles[-1]} are being"


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.removesuffix("```").rstrip()
    lines = text.splitlines()
    # The model may repeat the part heading; the caller adds it.
    if lines and lines[0].strip().lower() in ("# learned", "# prior"):
        lines = lines[1:]
    return "\n".join(lines)


def write_atomic(path: Path, text: str) -> None:
    """Write through a rename so the poller never reads a half-written file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)


def _log_failure(future: Future) -> None:
    """Pool threads swallow exceptions, so log them where the task ends."""
    if future.cancelled():
        return
    if isinstance(future.exception(), llm.Stopped):
        log.info("Rewrite stopped by a reset")
    elif future.exception() is not None:
        log.error("Rewrite failed", exc_info=future.exception())
