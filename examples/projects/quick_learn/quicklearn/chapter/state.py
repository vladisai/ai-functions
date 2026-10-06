"""One page for one reader: the vault's page with the reader's rewrites on top.

A page is a chapter folder's chapter.md or a one-file page like lectures/lecture_1.md, and the
reader's versions of it are in `personalization_data/<reader>/<key>/v_0, v_1, ...`. The page is a
list of Sections, one per block (see vault/chapter.py):

| Block | Section id | Section content |
|---|---|---|
| fixed text | fixed-1, fixed-2, ... | the text as written |
| embedded section | its file name, e.g. random-variables | the rewritten body, or the vault file's |
| inline section | a slug of its heading, e.g. symbols-at-a-glance | the rewritten body, or the page's text |
| prior / learned quiz | random-variables.prior | `<!-- quiz:random-variables.prior -->` |
| text input | a slug of its title | `<!-- text_input:tell-us-about-yourself -->` |

Every section has both quiz slots. A quiz comes from `<name>.quiz.md` in the current version, else
from the vault's quiz file, and a slot without questions shows nothing until they exist.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

from quicklearn.chapter.live import ContentLive, LiveMaterial, LiveSection, QuizLive, fingerprint
from quicklearn.chapter.versions import (
    create_version,
    get_current_version,
    get_current_version_dir,
    list_versions,
    set_current_version,
)
from quicklearn.core.material import Material, Section, Snapshot
from quicklearn.core.quiz import Quiz, QuizQuestion, QuizState
from quicklearn.core.text_input import TextInput, TextInputState
from quicklearn.reader.store import ReaderStore
from quicklearn.vault.chapter import QUIZ_SUFFIX, Block, ChapterDoc, parse_page, read_section
from quicklearn.vault.links import render_links
from quicklearn.vault.quiz_md import parse_quiz

log = logging.getLogger(__name__)

SOURCES_FILE = "sources.json"
QUIZ_TITLES = {"prior": "Checking prior knowledge", "learned": "Checking what you learned"}
_NOTE = re.compile(r"<!--\s*note:.*?-->\n?")


def vault_hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:16]


class ChapterState:
    def __init__(self, page: Path, vault: Path, store: ReaderStore, resolve_link=None) -> None:
        """page: chapter.md of a chapter folder, or a one-file page."""
        self.vault = vault
        self.store = store
        self.doc: ChapterDoc = parse_page(page, vault)
        self.key = self.doc.key
        self.dir = store.chapter_dir(self.key)
        self._resolve_link = resolve_link or (lambda path: None)
        self.page_mtime = page.stat().st_mtime
        # v_0 is the page as the vault has it, an empty folder, which git leaves out of a demo reader
        (self.dir / "v_0").mkdir(parents=True, exist_ok=True)
        if get_current_version_dir(self.dir) is None:
            set_current_version(self.dir, max(list_versions(self.dir)))

        self.quizzes: dict[str, Quiz] = {}
        self.text_inputs: dict[str, TextInput] = {}
        for block in self.doc.blocks:
            if block.kind in ("prior", "learned"):
                self.quizzes[block.id] = Quiz(id=block.id, questions=self.quiz_questions(block.section, block.kind))
            elif block.kind == "text_input":
                self.text_inputs[block.id] = TextInput(block.id, block.title, block.text)
        self._restore_answers()

        self.material = Material(self._sections(self.version_dir))
        self.sync_version_stack()
        sections = {s.id: s for s in self.material.sections}
        live: list[LiveSection] = []
        for block in self.doc.blocks:
            section = sections[block.id]
            if block.kind == "section":
                live.append(ContentLive(section, self, block.section))
            elif block.kind in ("prior", "learned"):
                live.append(QuizLive(section, self, block.section, block.kind, self.quizzes[block.id]))
            else:
                live.append(LiveSection(section))
        self.live = LiveMaterial(self, live)

    # -- Files --

    @property
    def title(self) -> str:
        return self.doc.title

    @property
    def version_dir(self) -> Path:
        return get_current_version_dir(self.dir)

    @property
    def section_names(self) -> list[str]:
        return [b.section for b in self.doc.blocks if b.kind == "section"]

    def override_path(self, name: str, version_dir: Path | None = None) -> Path:
        return (version_dir or self.version_dir) / f"{name}.md"

    def section_path(self, name: str, version_dir: Path | None = None) -> Path:
        """The file the reader sees for a section: the rewrite in this version, or the vault file."""
        override = self.override_path(name, version_dir)
        return override if override.exists() else self.doc.sections[name].path

    def vault_body(self, name: str) -> str:
        """The section's text in the vault now, re-read so edits in Obsidian show up. An inline
        section re-reads the page, and keeps its text as loaded if the page no longer has it."""
        section = self.doc.sections[name]
        if not section.inline:
            return read_section(section.path).body
        now = parse_page(self.doc.page, self.vault).sections.get(name)
        return now.body if now is not None and now.inline else section.body

    def section_text(self, name: str, version_dir: Path | None = None) -> str:
        override = self.override_path(name, version_dir)
        text = override.read_text() if override.exists() else self.vault_body(name)
        return self._links(text)

    def quiz_paths(self, name: str, version_dir: Path | None = None) -> list[Path]:
        """The vault's quiz file of the section, and the reader's in this version."""
        return [self.doc.quiz_path(name), (version_dir or self.version_dir) / f"{name}{QUIZ_SUFFIX}"]

    def quiz_questions(self, name: str, part: str, version_dir: Path | None = None) -> list[QuizQuestion]:
        """A part of the section's quiz: the rewritten one in this version, or the vault's."""
        vault_file, override_file = self.quiz_paths(name, version_dir)
        for path in (override_file, vault_file):
            if path.exists():
                questions = parse_quiz(path.read_text()).questions(part)
                if questions is not None:
                    return questions
        return []

    def _links(self, text: str) -> str:
        """Wikilinks in the text: a section of this chapter links to its place on the page."""

        def resolve(path: str) -> str | None:
            if path in self.doc.sections:
                return f"#section-{path}"
            return self._resolve_link(path)

        return render_links(text, resolve)

    # -- Sections of the page --

    def _sections(self, version_dir: Path) -> list[Section]:
        sections = []
        for block in self.doc.blocks:
            sections.append(self._section(block, version_dir))
        return sections

    def _section(self, block: Block, version_dir: Path) -> Section:
        if block.kind == "fixed":
            return Section(block.id, block.title, self._links(block.text), block.level)
        if block.kind == "section":
            return Section(block.id, block.title, self.section_text(block.section, version_dir), block.level)
        if block.kind in ("prior", "learned"):
            return Section(block.id, QUIZ_TITLES[block.kind], f"<!-- quiz:{block.id} -->", block.level)
        return Section(block.id, block.title, f"<!-- text_input:{block.id} -->", block.level)

    def sync_version_stack(self) -> None:
        """Load prior versions from disk into the version stack, so the version bar can show them."""
        current = get_current_version(self.dir)
        prior = [v for v in list_versions(self.dir) if v < current]
        stack = self.material.version_stack
        for v in prior[len(stack):]:
            stack.append(Snapshot(sections=self._sections(self.dir / f"v_{v}")))

    # -- Versions --

    def new_version(self) -> Path:
        """Start a rewrite pass: copy the current version folder and make the copy current.

        The in-memory material is snapshotted first so the version bar can go back, and the old
        change notes are dropped, so only the new pass's notes show.
        """
        current = get_current_version(self.dir)
        self.material.snapshot()
        new_dir = create_version(self.dir, from_version=current)
        set_current_version(self.dir, int(new_dir.name.removeprefix("v_")))
        for md in new_dir.glob("*.md"):
            text = md.read_text()
            if _NOTE.search(text):
                md.write_text(_NOTE.sub("", text))
        log.info("%s: opened %s", self.key, new_dir.name)
        return new_dir

    def record_source(self, name: str, version_dir: Path | None = None) -> None:
        """Remember which vault text a rewrite was based on, for Personalize again."""
        path = (version_dir or self.version_dir) / SOURCES_FILE
        with self.store.lock:
            sources = self.store.load_json(path, {})
            sources[name] = vault_hash(self.vault_body(name))
            self.store.save_json(path, sources)

    def stale_sections(self) -> list[str]:
        """Rewritten sections whose vault text changed since, e.g. after a git pull."""
        sources = self.store.load_json(self.version_dir / SOURCES_FILE, {})
        return [
            name for name in self.section_names
            if self.override_path(name).exists() and sources.get(name) != vault_hash(self.vault_body(name))
        ]

    def is_compact(self, name: str) -> bool:
        """True if the section is at most a quarter longer than the vault's, the compact expert version.

        Expert rewrites stay near the vault's length, and condensing them again only adds nuance.
        """
        current = len(self.section_text(name).split())
        return current <= 1.25 * len(self.vault_body(name).split())

    def empty_sections(self) -> list[str]:
        """Sections with no text yet in the vault or the reader folder, which the book writes on the first visit."""
        return [name for name in self.section_names if not self.section_text(name).strip()]

    # -- Answers --

    def save_answers(self) -> None:
        data = {
            "quizzes": {
                qid: {
                    "state": quiz.state.value,
                    "answers": {str(i): a for i, a in quiz.answers.items()},
                    "fingerprint": fingerprint(quiz.questions),
                }
                for qid, quiz in self.quizzes.items()
                if quiz.answers or quiz.state != QuizState.ACTIVE
            },
            "text_inputs": {
                tid: {"state": ti.state.value, "answer": ti.answer}
                for tid, ti in self.text_inputs.items()
                if ti.answer or ti.state != TextInputState.ACTIVE
            },
        }
        self.store.save_json(self.store.answers_path(self.key), data)

    def _restore_answers(self) -> None:
        """Answers come back only for the questions they were given to, by the quiz's fingerprint."""
        data = self.store.load_json(self.store.answers_path(self.key), {})
        for qid, saved in data.get("quizzes", {}).items():
            quiz = self.quizzes.get(qid)
            if quiz is None or saved.get("fingerprint") != fingerprint(quiz.questions):
                continue
            quiz.state = QuizState(saved["state"])
            quiz.answers = {int(i): a for i, a in saved.get("answers", {}).items()}
        for tid, saved in data.get("text_inputs", {}).items():
            if tid in self.text_inputs:
                self.text_inputs[tid].state = TextInputState(saved["state"])
                self.text_inputs[tid].answer = saved.get("answer", "")

    # -- For the model --

    def section_list(self) -> str:
        """The chapter's sections for a prompt, one line each."""
        lines = []
        for name in self.section_names:
            sf = self.doc.sections[name]
            lines.append(f"- {name}: {sf.title}" + (f" (topics: {'; '.join(sf.topics)})" if sf.topics else ""))
        return "\n".join(lines)

    def is_outdated(self) -> bool:
        """The page file changed since this state was built, e.g. an author added a section."""
        return self.doc.page.stat().st_mtime != self.page_mtime
