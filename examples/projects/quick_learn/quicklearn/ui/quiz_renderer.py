"""Render Quiz objects as NiceGUI UI components.

Shows one question at a time with prev/next navigation.
Supports pick-one (single select) and multi-tf (true/false per option).
Shows correct/incorrect feedback after quiz completion.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from nicegui import ui

from quicklearn.core.quiz import QuestionType, Quiz, QuizState
from quicklearn.ui.math_markdown import math_markdown

log = logging.getLogger(__name__)


def render_quiz(
    quiz: Quiz,
    on_submit: Callable | None = None,
    on_partial: Callable | None = None,
    on_skip: Callable | None = None,
    on_feedback: Callable[[str], None] | None = None,
    title: str | None = None,
) -> None:
    """Render a quiz inline in the content area.

    Active quizzes are collapsed by default — a subtle grey bar with a
    "Take quiz" button that expands to the full quiz UI on click.

    on_submit(quiz, on_progress) -> {"feedback": str, "content_changed": bool}.
    on_feedback pushes assistant text to the chat widget.
    """
    label = f"Quiz: {title}" if title else "Quiz"
    if quiz.state == QuizState.ACTIVE:
        _render_collapsed_quiz(
            quiz,
            on_submit=on_submit,
            on_partial=on_partial,
            on_skip=on_skip,
            on_feedback=on_feedback,
            label=label,
        )
    elif quiz.state == QuizState.COMPLETED:
        _render_completed_quiz(quiz, label=label)
    elif quiz.state == QuizState.SKIPPED:
        _render_skipped_quiz(quiz, label=label)


def _render_collapsed_quiz(
    quiz: Quiz,
    on_submit: Callable | None,
    on_partial: Callable | None,
    on_skip: Callable | None,
    on_feedback: Callable[[str], None] | None,
    label: str = "Quiz",
) -> None:
    """Render a subtle grey bar with a button to expand into the full quiz."""
    n_questions = len(quiz.questions)
    desc = f"{n_questions} question{'s' if n_questions != 1 else ''}" if n_questions else "questions loading"

    container = ui.column().classes("w-full")
    with container:
        # Collapsed bar
        collapsed = ui.row().classes(
            "w-full items-center justify-between px-4 py-2 my-3 "
            "rounded bg-gray-50 border border-gray-200"
        )
        with collapsed:
            with ui.row().classes("items-center gap-2"):
                ui.icon("quiz").classes("text-gray-400 text-base")
                ui.label(label).classes("text-sm text-gray-500")
                ui.label(f"· {desc}").classes("text-xs text-gray-400")
            take_btn = ui.button("Take quiz", icon="play_arrow").props(
                "flat dense size=sm color=grey"
            ).classes("text-xs")

        # Expanded quiz (hidden initially)
        expanded = ui.column().classes("w-full")
        expanded.set_visibility(False)

    def _expand() -> None:
        collapsed.set_visibility(False)
        expanded.set_visibility(True)
        with expanded:
            # Collapse button at top-right of the quiz card
            with ui.row().classes("w-full justify-end"):
                ui.button("Collapse", icon="unfold_less").props(
                    "flat dense size=sm color=grey"
                ).classes("text-xs").on("click", _collapse)
            _render_active_quiz(
                quiz,
                on_submit=on_submit,
                on_partial=on_partial,
                on_skip=on_skip,
                on_feedback=on_feedback,
                label=label,
            )

    def _collapse() -> None:
        expanded.clear()
        expanded.set_visibility(False)
        collapsed.set_visibility(True)

    take_btn.on("click", _expand)


def _compile_answers(quiz: Quiz, state: dict) -> None:
    """Save the checked questions' answers from the UI state dict into the quiz.

    A multi_tf question sets every option to "F" as soon as it is shown, so
    saving unchecked questions would grade the ones the reader only looked at.
    """
    for idx in sorted(state["checked"]):
        q = quiz.questions[idx]
        parts = []

        if q.question_type == QuestionType.MULTI_TF and q.options:
            tf_parts = []
            for j in range(len(q.options)):
                key = chr(ord("a") + j)
                val = state["answers"].get(f"{idx}_tf_{j}", None)
                if val is not None:
                    tf_parts.append(f"{key}:{val}")
            if tf_parts:
                parts.append(",".join(tf_parts))
        elif q.question_type == QuestionType.PICK_ONE:
            sel = state["answers"].get(f"{idx}_pick", None)
            if sel is not None:
                parts.append(sel)

        freeform = state["answers"].get(f"{idx}_freeform", "")
        if freeform and freeform.strip():
            parts.append(freeform.strip())

        if parts:
            quiz.submit_answer(idx, " | ".join(parts))


def _restore_answers(quiz: Quiz) -> dict:
    """UI answer state from the answers saved on the quiz, the inverse of _compile_answers."""
    answers = {}
    for idx, answer in quiz.answers.items():
        q = quiz.questions[idx]
        head, _, freeform = answer.partition(" | ")
        letters = [chr(ord("a") + j) for j in range(len(q.options or []))]
        if q.question_type == QuestionType.MULTI_TF and ":" in head:
            for pair in head.split(","):
                key, val = pair.split(":", 1)
                answers[f"{idx}_tf_{letters.index(key)}"] = val
        elif q.question_type == QuestionType.PICK_ONE and head in letters:
            answers[f"{idx}_pick"] = head
        else:
            freeform = answer
        if freeform:
            answers[f"{idx}_freeform"] = freeform
    return answers


def _render_active_quiz(
    quiz: Quiz,
    on_submit: Callable | None,
    on_partial: Callable | None,
    on_skip: Callable | None,
    on_feedback: Callable[[str], None] | None,
    label: str = "Quiz",
) -> None:
    if not quiz.questions:
        # No questions yet — subtle grey bar with skip option
        with ui.row().classes(
            "w-full items-center justify-between px-4 py-2 my-3 "
            "rounded bg-gray-50 border border-gray-200"
        ).style("position: relative; overflow: hidden;"):
            empty_spinner = ui.element("div").classes(
                "absolute inset-0 flex items-center justify-center bg-gray-50/90 z-10"
            ).style("display: none;")
            with empty_spinner:
                with ui.row().classes("items-center gap-2"):
                    ui.spinner("dots", size="md", color="grey")
                    ui.label("Generating content...").classes("text-sm text-gray-500")

            with ui.row().classes("items-center gap-2"):
                ui.icon("quiz").classes("text-gray-400 text-base")
                ui.label(label).classes("text-sm text-gray-500")
                empty_msg = ui.label("· no questions yet").classes("text-xs text-gray-400")

            empty_btn = ui.button("Skip quiz", icon="skip_next").props(
                "flat dense size=sm color=grey"
            ).classes("text-xs")

        async def _handle_skip_empty() -> None:
            if quiz.state != QuizState.ACTIVE:
                return
            quiz.skip()
            empty_spinner.style("display: flex;")
            if on_skip:
                await on_skip(quiz)
            empty_spinner.style("display: none;")
            empty_msg.text = "· skipped"
            empty_btn.delete()

        empty_btn.on("click", _handle_skip_empty)
        return

    # State for current question index and collected answers. Answers saved on
    # the quiz come back as checked, so collapsing or reloading keeps the reader's place.
    unanswered = [i for i in range(len(quiz.questions)) if i not in quiz.answers]
    state = {
        "current": unanswered[0] if unanswered else len(quiz.questions) - 1,
        "answers": _restore_answers(quiz),  # UI keys like "0_pick", "1_tf_2", "0_freeform"
        "checked": set(quiz.answers),  # q_indices that have been checked
    }

    with ui.card().classes("w-full my-4 border-l-4 border-amber-500").style("position: relative; overflow: hidden;"):
        # Loading overlay (hidden by default, absolutely positioned over card)
        spinner_overlay = ui.element("div").classes(
            "absolute inset-0 flex items-center justify-center bg-white/80 z-10"
        ).style("display: none;")
        with spinner_overlay:
            with ui.column().classes("items-center gap-3"):
                ui.spinner("dots", size="xl", color="amber")
                spinner_label = ui.label("Analyzing your answers...").classes("text-sm text-gray-600")

        # Header with progress
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(label).classes("text-lg font-bold text-amber-800")
            progress_label = ui.label(
                f"Question 1 of {len(quiz.questions)}"
            ).classes("text-sm text-gray-500")

        # Question and feedback containers
        question_container = ui.column().classes("w-full mt-2")
        feedback_container = ui.column().classes("w-full")

        # Agent feedback container (shown after submission)
        agent_feedback_container = ui.column().classes("w-full")

        # Navigation buttons
        with ui.row().classes("w-full items-center justify-between mt-4") as btn_row:
            prev_btn = ui.button(
                "Previous", icon="arrow_back",
            ).props("flat color=grey")
            prev_btn.set_visibility(False)

            with ui.row().classes("gap-2"):
                skip_btn = ui.button("Skip quiz").props("flat color=grey")
                partial_btn = ui.button(
                    "Submit progress", icon="save",
                ).props("flat color=orange")
                check_btn = ui.button(
                    "Check", icon="fact_check",
                ).props("color=amber-8")
                next_btn = ui.button(
                    "Next", icon="arrow_forward",
                ).props("color=amber-8").classes("icon-right")
                next_btn.set_visibility(False)
                submit_btn = ui.button(
                    "Submit quiz", icon="check",
                ).props("color=amber-8")
                submit_btn.set_visibility(False)

    def _has_answer(idx: int) -> bool:
        q = quiz.questions[idx]
        if q.question_type == QuestionType.PICK_ONE:
            return f"{idx}_pick" in state["answers"]
        elif q.question_type == QuestionType.MULTI_TF and q.options:
            return any(
                f"{idx}_tf_{j}" in state["answers"]
                for j in range(len(q.options))
            )
        return f"{idx}_freeform" in state["answers"] and state["answers"][f"{idx}_freeform"].strip()

    def _show_feedback(idx: int) -> None:
        question = quiz.questions[idx]
        _compile_answers(quiz, state)
        result = quiz.check_answer(idx)

        feedback_container.clear()
        with feedback_container:
            if result is True:
                with ui.row().classes("items-center gap-2 p-2 rounded bg-green-50"):
                    ui.icon("check_circle").classes("text-green-700")
                    ui.label("Correct!").classes("text-sm font-bold text-green-700")
            elif result is False:
                with ui.column().classes("p-2 rounded bg-red-50 gap-1"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("cancel").classes("text-red-700")
                        ui.label("Incorrect").classes("text-sm font-bold text-red-700")
                    if question.correct_answer:
                        math_markdown(
                            f"Correct answer: {_format_correct(question)}",
                            classes="text-sm ml-8 text-green-700 italic",
                        )
            else:
                with ui.row().classes("items-center gap-2 p-2 rounded bg-gray-50"):
                    ui.icon("help_outline").classes("text-gray-500")
                    ui.label("Answer recorded").classes("text-sm text-gray-500")

    def _update_buttons() -> None:
        idx = state["current"]
        is_last = idx == len(quiz.questions) - 1
        checked = idx in state["checked"]

        check_btn.set_visibility(not checked)
        next_btn.set_visibility(checked and not is_last)
        submit_btn.set_visibility(checked and is_last)
        prev_btn.set_visibility(idx > 0)

    def render_current_question() -> None:
        idx = state["current"]
        question = quiz.questions[idx]

        question_container.clear()
        feedback_container.clear()
        with question_container:
            math_markdown(question.text, classes="text-base")

            if question.options:
                if question.question_type == QuestionType.MULTI_TF:
                    _render_multi_tf(idx, question.options, state["answers"])
                else:
                    _render_pick_one(idx, question.options, state["answers"])

            if question.allow_freeform:
                existing = state["answers"].get(f"{idx}_freeform", "")
                ff = ui.input(
                    placeholder=(
                        "Additional thoughts (optional)"
                        if question.options
                        else "Your answer"
                    ),
                    value=existing,
                ).classes("w-full mt-2")

                def on_ff_change(e, i=idx, inp=ff) -> None:
                    state["answers"][f"{i}_freeform"] = inp.value

                ff.on("blur", on_ff_change)

        if idx in state["checked"]:
            _show_feedback(idx)

        progress_label.text = f"Question {idx + 1} of {len(quiz.questions)}"
        _update_buttons()

    def handle_check() -> None:
        idx = state["current"]
        if not _has_answer(idx):
            ui.notify("Please select an answer first", type="warning")
            return
        state["checked"].add(idx)
        _show_feedback(idx)
        _update_buttons()

    def go_prev() -> None:
        if state["current"] > 0:
            state["current"] -= 1
            render_current_question()

    def go_next() -> None:
        if state["current"] < len(quiz.questions) - 1:
            state["current"] += 1
            render_current_question()

    async def handle_submit() -> None:
        if quiz.state != QuizState.ACTIVE:
            return  # a second click that landed before the overlay showed, or a submit from another tab
        _compile_answers(quiz, state)
        quiz.complete()

        # Show spinner overlay
        spinner_overlay.style("display: flex;")

        def update_progress(msg: str) -> None:
            spinner_label.text = msg

        # Count results for the summary
        num_correct = sum(1 for i in range(len(quiz.questions)) if quiz.check_answer(i) is True)
        num_checked = sum(1 for i in range(len(quiz.questions)) if quiz.check_answer(i) is not None)

        result = None
        if on_submit:
            try:
                result = await on_submit(quiz, update_progress)
            except Exception:
                log.exception("Quiz submission failed in UI")
                result = {
                    "feedback": "Something went wrong processing the quiz. Check the server logs.",
                    "content_changed": False,
                }

        # Hide spinner
        spinner_overlay.style("display: none;")

        # Parse result
        feedback_text = ""
        content_changed = False
        if isinstance(result, dict):
            feedback_text = result.get("feedback", "")
            content_changed = result.get("content_changed", False)

        # Replace quiz content with score + agent feedback
        question_container.clear()
        feedback_container.clear()
        btn_row.set_visibility(False)
        progress_label.text = ""

        with agent_feedback_container:
            # Score summary
            summary = f"**Completed:** {len(quiz.answers)}/{len(quiz.questions)} answered"
            if num_checked > 0:
                summary += f", {num_correct}/{num_checked} correct"
            math_markdown(summary, classes="text-base font-semibold")

            if feedback_text:
                ui.separator().classes("my-2")
                math_markdown(feedback_text, classes="text-sm leading-relaxed")

            if content_changed:
                ui.separator().classes("my-2")
                with ui.row().classes("items-center gap-2 text-green-700"):
                    ui.icon("auto_fix_high")
                    ui.label("Rewriting the section for you. Changes appear as they are written.").classes("text-sm")

        # Push feedback to chat
        if feedback_text and on_feedback:
            on_feedback(feedback_text)

    async def handle_partial() -> None:
        _compile_answers(quiz, state)
        spinner_overlay.style("display: flex;")
        if on_partial:
            await on_partial(quiz)
        spinner_overlay.style("display: none;")
        ui.notify("Progress saved", type="positive")

    async def handle_skip() -> None:
        if quiz.state != QuizState.ACTIVE:
            return
        quiz.skip()
        spinner_overlay.style("display: flex;")
        if on_skip:
            await on_skip(quiz)
        spinner_overlay.style("display: none;")

        # Replace quiz content with skipped message
        question_container.clear()
        feedback_container.clear()
        btn_row.set_visibility(False)
        progress_label.text = ""
        with agent_feedback_container:
            ui.label("Quiz skipped.").classes("text-sm text-gray-500 italic")

    prev_btn.on("click", go_prev)
    check_btn.on("click", handle_check)
    next_btn.on("click", go_next)
    submit_btn.on("click", handle_submit)
    partial_btn.on("click", handle_partial)
    skip_btn.on("click", handle_skip)

    # Render first question
    render_current_question()


def _render_pick_one(
    q_index: int,
    options: list[str],
    answers: dict,
) -> None:
    """Render single-select options as clickable cards."""
    current_sel = answers.get(f"{q_index}_pick")
    cards: list[tuple[str, ui.card]] = []

    with ui.column().classes("w-full gap-1 mt-2"):
        for j, opt in enumerate(options):
            key = chr(ord("a") + j)
            is_selected = current_sel == key

            card = ui.card().classes(
                "w-full p-2 cursor-pointer transition-colors "
                + (
                    "border-2 border-amber-500 bg-amber-50"
                    if is_selected
                    else "border hover:bg-amber-50"
                )
            )
            cards.append((key, card))

            with card:
                with ui.row().classes("items-center gap-2 w-full"):
                    ui.badge(key).props(
                        "color=amber-8" if is_selected else "outline"
                    ).classes("text-sm")
                    math_markdown(opt, classes="text-sm flex-grow")

        # Attach click handlers after all cards exist
        for key, card in cards:

            def make_handler(k: str = key) -> None:
                def handler() -> None:
                    answers[f"{q_index}_pick"] = k
                    # Re-style all cards
                    for ck, cc in cards:
                        if ck == k:
                            cc.classes(
                                remove="border hover:bg-amber-50",
                                add="border-2 border-amber-500 bg-amber-50",
                            )
                        else:
                            cc.classes(
                                remove="border-2 border-amber-500 bg-amber-50",
                                add="border hover:bg-amber-50",
                            )

                return handler

            card.on("click", make_handler())


def _render_multi_tf(
    q_index: int,
    options: list[str],
    answers: dict,
) -> None:
    """Render toggle cards per option. Lit up = True, unlit = False."""
    cards: list[tuple[int, str, ui.card, ui.badge]] = []

    # Initialize all options to "F" (unlit) if not already set
    for j in range(len(options)):
        akey = f"{q_index}_tf_{j}"
        if akey not in answers:
            answers[akey] = "F"

    with ui.column().classes("w-full gap-1 mt-2"):
        for j, opt in enumerate(options):
            key = chr(ord("a") + j)
            answer_key = f"{q_index}_tf_{j}"
            current_val = answers.get(answer_key)
            is_on = current_val == "T"

            card = ui.card().classes(
                "w-full p-2 cursor-pointer transition-colors "
                + (
                    "border-2 border-amber-500 bg-amber-50"
                    if is_on
                    else "border hover:bg-amber-50"
                )
            )

            with card:
                with ui.row().classes("items-center gap-2 w-full"):
                    badge = ui.badge(key).props(
                        "color=amber-8" if is_on else "outline"
                    ).classes("text-sm")
                    math_markdown(opt, classes="text-sm flex-grow")

            cards.append((j, answer_key, card, badge))

        # Attach click handlers after all cards exist
        for j, akey, card, badge in cards:

            def make_handler(
                _j: int = j, _akey: str = akey, _card: ui.card = card, _badge: ui.badge = badge,
            ) -> None:
                def handler() -> None:
                    current = answers.get(_akey)
                    if current == "T":
                        # Toggle off -> False
                        answers[_akey] = "F"
                        _card.classes(
                            remove="border-2 border-amber-500 bg-amber-50",
                            add="border hover:bg-amber-50",
                        )
                        _badge.props(remove="color=amber-8")
                        _badge.props("outline")
                    else:
                        # Toggle on -> True
                        answers[_akey] = "T"
                        _card.classes(
                            remove="border hover:bg-amber-50",
                            add="border-2 border-amber-500 bg-amber-50",
                        )
                        _badge.props(remove="outline")
                        _badge.props("color=amber-8")

                return handler

            card.on("click", make_handler())


def _render_completed_quiz(quiz: Quiz, label: str = "Quiz") -> None:
    """Render a completed quiz with correct/incorrect feedback per question."""
    # Count results
    num_correct = 0
    num_checked = 0
    for i in range(len(quiz.questions)):
        result = quiz.check_answer(i)
        if result is not None:
            num_checked += 1
            if result:
                num_correct += 1

    summary = f"{label} (completed — {len(quiz.answers)}/{len(quiz.questions)} answered"
    if num_checked > 0:
        summary += f", {num_correct}/{num_checked} correct"
    summary += ")"

    with ui.expansion(summary, icon="check_circle").classes(
        "w-full my-4 bg-green-50"
    ).props("dense"):
        for i, question in enumerate(quiz.questions):
            answer = quiz.answers.get(i, None)
            result = quiz.check_answer(i)

            # Color-code by correctness
            if result is True:
                icon = "check_circle"
                color = "text-green-700"
                bg = "bg-green-50"
            elif result is False:
                icon = "cancel"
                color = "text-red-700"
                bg = "bg-red-50"
            else:
                icon = "help_outline"
                color = "text-gray-600"
                bg = ""

            with ui.card().classes(f"w-full p-3 my-1 {bg}"):
                math_markdown(question.text, classes=f"text-sm {color}")
                if answer is not None:
                    with ui.row().classes("items-center gap-2 ml-4"):
                        ui.icon(icon).classes(color)
                        ui.label(f"Your answer: {_format_answer(question, answer)}").classes(
                            f"text-sm {color}"
                        )
                    if result is False and question.correct_answer:
                        math_markdown(
                            f"Correct answer: {_format_correct(question)}",
                            classes="text-sm ml-10 text-green-700 italic",
                        )
                else:
                    ui.label("(not answered)").classes("text-sm ml-4 text-gray-400 italic")


def _format_answer(question, answer: str) -> str:
    """Format a stored answer for display."""
    parts = answer.split(" | ")
    if question.question_type == QuestionType.PICK_ONE and question.options:
        pick = parts[0].strip()
        idx = ord(pick) - ord("a") if len(pick) == 1 and pick.isalpha() else -1
        if 0 <= idx < len(question.options):
            return f"({pick}) {question.options[idx]}"
    if question.question_type == QuestionType.MULTI_TF:
        # Show as readable list
        tf_part = parts[0].strip()
        items = []
        for pair in tf_part.split(","):
            pair = pair.strip()
            if ":" in pair:
                k, v = pair.split(":", 1)
                idx = ord(k.strip()) - ord("a")
                label = question.options[idx] if question.options and 0 <= idx < len(question.options) else k
                items.append(f"{label}: {'True' if v.strip() == 'T' else 'False'}")
        if items:
            return "; ".join(items)
    return answer


def _format_correct(question) -> str:
    """Format the correct answer for display."""
    ca = question.correct_answer
    if question.question_type == QuestionType.PICK_ONE and question.options:
        idx = ord(ca) - ord("a") if len(ca) == 1 and ca.isalpha() else -1
        if 0 <= idx < len(question.options):
            return f"({ca}) {question.options[idx]}"
    if question.question_type == QuestionType.MULTI_TF and question.options:
        items = []
        for pair in ca.split(","):
            pair = pair.strip()
            if ":" in pair:
                k, v = pair.split(":", 1)
                idx = ord(k.strip()) - ord("a")
                label = question.options[idx] if 0 <= idx < len(question.options) else k
                items.append(f"{label}: {'True' if v.strip() == 'T' else 'False'}")
        if items:
            return "; ".join(items)
    return ca


def _render_skipped_quiz(quiz: Quiz, label: str = "Quiz") -> None:
    with ui.expansion(f"{label} (skipped)", icon="skip_next").classes(
        "w-full my-4 bg-gray-50"
    ).props("dense"):
        ui.label("You skipped this quiz.").classes("text-sm text-gray-500")
