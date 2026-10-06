"""The reader folder: everything the book keeps about one reader.

    content/personalization_data/<reader>/      QUICKLEARN_READER, "default" if unset
      reader.md                                 "# About the reader", shared by every chapter
      chat.json                                 the chat as shown, and events the tutor has not seen yet
      chat_session/                             the tutor's AI Functions session, its event log
      <chapter key>/                            e.g. book/probability
        notes.md                                "# Inputs", "# Quiz results", "# Notes"
        answers.json                            quiz answers and text input answers
        v_0/, v_1/, current                     versions of the rewritten sections

A copy of a reader folder is a snapshot of that reader. The folder is git-ignored, and the app
reads it at start, so a restart brings everything back. Reset empties it. A reader named like a
folder in demo_readers/ starts as a copy of it, and Reset goes back to that copy.
"""

from __future__ import annotations

import json
import re
import shutil
import threading
from datetime import datetime
from pathlib import Path

PERSONAL_DIR = "personalization_data"
READER_FILE = "reader.md"
CHAT_FILE = "chat.json"
NOTES_FILE = "notes.md"
ANSWERS_FILE = "answers.json"
ABOUT = "About the reader"
NOTES_PARTS = ("Inputs", "Quiz results", "Notes")

_EMPTY_ABOUT = "Nothing yet."


def get_part(text: str, title: str) -> str:
    """The text under `# title`, up to the next `# ` heading."""
    match = re.search(rf"^# {re.escape(title)}[ \t]*\n(.*?)(?=^# |\Z)", text, re.DOTALL | re.MULTILINE)
    return match.group(1).strip() if match else ""


def set_part(text: str, title: str, body: str) -> str:
    """Replace the text under `# title`, adding the part at the end if the file has none."""
    block = f"# {title}\n\n{body.strip()}\n\n" if body.strip() else f"# {title}\n\n"
    pattern = re.compile(rf"^# {re.escape(title)}[ \t]*\n.*?(?=^# |\Z)", re.DOTALL | re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1).rstrip() + "\n"
    return (text.rstrip() + "\n\n" + block).lstrip().rstrip() + "\n"


class ReaderStore:
    """Reads and writes the reader folder. One lock guards the markdown files, which several
    threads update: the app appends inputs and quiz results, the note step rewrites the notes."""

    def __init__(self, vault: Path, reader: str, demo_readers: Path | None = None) -> None:
        self.vault = vault
        self.reader = reader
        self.dir = vault / PERSONAL_DIR / reader
        self.demo = demo_readers / reader if demo_readers is not None and (demo_readers / reader).is_dir() else None
        self.lock = threading.RLock()
        self._create()

    def _create(self) -> None:
        """A new reader folder starts as the demo reader of the same name, or else empty."""
        if not self.dir.exists() and self.demo is not None:
            shutil.copytree(self.demo, self.dir, symlinks=True)
        self.dir.mkdir(parents=True, exist_ok=True)
        if not self.reader_path.exists():
            self.reader_path.write_text(f"# {ABOUT}\n\n{_EMPTY_ABOUT}\n")

    # -- Paths --

    @property
    def reader_path(self) -> Path:
        return self.dir / READER_FILE

    def chapter_dir(self, key: str) -> Path:
        path = self.dir / key
        path.mkdir(parents=True, exist_ok=True)
        return path

    def notes_path(self, key: str) -> Path:
        return self.chapter_dir(key) / NOTES_FILE

    # -- reader.md --

    def reader_md(self) -> str:
        return self.reader_path.read_text()

    def about(self) -> str:
        about = get_part(self.reader_md(), ABOUT)
        return "" if about == _EMPTY_ABOUT else about

    def set_about(self, body: str) -> None:
        with self.lock:
            self.reader_path.write_text(set_part(self.reader_md(), ABOUT, body or _EMPTY_ABOUT))

    def add_about(self, note: str) -> None:
        with self.lock:
            self.set_about(_append_bullet(self.about(), note))

    # -- notes.md --

    def notes_md(self, key: str) -> str:
        path = self.notes_path(key)
        if not path.exists():
            return "".join(f"# {part}\n\n" for part in NOTES_PARTS).rstrip() + "\n"
        return path.read_text()

    def set_notes_part(self, key: str, part: str, body: str) -> None:
        with self.lock:
            self.notes_path(key).write_text(set_part(self.notes_md(key), part, body))

    def add_note(self, key: str, note: str) -> None:
        with self.lock:
            self.set_notes_part(key, "Notes", _append_bullet(get_part(self.notes_md(key), "Notes"), note))

    def record_input(self, key: str, title: str, prompt: str, answer: str) -> None:
        """Put the reader's answer under "# Inputs", replacing an earlier answer to the same question."""
        with self.lock:
            inputs = get_part(self.notes_md(key), "Inputs")
            entries = _split_entries(inputs)
            quoted = "\n".join(f"> {line}" for line in prompt.strip().splitlines())
            entries[title] = f"## {title}\n\n" + (f"{quoted}\n\n" if quoted else "") + answer.strip()
            self.set_notes_part(key, "Inputs", "\n\n".join(entries.values()))

    def record_quiz(self, key: str, title: str, summary: str) -> None:
        """Add a quiz result under "# Quiz results"; every submit adds one, so retakes show up."""
        with self.lock:
            results = get_part(self.notes_md(key), "Quiz results")
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"## {title} ({stamp})\n\n{summary.strip()}"
            self.set_notes_part(key, "Quiz results", (results + "\n\n" + entry).strip())

    # -- JSON files --

    def load_json(self, path: Path, default):
        return json.loads(path.read_text()) if path.exists() else default

    def save_json(self, path: Path, data) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(path)

    @property
    def chat_path(self) -> Path:
        return self.dir / CHAT_FILE

    def answers_path(self, key: str) -> Path:
        return self.chapter_dir(key) / ANSWERS_FILE

    # -- Reset --

    def wipe(self) -> None:
        """Empty the reader folder. A demo reader goes back to its snapshot in demo_readers/."""
        with self.lock:
            shutil.rmtree(self.dir)
            self._create()


def _append_bullet(body: str, note: str) -> str:
    note = " ".join(note.split())
    return (body.rstrip() + f"\n- {note}").strip()


def _split_entries(text: str) -> dict[str, str]:
    """{title: "## title ..." block} for the `## ` entries of a part, in order."""
    entries: dict[str, str] = {}
    for block in re.split(r"(?=^## )", text, flags=re.MULTILINE):
        block = block.strip()
        if block.startswith("## "):
            entries[block[3:].split("\n", 1)[0].strip()] = block
    return entries
