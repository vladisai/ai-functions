"""Quizzes written as markdown: the question kinds, the parts, and formatting back to the same file."""

from pathlib import Path

from quicklearn.core.quiz import QuestionType, QuizQuestion
from quicklearn.vault.quiz_md import format_questions, format_quiz, parse_quiz

QUIZ = """\
# Prior

1. Which statement about a density $p(x)$ is right?
   - [ ] $p(x) = \\mathbb{P}(X = x)$
   - [x] $\\int p(x)\\,dx = 1$
   - [ ] It is at most 1
2) Evaluate these statements:
   - [T] The marginal is $\\int p(x, y)\\,dy$.
   - [F] Independence means $p(x, y) = p(x) + p(y)$.
3. Explain entropy
   in your own words.

# Learned

1. One more
   * [X] picked
   + [ ] not picked
"""


def test_question_kinds():
    quiz = parse_quiz(QUIZ)
    pick, tf, free = quiz.questions("prior")
    assert pick.question_type == QuestionType.PICK_ONE
    assert pick.text == "Which statement about a density $p(x)$ is right?"
    assert pick.options == ["$p(x) = \\mathbb{P}(X = x)$", "$\\int p(x)\\,dx = 1$", "It is at most 1"]
    assert pick.correct_answer == "b"
    assert tf.question_type == QuestionType.MULTI_TF
    assert tf.correct_answer == "a:T,b:F"
    assert free.question_type == QuestionType.FREE_FORM
    assert free.options is None and free.correct_answer is None
    assert free.text == "Explain entropy\nin your own words."
    learned = quiz.questions("learned")
    assert [(q.options, q.correct_answer) for q in learned] == [(["picked", "not picked"], "a")]


def test_lines_and_marks_for_the_check_command():
    prior = parse_quiz(QUIZ).prior
    assert [p.line for p in prior] == [3, 7, 10]
    assert [p.marks for p in prior[:2]] == [[" ", "x", " "], ["T", "F"]]


def test_pick_one_without_exactly_one_mark_has_no_answer():
    quiz = parse_quiz("# Prior\n\n1. None\n   - [ ] a\n   - [ ] b\n2. Two\n   - [x] a\n   - [x] b\n")
    assert [q.correct_answer for q in quiz.questions("prior")] == [None, None]


def test_wrapped_option_lines_join_the_option():
    quiz = parse_quiz("# Prior\n\n1. Pick\n   - [x] a long option\n     that wraps\n   - [ ] short\n")
    assert quiz.questions("prior")[0].options == ["a long option that wraps", "short"]


def test_missing_part_is_none_and_empty_part_is_empty():
    assert parse_quiz(QUIZ).learned is not None
    only_prior = parse_quiz("# Prior\n\n1. Q\n   - [x] a\n")
    assert only_prior.learned is None and only_prior.questions("learned") is None
    empty_learned = parse_quiz("# Prior\n\n1. Q\n   - [x] a\n\n# Learned\n")
    assert empty_learned.learned == [] and empty_learned.questions("learned") == []
    assert parse_quiz("").prior is None


def test_unknown_parts_and_text_outside_parts_are_ignored():
    quiz = parse_quiz("Intro text\n1. Not a question\n\n# Posterior\n\n1. Ignored\n\n# prior\n\n1. Kept\n   - [x] a\n")
    assert quiz.unknown_parts == ["Posterior"]
    assert [q.text for q in quiz.questions("prior")] == ["Kept"]


def test_round_trip():
    quiz = parse_quiz(QUIZ)
    text = format_quiz(quiz.questions("prior"), quiz.questions("learned"))
    again = parse_quiz(text)
    assert again.questions("prior") == quiz.questions("prior")
    assert again.questions("learned") == quiz.questions("learned")
    assert format_quiz(again.questions("prior"), again.questions("learned")) == text


def test_format_quiz():
    questions = [
        QuizQuestion(text="Pick", options=["a", "b"], correct_answer="b"),
        QuizQuestion(text="Judge", question_type=QuestionType.MULTI_TF, options=["x", "y"], correct_answer="a:T,b:F"),
        QuizQuestion(text="Explain\nwhy"),
    ]
    assert format_questions(questions) == (
        "1. Pick\n   - [ ] a\n   - [x] b\n"
        "2. Judge\n   - [T] x\n   - [F] y\n"
        "3. Explain\n   why"
    )
    assert format_quiz(None, questions[:1]) == "# Learned\n\n1. Pick\n   - [ ] a\n   - [x] b\n"
    assert format_quiz([], []) == "# Prior\n\n# Learned\n"
    assert format_quiz(None, None) == ""


def test_option_whitespace_is_collapsed_by_format():
    q = QuizQuestion(text="Pick", options=["two\n  lines"], correct_answer="a")
    assert format_questions([q]) == "1. Pick\n   - [x] two lines"


def test_shipped_quizzes_round_trip(shipped_vault: Path):
    paths = sorted(shipped_vault.rglob("*.quiz.md"))
    assert paths
    for path in paths:
        quiz = parse_quiz(path.read_text())
        again = parse_quiz(format_quiz(quiz.questions("prior"), quiz.questions("learned")))
        assert again.questions("prior") == quiz.questions("prior"), path
