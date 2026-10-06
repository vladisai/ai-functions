"""Check the vault for the mistakes the app would otherwise show silently.

    uv run python -m quicklearn.check            # the vault in content/
    uv run python -m quicklearn.check path/to/vault --strict

| Problem | Level |
|---|---|
| an embed or outline link to a file that does not exist | error |
| an embed whose name more than one file in the vault has, so Obsidian may open another one | error |
| a pick-one question without exactly one `[x]`, or a question mixing `[x]` and `[T]`/`[F]` | error |
| a quiz part other than Prior and Learned, or a quiz file without a section | error |
| a quiz tag, like `[[lecture_1#Learning]]`, that names no section of the page | error |
| two blocks of a page with the same id, e.g. a section embedded twice | error |
| math that does not render: unclosed `$`, unbalanced braces, an unknown command | error |
| a file under personalization_data/ that git tracks | error |
| an embedded section without a quiz file, or with an empty Prior part, which the book cannot adapt | warning |
| a question of the page's own quiz without a tag, whose miss rewrites nothing | warning |
| a chapter.md the outline does not link | warning |

Every page is checked: each chapter.md, and each other file the outline links, a one-file page. The
quiz files of inline sections, the headings of a page with their text, are checked when they exist,
and so is the page's own quiz file, `<page stem>.quiz.md`.

Errors make the exit code 1, and warnings too with --strict.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from latex2mathml.converter import convert

from quicklearn.reader.store import PERSONAL_DIR
from quicklearn.vault.chapter import CHAPTER_FILE, QUIZ_SUFFIX, ChapterDoc, parse_page
from quicklearn.vault.outline import parse_outline
from quicklearn.vault.quiz_md import parse_quiz

OUTLINE_FILE = "outline.md"


@dataclass
class Problem:
    path: Path
    line: int
    message: str
    warning: bool = False

    def format(self, root: Path) -> str:
        path = self.path.relative_to(root) if self.path.is_relative_to(root) else self.path
        level = "warning" if self.warning else "error"
        return f"{path}:{self.line}: {level}: {self.message}"


def vault_files(vault: Path) -> list[Path]:
    """The markdown files of the book, without the reader folders and Obsidian's settings."""
    return sorted(
        p for p in vault.rglob("*.md")
        if PERSONAL_DIR not in p.relative_to(vault).parts
        and not any(part.startswith(".") for part in p.relative_to(vault).parts)
    )


def check_vault(vault: Path) -> list[Problem]:
    files = vault_files(vault)
    problems = check_outline(vault)
    problems += check_chapters(vault, files)
    for path in files:
        problems += check_math(path)
    problems += check_personal_data(vault)
    return problems


# -- Outline and chapters --


def check_outline(vault: Path) -> list[Problem]:
    outline = vault / OUTLINE_FILE
    if not outline.is_file():
        return [Problem(outline, 0, "the vault has no outline.md, so the app has no pages")]
    return [
        Problem(outline, entry.line, f"links {entry.target}.md, which does not exist")
        for entry in parse_outline(outline)
        if entry.target and not (vault / f"{entry.target}.md").is_file()
    ]


def check_chapters(vault: Path, files: list[Path]) -> list[Problem]:
    """Every page: each chapter.md, and each other file the outline links."""
    problems: list[Problem] = []
    by_name: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        by_name[path.stem].append(path)
    outline = vault / OUTLINE_FILE
    linked = {e.target for e in parse_outline(outline)} if outline.is_file() else set()
    pages = [p for p in files if p.name == CHAPTER_FILE]
    pages += [vault / f"{t}.md" for t in sorted(linked) if Path(t).name != "chapter" and (vault / f"{t}.md").is_file()]

    for page in pages:
        folder = page.parent
        doc = parse_page(page, vault)
        if doc.is_chapter_folder and (Path(doc.key) / "chapter").as_posix() not in linked:
            problems.append(Problem(page, 1, "the outline does not link this chapter", warning=True))
        for line, name in doc.missing_embeds:
            problems.append(Problem(page, line, f"embeds {name}, but {folder.name}/ has no {name}.md"))
        for line, name in _embeds(page):
            others = [p for p in by_name[name] if p != folder / f"{name}.md"]
            if others and (folder / f"{name}.md").is_file():
                where = ", ".join(str(p.relative_to(vault)) for p in others)
                problems.append(Problem(
                    page, line,
                    f"embeds {name}, a name {where} has too, so Obsidian may show another file",
                ))
        for block_id, count in Counter(b.id for b in doc.blocks).items():
            if count > 1:
                problems.append(Problem(
                    page, 1,
                    f"{count} blocks have the id {block_id}; each section and text input can appear once",
                ))
        for name, section in doc.sections.items():
            # An inline section adapts without a quiz too, through the tutor and the text inputs
            if doc.quiz_path(name).is_file() or not section.inline:
                problems += check_quiz(doc.quiz_path(name), section.path, doc)
        if doc.is_page(doc.stem) and doc.page_quiz_path.is_file():
            problems += check_quiz(doc.page_quiz_path, page, doc, page_quiz=True)
        problems += _orphan_quizzes(doc)
    return problems


def _embeds(page: Path) -> list[tuple[int, str]]:
    pattern = re.compile(r"^\s*!\[\[([^\[\]|#]+)")
    return [
        (lineno, match.group(1).strip().removesuffix(".md"))
        for lineno, line in enumerate(page.read_text().splitlines(), start=1)
        if (match := pattern.match(line))
    ]


def _orphan_quizzes(doc: ChapterDoc) -> list[Problem]:
    """Quiz files of the page whose name no section has: `*.quiz.md` in a chapter folder, and
    `<stem>.*.quiz.md` next to a one-file page. The page's own quiz, chapter.quiz.md, is no orphan."""
    prefix = doc.quiz_path("").name.removesuffix(QUIZ_SUFFIX)
    return [
        Problem(path, 1, "no section of the page has this name, so the quiz never shows")
        for path in sorted(doc.folder.glob(f"{prefix}*{QUIZ_SUFFIX}"))
        if path.name.removeprefix(prefix).removesuffix(QUIZ_SUFFIX) not in doc.sections
        and not (doc.is_page(doc.stem) and path == doc.page_quiz_path)
    ]


def check_quiz(path: Path, section_path: Path, doc: ChapterDoc, page_quiz: bool = False) -> list[Problem]:
    """The quiz file of a section, or with `page_quiz` of the page, whose tags must name sections of `doc`."""
    if not path.is_file():
        return [
            Problem(section_path, 1, f"no {path.name}, so the book cannot test or adapt this section", warning=True)
        ]
    quiz = parse_quiz(path.read_text())
    problems = [
        Problem(path, 1, f"unknown part '# {name}'; the parts are Prior and Learned")
        for name in quiz.unknown_parts
    ]
    if not quiz.prior and not quiz.learned:
        problems.append(Problem(path, 1, "no questions, so only the tutor can adapt this section", warning=True))
    for parsed in (quiz.prior or []) + (quiz.learned or []):
        problems += [
            Problem(path, parsed.line, f"the tag [[{link}]] names no section of {doc.page.name}")
            for link in parsed.links if doc.link_section(link) is None
        ]
        if page_quiz and not parsed.links:
            problems.append(Problem(
                path, parsed.line, "has no tag, so a miss rewrites no section and only goes to the notes", warning=True,
            ))
        marks = parsed.marks
        if not marks:
            continue
        true_false = sum(m in "TF" for m in marks)
        picked = sum(m in "xX" for m in marks)
        if true_false and true_false < len(marks):
            problems.append(Problem(
                path, parsed.line,
                "mixes [T]/[F] with [ ]/[x]; mark every option of a true-or-false question with T or F",
            ))
        elif not true_false and picked != 1:
            problems.append(Problem(
                path, parsed.line,
                f"has {picked} options marked [x]; a pick-one question needs exactly one",
            ))
    return problems


# -- Math --

_CODE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
_SINGLE = re.compile(r"(?<!\$)\$(?!\$)(.*?)\$")  # markdown2's latex extra, which runs this first
_DOUBLE = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
_UNKNOWN = re.compile(r"<m[io]>(\\[A-Za-z]+)</m[io]>")


def math_spans(text: str) -> tuple[list[tuple[int, str]], list[int]]:
    """The formulas of a markdown text as (offset, latex), and the offsets of dollars that open
    nothing, found the way the page finds them."""
    masked = _CODE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text).replace("\\$", "  ")
    spans = []

    def take(match: re.Match) -> str:
        spans.append((match.start(), match.group(1)))
        return re.sub(r"[^\n]", " ", match.group(0))

    masked = _SINGLE.sub(take, masked)
    masked = _DOUBLE.sub(take, masked)
    return sorted(spans), [i for i, c in enumerate(masked) if c == "$"]


def formula_error(latex: str) -> str | None:
    """Why a formula would not render, or None."""
    depth = 0
    for i, c in enumerate(latex):
        if c in "{}" and (i == 0 or latex[i - 1] != "\\"):
            depth += 1 if c == "{" else -1
            if depth < 0:
                return "a } closes no {"
    if depth:
        return "a { is not closed"
    try:
        mathml = convert(latex.replace("\\bm{", "\\boldsymbol{"))
    except Exception as error:  # latex2mathml's errors share no base class
        return f"{type(error).__name__} {error}".strip()
    unknown = _UNKNOWN.search(mathml)
    return f"unknown command {unknown.group(1)}" if unknown else None


def check_math(path: Path) -> list[Problem]:
    text = path.read_text()
    spans, stray = math_spans(text)

    def line(offset: int) -> int:
        return text.count("\n", 0, offset) + 1

    problems = [Problem(path, line(i), "a $ that is not closed on its line, so the math shows as text") for i in stray]
    for offset, latex in spans:
        error = formula_error(latex)
        if error:
            problems.append(Problem(path, line(offset), f"${_short(latex)}$: {error}"))
    return problems


def _short(latex: str, limit: int = 50) -> str:
    latex = " ".join(latex.split())
    return latex if len(latex) <= limit else latex[:limit] + "…"


# -- Reader data --


def check_personal_data(vault: Path) -> list[Problem]:
    """Reader folders hold a student's answers and chat, which must not reach the shared repo."""
    result = subprocess.run(
        ["git", "-C", str(vault), "ls-files", "--", PERSONAL_DIR],
        capture_output=True, text=True,
    )
    if result.returncode != 0:  # not a git checkout
        return []
    return [
        Problem(vault / name, 0, "git tracks this reader file; remove it with git rm --cached")
        for name in result.stdout.splitlines()
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the QuickLearn vault")
    parser.add_argument("vault", nargs="?", type=Path, default=Path(__file__).parent.parent / "content")
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    args = parser.parse_args(argv)
    vault = args.vault.resolve()

    problems = check_vault(vault)
    root = vault.parent
    for problem in problems:
        print(problem.format(root))
    errors = sum(not p.warning for p in problems)
    warnings = len(problems) - errors
    print(f"{len(vault_files(vault))} files checked: {errors} errors, {warnings} warnings")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
