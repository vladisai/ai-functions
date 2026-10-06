"""The book's reader actions: what each one saves, which note step it runs, and what it rewrites."""

import json
import os
from pathlib import Path

import pytest
from conftest import FakeLLM
from quicklearn.book import Book
from quicklearn.chapter.versions import list_versions
from quicklearn.core.text_input import TextInputState
from quicklearn.reader.store import get_part


@pytest.fixture
def book(small_vault: Path):
    book = Book(small_vault, "tester")
    yield book
    book.stop()


def wait(book: Book) -> None:
    """Wait for the rewrites and note steps. The book takes no new tasks after this."""
    book.adapter._pool.shutdown(wait=True)
    book._notes_pool.shutdown(wait=True)


def bump_mtime(path: Path) -> None:
    st = path.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))


def test_a_chapter_is_loaded_once_with_the_book_links(book: Book):
    chapter = book.chapter("ch")
    assert book.chapter("ch") is chapter
    assert chapter.material.get_section("welcome").content == (
        "Fixed text that links [beta](#section-beta), [a page](/page) and nowhere.\n"
    )


def test_an_edited_chapter_reloads_once_no_rewrite_writes_into_it(book: Book, small_vault: Path):
    chapter = book.chapter("ch")
    (small_vault / "ch" / "gamma.md").write_text("# Gamma\n\nNew.\n")
    path = small_vault / "ch" / "chapter.md"
    path.write_text(path.read_text() + "\n![[gamma]]\n")
    bump_mtime(path)

    book.adapter._active["ch"] = 1
    assert book.chapter("ch") is chapter
    book.adapter._active["ch"] = 0
    again = book.chapter("ch")
    assert again is not chapter and again.section_names == ["welcome", "alpha", "beta", "symbols", "gamma"]


def test_submit_quiz_rewrites_and_records_the_result(book: Book, fake_llm: FakeLLM):
    chapter = book.chapter("ch")
    quiz = chapter.quizzes["alpha.prior"]
    quiz.submit_answer(0, "a")
    quiz.complete()
    plan = book.submit_quiz(chapter, quiz)
    assert [(t.section, t.quiz) for t in plan.tasks] == [("alpha", "learned")]
    wait(book)

    saved = json.loads(book.store.answers_path("ch").read_text())
    assert saved["quizzes"]["alpha.prior"]["answers"] == {"0": "a"}
    results = get_part(book.store.notes_md("ch"), "Quiz results")
    assert results.startswith("## Alpha, prior knowledge (") and results.endswith("0 of 1 right. Missed: Q1 Pick one.")
    assert sorted(p.name for p in chapter.version_dir.iterdir()) == ["alpha.md", "alpha.quiz.md", "sources.json"]
    assert sorted(name for name, _ in fake_llm.calls) == ["learned_quiz", "memory", "rewrite"]
    assert (
        "The reader submitted the quiz Alpha, prior knowledge:\n\nQ1 (WRONG): Pick one"
        in fake_llm.requests("memory")[0]
    )
    assert chapter.live.poll_all() == {"alpha", "alpha.learned"}
    assert book.running() == 0


def test_quiz_feedback_goes_into_the_chat(book: Book, fake_llm: FakeLLM):
    chapter = book.chapter("ch")
    quiz = chapter.quizzes["alpha.prior"]
    quiz.submit_answer(0, "b")
    plan = book.adapter.plan_for_quiz(chapter, quiz)
    assert book.quiz_feedback(chapter, quiz, plan) == "Well done."
    assert book.chat.display[-1] == {"role": "assistant", "content": "Well done."}
    assert json.loads(book.store.chat_path.read_text())["display"][-1]["content"] == "Well done."


def test_a_text_input_the_note_step_acts_on_rewrites_every_section(book: Book, fake_llm: FakeLLM):
    fake_llm.replies["memory"] = (
        "<about_reader>- A physicist.</about_reader><rewrite>yes</rewrite><reason>New background.</reason>"
    )
    chapter = book.chapter("ch")
    text_input = chapter.text_inputs["about-you"]
    assert book.submit_text_input(chapter, text_input, "  A physicist.\n")
    assert (text_input.answer, text_input.state) == ("A physicist.", TextInputState.DONE)
    assert book.store.about() == "- A physicist."
    assert get_part(book.store.notes_md("ch"), "Inputs") == "## About you\n\n> Tell us about yourself.\n\nA physicist."
    wait(book)

    assert list_versions(chapter.dir) == [0, 1]
    assert sorted(p.name for p in chapter.version_dir.iterdir()) == [
        "alpha.md", "beta.md", "sources.json", "symbols.md", "welcome.md",
    ]
    for request in fake_llm.requests("rewrite"):
        assert 'The reader just answered "About you" with: A physicist.\n\n' in request
        assert "The book's reason to rewrite: New background." in request
    saved = json.loads(book.store.answers_path("ch").read_text())
    assert saved["text_inputs"] == {"about-you": {"state": "done", "answer": "A physicist."}}


def test_a_text_input_the_note_step_ignores_rewrites_nothing(book: Book, fake_llm: FakeLLM):
    chapter = book.chapter("ch")
    assert not book.submit_text_input(chapter, chapter.text_inputs["about-you"], "Nothing much.")
    assert list_versions(chapter.dir) == [0]
    assert [name for name, _ in fake_llm.calls] == ["memory"]
    assert book.running() == 0


def test_skip_text_input_is_saved(book: Book):
    chapter = book.chapter("ch")
    book.skip_text_input(chapter, chapter.text_inputs["about-you"])
    saved = json.loads(book.store.answers_path("ch").read_text())
    assert saved["text_inputs"] == {"about-you": {"state": "skipped", "answer": ""}}


def test_first_visit_writes_the_unwritten_sections(book: Book, small_vault: Path, fake_llm: FakeLLM):
    chapter = book.chapter("ch")
    book.first_visit(chapter)
    assert list_versions(chapter.dir) == [0]

    (small_vault / "ch" / "beta.md").write_text("---\ntopics: [third topic]\n---\n# Beta\n")
    book.adapter._active["ch"] = 1
    book.first_visit(chapter)
    assert list_versions(chapter.dir) == [0]
    book.adapter._active["ch"] = 0
    book.first_visit(chapter)
    wait(book)
    assert sorted(p.name for p in chapter.version_dir.iterdir()) == ["beta.md", "sources.json"]
    [request] = fake_llm.requests("rewrite")
    assert "The section has no text yet." in request and request.endswith("(not written yet)")


def test_personalize_again_rewrites_what_the_author_changed(book: Book, small_vault: Path, fake_llm: FakeLLM):
    chapter = book.chapter("ch")
    assert book.personalize_again(chapter) == []
    chapter.override_path("alpha").write_text("Alpha for the reader.\n")
    chapter.record_source("alpha")
    (small_vault / "ch" / "alpha.md").write_text("# Alpha\n\nThe author's new text.\n")

    assert book.personalize_again(chapter) == ["alpha"]
    wait(book)
    assert chapter.version_dir.name == "v_1" and chapter.stale_sections() == []
    [request] = fake_llm.requests("rewrite")
    assert "The author updated this section" in request
    assert request.endswith("Current text of the section:\n\nThe author's new text.")


def test_wipe_empties_the_reader_folder(book: Book, fake_llm: FakeLLM):
    chapter = book.chapter("ch")
    book.store.add_about("Knows calculus.")
    chapter.new_version()
    book.wipe()
    assert sorted(p.name for p in book.store.dir.iterdir()) == ["reader.md"]


def test_a_one_file_page_is_adaptive(book: Book, small_vault: Path):
    page = book.chapter("page")
    assert (page.key, page.title, page.doc.page) == ("page", "A Page", small_vault / "page.md")
    assert page.dir == book.store.dir / "page" and page.version_dir.name == "v_0"
    # Its only heading is its title, so the page is one section
    assert page.section_names == ["a-page"] and [b.kind for b in page.doc.blocks] == ["prior", "section", "learned"]
    # A page-file edit reloads the page
    (small_vault / "page.md").write_text("# A Page\n\n## Part\n\nMore.\n")
    bump_mtime(small_vault / "page.md")
    reloaded = book.chapter("page")
    assert reloaded is not page and reloaded.section_names == ["part"] and reloaded.doc.sections["part"].inline
    assert reloaded.quiz_paths("part")[0] == small_vault / "page.part.quiz.md"
