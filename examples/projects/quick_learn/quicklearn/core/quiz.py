from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class QuizState(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class QuestionType(Enum):
    PICK_ONE = "pick_one"  # Single correct answer
    MULTI_TF = "multi_tf"  # Each option is independently True/False
    FREE_FORM = "free_form"  # Open-ended text response


@dataclass
class QuizQuestion:
    text: str
    question_type: QuestionType = QuestionType.PICK_ONE
    options: list[str] | None = None  # None means free-form only
    allow_freeform: bool = True  # Always True when options is None
    # Correct answer: for pick_one "a"/"b"/etc, for multi_tf "a:T,b:F,c:T", or None if unknown
    correct_answer: str | None = None

    def __post_init__(self) -> None:
        if self.options is None:
            self.question_type = QuestionType.FREE_FORM
            self.allow_freeform = True


@dataclass
class Quiz:
    """A quiz placed inline in content via <!-- quiz:id --> tags."""

    id: str = field(default_factory=lambda: f"quiz_{uuid.uuid4().hex[:8]}")
    questions: list[QuizQuestion] = field(default_factory=list)
    # question_index -> answer string (for pick_one: "a", for multi_tf: "a:T,b:F,c:T,d:F")
    answers: dict[int, str] = field(default_factory=dict)
    state: QuizState = QuizState.ACTIVE

    def submit_answer(self, question_index: int, answer: str) -> None:
        if question_index < 0 or question_index >= len(self.questions):
            raise IndexError(
                f"Question index {question_index} out of range "
                f"(quiz has {len(self.questions)} questions)"
            )
        self.answers[question_index] = answer

    def skip(self) -> None:
        self.state = QuizState.SKIPPED

    def complete(self) -> None:
        self.state = QuizState.COMPLETED

    @property
    def is_fully_answered(self) -> bool:
        return len(self.answers) == len(self.questions)

    def check_answer(self, question_index: int) -> bool | None:
        """Check if the answer to a question is correct.

        Returns True/False if we have both an answer and a correct_answer,
        None otherwise.
        """
        if question_index not in self.answers:
            return None
        q = self.questions[question_index]
        if q.correct_answer is None:
            return None

        answer = self.answers[question_index]

        if q.question_type == QuestionType.PICK_ONE:
            # Answer is like "b" or "b | some freeform text"
            user_pick = answer.split("|")[0].strip()
            return user_pick == q.correct_answer

        if q.question_type == QuestionType.MULTI_TF:
            # Answer is like "a:T,b:F,c:T" or "a:T,b:F,c:T | freeform"
            user_part = answer.split("|")[0].strip()
            # Parse into dict
            user_tf = {}
            for pair in user_part.split(","):
                pair = pair.strip()
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    user_tf[k.strip()] = v.strip()
            correct_tf = {}
            for pair in q.correct_answer.split(","):
                pair = pair.strip()
                if ":" in pair:
                    k, v = pair.split(":", 1)
                    correct_tf[k.strip()] = v.strip()
            return user_tf == correct_tf

        return None
