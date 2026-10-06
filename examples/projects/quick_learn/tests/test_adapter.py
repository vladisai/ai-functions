"""The adapter: which reader actions rewrite which sections, and how one rewrite writes into a version."""

import json
import shutil
import threading
from pathlib import Path

import pytest
from conftest import FakeLLM, words
from quicklearn import llm
from quicklearn.agents import adapter as adapter_module
from quicklearn.agents.adapter import (
    WRITING_MARK,
    Adapter,
    Task,
    _strip_fences,
    format_answers,
    has_gaps,
    quiz_summary,
)
from quicklearn.chapter.state import SOURCES_FILE, ChapterState, vault_hash
from quicklearn.chapter.versions import list_versions
from quicklearn.core.quiz import QuestionType, Quiz, QuizQuestion
from quicklearn.reader.store import ReaderStore


@pytest.fixture
def adapter(store: ReaderStore):
    adapter = Adapter(store)
    yield adapter
    adapter.stop()


def answered(quiz_id: str, *answers: str) -> Quiz:
    """A quiz of two pick-one questions whose right answers are "a", with the reader's answers."""
    quiz = Quiz(id=quiz_id, questions=[
        QuizQuestion(text="First?", options=["x", "y"], correct_answer="a"),
        QuizQuestion(text="Second?", options=["x", "y"], correct_answer="a"),
    ])
    for i, answer in enumerate(answers):
        quiz.submit_answer(i, answer)
    return quiz


# -- Plans --


def test_prior_quiz_all_right_on_a_compact_section_rewrites_nothing(adapter: Adapter, chapter: ChapterState):
    plan = adapter.plan_for_quiz(chapter, answered("alpha.prior", "a", "a"))
    assert plan.tasks == [] and "compact reference" in plan.next_step


def test_prior_quiz_all_right_on_a_long_section_condenses_it(adapter: Adapter, chapter: ChapterState):
    chapter.override_path("alpha").write_text(words("longer", 126))
    plan = adapter.plan_for_quiz(chapter, answered("alpha.prior", "a", "a"))
    assert [(t.section, t.quiz, t.from_vault) for t in plan.tasks] == [("alpha", "", False)]
    assert "condensed" in plan.next_step
    assert "Q1 (correct)" in plan.tasks[0].reason and "Q2 (correct)" in plan.tasks[0].reason


def test_prior_quiz_with_gaps_rewrites_and_adds_a_learned_quiz(adapter: Adapter, chapter: ChapterState):
    plan = adapter.plan_for_quiz(chapter, answered("beta.prior", "a", "b"))
    assert [(t.section, t.quiz) for t in plan.tasks] == [("beta", "learned")]
    assert "Q2 (WRONG)" in plan.tasks[0].reason
    # An unanswered question is a gap too
    assert len(adapter.plan_for_quiz(chapter, answered("beta.prior", "a")).tasks) == 1


def test_learned_quiz_with_gaps_rewrites_with_a_fresh_quiz(adapter: Adapter, chapter: ChapterState):
    plan = adapter.plan_for_quiz(chapter, answered("alpha.learned", "b", "a"))
    assert [(t.section, t.quiz) for t in plan.tasks] == [("alpha", "learned")]
    assert "quiz after it" in plan.tasks[0].reason
    last = adapter.plan_for_quiz(chapter, answered("beta.learned", "b", "b"))
    assert [(t.section, t.quiz) for t in last.tasks] == [("beta", "learned")]


def test_learned_quiz_all_right_moves_on(adapter: Adapter, chapter: ChapterState):
    plan = adapter.plan_for_quiz(chapter, answered("alpha.learned", "a", "a"))
    assert (plan.next_step, plan.tasks) == ("You are ready for the next section.", [])
    # Symbols comes after Beta, but it has no quiz, so Beta's ends the chapter
    last = adapter.plan_for_quiz(chapter, answered("beta.learned", "a", "a"))
    assert (last.next_step, last.tasks) == ("That completes the chapter.", [])


def test_plan_for_all_stale_and_empty(adapter: Adapter, chapter: ChapterState, small_vault: Path):
    assert [(t.section, t.reason) for t in adapter.plan_for_all(chapter, "New goals.")] == [
        ("welcome", "New goals."), ("alpha", "New goals."), ("beta", "New goals."), ("symbols", "New goals."),
    ]
    assert adapter.plan_for_stale(chapter) == [] and adapter.plan_for_empty(chapter) == []

    chapter.override_path("alpha").write_text("Alpha for the reader.\n")
    chapter.record_source("alpha")
    (small_vault / "ch" / "alpha.md").write_text("# Alpha\n\nThe author's new text.\n")
    assert [(t.section, t.from_vault, t.quiz) for t in adapter.plan_for_stale(chapter)] == [
        ("alpha", True, "")
    ]

    (small_vault / "ch" / "beta.md").write_text("---\ntopics: [third topic]\n---\n# Beta\n")
    assert [(t.section, t.from_vault) for t in adapter.plan_for_empty(chapter)] == [("beta", False)]


# -- Answers for the model and for notes.md --


def test_has_gaps():
    assert not has_gaps(answered("q", "a", "a"))
    assert has_gaps(answered("q", "a", "b"))
    assert has_gaps(answered("q", "a"))
    assert not has_gaps(Quiz(id="q", questions=[]))


def test_quiz_summary():
    assert quiz_summary(answered("q", "a", "a")) == "2 of 2 right."
    assert quiz_summary(answered("q", "b")) == "0 of 2 right. Missed: Q1 First?; Q2 Second?."
    long = Quiz(id="q", questions=[
        QuizQuestion(text=" ".join(f"w{i}" for i in range(20)), options=["x"], correct_answer="a"),
    ])
    assert quiz_summary(long) == "0 of 1 right. Missed: Q1 w0 w1 w2 w3 w4 w5 w6 w7 w8 w9 w10 w11…."


def test_format_answers():
    quiz = Quiz(id="q", questions=[
        QuizQuestion(text="Judge", question_type=QuestionType.MULTI_TF, options=["p", "q"], correct_answer="a:T,b:F"),
        QuizQuestion(text="Explain", question_type=QuestionType.FREE_FORM),
    ])
    quiz.submit_answer(0, "a:T,b:T")
    assert format_answers(quiz) == (
        "Q1 (WRONG): Judge\n  a) p\n  b) q\n  Reader answered: a:T,b:T\n  Correct answer: a:T,b:F\n\n"
        "Q2 (unanswered): Explain\n  Reader answered: -\n  Correct answer: None"
    )


def test_strip_fences():
    assert _strip_fences("```markdown\n# Learned\n\n1. Q\n   - [x] a\n```\n") == "\n1. Q\n   - [x] a"
    assert _strip_fences("  1. Q\n   - [x] a\n") == "1. Q\n   - [x] a"
    assert _strip_fences("# Prior\n1. Q") == "1. Q"
    assert _strip_fences("```") == ""


# -- One rewrite --


def test_rewrite_streams_into_the_version_and_records_its_source(
    adapter: Adapter, chapter: ChapterState, store: ReaderStore, fake_llm: FakeLLM
):
    store.add_about("Knows calculus.")
    store.add_note("ch", "Mixes up pmf and pdf.")
    v1 = chapter.new_version()
    text = adapter._rewrite(chapter, Task("alpha", "The reader asked for examples."), v1)

    assert text == (v1 / "alpha.md").read_text() == "New text.\n\nMore text.\n"
    assert json.loads((v1 / SOURCES_FILE).read_text()) == {"alpha": vault_hash(chapter.vault_body("alpha"))}
    assert chapter.stale_sections() == []
    [request] = fake_llm.requests("rewrite")
    assert "<reader>\n# About the reader\n\n- Knows calculus.\n</reader>" in request
    assert "- Mixes up pmf and pdf.\n</chapter_notes>" in request
    assert "<chapter_guide>\nHints for the rewrites.\n</chapter_guide>" in request
    assert "The reader asked for examples." in request
    assert 'Section: "Alpha". Subsection headers use ##.\nTopics: first topic; second topic\n' in request
    assert request.endswith("Current text of the section:\n\n" + words("alpha", 100).strip())


def test_rewrite_starts_from_the_reader_text_or_the_vault(adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM):
    chapter.override_path("alpha").write_text("The reader's version.\n")
    adapter._rewrite(chapter, Task("alpha", "Again."), chapter.version_dir)
    adapter._rewrite(chapter, Task("alpha", "The author changed it.", from_vault=True), chapter.version_dir)
    again, from_vault = fake_llm.requests("rewrite")
    assert again.endswith("Current text of the section:\n\nThe reader's version.")
    assert from_vault.endswith(words("alpha", 100).strip())


def test_rewrite_of_an_unwritten_section(make_vault, fake_llm: FakeLLM):
    vault = make_vault({"ch/chapter.md": "![[todo]]\n", "ch/todo.md": "### Todo\n"})
    chapter = ChapterState(vault / "ch" / "chapter.md", vault, ReaderStore(vault, "tester"))
    Adapter(chapter.store)._rewrite(chapter, Task("todo", "Write it."), chapter.version_dir)
    [request] = fake_llm.requests("rewrite")
    assert "Subsection headers use ####.\nTopics: as in the current text\n" in request
    assert "<chapter_guide>\n\n</chapter_guide>" in request
    assert request.endswith("(not written yet)")


def test_rewrite_shows_the_finished_paragraphs_while_it_streams(
    adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(adapter_module, "_FLUSH_SECONDS", -1)
    path = chapter.override_path("alpha")
    seen = []
    fake_llm.replies["rewrite"] = ["First paragraph.\n\nSecond", lambda: seen.append(path.read_text()), " paragraph."]
    adapter._rewrite(chapter, Task("alpha", "reason"), chapter.version_dir)
    assert seen == ["First paragraph." + WRITING_MARK]
    assert path.read_text() == "First paragraph.\n\nSecond paragraph.\n"


def test_a_stopped_rewrite_puts_back_the_file(
    adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(adapter_module, "_FLUSH_SECONDS", -1)
    fake_llm.replies["rewrite"] = ["Half of it.\n\n", "More", adapter._stopped.set, " and the end."]
    path = chapter.override_path("alpha")

    with pytest.raises(llm.Stopped):
        adapter._rewrite(chapter, Task("alpha", "reason"), chapter.version_dir)
    # There was no rewrite before, so the vault text shows again
    assert not path.exists() and chapter.section_path("alpha") == chapter.doc.sections["alpha"].path

    path.write_text("The earlier rewrite.\n")
    adapter._stopped.clear()
    with pytest.raises(llm.Stopped):
        adapter._rewrite(chapter, Task("alpha", "reason"), chapter.version_dir)
    assert path.read_text() == "The earlier rewrite.\n"
    assert not (chapter.version_dir / SOURCES_FILE).exists()


def test_a_rewrite_stopped_by_a_reset_leaves_no_folder(adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM):
    version_dir = chapter.version_dir

    def reset():
        shutil.rmtree(chapter.store.dir)
        adapter._stopped.set()

    fake_llm.replies["rewrite"] = ["Half.\n\n", reset, "The rest."]
    with pytest.raises(llm.Stopped):
        adapter._rewrite(chapter, Task("alpha", "reason"), version_dir)
    assert not version_dir.exists()


# -- The learned quiz --


def test_learned_quiz_is_written_into_the_version(adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM):
    fake_llm.replies["learned_quiz"] = "```markdown\n# Learned\n\n1. About alpha\n   - [ ] no\n   - [x] yes\n```"
    adapter._write_quiz(chapter, Task("alpha", "Missed Q1.", quiz="learned"), chapter.version_dir, "The new text.\n")

    path = chapter.version_dir / "alpha.quiz.md"
    assert path.read_text() == "# Learned\n\n1. About alpha\n   - [ ] no\n   - [x] yes\n"
    # The vault's quiz has one question, so the new quiz has as many
    [request] = fake_llm.requests("learned_quiz")
    assert "Missed Q1.\n\nThis quiz comes after the section" in request
    assert "Write 1 questions about this section:\n\nThe new text.\n" in request
    assert chapter.live.poll_all() == {"alpha.learned"}
    assert [q.text for q in chapter.quizzes["alpha.learned"].questions] == ["About alpha"]
    assert [q.text for q in chapter.quizzes["alpha.prior"].questions] == ["Pick one"]


def test_learned_quiz_without_questions_writes_nothing(adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM):
    fake_llm.replies["learned_quiz"] = "Sorry, I cannot write a quiz."
    adapter._write_quiz(chapter, Task("alpha", "reason", quiz="learned"), chapter.version_dir, "Text.\n")
    assert not (chapter.version_dir / "alpha.quiz.md").exists()


def test_learned_quiz_of_a_section_without_a_quiz_file(make_vault, fake_llm: FakeLLM):
    vault = make_vault({"ch/chapter.md": "![[plain]]\n", "ch/plain.md": "# Plain\n\nText.\n"})
    chapter = ChapterState(vault / "ch" / "chapter.md", vault, ReaderStore(vault, "tester"))
    Adapter(chapter.store)._write_quiz(chapter, Task("plain", "reason", quiz="learned"), chapter.version_dir, "Text.\n")
    assert "Write 4 questions" in fake_llm.requests("learned_quiz")[0]
    assert (chapter.version_dir / "plain.quiz.md").read_text().startswith("# Learned\n\n1. A new question\n")


def test_run_rewrites_then_writes_the_quiz_and_counts_down(adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM):
    adapter._active["ch"] = 1
    adapter._run(chapter, Task("alpha", "reason", quiz="learned"), chapter.version_dir)
    assert [name for name, _ in fake_llm.calls] == ["rewrite", "learned_quiz"]
    assert "Write 1 questions about this section:\n\nNew text.\n\nMore text.\n" in fake_llm.requests("learned_quiz")[0]
    assert adapter.active_in("ch") == 0

    adapter._active["ch"] = 1
    adapter._stopped.set()
    with pytest.raises(llm.Stopped):
        adapter._run(chapter, Task("alpha", "reason"), chapter.version_dir)
    assert adapter.active_in("ch") == 0


def test_feedback(adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM):
    fake_llm.replies["feedback"] = "  Well done.\n"
    assert adapter.feedback(chapter, answered("alpha.prior", "a", "b"), "The section is rewritten.") == "Well done."
    [request] = fake_llm.requests("feedback")
    assert "Quiz answers:\n\nQ1 (correct): First?" in request
    assert request.endswith("What the book does next: The section is rewritten.")


# -- In the background --


def test_tasks_started_while_others_write_share_one_version(
    adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM
):
    gate = threading.Event()
    fake_llm.replies["rewrite"] = [lambda: gate.wait(5), "New text."]
    adapter.start(chapter, [])
    assert list_versions(chapter.dir) == [0]

    adapter.start(chapter, [Task("alpha", "reason")])
    adapter.start(chapter, [Task("beta", "reason")])
    assert adapter.active_tasks() == 2 and adapter.active_in("ch") == 2
    gate.set()
    adapter._pool.shutdown(wait=True)

    assert list_versions(chapter.dir) == [0, 1] and chapter.version_dir.name == "v_1"
    assert sorted(p.name for p in chapter.version_dir.iterdir()) == ["alpha.md", "beta.md", SOURCES_FILE]
    assert (chapter.version_dir / "alpha.md").read_text() == "New text.\n"
    assert adapter.active_tasks() == 0


def test_stop_ends_a_running_task_before_it_writes(adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM):
    started, gate = threading.Event(), threading.Event()
    fake_llm.replies["rewrite"] = [started.set, lambda: gate.wait(5), "New text."]
    adapter.start(chapter, [Task("alpha", "reason")])
    assert started.wait(5)
    adapter.stop()
    gate.set()
    adapter._pool.shutdown(wait=True)

    assert not chapter.override_path("alpha").exists()
    assert adapter.active_tasks() == 0


# -- add_quiz: a quiz without a rewrite --


def test_a_quiz_task_writes_only_the_quiz_into_a_new_version(
    adapter: Adapter, chapter: ChapterState, fake_llm: FakeLLM,
):
    """What the tutor's add_quiz starts: Task(rewrite=False, quiz=part), here on the inline section welcome."""
    (chapter.version_dir / "welcome.quiz.md").write_text("# Learned\n\n1. Kept\n   - [x] yes\n   - [ ] no\n")
    assert chapter.live.poll_all() == {"welcome.learned"}
    adapter.start(chapter, [Task("welcome", "The reader asked in chat: test me first.", quiz="prior", rewrite=False)])
    adapter._pool.shutdown(wait=True)

    assert list_versions(chapter.dir) == [0, 1] and chapter.version_dir.name == "v_1"
    assert [name for name, _ in fake_llm.calls] == ["learned_quiz"]
    [request] = fake_llm.requests("learned_quiz")
    assert "This quiz comes before the section" in request
    assert "Write 4 questions about this section:\n\nFixed text that links [beta](#section-beta)" in request
    # The text stays the vault's, and the quiz keeps the learned part the version had
    assert sorted(p.name for p in chapter.version_dir.iterdir()) == ["welcome.quiz.md"]
    assert (chapter.version_dir / "welcome.quiz.md").read_text() == (
        "# Prior\n\n1. A new question\n   - [x] right\n   - [ ] wrong\n\n"
        "# Learned\n\n1. Kept\n   - [x] yes\n   - [ ] no\n"
    )
    assert chapter.live.poll_all() == {"welcome.prior"}
    assert [q.text for q in chapter.quizzes["welcome.prior"].questions] == ["A new question"]
    assert [q.text for q in chapter.quizzes["welcome.learned"].questions] == ["Kept"]
    assert adapter.active_in("ch") == 0


def test_the_quiz_rules_apply_to_an_inline_section(adapter: Adapter, chapter: ChapterState):
    chapter.quizzes["symbols.prior"].questions = [QuizQuestion(text="Q", options=["a", "b"], correct_answer="a")]
    plan = adapter.plan_for_quiz(chapter, chapter.quizzes["symbols.prior"])
    assert [(t.section, t.quiz, t.rewrite) for t in plan.tasks] == [("symbols", "learned", True)]
