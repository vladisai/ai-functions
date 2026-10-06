"""A page of the book: a chapter folder with a chapter.md, or a one-file page like lectures/lecture_1.md.

    content/book/probability/
      chapter.md                     the page: text, text inputs and embeds
      random-variables.md            a section the book rewrites for the reader
      random-variables.quiz.md       its quizzes, the prior one before it and the learned one after it
      symbols-at-a-glance.quiz.md    the quizzes of an inline section of chapter.md
      chapter.quiz.md                the page's own quiz
      agent.md                       hints for the chat agent and the rewrites
      reference.md                   source material the chat agent can read
    content/lectures/
      lecture_1.md                   a one-file page, read the same way as chapter.md
      lecture_1.quiz.md              the page's own quiz
      lecture_1.learning.quiz.md     the quizzes of its section "Learning"

A link in the outline to a chapter.md is a chapter folder, and a link to any other file a one-file
page. The page's key is the chapter's folder, e.g. book/probability, or the file's path without
.md, e.g. lectures/lecture_1. Its title is the `title` property, else for a one-file page its
first `# ` heading, else the folder's or the file's name. agent.md and reference.md come from the
page's folder.

A page is read in order:

- `![[name]]` on its own line embeds the section `name.md` from the page's folder, one level deep
  and whole files only.
- `_TEXT_INPUT_: Title` asks the reader a question, with the lines under it as the prompt.
- A heading with text under it, up to the next heading, embed or text input, is an inline section
  named `slug(title)`, made unique with -2, -3, ... and never the name of an embed or text input.
- The page's first `# ` heading is its title. It and the text under it, like a byline, stay fixed,
  unless it is the page's only heading, as in a preface. A heading with no text under it and text
  under no heading stay fixed too.

Headings, embeds and text inputs inside code fences are text. A footnote's definition moves to the
block that cites it, since each block renders on its own.

Every section, embedded or inline, has a prior quiz slot before it and a learned one after it. A
slot without questions shows nothing. The quiz file is `<name>.quiz.md` in a chapter folder, and
`<page stem>.<name>.quiz.md` next to a one-file page.

The page has quiz slots of its own, from `<page stem>.quiz.md`, i.e. chapter.quiz.md or
lecture_1.quiz.md: `<stem>.prior`, the background check, right after the title block (else first),
and `<stem>.learned` at the end. When that file exists no inline section takes the stem's name.
Without it a section may, like the preface's only section, and then its slots stand for the page's.
A question's tags, the wikilinks that end it, name the sections it is about: `[[lecture_1#Learning]]`
a heading of the page, matched by slug, and `[[random-variables]]` an embedded section (see
`link_section`).

A section file has a `topics` property, then a `# Heading`, then its starting text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from quicklearn.vault.frontmatter import split_front_matter, topics_of
from quicklearn.vault.links import split_target
from quicklearn.vault.quiz_md import QuizFile, parse_quiz

CHAPTER_FILE = "chapter.md"
AGENT_FILE = "agent.md"
REFERENCE_FILE = "reference.md"
QUIZ_SUFFIX = ".quiz.md"
FIXED_PREFIX = "fixed-"  # the ids of fixed blocks, fixed-1, fixed-2, ...
# An image embed like ![[lecture_2/fig.svg]] is text, see ui/figures.py
_EMBED_LINE = re.compile(r"^!\[\[(?![^\]]*\.(?i:svg|png|jpe?g|gif|webp|avif|bmp)\]\])([^\[\]|#^]+?)(?:\.md)?\]\]\s*$")
_TEXT_INPUT = re.compile(r"^_TEXT_INPUT_:\s*(.+?)\s*$")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FOOTNOTE_DEF = re.compile(r"^\[\^([^\]]+)\]:")
_FOOTNOTE_REF = re.compile(r"\[\^([^\]]+)\](?!:)")


@dataclass
class SectionFile:
    name: str
    path: Path  # the section's file, or the page for an inline section
    title: str
    level: int
    topics: list[str]
    body: str  # the starting text, without the heading
    inline: bool = False  # a heading of the page with its text, not a file of its own


@dataclass
class Block:
    """One entry of the page, in order."""

    kind: str  # "fixed", "section", "prior", "learned" or "text_input"
    id: str
    title: str = ""
    level: int = 1
    text: str = ""  # fixed: the markdown; text_input: the prompt
    section: str = ""  # section, prior, learned: the section's name, or the page's stem for its own quiz


@dataclass
class ChapterDoc:
    page: Path  # chapter.md, or the one-file page
    key: str  # e.g. "book/probability" or "lectures/lecture_1"
    title: str
    blocks: list[Block]
    sections: dict[str, SectionFile] = field(default_factory=dict)
    missing_embeds: list[tuple[int, str]] = field(default_factory=list)  # (line, name)

    @property
    def folder(self) -> Path:
        return self.page.parent

    @property
    def is_chapter_folder(self) -> bool:
        return self.page.name == CHAPTER_FILE

    @property
    def stem(self) -> str:
        """The name of the page's own quiz: chapter, or the one-file page's stem like lecture_1."""
        return self.page.stem

    @property
    def agent_notes(self) -> str:
        path = self.folder / AGENT_FILE
        return path.read_text() if path.is_file() else ""

    @property
    def page_quiz_path(self) -> Path:
        """The vault's file of the page's own quiz, e.g. chapter.quiz.md or lecture_1.quiz.md."""
        return self.folder / f"{self.stem}{QUIZ_SUFFIX}"

    def is_page(self, name: str) -> bool:
        """True if `name` is the page's own quiz slots rather than a section's."""
        return name == self.stem and name not in self.sections

    def quiz_path(self, name: str) -> Path:
        """The vault's quiz file of a section, or of the page for its stem."""
        if self.is_page(name):
            return self.page_quiz_path
        prefix = "" if self.is_chapter_folder else f"{self.stem}."
        return self.folder / f"{prefix}{name}{QUIZ_SUFFIX}"

    def link_section(self, link: str) -> str | None:
        """The section a quiz tag names, or None. "lecture_1#Learning" is the page's heading whose
        slug is learning, and "random-variables" the embedded section random-variables."""
        path, anchor = split_target(link)
        path = path.rsplit("/", 1)[-1]
        section = self.sections.get(path)
        if section is not None and not section.inline:
            return path
        if not anchor or path not in ("", self.stem):
            return None
        wanted = slug(anchor)
        found = next((n for n, s in self.sections.items() if s.inline and slug(s.title) == wanted), None)
        return found or (wanted if wanted in self.sections else None)

    def tag(self, name: str) -> str:
        """The tag of a section, the inverse of link_section."""
        section = self.sections[name]
        return f"{self.stem}#{section.title}" if section.inline else name

    def quiz_file(self, name: str) -> QuizFile | None:
        path = self.quiz_path(name)
        return parse_quiz(path.read_text()) if path.is_file() else None


def read_section(path: Path) -> SectionFile:
    properties, text = split_front_matter(path.read_text())
    title, level, body = path.stem, 1, text.strip("\n")
    lines = body.splitlines()
    first = next((i for i, line in enumerate(lines) if line.strip()), None)
    if first is not None:
        match = _HEADING.match(lines[first])
        if match:
            level, title = len(match.group(1)), match.group(2)
            body = "\n".join(lines[first + 1:]).strip("\n")
    return SectionFile(path.stem, path, title, level, topics_of(properties), body + "\n" if body else "")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def page_key(target: str) -> str:
    """The key of the page a vault path names: book/probability/chapter → book/probability,
    lectures/lecture_1.md → lectures/lecture_1."""
    path = target.strip("/").removesuffix(".md")
    if path == "chapter" or path.endswith("/chapter"):
        return path.removesuffix("chapter").rstrip("/")
    return path


def page_path(vault: Path, key: str) -> Path:
    """The page file of a key: the chapter folder's chapter.md, else the one-file page."""
    chapter = vault / key / CHAPTER_FILE
    return chapter if chapter.is_file() else vault / f"{key}.md"


def parse_chapter(folder: Path, vault: Path) -> ChapterDoc:
    """Read a chapter folder's chapter.md and the sections it embeds."""
    return parse_page(folder / CHAPTER_FILE, vault)


def _lines(lines: list[str]) -> list[tuple[int, str, re.Match | None]]:
    """(line number, kind, match) per line: "heading", "embed", "text_input", or "text" in a code fence too."""
    out: list[tuple[int, str, re.Match | None]] = []
    in_code = False
    for number, line in enumerate(lines, start=1):
        if line.startswith("```"):
            in_code = not in_code
        matches = {} if in_code else {
            "heading": _HEADING.match(line), "embed": _EMBED_LINE.match(line), "text_input": _TEXT_INPUT.match(line),
        }
        kind = next((k for k, m in matches.items() if m), "text")
        out.append((number, kind, matches.get(kind)))
    return out


def _take_footnotes(lines: list[str]) -> tuple[list[str], dict[str, str]]:
    """The lines without the definitions of footnotes the page cites, and {label: definition}."""
    cited = {m.group(1) for line in lines if not _FOOTNOTE_DEF.match(line) for m in _FOOTNOTE_REF.finditer(line)}
    kept: list[str] = []
    footnotes: dict[str, str] = {}
    label = None
    for (_, kind, _), line in zip(_lines(lines), lines, strict=True):
        match = _FOOTNOTE_DEF.match(line) if kind == "text" else None
        if match and match.group(1) in cited:
            label = match.group(1)
            footnotes[label] = line
        elif label and not line.strip():
            continue  # the blank lines after a definition go with it
        elif label and line.startswith(("    ", "\t")):
            footnotes[label] += "\n" + line  # an indented continuation of the definition
        else:
            label = None
            kept.append(line)
    return kept, footnotes


def parse_page(page: Path, vault: Path) -> ChapterDoc:
    """Read a page, chapter.md or a one-file page, and the sections it embeds."""
    properties, text = split_front_matter(page.read_text())
    lines, footnotes = _take_footnotes(text.splitlines())
    tokens = _lines(lines)
    is_chapter = page.name == CHAPTER_FILE
    # The first `# ` heading is the page's title: it and the text under it stay as written
    title_at = next((i for i, (_, kind, m) in enumerate(tokens) if kind == "heading" and m.group(1) == "#"), None)
    first_title = None if title_at is None else tokens[title_at][2].group(2)
    # A page whose only heading is its title, like the preface, is one section rather than fixed text
    title_fixed = sum(kind == "heading" for _, kind, _ in tokens) > 1
    title = properties.get("title") or (None if is_chapter else first_title) or (
        page.parent.name if is_chapter else page.stem
    )
    doc = ChapterDoc(page, page_key(page.relative_to(vault).as_posix()), str(title), [])
    # Inline sections take names that no embed, text input or the page's own quiz has, so every block id is unique
    taken = {m.group(1).strip() for _, kind, m in tokens if kind == "embed"}
    taken |= {slug(m.group(1)) for _, kind, m in tokens if kind == "text_input"}
    if doc.page_quiz_path.is_file():
        taken.add(doc.stem)
    placed: set[str] = set()
    fixed_count = 0
    title_block: int | None = None  # the index of the title's fixed block

    def with_footnotes(body: str) -> str:
        """The body with the definitions of the footnotes it cites first on the page."""
        labels = [m.group(1) for m in _FOOTNOTE_REF.finditer(body)]
        new = [label for label in dict.fromkeys(labels) if label in footnotes and label not in placed]
        placed.update(new)
        return "\n\n".join([body, *(footnotes[label] for label in new)]) if new else body

    def add_section(section: SectionFile) -> None:
        name = section.name
        doc.sections[name] = section
        doc.blocks.append(Block("prior", f"{name}.prior", section.title, section.level, section=name))
        doc.blocks.append(Block("section", name, section.title, section.level, section=name))
        doc.blocks.append(Block("learned", f"{name}.learned", section.title, section.level, section=name))

    def flush(heading: tuple[int, str] | None, chunk: list[str], is_title: bool) -> None:
        nonlocal fixed_count, title_block
        body = with_footnotes("\n".join(chunk).strip("\n"))
        if heading is not None and body.strip() and not is_title:
            base = slug(heading[1]) or "section"
            name, n = base, 1
            while name in taken:
                n += 1
                name = f"{base}-{n}"
            taken.add(name)
            add_section(SectionFile(name, page, heading[1], heading[0], [], body + "\n", inline=True))
        elif heading is not None or body.strip():
            fixed_count += 1
            level, title = heading or (1, "")
            if is_title:
                title_block = len(doc.blocks)
            doc.blocks.append(Block("fixed", f"{FIXED_PREFIX}{fixed_count}", title, level, body))

    heading: tuple[int, str] | None = None
    heading_at: int | None = None
    chunk: list[str] = []
    i = 0
    while i < len(tokens):
        number, kind, match = tokens[i]
        if kind == "text":
            chunk.append(lines[i])
            i += 1
            continue
        flush(heading, chunk, title_fixed and heading_at == title_at)
        heading, heading_at, chunk = None, None, []
        if kind == "heading":
            heading, heading_at = (len(match.group(1)), match.group(2)), i
        elif kind == "embed":
            name = match.group(1).strip()
            path = page.parent / f"{name}.md"
            if path.is_file():
                add_section(read_section(path))
            else:
                doc.missing_embeds.append((number, name))
        else:
            prompt = []
            while i + 1 < len(lines) and lines[i + 1].strip():
                i += 1
                prompt.append(lines[i])
            doc.blocks.append(Block("text_input", slug(match.group(1)), match.group(1), text="\n".join(prompt)))
        i += 1
    flush(heading, chunk, title_fixed and heading_at == title_at)
    # The page's own quiz: the background check after the title, and a learned quiz at the end
    if doc.is_page(doc.stem):
        at = 0 if title_block is None else title_block + 1
        doc.blocks.insert(at, Block("prior", f"{doc.stem}.prior", doc.title, section=doc.stem))
        doc.blocks.append(Block("learned", f"{doc.stem}.learned", doc.title, section=doc.stem))
    return doc
