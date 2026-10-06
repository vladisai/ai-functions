"""How a section's text is rendered: quiz and text input tags, change notes, and the drawer's table of contents."""

import pytest
from quicklearn.chapter.state import ChapterState
from quicklearn.ui.content_renderer import (
    NOTE_TAG_PATTERN,
    QUIZ_TAG_PATTERN,
    TEXT_INPUT_TAG_PATTERN,
    _split_noted_section,
    is_quiz_section,
)
from quicklearn.ui.layout import _section_toc


@pytest.mark.parametrize("content", [
    "<!-- quiz:alpha.prior -->", "  <!-- quiz:alpha.prior -->  ", "\n<!-- quiz:q1 -->\n", "<!--  quiz:q1  -->",
])
def test_quiz_tag(content: str):
    assert is_quiz_section(content)


@pytest.mark.parametrize("content", [
    "", "# Heading\n\nText.", "<!-- quiz -->", "<!-- quiz: -->", "Read this first <!-- quiz:q1 -->",
    "<!-- quiz:q1 --> and some instructions", "<!-- text_input:about-you -->",
])
def test_not_a_quiz(content: str):
    assert not is_quiz_section(content)


def test_quiz_id():
    assert QUIZ_TAG_PATTERN.search("<!-- quiz:random-variables.learned -->").group(1) == "random-variables.learned"


def test_text_input_tag():
    assert TEXT_INPUT_TAG_PATTERN.match("\n<!-- text_input:about-you -->\n").group(1) == "about-you"
    assert TEXT_INPUT_TAG_PATTERN.match("Intro <!-- text_input:about-you -->") is None
    assert TEXT_INPUT_TAG_PATTERN.match("<!-- quiz:about-you -->") is None


def test_note_tag():
    assert NOTE_TAG_PATTERN.search("<!-- note:   padded text   -->").group(1) == "padded text"
    assert NOTE_TAG_PATTERN.search("<!-- quiz:q1 -->") is None
    text = "before\n<!-- note: reason one -->\nmiddle\n<!-- note: reason two -->\nafter"
    assert NOTE_TAG_PATTERN.split(text) == ["before\n", "reason one", "\nmiddle\n", "reason two", "\nafter"]


def test_a_note_spans_its_subsection_or_paragraph():
    assert _split_noted_section("## A\ntext\n### Sub\nmore\n## B\nrest") == (
        "## A\ntext\n### Sub\nmore", "\n## B\nrest"
    )
    assert _split_noted_section("### Sub\nmore\n# Top\nrest") == ("### Sub\nmore", "\n# Top\nrest")
    assert _split_noted_section("# Top\ntext\n## Sub\nmore\n# Next") == ("# Top\ntext\n## Sub\nmore", "\n# Next")
    assert _split_noted_section("Para one\nline\n\nPara two") == ("Para one\nline", "\n\nPara two")
    assert _split_noted_section("Only one") == ("Only one", "")


def test_the_drawer_lists_sections_with_a_heading(chapter: ChapterState):
    assert _section_toc(chapter.material) == [
        ("section-fixed-1", "Small Chapter"), ("section-welcome", "Welcome"), ("section-alpha", "Alpha"),
        ("section-beta", "Beta"), ("section-symbols", "Symbols"),
    ]
