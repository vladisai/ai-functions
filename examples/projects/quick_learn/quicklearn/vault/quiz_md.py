"""Quizzes written as markdown, in `<section>.quiz.md` next to the section.

    # Prior

    1. Which statement about a density $p(x)$ is right?
       - [ ] $p(x) = \\mathbb{P}(X = x)$
       - [x] $\\int p(x)\\,dx = 1$
    2. Evaluate these statements:
       - [T] The marginal is $\\int p(x, y)\\,dy$.
       - [F] Independence means $p(x, y) = p(x) + p(y)$.

    # Learned

A numbered item is a question. Options marked `[ ]` and `[x]` make a pick-one question with the
`[x]` option correct, and options marked `[T]` and `[F]` make true-or-false statements. A question
without options takes a free-form answer. An empty Learned part means the book writes the learned
quiz itself when the reader shows gaps. LaTeX is written as it is, without escaping.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from quicklearn.core.quiz import QuestionType, QuizQuestion

PARTS = ("prior", "learned")
_QUESTION = re.compile(r"^(\d+)[.)]\s+(.*)$")
_OPTION = re.compile(r"^\s*[-*+]\s+\[([ xXTF])\]\s?(.*)$")
_PART = re.compile(r"^#\s+(.+?)\s*$")


@dataclass
class ParsedQuestion:
    question: QuizQuestion
    line: int  # 1-based line of the question in the file, for the check command
    marks: list[str] = field(default_factory=list)  # the raw marks, e.g. [" ", "x", " "]


@dataclass
class QuizFile:
    """The parts of a quiz file. A part the file does not have is None, an empty part is []."""

    prior: list[ParsedQuestion] | None = None
    learned: list[ParsedQuestion] | None = None
    unknown_parts: list[str] = field(default_factory=list)

    def questions(self, part: str) -> list[QuizQuestion] | None:
        parsed = getattr(self, part)
        return None if parsed is None else [p.question for p in parsed]


def parse_quiz(text: str) -> QuizFile:
    quiz = QuizFile()
    part: str | None = None
    current: dict | None = None
    questions: list[dict] = []

    def close_part() -> None:
        if part is not None:
            setattr(quiz, part, [_build(q) for q in questions])

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        part_match = _PART.match(line)
        if part_match:
            close_part()
            name = part_match.group(1).strip().lower()
            part = name if name in PARTS else None
            if part is None:
                quiz.unknown_parts.append(part_match.group(1))
            questions, current = [], None
            continue
        if part is None:
            continue
        question_match = _QUESTION.match(line)
        if question_match:
            current = {"text": [question_match.group(2)], "options": [], "line": lineno}
            questions.append(current)
            continue
        option_match = _OPTION.match(line)
        if option_match and current is not None:
            current["options"].append([option_match.group(1), option_match.group(2).strip()])
            continue
        if current is None or not line.strip():
            continue
        if current["options"]:
            current["options"][-1][1] += " " + line.strip()  # an option that wraps onto the next line
        else:
            current["text"].append(line.strip())
    close_part()
    return quiz


def _build(raw: dict) -> ParsedQuestion:
    text = "\n".join(raw["text"]).strip()
    marks = [mark for mark, _ in raw["options"]]
    options = [option for _, option in raw["options"]] or None
    letters = "abcdefghijklmnopqrstuvwxyz"
    if options is None:
        question = QuizQuestion(text=text, options=None)
    elif any(mark in "TF" for mark in marks):
        correct = ",".join(f"{letters[i]}:{'T' if m == 'T' else 'F'}" for i, m in enumerate(marks))
        question = QuizQuestion(text=text, question_type=QuestionType.MULTI_TF, options=options, correct_answer=correct)
    else:
        picked = [letters[i] for i, m in enumerate(marks) if m in "xX"]
        question = QuizQuestion(
            text=text, question_type=QuestionType.PICK_ONE, options=options,
            correct_answer=picked[0] if len(picked) == 1 else None,
        )
    return ParsedQuestion(question, raw["line"], marks)


def format_questions(questions: list[QuizQuestion]) -> str:
    """The numbered questions of one part, the inverse of parse_quiz."""
    blocks = []
    for n, q in enumerate(questions, start=1):
        text_lines = q.text.strip().splitlines() or [""]
        lines = [f"{n}. {text_lines[0]}"] + [f"   {line}" for line in text_lines[1:]]
        for i, option in enumerate(q.options or []):
            lines.append(f"   - [{_mark(q, i)}] {' '.join(option.split())}")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


def format_quiz(prior: list[QuizQuestion] | None, learned: list[QuizQuestion] | None) -> str:
    parts = []
    for title, questions in (("Prior", prior), ("Learned", learned)):
        if questions is not None:
            body = format_questions(questions)
            parts.append(f"# {title}\n\n{body}\n" if body else f"# {title}\n")
    return "\n".join(parts)


def _mark(q: QuizQuestion, i: int) -> str:
    letter = "abcdefghijklmnopqrstuvwxyz"[i]
    if q.question_type == QuestionType.MULTI_TF:
        pairs = dict(pair.split(":") for pair in (q.correct_answer or "").split(",") if ":" in pair)
        return pairs.get(letter, "F")
    return "x" if q.correct_answer == letter else " "
