"""Tests for quiz grading (check_answer) and answer formatting (format_answers).

Covers:
- pick_one grading with and without freeform text
- multi_tf grading with various orderings and formats
- free_form (always returns None — no correct answer)
- Edge cases: no answer, no correct_answer, out of range
- format_answers() output for the fast adapter's prompts
- saved answers coming back into the quiz UI after a collapse or reload
"""

from __future__ import annotations

import pytest
from quicklearn.agents.adapter import format_answers
from quicklearn.core.quiz import QuestionType, Quiz, QuizQuestion, QuizState
from quicklearn.ui.quiz_renderer import _compile_answers, _restore_answers

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_pick_one_quiz() -> Quiz:
    """Quiz with pick_one questions."""
    return Quiz(
        id="test_pick",
        questions=[
            QuizQuestion(
                text="What is 1+1?",
                options=["1", "2", "3"],
                correct_answer="b",
            ),
            QuizQuestion(
                text="What is the capital of France?",
                options=["London", "Paris", "Berlin"],
                correct_answer="b",
            ),
        ],
    )


def _make_multi_tf_quiz() -> Quiz:
    """Quiz with multi_tf questions."""
    return Quiz(
        id="test_tf",
        questions=[
            QuizQuestion(
                text="Mark true/false for each:",
                question_type=QuestionType.MULTI_TF,
                options=["1+1=2", "2+2=5", "3+3=6"],
                correct_answer="a:T,b:F,c:T",
            ),
        ],
    )


def _make_free_form_quiz() -> Quiz:
    """Quiz with free-form questions (no options)."""
    return Quiz(
        id="test_free",
        questions=[
            QuizQuestion(text="Explain entropy in your own words."),
        ],
    )


# ---------------------------------------------------------------------------
# check_answer() — PICK_ONE
# ---------------------------------------------------------------------------

class TestCheckAnswerPickOne:
    def test_correct_answer(self):
        quiz = _make_pick_one_quiz()
        quiz.submit_answer(0, "b")
        assert quiz.check_answer(0) is True

    def test_incorrect_answer(self):
        quiz = _make_pick_one_quiz()
        quiz.submit_answer(0, "a")
        assert quiz.check_answer(0) is False

    def test_correct_with_freeform(self):
        """Answer like 'b | because 1+1 is 2' should still check the pick part."""
        quiz = _make_pick_one_quiz()
        quiz.submit_answer(0, "b | because 1+1 is obviously 2")
        assert quiz.check_answer(0) is True

    def test_incorrect_with_freeform(self):
        quiz = _make_pick_one_quiz()
        quiz.submit_answer(0, "c | I think it's 3")
        assert quiz.check_answer(0) is False

    def test_no_answer_submitted(self):
        quiz = _make_pick_one_quiz()
        assert quiz.check_answer(0) is None

    def test_no_correct_answer_defined(self):
        quiz = Quiz(
            id="no_key",
            questions=[
                QuizQuestion(text="What?", options=["A", "B"], correct_answer=None),
            ],
        )
        quiz.submit_answer(0, "a")
        assert quiz.check_answer(0) is None

    def test_whitespace_in_answer(self):
        """Answer with leading/trailing whitespace around the pick letter."""
        quiz = _make_pick_one_quiz()
        quiz.submit_answer(0, " b ")
        # split("|")[0].strip() should handle this
        assert quiz.check_answer(0) is True


# ---------------------------------------------------------------------------
# check_answer() — MULTI_TF
# ---------------------------------------------------------------------------

class TestCheckAnswerMultiTF:
    def test_all_correct(self):
        quiz = _make_multi_tf_quiz()
        quiz.submit_answer(0, "a:T,b:F,c:T")
        assert quiz.check_answer(0) is True

    def test_one_wrong(self):
        quiz = _make_multi_tf_quiz()
        quiz.submit_answer(0, "a:T,b:T,c:T")  # b should be F
        assert quiz.check_answer(0) is False

    def test_different_order(self):
        """Order of pairs shouldn't matter as long as all are present."""
        quiz = _make_multi_tf_quiz()
        quiz.submit_answer(0, "c:T,a:T,b:F")
        assert quiz.check_answer(0) is True

    def test_with_freeform_appended(self):
        """Answer like 'a:T,b:F,c:T | my reasoning' should still grade correctly."""
        quiz = _make_multi_tf_quiz()
        quiz.submit_answer(0, "a:T,b:F,c:T | because 2+2 is not 5")
        assert quiz.check_answer(0) is True

    def test_with_spaces(self):
        """Spaces around colons and commas should be handled."""
        quiz = _make_multi_tf_quiz()
        quiz.submit_answer(0, "a : T , b : F , c : T")
        assert quiz.check_answer(0) is True

    def test_missing_option_is_wrong(self):
        """If user omits an option, it shouldn't match."""
        quiz = _make_multi_tf_quiz()
        quiz.submit_answer(0, "a:T,b:F")  # missing c
        assert quiz.check_answer(0) is False

    def test_extra_option_is_wrong(self):
        """If user adds an extra option, it shouldn't match."""
        quiz = _make_multi_tf_quiz()
        quiz.submit_answer(0, "a:T,b:F,c:T,d:T")
        assert quiz.check_answer(0) is False


# ---------------------------------------------------------------------------
# check_answer() — FREE_FORM
# ---------------------------------------------------------------------------

class TestCheckAnswerFreeForm:
    def test_always_returns_none(self):
        """Free-form questions have no correct answer — always None."""
        quiz = _make_free_form_quiz()
        quiz.submit_answer(0, "Entropy is a measure of disorder.")
        assert quiz.check_answer(0) is None

    def test_question_type_is_free_form(self):
        """QuizQuestion with no options should be FREE_FORM."""
        q = QuizQuestion(text="Explain something.")
        assert q.question_type == QuestionType.FREE_FORM
        assert q.allow_freeform is True
        assert q.options is None


# ---------------------------------------------------------------------------
# submit_answer() edge cases
# ---------------------------------------------------------------------------

class TestSubmitAnswer:
    def test_submit_valid_index(self):
        quiz = _make_pick_one_quiz()
        quiz.submit_answer(0, "a")
        assert quiz.answers[0] == "a"

    def test_submit_out_of_range_raises(self):
        quiz = _make_pick_one_quiz()
        with pytest.raises(IndexError):
            quiz.submit_answer(99, "a")

    def test_submit_negative_index_raises(self):
        quiz = _make_pick_one_quiz()
        with pytest.raises(IndexError):
            quiz.submit_answer(-1, "a")

    def test_overwrite_answer(self):
        """Submitting twice to the same question should overwrite."""
        quiz = _make_pick_one_quiz()
        quiz.submit_answer(0, "a")
        quiz.submit_answer(0, "b")
        assert quiz.answers[0] == "b"

    def test_is_fully_answered(self):
        quiz = _make_pick_one_quiz()
        assert quiz.is_fully_answered is False
        quiz.submit_answer(0, "a")
        assert quiz.is_fully_answered is False
        quiz.submit_answer(1, "b")
        assert quiz.is_fully_answered is True

    def test_empty_quiz_is_fully_answered(self):
        """A quiz with no questions is trivially 'fully answered'."""
        quiz = Quiz(id="empty", questions=[])
        assert quiz.is_fully_answered is True


# ---------------------------------------------------------------------------
# Quiz state transitions
# ---------------------------------------------------------------------------

class TestQuizState:
    def test_initial_state_active(self):
        quiz = Quiz(id="test")
        assert quiz.state == QuizState.ACTIVE

    def test_skip(self):
        quiz = Quiz(id="test")
        quiz.skip()
        assert quiz.state == QuizState.SKIPPED

    def test_complete(self):
        quiz = Quiz(id="test")
        quiz.complete()
        assert quiz.state == QuizState.COMPLETED


# ---------------------------------------------------------------------------
# format_answers()
# ---------------------------------------------------------------------------

class TestFormatAnswers:
    def test_status_and_answers(self):
        quiz = _make_pick_one_quiz()
        quiz.submit_answer(0, "b")
        quiz.submit_answer(1, "a")
        result = format_answers(quiz)
        assert "Q1 (correct): What is 1+1?" in result
        assert "Q2 (WRONG): What is the capital of France?" in result
        assert "Reader answered: a" in result
        assert "Correct answer: b" in result

    def test_lists_options_with_letters(self):
        result = format_answers(_make_pick_one_quiz())
        assert "  a) London\n  b) Paris\n  c) Berlin" in result

    def test_unanswered_questions_are_listed(self):
        quiz = _make_pick_one_quiz()
        quiz.submit_answer(0, "b")
        result = format_answers(quiz)
        assert "Q2 (unanswered)" in result
        assert "Reader answered: -" in result

    def test_free_form_answer_is_not_graded(self):
        quiz = _make_free_form_quiz()
        quiz.submit_answer(0, "My explanation of entropy")
        result = format_answers(quiz)
        assert "Q1 (not graded)" in result
        assert "Reader answered: My explanation of entropy" in result


# ---------------------------------------------------------------------------
# _restore_answers() — the UI state rebuilt from saved answers
# ---------------------------------------------------------------------------

class TestRestoreAnswers:
    @pytest.mark.parametrize("make_quiz, answer", [
        (_make_pick_one_quiz, "b"),
        (_make_pick_one_quiz, "b | because Paris"),
        (_make_pick_one_quiz, "no idea | really"),
        (_make_multi_tf_quiz, "a:T,b:F,c:T"),
        (_make_multi_tf_quiz, "a:F,b:F,c:T | unsure about c"),
        (_make_free_form_quiz, "Disorder | roughly"),
    ])
    def test_compiling_restored_answers_gives_them_back(self, make_quiz, answer):
        quiz = make_quiz()
        quiz.submit_answer(0, answer)
        restored = make_quiz()
        _compile_answers(restored, {"answers": _restore_answers(quiz), "checked": {0}})
        assert restored.answers == {0: answer}

    def test_only_checked_questions_are_saved(self):
        # Question 1 was shown, so its options hold the "F" defaults, but it was never checked
        quiz = _make_multi_tf_quiz()
        quiz.questions.append(quiz.questions[0])
        answers = {"0_tf_0": "T", "0_tf_1": "F", "0_tf_2": "T", "1_tf_0": "F", "1_tf_1": "F", "1_tf_2": "F"}
        _compile_answers(quiz, {"answers": answers, "checked": {0}})
        assert quiz.answers == {0: "a:T,b:F,c:T"}
