"""A text input box of a chapter, from `_TEXT_INPUT_: Title` in chapter.md.

| State | Shows |
|---|---|
| active | the prompt, a text area, Submit and Skip |
| done | the reader's answer, with Edit to open the box again |
| skipped | one line, with Answer to open the box |

The box re-renders in place. Submit waits for the note step, about 2 s, with a spinner.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from nicegui import ui

from quicklearn.core.text_input import TextInput, TextInputState
from quicklearn.ui.math_markdown import math_markdown

# on_submit(text_input, answer) -> True if the chapter is being rewritten
OnSubmit = Callable[[TextInput, str], Awaitable[bool]]
OnSkip = Callable[[TextInput], Awaitable[None]]


def render_text_input(text_input: TextInput, on_submit: OnSubmit | None, on_skip: OnSkip | None) -> None:
    container = ui.column().classes("w-full")

    def show(editing: bool = False, rewriting: bool = False) -> None:
        container.clear()
        with container:
            if editing or text_input.state == TextInputState.ACTIVE:
                _active(text_input, on_submit, on_skip, show)
            elif text_input.state == TextInputState.DONE:
                _done(text_input, rewriting, lambda: show(editing=True))
            else:
                _skipped(text_input, lambda: show(editing=True))

    show()


def _active(text_input: TextInput, on_submit: OnSubmit | None, on_skip: OnSkip | None, show: Callable) -> None:
    with ui.card().classes("w-full my-4 p-6"):
        ui.label(text_input.title).classes("text-lg font-semibold mb-2")
        if text_input.prompt:
            math_markdown(text_input.prompt, classes="text-sm text-gray-600 mb-2")
        area = ui.textarea(value=text_input.answer).classes("w-full").props("autogrow outlined")

        with ui.row().classes("mt-4 gap-3 items-center") as busy_row:
            ui.spinner(size="sm")
            ui.label("Reading your answer...").classes("text-sm text-gray-500 italic")
        busy_row.set_visibility(False)

        with ui.row().classes("mt-4 gap-3") as button_row:

            async def submit() -> None:
                answer = (area.value or "").strip()
                if not answer:
                    ui.notify("Write an answer first, or skip.", type="warning")
                    return
                button_row.set_visibility(False)
                area.props("disable")
                busy_row.set_visibility(True)
                rewriting = await on_submit(text_input, answer) if on_submit else False
                show(rewriting=rewriting)

            async def skip() -> None:
                if on_skip:
                    await on_skip(text_input)
                show()

            ui.button("Submit", icon="send", on_click=submit).props("color=primary")
            if text_input.state == TextInputState.ACTIVE:
                ui.button("Skip", on_click=skip).props("flat color=grey")
            else:
                ui.button("Cancel", on_click=lambda: show()).props("flat color=grey")


def _done(text_input: TextInput, rewriting: bool, edit: Callable[[], None]) -> None:
    with ui.card().classes("w-full my-4 p-6 bg-blue-50"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(text_input.title).classes("text-sm font-semibold")
            ui.button("Edit", icon="edit", on_click=edit).props("flat dense size=sm color=grey")
        ui.label(text_input.answer).classes("text-sm text-gray-700 leading-relaxed whitespace-pre-wrap")
        if rewriting:
            with ui.row().classes("items-center gap-2 text-green-700 mt-2"):
                ui.icon("auto_fix_high")
                ui.label("Rewriting the chapter for you. Changes appear as they are written.").classes("text-sm")


def _skipped(text_input: TextInput, answer: Callable[[], None]) -> None:
    with ui.row().classes(
        "w-full items-center justify-between px-4 py-2 my-3 rounded bg-gray-50 border border-gray-200"
    ):
        ui.label(f"{text_input.title} · skipped").classes("text-sm text-gray-500")
        ui.button("Answer", icon="edit", on_click=answer).props("flat dense size=sm color=grey")
