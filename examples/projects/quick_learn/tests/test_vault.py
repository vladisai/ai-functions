"""Reading the vault: pages with their embeds, inline sections, text inputs and fixed text, section files."""

from pathlib import Path

from quicklearn.vault.chapter import FIXED_PREFIX, Block, page_path, parse_chapter, parse_page, read_section, slug
from quicklearn.vault.frontmatter import split_front_matter, topics_of


def blocks(doc) -> list[tuple[str, str]]:
    return [(b.kind, b.id) for b in doc.blocks]


def slots(name: str) -> list[tuple[str, str]]:
    return [("prior", f"{name}.prior"), ("section", name), ("learned", f"{name}.learned")]


def test_small_chapter_blocks_in_order(small_vault: Path):
    doc = parse_chapter(small_vault / "ch", small_vault)
    assert doc.key == "ch" and doc.title == "Small Chapter" and doc.is_chapter_folder
    assert blocks(doc) == [
        ("fixed", "fixed-1"), *slots("welcome"), ("text_input", "about-you"),
        *slots("alpha"), *slots("beta"), *slots("symbols"),
    ]
    assert list(doc.sections) == ["welcome", "alpha", "beta", "symbols"]
    assert [s.inline for s in doc.sections.values()] == [True, False, False, True]
    # The page's title heading and its byline stay as written
    assert (doc.blocks[0].title, doc.blocks[0].text) == ("Small Chapter", "*By the author*")
    assert doc.missing_embeds == []
    assert doc.agent_notes == "Hints for the rewrites.\n"
    assert doc.quiz_path("symbols") == small_vault / "ch" / "symbols.quiz.md"


def test_headings_with_text_are_inline_sections(make_vault):
    vault = make_vault({
        "ch/chapter.md": (
            "Intro without a heading.\n\n# Title\n\n*A byline*\n\n"
            "# One\n\nText one.\n\n## Two\n\n```\n# not a heading\n![[sec]]\n```\n\n"
            "![[sec]]\n\nAfter the embed.\n\n# Empty\n\n## Sec\n\nNamed like the embed.\n\n## One\n\nAgain.\n\n"
            "## One\n\nAnd again.\n\n# $$\n\nNo letters.\n"
        ),
        "ch/sec.md": "# Sec\n",
    })
    doc = parse_chapter(vault / "ch", vault)
    assert [(b.kind, b.id, b.title, b.level) for b in doc.blocks if b.kind not in ("prior", "learned")] == [
        ("fixed", "fixed-1", "", 1),
        # The first `# ` heading is the title: it and its text stay fixed
        ("fixed", "fixed-2", "Title", 1),
        ("section", "one", "One", 1),
        ("section", "two", "Two", 2),
        ("section", "sec", "Sec", 1),
        ("fixed", "fixed-3", "", 1),
        # A heading with no text under it stays fixed
        ("fixed", "fixed-4", "Empty", 1),
        # Never an embed's name, and unique on the page
        ("section", "sec-2", "Sec", 2),
        ("section", "one-2", "One", 2),
        ("section", "one-3", "One", 2),
        ("section", "section", "$$", 1),
    ]
    assert (doc.blocks[0].text, doc.blocks[1].text) == ("Intro without a heading.", "*A byline*")
    # A code fence is text: its heading and embed stay in the section
    two = doc.sections["two"]
    assert (two.body, two.path, two.inline, two.topics) == (
        "```\n# not a heading\n![[sec]]\n```\n", vault / "ch" / "chapter.md", True, []
    )
    assert doc.sections["one"].body == "Text one.\n"
    assert all(b.id.startswith(FIXED_PREFIX) for b in doc.blocks if b.kind == "fixed")
    # Without a title property the folder names the chapter
    assert doc.title == "ch"


def test_an_inline_section_ends_at_a_text_input(make_vault):
    vault = make_vault({
        "ch/chapter.md": (
            "# Page\n\n# Ask\n\nWhy we ask.\n\n_TEXT_INPUT_: Ask\nThe prompt.\n\n# Bare\n\n_TEXT_INPUT_: Q\n"
        ),
    })
    doc = parse_chapter(vault / "ch", vault)
    # The text input took the slug ask, so the section is ask-2
    assert [(b.kind, b.id) for b in doc.blocks] == [
        ("fixed", "fixed-1"), *slots("ask-2"), ("text_input", "ask"), ("fixed", "fixed-2"), ("text_input", "q"),
    ]
    assert doc.sections["ask-2"].body == "Why we ask.\n"


def test_footnotes_move_to_the_block_that_cites_them(make_vault):
    vault = make_vault({"page.md": (
        "# Page\n\n## A\n\nCites[^1] and[^x].\n\n## B\n\nCites[^1] again.\n\n"
        "[^1]: The first.\n    More of it.\n\n[^x]: The second.\n\n[^unused]: Stays.\n"
    )})
    doc = parse_page(vault / "page.md", vault)
    assert doc.sections["a"].body == "Cites[^1] and[^x].\n\n[^1]: The first.\n    More of it.\n\n[^x]: The second.\n"
    assert doc.sections["b"].body == "Cites[^1] again.\n\n[^unused]: Stays.\n"


def test_a_one_file_page(make_vault):
    vault = make_vault({
        "lectures/lecture_1.md": "# Lecture 1\n\n## Learning\n\nText.\n\n![[extra]]\n",
        "lectures/lecture_1.learning.quiz.md": "# Prior\n\n1. Pick one\n   - [x] yes\n   - [ ] no\n",
        "lectures/extra.md": "# Extra\n\nEmbedded.\n",
        "lectures/agent.md": "Lecture hints.\n",
        "book/preface.md": "---\ntitle: The Preface\n---\n\nWelcome.\n",
        "book/notes.md": "Just text.\n",
    })
    doc = parse_page(vault / "lectures" / "lecture_1.md", vault)
    assert (doc.key, doc.title, doc.is_chapter_folder) == ("lectures/lecture_1", "Lecture 1", False)
    assert blocks(doc) == [("fixed", "fixed-1"), *slots("learning"), *slots("extra")]
    assert doc.quiz_path("learning") == vault / "lectures" / "lecture_1.learning.quiz.md"
    assert doc.quiz_path("extra") == vault / "lectures" / "lecture_1.extra.quiz.md"
    assert [q.text for q in doc.quiz_file("learning").questions("prior")] == ["Pick one"]
    assert doc.agent_notes == "Lecture hints.\n"
    # The title property wins, and a page without either is named by its file
    assert parse_page(vault / "book" / "preface.md", vault).title == "The Preface"
    assert parse_page(vault / "book" / "notes.md", vault).title == "notes"
    assert page_path(vault, "lectures/lecture_1") == vault / "lectures" / "lecture_1.md"
    assert page_path(vault, "book/preface") == vault / "book" / "preface.md"


def test_blank_text_makes_no_block(make_vault):
    vault = make_vault({"ch/chapter.md": "\n\n![[sec]]\n\n\n", "ch/sec.md": "# Sec\n"})
    assert blocks(parse_chapter(vault / "ch", vault)) == slots("sec")


def test_embeds(make_vault):
    vault = make_vault({
        "ch/chapter.md": (
            "![[quizzed]]\n![[plain.md]]\n![[gone]]\nText with ![[plain]] inline.\n![[plain#Heading]]\n"
        ),
        "ch/quizzed.md": "# Quizzed\n\nBody.\n",
        "ch/quizzed.quiz.md": "# Prior\n\n# Learned\n",
        "ch/plain.md": "## Plain\n\nBody.\n",
    })
    doc = parse_chapter(vault / "ch", vault)
    # Every section has its quiz slots, with a quiz file or not; an embed inside text or of a heading stays text
    assert blocks(doc) == [*slots("quizzed"), *slots("plain"), ("fixed", "fixed-1")]
    assert doc.blocks[0] == Block("prior", "quizzed.prior", "Quizzed", 1, section="quizzed")
    assert doc.blocks[4].level == 2
    assert doc.missing_embeds == [(3, "gone")]
    assert "![[plain]]" in doc.blocks[6].text and "![[plain#Heading]]" in doc.blocks[6].text


def test_text_input_takes_the_lines_under_it_as_prompt(make_vault):
    vault = make_vault({"ch/chapter.md": (
        "_TEXT_INPUT_: What brings you here?\nFirst line.\nSecond line.\n\nAfter the prompt.\n"
        "_TEXT_INPUT_:   Bare  \n"
    )})
    doc = parse_chapter(vault / "ch", vault)
    first, fixed, bare = doc.blocks
    assert (first.kind, first.id, first.title, first.text) == (
        "text_input", "what-brings-you-here", "What brings you here?", "First line.\nSecond line."
    )
    assert (fixed.kind, fixed.text) == ("fixed", "After the prompt.")
    assert (bare.id, bare.title, bare.text) == ("bare", "Bare", "")


def test_slug():
    assert slug("Tell us about yourself") == "tell-us-about-yourself"
    assert slug("  What's $X$?  ") == "what-s-x"


def test_read_section(tmp_path: Path):
    path = tmp_path / "sec.md"
    path.write_text(
        "---\ntopics:\n  - one\n  - \"two, three\"\n---\n\n\n### Deep Title ###\n\nBody line.\n\n## Sub\n\nMore.\n\n"
    )
    section = read_section(path)
    assert (section.name, section.title, section.level) == ("sec", "Deep Title", 3)
    assert section.topics == ["one", "two, three"]
    assert section.body == "Body line.\n\n## Sub\n\nMore.\n"
    assert not section.inline


def test_section_without_heading_or_body(tmp_path: Path):
    no_heading = tmp_path / "no-heading.md"
    no_heading.write_text("Just text.\n")
    assert (read_section(no_heading).title, read_section(no_heading).body) == ("no-heading", "Just text.\n")
    heading_only = tmp_path / "heading-only.md"
    heading_only.write_text("---\ntopics: a, b\n---\n# Only a heading\n")
    section = read_section(heading_only)
    assert (section.title, section.body, section.topics) == ("Only a heading", "", ["a", "b"])


def test_front_matter():
    assert split_front_matter("---\ntitle: T\n---\nBody\n") == ({"title": "T"}, "Body\n")
    assert split_front_matter("---\n---\nBody\n") == ({}, "Body\n")
    assert split_front_matter("No block\n---\n") == ({}, "No block\n---\n")
    assert split_front_matter("---\ntitle: never closed\n") == ({}, "---\ntitle: never closed\n")


def test_topics_of():
    assert topics_of({"topics": ["a", " b ", ""]}) == ["a", "b"]
    assert topics_of({"topics": "a, b,, c"}) == ["a", "b", "c"]
    assert topics_of({}) == []


def test_shipped_chapter(shipped_vault: Path):
    doc = parse_chapter(shipped_vault / "book" / "probability", shipped_vault)
    assert doc.key == "book/probability"
    assert doc.title == "Probability and Statistics Primer"
    embedded = [name for name, s in doc.sections.items() if not s.inline]
    assert embedded == ["random-variables", "expectation", "information-theory"]
    assert "symbols-at-a-glance" in doc.sections
    assert doc.missing_embeds == []
    for name in embedded:
        section = doc.sections[name]
        assert section.topics and section.body
        assert len(doc.quiz_file(name).prior) == 4
        assert doc.quiz_file(name).learned == []


def test_a_lecture_keeps_its_title_and_byline(make_vault):
    vault = make_vault({"lectures/lecture_2.md": (
        "# Lecture 2: Agents\n\n*Alessandro Achille, September 30, 2026*\n\n"
        "## Agents act\n\nText.\n\n# Later\n\nMore.\n"
    )})
    doc = parse_page(vault / "lectures" / "lecture_2.md", vault)
    assert doc.title == "Lecture 2: Agents"
    assert [(b.kind, b.id) for b in doc.blocks] == [("fixed", "fixed-1"), *slots("agents-act"), *slots("later")]
    byline = "*Alessandro Achille, September 30, 2026*"
    assert (doc.blocks[0].title, doc.blocks[0].text) == ("Lecture 2: Agents", byline)
    assert list(doc.sections) == ["agents-act", "later"]


def test_a_page_with_only_its_title_heading_is_one_section(make_vault):
    vault = make_vault({"book/preface.md": "# Preface\n\nWhy this book.\n\nHow to read it.\n"})
    doc = parse_page(vault / "book" / "preface.md", vault)
    assert doc.title == "Preface"
    assert [(b.kind, b.id) for b in doc.blocks] == slots("preface")
    assert doc.sections["preface"].body == "Why this book.\n\nHow to read it.\n"
