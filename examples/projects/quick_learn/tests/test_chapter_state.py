"""One chapter for one reader: the page's sections, version folders with overrides, staleness, answers."""

import json
import os
from pathlib import Path

from conftest import words
from quicklearn.chapter.state import QUIZ_TITLES, SOURCES_FILE, ChapterState
from quicklearn.core.quiz import QuizState
from quicklearn.core.text_input import TextInputState
from quicklearn.reader.store import ReaderStore


def reload(chapter: ChapterState) -> ChapterState:
    """The chapter as a restarted app builds it from disk."""
    return ChapterState(chapter.doc.page, chapter.vault, ReaderStore(chapter.vault, chapter.store.reader))


def bump_mtime(path: Path) -> None:
    """Move the mtime on, since two writes in a row can land on the same mtime tick."""
    st = path.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))


def rewrite(chapter: ChapterState, name: str, text: str) -> None:
    """What a rewrite leaves in the current version: the section's file and its source."""
    chapter.override_path(name).write_text(text)
    chapter.record_source(name)


def test_first_load_opens_an_empty_v0(chapter: ChapterState, store: ReaderStore):
    assert chapter.key == "ch" and chapter.title == "Small Chapter"
    assert chapter.dir == store.dir / "ch"
    assert chapter.version_dir == store.dir / "ch" / "v_0"
    assert os.readlink(store.dir / "ch" / "current") == "v_0"
    assert list(chapter.version_dir.iterdir()) == []
    assert chapter.section_names == ["welcome", "alpha", "beta", "symbols"]


def test_sections_of_the_page(chapter: ChapterState):
    sections = {s.id: s for s in chapter.material.sections}
    assert list(sections) == [
        "fixed-1", "chapter.prior", "welcome.prior", "welcome", "welcome.learned", "about-you", "alpha.prior", "alpha",
        "alpha.learned", "beta.prior", "beta", "beta.learned", "symbols.prior", "symbols", "symbols.learned",
        "chapter.learned",
    ]
    assert (sections["welcome"].title, sections["welcome"].level) == ("Welcome", 1)
    # A section of this chapter links to its place on the page; other links need the book's routes
    assert sections["welcome"].content == "Fixed text that links [beta](#section-beta), a page and nowhere.\n"
    assert (sections["about-you"].title, sections["about-you"].content) == (
        "About you", "<!-- text_input:about-you -->"
    )
    assert (sections["alpha.prior"].title, sections["alpha.prior"].content) == (
        QUIZ_TITLES["prior"], "<!-- quiz:alpha.prior -->"
    )
    assert (sections["alpha"].title, sections["alpha"].level) == ("Alpha", 1)
    assert sections["alpha"].content == words("alpha", 100)
    assert sections["symbols"].content == "| a | b |\n"


def test_links_to_other_pages(small_vault: Path, store: ReaderStore):
    chapter = ChapterState(small_vault / "ch" / "chapter.md", small_vault, store, {"page": "/page"}.get)
    assert chapter.material.get_section("welcome").content == (
        "Fixed text that links [beta](#section-beta), [a page](/page) and nowhere.\n"
    )


def test_quizzes_and_text_inputs(chapter: ChapterState):
    # Every section has both quiz slots, empty ones too, and so does the page
    slots = [f"{n}.{p}" for n in chapter.section_names for p in ("prior", "learned")]
    assert list(chapter.quizzes) == ["chapter.prior", *slots, "chapter.learned"]
    assert chapter.quizzes["welcome.prior"].questions == [] == chapter.quizzes["symbols.learned"].questions
    assert [q.text for q in chapter.quizzes["alpha.prior"].questions] == ["Pick one"]
    assert chapter.quizzes["alpha.learned"].questions == []
    text_input = chapter.text_inputs["about-you"]
    assert (text_input.title, text_input.prompt, text_input.state) == (
        "About you", "Tell us about yourself.", TextInputState.ACTIVE
    )


def test_a_version_folder_holds_only_the_overrides(chapter: ChapterState, small_vault: Path):
    v1 = chapter.new_version()
    assert v1 == chapter.version_dir == chapter.dir / "v_1"
    rewrite(chapter, "alpha", "Alpha, rewritten.\n")
    (v1 / "alpha.quiz.md").write_text("# Learned\n\n1. New\n   - [x] yes\n   - [ ] no\n")
    assert sorted(p.name for p in v1.iterdir()) == ["alpha.md", "alpha.quiz.md", SOURCES_FILE]
    assert list((chapter.dir / "v_0").iterdir()) == []
    assert chapter.section_path("alpha") == v1 / "alpha.md"
    assert chapter.section_path("beta") == small_vault / "ch" / "beta.md"
    assert chapter.section_path("alpha", chapter.dir / "v_0") == small_vault / "ch" / "alpha.md"
    assert chapter.section_text("alpha") == "Alpha, rewritten.\n"
    # The rewritten quiz has only a Learned part, so the Prior part still comes from the vault
    assert [q.text for q in chapter.quiz_questions("alpha", "learned")] == ["New"]
    assert [q.text for q in chapter.quiz_questions("alpha", "prior")] == ["Pick one"]
    assert chapter.quiz_questions("beta", "learned") == []
    sources = json.loads((v1 / SOURCES_FILE).read_text())
    assert list(sources) == ["alpha"]


def test_stale_sections_after_a_vault_edit(chapter: ChapterState, small_vault: Path):
    chapter.new_version()
    rewrite(chapter, "alpha", "Alpha, rewritten.\n")
    assert chapter.stale_sections() == []
    (small_vault / "ch" / "alpha.md").write_text("# Alpha\n\nThe author's new text.\n")
    (small_vault / "ch" / "beta.md").write_text("# Beta\n\nAlso new, but never rewritten.\n")
    assert chapter.vault_body("alpha") == "The author's new text.\n"
    assert chapter.stale_sections() == ["alpha"]
    # Only the body counts: new topics do not make a rewrite stale
    rewrite(chapter, "alpha", "Alpha, rewritten again.\n")
    (small_vault / "ch" / "alpha.md").write_text("---\ntopics: [new]\n---\n# Alpha\n\nThe author's new text.\n")
    assert chapter.stale_sections() == []


def test_empty_sections(make_vault):
    vault = make_vault({
        "ch/chapter.md": "![[written]]\n\n![[unwritten]]\n",
        "ch/written.md": "# Written\n\nText.\n",
        "ch/unwritten.md": "---\ntopics: [a topic]\n---\n# Not yet\n",
    })
    chapter = ChapterState(vault / "ch" / "chapter.md", vault, ReaderStore(vault, "tester"))
    assert chapter.empty_sections() == ["unwritten"]
    chapter.override_path("unwritten").write_text("Written for the reader.\n")
    assert chapter.empty_sections() == []


def test_is_compact(chapter: ChapterState):
    assert chapter.is_compact("alpha")
    chapter.override_path("alpha").write_text(words("longer", 125))
    assert chapter.is_compact("alpha")
    chapter.override_path("alpha").write_text(words("longer", 126))
    assert not chapter.is_compact("alpha")


def test_new_version_drops_the_change_notes(chapter: ChapterState):
    v1 = chapter.new_version()
    noted = "Intro.\n<!-- note: Added an example -->\nThe example.\n"
    (v1 / "alpha.md").write_text(noted)
    v2 = chapter.new_version()
    assert (v2 / "alpha.md").read_text() == "Intro.\nThe example.\n"
    assert (v1 / "alpha.md").read_text() == noted
    assert len(chapter.material.version_stack) == 2


def test_versions_survive_a_reload(chapter: ChapterState):
    chapter.new_version()
    rewrite(chapter, "alpha", "Alpha, first rewrite.\n")
    chapter.new_version()
    rewrite(chapter, "alpha", "Alpha, second rewrite.\n")

    again = reload(chapter)
    assert again.version_dir.name == "v_2"
    material = again.material
    assert material.get_section("alpha").content == "Alpha, second rewrite.\n"
    assert material.total_versions == 3
    material.go_to_version(0)
    assert material.get_section("alpha").content == words("alpha", 100)
    material.go_to_version(1)
    assert material.get_section("alpha").content == "Alpha, first rewrite.\n"
    material.go_to_head()
    assert material.get_section("alpha").content == "Alpha, second rewrite.\n"
    assert again.stale_sections() == []


def test_answers_survive_a_reload(chapter: ChapterState):
    prior = chapter.quizzes["alpha.prior"]
    prior.submit_answer(0, "b")
    prior.complete()
    chapter.quizzes["beta.prior"].skip()
    text_input = chapter.text_inputs["about-you"]
    text_input.answer, text_input.state = "A physicist.", TextInputState.DONE
    chapter.save_answers()

    saved = json.loads(chapter.store.answers_path("ch").read_text())
    assert sorted(saved["quizzes"]) == ["alpha.prior", "beta.prior"]
    again = reload(chapter)
    assert (again.quizzes["alpha.prior"].state, again.quizzes["alpha.prior"].answers) == (QuizState.COMPLETED, {0: "b"})
    assert again.quizzes["beta.prior"].state == QuizState.SKIPPED
    assert again.quizzes["alpha.learned"].state == QuizState.ACTIVE
    assert (again.text_inputs["about-you"].answer, again.text_inputs["about-you"].state) == (
        "A physicist.", TextInputState.DONE
    )


def test_answers_to_changed_questions_do_not_come_back(chapter: ChapterState, small_vault: Path):
    chapter.quizzes["alpha.prior"].submit_answer(0, "b")
    chapter.quizzes["alpha.prior"].complete()
    chapter.save_answers()
    (small_vault / "ch" / "alpha.quiz.md").write_text("# Prior\n\n1. A different question\n   - [x] yes\n\n# Learned\n")
    quiz = reload(chapter).quizzes["alpha.prior"]
    assert (quiz.state, quiz.answers) == (QuizState.ACTIVE, {})


def test_section_list_and_outdated(chapter: ChapterState, small_vault: Path):
    assert chapter.section_list() == (
        "- welcome: Welcome\n- alpha: Alpha (topics: first topic; second topic)\n"
        "- beta: Beta (topics: third topic)\n- symbols: Symbols"
    )
    assert not chapter.is_outdated()
    bump_mtime(small_vault / "ch" / "chapter.md")
    assert chapter.is_outdated()


def test_an_inline_section_re_reads_the_page(chapter: ChapterState, small_vault: Path):
    page = small_vault / "ch" / "chapter.md"
    assert chapter.doc.sections["welcome"].inline and chapter.section_path("welcome") == page
    rewrite(chapter, "symbols", "Symbols for the reader.\n")
    assert chapter.stale_sections() == [] and chapter.live.poll_all() == {"symbols"}

    page.write_text(page.read_text().replace("| a | b |", "| a | b | c |").replace("Fixed text", "Edited text"))
    bump_mtime(page)
    assert chapter.vault_body("welcome").startswith("Edited text that links")
    # Personalize again finds the rewritten inline section the author changed
    assert chapter.stale_sections() == ["symbols"]
    assert chapter.live.poll_all() == {"welcome"}
    assert chapter.material.get_section("welcome").content.startswith("Edited text")
    assert chapter.is_outdated()


def test_an_inline_section_the_page_lost_keeps_its_text(chapter: ChapterState, small_vault: Path):
    page = small_vault / "ch" / "chapter.md"
    page.write_text(page.read_text().replace("# Symbols\n\n| a | b |\n", ""))
    assert chapter.vault_body("symbols") == "| a | b |\n"


def test_a_one_file_page_for_a_reader(make_vault, tmp_path: Path):
    vault = make_vault({
        "lectures/lecture_1.md": "# Lecture 1\n\n## Learning\n\nText.\n",
        "lectures/lecture_1.learning.quiz.md": "# Prior\n\n1. Pick one\n   - [x] yes\n   - [ ] no\n",
    })
    store = ReaderStore(vault, "tester")
    chapter = ChapterState(vault / "lectures" / "lecture_1.md", vault, store)
    assert (chapter.key, chapter.title) == ("lectures/lecture_1", "Lecture 1")
    assert chapter.dir == store.dir / "lectures" / "lecture_1"
    assert chapter.version_dir == chapter.dir / "v_0"
    assert chapter.quiz_paths("learning") == [
        vault / "lectures" / "lecture_1.learning.quiz.md", chapter.dir / "v_0" / "learning.quiz.md",
    ]
    assert [q.text for q in chapter.quizzes["learning.prior"].questions] == ["Pick one"]
    assert chapter.section_text("learning") == "Text.\n"
