"""QuickLearn's web app: every page the outline links, served by NiceGUI.

    uv run python -m quicklearn.app --port 8889

| Variable | Default | Meaning |
|---|---|---|
| QUICKLEARN_CONTENT | content/ | the content folder, the vault with outline.md |
| QUICKLEARN_READER | default | the reader folder in content/personalization_data/ |

Every page the outline links is adaptive and served by chapter_page: a link to a chapter.md is a
chapter folder, and a link to any other file, e.g. lectures/lecture_1, a one-file page, parsed the
same way (see vault/chapter.py). `/` opens the first chapter folder, else the first page.
"""

from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Callable
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from nicegui import app, run, ui

from quicklearn.book import Book
from quicklearn.core.quiz import Quiz
from quicklearn.core.text_input import TextInput
from quicklearn.logging_setup import setup_session_logging
from quicklearn.ui.figures import add_vault_route, page_folder, set_page_folder
from quicklearn.ui.layout import render_page
from quicklearn.vault.chapter import page_key
from quicklearn.vault.outline import OutlineEntry

SESSION_LOG_DIR = setup_session_logging()
log = logging.getLogger("quicklearn.app")

REPO = Path(__file__).parent.parent
VAULT = Path(os.environ.get("QUICKLEARN_CONTENT", REPO / "content")).resolve()
DEMO_READERS = REPO / "demo_readers"

# One reader at a time. Reset replaces the Book.
BOOK: Book | None = None


def get_book() -> Book:
    global BOOK
    if BOOK is None:
        BOOK = Book(VAULT, os.environ.get("QUICKLEARN_READER", "default"), DEMO_READERS)
    return BOOK


def running_tasks() -> int:
    """For the header indicator. Looks up BOOK on every call, since Reset replaces it."""
    return BOOK.running() if BOOK is not None else 0


def reset() -> None:
    global BOOK
    log.info("Reset: emptying the reader folder")
    get_book().wipe()
    BOOK = None


def _shutdown() -> None:
    """Python waits for the pool threads before it exits, so stop them to keep Ctrl-C quick."""
    if BOOK is not None:
        BOOK.stop()


app.on_shutdown(_shutdown)
# /vault/<path>: the figures and embedded pages the pages link, see ui/figures.py
add_vault_route(app, lambda: VAULT)


@app.get("/debug/material")
def debug_material(chapter: str = ""):
    """The sections and quizzes of a page, e.g. /debug/material?chapter=book/probability or lectures/lecture_1."""
    if BOOK is None:
        return {"error": "not initialized"}
    key = chapter or next((page_key(e.target) for e in BOOK.pages().values() if e.is_chapter), "")
    state = BOOK.chapter(key)
    return {
        "chapter": key,
        "version": state.version_dir.name,
        "sections": [
            {"id": s.id, "title": s.title, "level": s.level, "content_len": len(s.content), "start": s.content[:80]}
            for s in state.material.sections
        ],
        "quizzes": {
            qid: {"n": len(q.questions), "state": q.state.value, "answers": len(q.answers)}
            for qid, q in state.quizzes.items()
        },
        "text_inputs": {tid: {"state": t.state.value, "answer": t.answer[:80]} for tid, t in state.text_inputs.items()},
        "stale": state.stale_sections(),
        "running": BOOK.running(),
    }


@ui.page("/")
def index_page():
    pages = get_book().pages()
    first = next((route for route, e in pages.items() if e.is_chapter), next(iter(pages), None))
    if first is None:
        raise HTTPException(404, "The outline links no pages")
    return RedirectResponse(first)


def chapter_page(book: Book, route: str, entry: OutlineEntry) -> None:
    """Any page of the outline, a chapter folder or a one-file page."""
    if not (book.vault / f"{entry.target}.md").is_file():
        raise HTTPException(404, f"{entry.target}.md is not in the vault")
    chapter = book.chapter(page_key(entry.target))
    # Pick up what was written while no page was open
    chapter.live.poll_all()
    book.first_visit(chapter)
    # Figure links, in the vault and in rewrites alike, are relative to the page's vault folder
    set_page_folder(page_folder(entry.target))

    async def on_quiz_submit(quiz: Quiz, on_progress: Callable[[str], None] | None = None) -> dict:
        plan = book.submit_quiz(chapter, quiz)
        if on_progress:
            on_progress("Reading your answers...")
        feedback = await run.io_bound(book.quiz_feedback, chapter, quiz, plan)
        return {"feedback": feedback, "content_changed": bool(plan.tasks)}

    async def on_quiz_partial(quiz: Quiz) -> None:
        chapter.save_answers()

    async def on_quiz_skip(quiz: Quiz) -> None:
        book.skip_quiz(chapter, quiz)

    async def on_text_input_submit(text_input: TextInput, answer: str) -> bool:
        return await run.io_bound(book.submit_text_input, chapter, text_input, answer)

    async def on_text_input_skip(text_input: TextInput) -> None:
        book.skip_text_input(chapter, text_input)

    async def on_personalize_again() -> None:
        names = book.personalize_again(chapter)
        if names:
            titles = ", ".join(chapter.doc.sections[n].title for n in names)
            ui.notify(f"Rewriting the updated sections for you: {titles}", type="positive")
        else:
            ui.notify("No section changed since it was written for you.")

    refresh_all = render_page(
        live_material=chapter.live,
        title=chapter.title,
        route=route,
        outline=book.outline(),
        # The widget appends to its list, so it gets a copy of the saved chat
        chat_messages=list(book.chat.display),
        render_kwargs=dict(
            text_inputs=chapter.text_inputs,
            on_quiz_submit=on_quiz_submit,
            on_quiz_partial=on_quiz_partial,
            on_quiz_skip=on_quiz_skip,
            on_text_input_submit=on_text_input_submit,
            on_text_input_skip=on_text_input_skip,
        ),
        on_chat_send=lambda message: book.chat.handle(message, chapter),
        on_reset=reset,
        on_personalize_again=on_personalize_again,
        get_running_threads=running_tasks,
    )

    def poll() -> None:
        """Errors here are logged by NiceGUI's timer, which keeps running."""
        changed = chapter.live.poll_all()
        if changed:
            log.debug("%s: %s changed on disk", chapter.key, sorted(changed))
        refresh_all(version_bar_only=True)

    ui.timer(2.0, poll)


# Registered last, so NiceGUI's own routes and the ones above come first
@ui.page("/{path:path}")
def outline_page(path: str) -> None:
    book = get_book()
    route = "/" + path.strip("/")
    entry = book.pages().get(route)
    if entry is None:
        raise HTTPException(404, f"No page at {route}")
    chapter_page(book, route, entry)


if __name__ in {"__main__", "__mp_main__"}:
    parser = argparse.ArgumentParser(description="QuickLearn")
    parser.add_argument("--port", type=int, default=8889, help="Port to serve on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    args, _ = parser.parse_known_args()

    log.info("Starting QuickLearn on %s:%d, vault %s", args.host, args.port, VAULT)
    ui.run(
        host=args.host,
        port=args.port,
        title="QuickLearn",
        storage_secret="quicklearn-dev-secret",
        reload=False,
    )
