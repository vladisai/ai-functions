"""Left drawer navigation: the lectures and the book's chapters from content/outline.md."""

from __future__ import annotations

from nicegui import ui

from quicklearn.vault.outline import OutlineEntry


def render_book_nav(outline: list[OutlineEntry], current: str, toc: list[tuple[str, str]]) -> None:
    """Render the outline, with the entry for this page expanded into its table of contents.

    current: the path of this page, e.g. "/" or "/lectures/lecture_1".
    toc: (anchor, title) pairs of this page's sections.
    """
    in_part = False
    for entry in outline:
        if entry.kind == "group":
            in_part = False
            ui.label(entry.title).classes("text-sm font-bold uppercase tracking-wide text-gray-500 mt-4 mb-1")
        elif entry.kind == "part":
            in_part = True
            ui.label(entry.title).classes("text-xs uppercase tracking-wide text-gray-400 mt-3 mb-1 ml-2")
        else:
            indent = "ml-4" if in_part else "ml-2"
            if not entry.link:
                ui.label(entry.title).classes(f"text-sm text-gray-300 py-0.5 {indent} cursor-default")
                continue
            is_current = entry.link == current
            ui.link(entry.title, target=entry.link).classes(
                f"text-sm no-underline block py-0.5 {indent} "
                + ("text-black font-semibold" if is_current else "text-gray-700 hover:text-black")
            )
            if is_current:
                for anchor, title in toc:
                    ui.link(title, target=f"#{anchor}").classes(
                        "text-sm text-gray-600 hover:text-black no-underline block py-0.5 ml-8"
                    )
