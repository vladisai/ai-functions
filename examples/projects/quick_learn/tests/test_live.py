"""Disk changes reach every open page, reset a quiz only when its questions change, and survive
browsing older versions.
"""

import json
import os
from pathlib import Path

from conftest import words
from quicklearn.chapter.live import fingerprint
from quicklearn.chapter.state import ChapterState
from quicklearn.core.quiz import QuizQuestion, QuizState
from quicklearn.reader.store import ReaderStore

LEARNED = "# Learned\n\n1. A new question\n   - [x] right\n   - [ ] wrong\n"


def bump_mtime(path: Path) -> None:
    """Move the mtime on, since two writes in a row can land on the same mtime tick."""
    st = path.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))


def test_a_change_reaches_every_bound_page_until_unbound(chapter: ChapterState):
    live = chapter.live.by_id["alpha"]
    seen: list[str] = []
    first, second = (lambda _: seen.append("first")), (lambda _: seen.append("second"))
    live.bind(first)
    live.bind(second)

    chapter.override_path("alpha").write_text("Rewritten.\n")
    assert chapter.live.poll_all() == {"alpha"}
    assert seen == ["first", "second"]
    assert chapter.material.get_section("alpha").content == "Rewritten.\n"

    live.unbind(first)
    chapter.override_path("alpha").write_text("Rewritten again.\n")
    bump_mtime(chapter.override_path("alpha"))
    assert chapter.live.poll_all() == {"alpha"}
    assert seen == ["first", "second", "second"]
    assert chapter.live.poll_all() == set()


def test_a_touched_file_with_the_same_text_is_no_change(chapter: ChapterState, small_vault: Path):
    seen = []
    chapter.live.by_id["alpha"].bind(seen.append)
    bump_mtime(small_vault / "ch" / "alpha.md")
    assert chapter.live.poll_all() == set() and seen == []


def test_a_vault_edit_shows_on_the_page(chapter: ChapterState, small_vault: Path):
    path = small_vault / "ch" / "beta.md"
    path.write_text("# Beta\n\nThe author's fix, see [[alpha]].\n")
    bump_mtime(path)
    assert chapter.live.poll_all() == {"beta"}
    assert chapter.material.get_section("beta").content == "The author's fix, see [alpha](#section-alpha).\n"


def test_a_new_learned_quiz_resets_only_that_quiz(chapter: ChapterState):
    prior, learned = chapter.quizzes["alpha.prior"], chapter.quizzes["alpha.learned"]
    prior.submit_answer(0, "b")
    prior.complete()
    learned.skip()
    seen = []
    chapter.live.by_id["alpha.learned"].bind(seen.append)

    (chapter.version_dir / "alpha.quiz.md").write_text(LEARNED)
    # The prior part still comes from the vault, so its answers stay
    assert chapter.live.poll_all() == {"alpha.learned"}
    assert len(seen) == 1
    assert [q.text for q in learned.questions] == ["A new question"]
    assert (learned.state, learned.answers) == (QuizState.ACTIVE, {})
    assert (prior.state, prior.answers) == (QuizState.COMPLETED, {0: "b"})
    saved = json.loads(chapter.store.answers_path("ch").read_text())["quizzes"]
    assert list(saved) == ["alpha.prior"]


def test_an_unchanged_quiz_keeps_its_answers_in_a_new_version(chapter: ChapterState):
    (chapter.version_dir / "alpha.quiz.md").write_text(LEARNED)
    chapter.live.poll_all()
    learned = chapter.quizzes["alpha.learned"]
    learned.submit_answer(0, "a")
    learned.complete()

    chapter.new_version()
    assert chapter.live.poll_all() == set()
    assert (learned.state, learned.answers) == (QuizState.COMPLETED, {0: "a"})


def test_a_change_while_browsing_an_older_version_shows_on_return(chapter: ChapterState):
    material = chapter.material
    head = material.get_section("alpha")
    chapter.new_version()
    material.go_to_version(0)

    chapter.override_path("alpha").write_text("Rewritten while you read v_0.\n")
    assert chapter.live.poll_all() == {"alpha"}
    assert material.get_section("alpha").content == words("alpha", 100)

    material.go_to_head()
    assert material.get_section("alpha") is head
    assert head.content == "Rewritten while you read v_0.\n"


def test_a_version_made_elsewhere_joins_the_version_bar(chapter: ChapterState, small_vault: Path):
    # E.g. the app restarted in another process, or a tool wrote the reader folder
    other = ChapterState(small_vault / "ch" / "chapter.md", small_vault, ReaderStore(small_vault, "tester"))
    other.new_version()
    other.override_path("alpha").write_text("From elsewhere.\n")

    assert chapter.material.total_versions == 1
    assert chapter.live.poll_all() == {"alpha"}
    assert chapter.material.total_versions == 2
    assert chapter.material.version_stack[0].sections[6].content == words("alpha", 100)


def test_fingerprint():
    question = QuizQuestion(text="Pick", options=["a", "b"], correct_answer="a")
    assert fingerprint([question]) == fingerprint([QuizQuestion(text="Pick", options=["a", "b"], correct_answer="a")])
    assert fingerprint([question]) != fingerprint([QuizQuestion(text="Pick", options=["a", "c"], correct_answer="a")])
    assert fingerprint([question]) != fingerprint([QuizQuestion(text="Pick", options=["a", "b"], correct_answer="b")])
    assert fingerprint([]) != fingerprint([question])


def test_an_empty_quiz_slot_shows_its_quiz_once_it_exists(chapter: ChapterState, small_vault: Path):
    assert chapter.quizzes["symbols.prior"].questions == []
    seen = []
    chapter.live.by_id["symbols.prior"].bind(seen.append)
    (small_vault / "ch" / "symbols.quiz.md").write_text("# Prior\n\n1. Which?\n   - [x] a\n   - [ ] b\n")
    assert chapter.live.poll_all() == {"symbols.prior"}
    assert [q.text for q in chapter.quizzes["symbols.prior"].questions] == ["Which?"] and len(seen) == 1
    # And in the reader's version folder, e.g. from the tutor's add_quiz
    (chapter.version_dir / "symbols.quiz.md").write_text("# Learned\n\n1. After?\n   - [x] a\n   - [ ] b\n")
    assert chapter.live.poll_all() == {"symbols.learned"}
    assert [q.text for q in chapter.quizzes["symbols.learned"].questions] == ["After?"]
