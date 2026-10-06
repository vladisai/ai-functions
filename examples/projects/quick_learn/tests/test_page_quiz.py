"""The page's own quiz and quiz tags: where the page quiz sits, which sections a tag names, what a submit rewrites."""

from pathlib import Path

import pytest
from conftest import FakeLLM
from quicklearn.agents.adapter import Adapter, Task
from quicklearn.book import Book
from quicklearn.chapter.state import PAGE_QUIZ_TITLES, ChapterState
from quicklearn.chapter.versions import list_versions
from quicklearn.reader.store import ReaderStore
from quicklearn.vault.chapter import parse_chapter, parse_page
from quicklearn.vault.quiz_md import parse_quiz, split_tags

LECTURE = """# Lecture

*By the author*

## Systems

Systems text.

## Policies

Policies text.

![[rewards]]
"""

# The page's background check: Q1 on systems, Q2 on policies and rewards, Q3 untagged
PAGE_QUIZ = """# Prior

1. About systems? [[lecture#Systems]]
   - [x] yes
   - [ ] no
2. About policies and rewards? [[lecture#Policies]] [[rewards]]
   - [x] yes
   - [ ] no
3. Untagged?
   - [x] yes
   - [ ] no
"""

# The learned quiz of a group, in its last section: Q1 on systems, Q2 on rewards, Q3 untagged so on rewards
GROUP_QUIZ = """# Learned

1. On systems? [[lecture#Systems]]
   - [x] yes
   - [ ] no
2. On rewards? [[rewards]]
   - [x] yes
   - [ ] no
3. Untagged?
   - [x] yes
   - [ ] no
"""

LECTURE_VAULT = {
    "outline.md": "# Book\n\n- [[lectures/lecture|Lecture]]\n",
    "lectures/lecture.md": LECTURE,
    "lectures/lecture.quiz.md": PAGE_QUIZ,
    "lectures/rewards.md": "# Rewards\n\nRewards text.\n",
    "lectures/lecture.rewards.quiz.md": GROUP_QUIZ,
}


@pytest.fixture
def vault(make_vault) -> Path:
    return make_vault(LECTURE_VAULT)


@pytest.fixture
def lecture(vault: Path) -> ChapterState:
    return ChapterState(vault / "lectures" / "lecture.md", vault, ReaderStore(vault, "tester"))


@pytest.fixture
def adapter(lecture: ChapterState):
    adapter = Adapter(lecture.store)
    yield adapter
    adapter.stop()


def answer(chapter: ChapterState, quiz_id: str, *answers: str):
    quiz = chapter.quizzes[quiz_id]
    for i, letter in enumerate(answers):
        quiz.submit_answer(i, letter)
    return quiz


# -- The page quiz's blocks --


def test_the_page_quiz_comes_after_the_title_and_at_the_end(vault: Path):
    doc = parse_page(vault / "lectures" / "lecture.md", vault)
    ids = [b.id for b in doc.blocks]
    assert ids[:3] == ["fixed-1", "lecture.prior", "systems.prior"] and ids[-1] == "lecture.learned"
    assert doc.quiz_path("lecture") == vault / "lectures" / "lecture.quiz.md"
    assert doc.quiz_path("systems") == vault / "lectures" / "lecture.systems.quiz.md"


def test_the_page_quiz_reserves_the_stem_only_when_its_file_exists(make_vault):
    vault = make_vault({"preface.md": "# Preface\n\nWhy.\n", "ch/chapter.md": "# Ch\n\n# Chapter\n\nText.\n"})
    # Without preface.quiz.md the only section keeps the stem's name, and its slots stand for the page's
    preface = parse_page(vault / "preface.md", vault)
    assert [b.id for b in preface.blocks] == ["preface.prior", "preface", "preface.learned"]
    assert preface.quiz_path("preface") == vault / "preface.preface.quiz.md"
    (vault / "preface.quiz.md").write_text(PAGE_QUIZ)
    preface = parse_page(vault / "preface.md", vault)
    assert [b.id for b in preface.blocks] == [
        "preface.prior", "preface-2.prior", "preface-2", "preface-2.learned", "preface.learned"
    ]
    (vault / "ch" / "chapter.quiz.md").write_text(PAGE_QUIZ)
    chapter = parse_chapter(vault / "ch", vault)
    assert [b.id for b in chapter.blocks][:3] == ["fixed-1", "chapter.prior", "chapter-2.prior"]


def test_the_page_quiz_shows_as_a_background_check(lecture: ChapterState):
    sections = {s.id: s for s in lecture.material.sections}
    assert sections["lecture.prior"].title == PAGE_QUIZ_TITLES["prior"]
    assert sections["lecture.learned"].title == PAGE_QUIZ_TITLES["learned"]
    assert [q.text for q in lecture.quizzes["lecture.prior"].questions] == [
        "About systems?", "About policies and rewards?", "Untagged?"
    ]
    # An empty slot has no questions, so the page shows nothing for it
    assert lecture.quizzes["lecture.learned"].questions == []
    assert lecture.quiz_paths("lecture")[1] == lecture.version_dir / "lecture.quiz.md"


# -- Tags --


def test_tags_end_the_text_and_stay_out_of_it():
    assert split_tags("About it? [[lecture_2#Stochastic dynamical systems]] [[random-variables]]") == (
        "About it?", ["lecture_2#Stochastic dynamical systems", "random-variables"]
    )
    assert split_tags("See [[here]] for more.") == ("See [[here]] for more.", [])
    assert split_tags("A figure ![[plot.png]]") == ("A figure ![[plot.png]]", [])
    assert split_tags("Aliased [[beta|the beta section]]") == ("Aliased", ["beta"])
    [parsed] = parse_quiz("# Prior\n\n1. Two lines\n   then tags [[a]]\n   - [x] yes\n   - [ ] no\n").prior
    assert (parsed.question.text, parsed.links) == ("Two lines\nthen tags", ["a"])


def test_a_tag_names_a_heading_by_its_slug_or_an_embedded_section(lecture: ChapterState):
    doc = lecture.doc
    assert doc.link_section("lecture#Systems") == "systems"
    assert doc.link_section("lectures/lecture#Policies") == "policies"
    assert doc.link_section("rewards") == "rewards" and doc.link_section("lecture#Rewards") == "rewards"
    assert doc.link_section("lecture#Nowhere") is None and doc.link_section("other#Systems") is None
    assert doc.link_section("nowhere") is None
    assert (doc.tag("systems"), doc.tag("rewards")) == ("lecture#Systems", "rewards")
    assert lecture.question_sections(lecture.quizzes["lecture.prior"]) == [["systems"], ["policies", "rewards"], []]


# -- Plans --


def test_a_page_prior_with_gaps_rewrites_the_tagged_sections_of_the_misses(adapter: Adapter, lecture: ChapterState):
    plan = adapter.plan_for_quiz(lecture, answer(lecture, "lecture.prior", "a", "b", "b"))
    # Q2 missed: policies and rewards, in page order; the untagged Q3 only goes to the notes
    assert [(t.section, t.quiz, t.rewrite) for t in plan.tasks] == [("policies", "", True), ("rewards", "", True)]
    assert "Q2 (WRONG): About policies and rewards?" in plan.tasks[0].reason
    assert "Q1" not in plan.tasks[0].reason and "Q3" not in plan.tasks[0].reason
    assert plan.next_step == 'The sections "Policies" and "Rewards" are being rewritten around what you missed.'


def test_a_page_prior_rewrites_nothing_without_gaps_or_tagged_misses(adapter: Adapter, lecture: ChapterState):
    plan = adapter.plan_for_quiz(lecture, answer(lecture, "lecture.prior", "a", "a", "a"))
    assert plan.tasks == [] and "background already" in plan.next_step
    lecture.quizzes["lecture.prior"].answers.clear()
    plan = adapter.plan_for_quiz(lecture, answer(lecture, "lecture.prior", "a", "a", "b"))
    assert plan.tasks == [] and "notes" in plan.next_step


def test_a_group_learned_quiz_with_gaps_rewrites_its_tagged_sections_then_a_fresh_quiz(
    adapter: Adapter, lecture: ChapterState
):
    plan = adapter.plan_for_quiz(lecture, answer(lecture, "rewards.learned", "b", "a", "a"))
    covers = ["systems", "rewards"]
    assert [(t.section, t.quiz, t.rewrite, t.covers) for t in plan.tasks] == [
        ("systems", "", True, []), ("rewards", "learned", False, covers),
    ]
    # The untagged Q3 is about the quiz's own section
    lecture.quizzes["rewards.learned"].answers.clear()
    plan = adapter.plan_for_quiz(lecture, answer(lecture, "rewards.learned", "a", "a", "b"))
    assert [(t.section, t.quiz, t.rewrite) for t in plan.tasks] == [
        ("rewards", "", True), ("rewards", "learned", False),
    ]


def test_a_learned_quiz_all_right_points_to_what_is_left(adapter: Adapter, lecture: ChapterState):
    plan = adapter.plan_for_quiz(lecture, answer(lecture, "rewards.learned", "a", "a", "a"))
    assert plan.next_step == "That completes the chapter."
    (lecture.version_dir / "lecture.quiz.md").write_text(GROUP_QUIZ)
    lecture.live.poll_all()
    assert adapter.plan_for_quiz(lecture, lecture.quizzes["rewards.learned"]).next_step == (
        "You are ready for the check at the end of the page."
    )
    assert adapter.plan_for_quiz(lecture, answer(lecture, "lecture.learned", "a", "a", "a")).next_step == (
        "That completes the chapter."
    )


def test_the_fresh_group_quiz_waits_for_the_rewrites_and_covers_every_section(
    adapter: Adapter, lecture: ChapterState, fake_llm: FakeLLM
):
    fake_llm.replies["learned_quiz"] = (
        "1. Fresh on systems [[lecture#Systems]] [[lecture#Nowhere]]\n   - [x] right\n   - [ ] wrong\n"
        "2. Fresh on rewards [[rewards]]\n   - [x] right\n   - [ ] wrong\n"
    )
    adapter.start(lecture, adapter.plan_for_quiz(lecture, answer(lecture, "rewards.learned", "b", "a", "a")).tasks)
    adapter._pool.shutdown(wait=True)

    assert list_versions(lecture.dir) == [0, 1]
    assert [name for name, _ in fake_llm.calls] == ["rewrite", "learned_quiz"]
    [request] = fake_llm.requests("learned_quiz")
    # The quiz is written from the rewritten text of systems and the text of rewards, each with its tag
    assert '<section title="Systems" tag="[[lecture#Systems]]">\nNew text.\n\nMore text.\n</section>' in request
    assert '<section title="Rewards" tag="[[rewards]]">\nRewards text.\n</section>' in request
    assert "Write 3 questions about these sections" in request
    # A tag that names no section is dropped, the others stay in the file
    assert (lecture.version_dir / "rewards.quiz.md").read_text() == (
        "# Learned\n\n1. Fresh on systems [[lecture#Systems]]\n   - [x] right\n   - [ ] wrong\n"
        "2. Fresh on rewards [[rewards]]\n   - [x] right\n   - [ ] wrong\n"
    )
    assert lecture.live.poll_all() == {"systems", "rewards.learned"}
    assert [q.text for q in lecture.quizzes["rewards.learned"].questions] == ["Fresh on systems", "Fresh on rewards"]
    assert adapter.active_in(lecture.key) == 0


def test_a_page_quiz_task_writes_the_page_quiz(adapter: Adapter, lecture: ChapterState, fake_llm: FakeLLM):
    """What the tutor's add_quiz starts for the page: its prior, on every section."""
    task = Task("lecture", "The reader asked in chat.", quiz="prior", rewrite=False, covers=lecture.section_names)
    adapter.start(lecture, [task])
    adapter._pool.shutdown(wait=True)

    [request] = fake_llm.requests("learned_quiz")
    assert "This quiz comes at the start of the page" in request and "Write 3 questions about these sections" in request
    assert (lecture.version_dir / "lecture.quiz.md").read_text().startswith("# Prior\n\n1. A new question\n")
    assert lecture.live.poll_all() == {"lecture.prior"}


def test_the_tutor_adds_the_page_quiz_by_the_page_name(vault: Path, monkeypatch: pytest.MonkeyPatch):
    book = Book(vault, "tester")
    lecture = book.chapter("lectures/lecture")
    started: list[Task] = []
    monkeypatch.setattr(book.adapter, "start", lambda chapter, tasks: started.extend(tasks))
    book.chat._chapter = lecture
    add_quiz = next(t for t in book.chat._tools() if t.tool_name == "add_quiz")
    assert add_quiz("lecture", "Test my background.", part="prior") == (
        "Writing a prior quiz for lecture now. It appears after the title when it is ready."
    )
    assert [(t.section, t.quiz, t.rewrite, t.covers) for t in started] == [
        ("lecture", "prior", False, ["systems", "policies", "rewards"])
    ]
    assert "is `lecture` for add_quiz" in book.chat.system_prompt(lecture)
    book.stop()


# -- End to end --


def test_a_page_prior_submit_rewrites_the_missed_sections(vault: Path, fake_llm: FakeLLM):
    book = Book(vault, "tester")
    lecture = book.chapter("lectures/lecture")
    plan = book.submit_quiz(lecture, answer(lecture, "lecture.prior", "b", "a", "b"))
    book.adapter._pool.shutdown(wait=True)
    book._notes_pool.shutdown(wait=True)
    book.stop()

    assert [t.section for t in plan.tasks] == ["systems"]
    assert sorted(p.name for p in lecture.version_dir.glob("*.md")) == ["systems.md"]
    assert "## Lecture, background check" in book.store.notes_md(lecture.key)
    assert "Missed: Q1 About systems?; Q3 Untagged?." in book.store.notes_md(lecture.key)
    assert lecture.live.poll_all() == {"systems"}
