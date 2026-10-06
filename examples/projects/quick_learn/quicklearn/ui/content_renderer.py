"""Render a chapter's sections: markdown with change notes, quizzes and text inputs.

A section's content is its markdown, or one tag that stands for a widget:
`<!-- quiz:random-variables.prior -->` or `<!-- text_input:tell-us-about-yourself -->`. Every
section has both quiz slots, and so has the page, e.g. `lecture_2.prior` after the title. A slot
without questions renders nothing until they exist.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from nicegui import ui

from quicklearn.core.material import Section
from quicklearn.core.quiz import Quiz
from quicklearn.core.text_input import TextInput
from quicklearn.ui.math_markdown import math_markdown
from quicklearn.ui.quiz_renderer import render_quiz
from quicklearn.ui.text_input_renderer import render_text_input
from quicklearn.vault.chapter import FIXED_PREFIX

QUIZ_TAG_PATTERN = re.compile(r"<!--\s*quiz:(\S+)\s*-->")
TEXT_INPUT_TAG_PATTERN = re.compile(r"^\s*<!--\s*text_input:(\S+)\s*-->\s*$")
NOTE_TAG_PATTERN = re.compile(r"<!--\s*note:\s*(.+?)\s*-->")
# A block renders as a document of its own, with the footnotes it cites at its end (see vault/chapter.py)
TEXT_EXTRAS = ("footnotes",)


def is_quiz_section(content: str) -> bool:
    """Check if section content is purely a quiz tag."""
    stripped = content.strip()
    # Section is a quiz section if it's only a quiz tag (possibly with surrounding text)
    match = QUIZ_TAG_PATTERN.search(stripped)
    if match:
        # Check if the non-quiz content is trivial
        without_quiz = QUIZ_TAG_PATTERN.sub("", stripped).strip()
        return len(without_quiz) == 0
    return False


def _split_noted_section(md: str) -> tuple[str, str]:
    """Split markdown into (highlighted, rest) for a note annotation.

    - If starts with a heading: spans until the next heading at same/higher level.
    - Otherwise (paragraph): spans until the next blank line.
    """
    first_line = md.lstrip().split("\n", 1)[0]
    if first_line.startswith("#"):
        level = len(first_line) - len(first_line.lstrip("#"))
        pattern = re.compile(r"\n(?=#{1," + str(level) + r"}(?!#))")
        match = pattern.search(md)
    else:
        # Paragraph: split at first blank line (two consecutive newlines)
        match = re.search(r"\n\n", md)

    if match:
        return md[: match.start()], md[match.start():]
    return md, ""


def _render_chunk_with_notes(text: str, show_notes: bool) -> ui.markdown | None:
    """Render a markdown chunk, extracting and displaying inline note markers.

    When show_notes is True, the content following a note gets a margin annotation
    bar on the right, spanning just the section under the note (up to the next
    heading). If show_notes is False, notes are silently stripped.
    """
    note_parts = NOTE_TAG_PATTERN.split(text)
    first_el: ui.markdown | None = None
    pending_note: str | None = None

    # Collect all sub-chunks to render (may expand due to heading splits)
    render_queue: list[tuple[str, str | None]] = []  # (markdown, note_or_None)

    for j, chunk in enumerate(note_parts):
        if j % 2 == 1:
            pending_note = chunk
            continue
        md = chunk.strip()
        if not md:
            continue
        if pending_note and show_notes:
            highlighted, rest = _split_noted_section(md)
            render_queue.append((highlighted.strip(), pending_note))
            if rest.strip():
                render_queue.append((rest.strip(), None))
            pending_note = None
        else:
            render_queue.append((md, None))
            pending_note = None

    for md, note in render_queue:
        if not md:
            continue
        if note:
            with ui.element("div").classes("relative w-full"):
                el = math_markdown(md, classes="text-base leading-relaxed", extras=TEXT_EXTRAS)
                with ui.column().classes(
                    "absolute top-0 bottom-0 border-l-2 border-amber-400 pl-2 py-1"
                ).style("left: calc(100% + 16px); width: 200px;"):
                    ui.label(note).classes(
                        "text-xs italic text-amber-700 leading-normal"
                    )
        else:
            el = math_markdown(md, classes="text-base leading-relaxed", extras=TEXT_EXTRAS)

        if first_el is None:
            first_el = el

    return first_el


def render_section(
    section: Section,
    quizzes: dict[str, Quiz],
    text_inputs: dict[str, TextInput] | None = None,
    on_quiz_submit: Callable | None = None,
    on_quiz_partial: Callable | None = None,
    on_quiz_skip: Callable | None = None,
    on_quiz_feedback: Callable[[str], None] | None = None,
    on_text_input_submit: Callable | None = None,
    on_text_input_skip: Callable | None = None,
    flash: bool = False,
) -> ui.markdown | None:
    """Render one section. Returns the first markdown element of a text section, for in-place updates."""
    level = "#" * section.level
    content = section.content
    flash_cls = "section-flash" if flash else ""
    with ui.column().classes(f"w-full relative {flash_cls}").props(f'id="section-{section.id}"'):
        text_input_match = TEXT_INPUT_TAG_PATTERN.match(content)
        if text_input_match:
            render_text_input(
                (text_inputs or {})[text_input_match.group(1)],
                on_submit=on_text_input_submit,
                on_skip=on_text_input_skip,
            )
            return None

        if is_quiz_section(content):
            quiz = quizzes[QUIZ_TAG_PATTERN.search(content).group(1)]
            # An empty slot, e.g. before the book or the tutor writes its quiz, shows nothing
            if quiz.questions:
                render_quiz(
                    quiz,
                    on_submit=on_quiz_submit,
                    on_partial=on_quiz_partial,
                    on_skip=on_quiz_skip,
                    on_feedback=on_quiz_feedback,
                    title=section.title,
                )
            return None

        if section.title:
            math_markdown(f"{level} {section.title}", classes="mt-6 mb-2")
        if not content.strip():
            if section.id.startswith(FIXED_PREFIX):
                return None  # a heading of chapter.md with no text under it
            ui.label("This section is being written for you...").classes("text-sm text-gray-400 italic ml-4")
            return None
        return _render_chunk_with_notes(content.strip(), bool(NOTE_TAG_PATTERN.search(content)))
