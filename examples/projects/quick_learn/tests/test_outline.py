"""The outline in the drawer, wikilinks and their routes, and the one-file pages the outline links."""

import re
from pathlib import Path

import markdown2
from quicklearn.ui.content_renderer import TEXT_EXTRAS
from quicklearn.ui.math_markdown import _fix_latex, _patch_markdown2
from quicklearn.vault.chapter import parse_page
from quicklearn.vault.links import render_links, route_of, split_target
from quicklearn.vault.outline import OutlineEntry, parse_outline


def test_parse_outline_reads_groups_parts_and_chapters(tmp_path: Path):
    path = tmp_path / "outline.md"
    path.write_text(
        "<!--\nA comment\n- [[not/an/entry]]\n-->\n\n- [[book/preface|Preface]]\n\n# Lectures\n\n"
        "- [[lectures/lecture_1.md|Lecture 1]]\n\n# Book\n## Background\n- [[book/probability/chapter|Primer]]\n"
        "- [[chapter]]\n- Information\nPlain text is ignored.\n"
    )
    assert parse_outline(path) == [
        OutlineEntry("chapter", "Preface", "/book/preface", "book/preface", 6),
        OutlineEntry("group", "Lectures", line=8),
        OutlineEntry("chapter", "Lecture 1", "/lectures/lecture_1", "lectures/lecture_1", 10),
        OutlineEntry("group", "Book", line=12),
        OutlineEntry("part", "Background", line=13),
        OutlineEntry("chapter", "Primer", "/book/probability", "book/probability/chapter", 14),
        OutlineEntry("chapter", "chapter", "/", "chapter", 15),
        OutlineEntry("chapter", "Information", line=16),
    ]
    assert [e.title for e in parse_outline(path) if e.is_chapter] == ["Primer", "chapter"]


def test_routes():
    assert route_of("book/probability/chapter") == "/book/probability"
    assert route_of("book/preface.md") == "/book/preface"
    assert route_of("/lectures/lecture_1") == "/lectures/lecture_1"
    assert route_of("chapter") == "/"
    assert split_target(" book/probability/chapter.md#Joint ") == ("book/probability/chapter", "Joint")
    assert split_target("page") == ("page", "")


def test_render_links():
    routes = {"book/preface": "/book/preface", "sec": "#section-sec"}
    text = (
        "[[book/preface]], [[book/preface|the Preface]], [[book/preface#Why|why]], [[book/preface#Why]], "
        "[[sec#Part]], [[missing|gone]], ![[book/preface]] and [[a/b/c]]"
    )
    assert render_links(text, routes.get) == (
        "[preface](/book/preface), [the Preface](/book/preface), [why](/book/preface#Why), [Why](/book/preface#Why), "
        "[Part](#section-sec), gone, preface and c"
    )


def test_shipped_outline_links_existing_pages(shipped_vault: Path):
    outline = parse_outline(shipped_vault / "outline.md")
    linked = [e for e in outline if e.link]
    links = [e.link for e in linked]
    assert links[:2] == ["/book/preface", "/lectures/lecture_1"] and "/book/probability" in links
    assert [e.title for e in outline if e.is_chapter] == ["Probability and Statistics Primer"]
    for entry in linked:
        assert (shipped_vault / f"{entry.target}.md").is_file(), entry.target
    assert outline[-1] == OutlineEntry(
        "chapter", "Algorithmic Information Primer: Transductive Inference", line=outline[-1].line
    )


def test_the_lecture_is_a_page_of_inline_sections_with_their_footnotes(shipped_vault: Path):
    _patch_markdown2()
    doc = parse_page(shipped_vault / "lectures" / "lecture_1.md", shipped_vault)
    # The title is the first # heading
    assert (doc.key, doc.title) == ("lectures/lecture_1", "Lecture 1")
    # The title heading and the byline under it stay as written
    assert (doc.blocks[0].kind, doc.blocks[0].title, doc.blocks[0].text) == ("fixed", "Lecture 1", "*Stefano Soatto*")
    assert list(doc.sections)[0] == "learning" and all(s.inline for s in doc.sections.values())
    assert [(doc.sections[n].title, doc.sections[n].level) for n in ("learning", "reward-and-loss")] == [
        ("Learning", 2), ("Reward and loss", 2),
    ]
    assert doc.quiz_path("learning") == shipped_vault / "lectures" / "lecture_1.learning.quiz.md"
    # Each footnote's definition moved to the section that cites it, so the section renders it
    for name in ("learning", "statistical-learning"):
        body = doc.sections[name].body
        rendered = markdown2.markdown(_fix_latex(body), extras=["latex", "tables", *TEXT_EXTRAS])
        assert 'class="footnotes"' in rendered and rendered.count('class="footnote-ref"') == 1
    last = doc.sections[list(doc.sections)[-1]].body
    assert "[^1]:" not in last and "[^2]:" not in last
    # Every $...$ became MathML
    text = "\n\n".join(s.body for s in doc.sections.values())
    rendered = markdown2.markdown(_fix_latex(text), extras=["latex", "tables", *TEXT_EXTRAS])
    assert not re.search(r"\$[^$\s]", re.sub(r"<math.*?</math>", "", rendered, flags=re.S))
