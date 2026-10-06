"""Main page layout: header, TOC sidebar, content area, and chat widget."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable

from nicegui import Client, ui

from quicklearn.chapter.live import LiveMaterial
from quicklearn.core.material import Material
from quicklearn.ui.book_nav import render_book_nav
from quicklearn.ui.chat_widget import render_chat_widget
from quicklearn.ui.colors import VERSION_BAR_BACK_BTN, VERSION_BAR_HISTORICAL
from quicklearn.ui.page_ui import PageUI
from quicklearn.vault.outline import OutlineEntry

WIDGET_TAG = re.compile(r"^\s*<!--\s*(quiz|text_input):")


def _setup_styles() -> None:
    """Add Splendor typography for markdown content + table styling."""
    ui.add_head_html("""
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Merriweather:300italic,300">
    <style>
        /* Splendor (markdowncss) — scoped to .nicegui-markdown */
        .nicegui-markdown {
            color: #1a1a1a;
            font-family: 'Merriweather', Georgia, serif;
            line-height: 1.85;
        }
        .nicegui-markdown p {
            font-size: 1rem;
            margin-bottom: 1.3rem;
            color: #2a2a2a;
            line-height: 1.45;
        }
        .nicegui-markdown h1,
        .nicegui-markdown h2,
        .nicegui-markdown h3,
        .nicegui-markdown h4 {
            margin: 1.414rem 0 .5rem;
            font-weight: inherit;
            line-height: 1.42;
        }
        .nicegui-markdown h1 { font-size: 1.8rem; margin-top: 0; }
        .nicegui-markdown h2 { font-size: 1.5rem; }
        .nicegui-markdown h3 { font-size: 1.25rem; }
        .nicegui-markdown h4 { font-size: 1.1rem; }
        .nicegui-markdown h5 { font-size: 1rem; }
        .nicegui-markdown h6 { font-size: .88rem; }
        .nicegui-markdown small { font-size: .707em; }
        .nicegui-markdown blockquote p {
            font-size: 1.5rem;
            font-style: italic;
        }
        .nicegui-markdown ul {
            list-style: disc !important;
            padding-left: 2rem !important;
            margin-bottom: 1rem !important;
            display: block !important;
        }
        .nicegui-markdown ol {
            list-style: decimal !important;
            padding-left: 2rem !important;
            margin-bottom: 1rem !important;
            display: block !important;
        }
        .nicegui-markdown li {
            margin-bottom: 0.25rem;
            display: list-item !important;
        }
        .nicegui-markdown pre,
        .nicegui-markdown code {
            font-family: Menlo, Monaco, "Courier New", monospace;
        }
        .nicegui-markdown pre {
            background-color: #fafafa;
            font-size: .8rem;
            overflow-x: auto;
            padding: 1.125em;
        }
        .nicegui-markdown a,
        .nicegui-markdown a:visited { color: #3498db; }
        .nicegui-markdown a:hover,
        .nicegui-markdown a:focus,
        .nicegui-markdown a:active { color: #2980b9; }

        /* Figures and embedded pages, see ui/figures.py */
        .nicegui-markdown img { max-width: 100%; height: auto; display: block; margin: 1.5rem auto 0.5rem; }
        .nicegui-markdown iframe { display: block; margin: 1.5rem 0 0.5rem; }
        .nicegui-markdown p:has(> img + img) img { display: inline-block; width: 32%; margin: 1.5rem 0.5% 0.5rem; }

        /* Tables */
        .nicegui-markdown table { border-collapse: collapse; margin: 1em 0; }
        .nicegui-markdown th,
        .nicegui-markdown td { padding: 0.5em 1em; border: 1px solid #d1d5db; }
        .nicegui-markdown th { background: #f3f4f6; font-weight: 600; }

        /* Section flash animation — orange bg fades out */
        @keyframes sectionFlash {
            from { background-color: #fef3c7; }
            to   { background-color: transparent; }
        }
        .section-flash {
            animation: sectionFlash 1.5s ease-out forwards;
        }

        /* Expose header height as CSS variable for fixed-position panels */
        :root { --ql-header-h: 50px; }
    </style>
    """)


def _render_agent_activity(get_running_threads: Callable[[], int]) -> None:
    """Header indicator: spinner + label while the chat agent or any rewrite task is running."""
    with ui.row().classes("items-center gap-2 ml-6") as row:
        ui.spinner("dots", size="md", color="amber-8")
        label = ui.label().classes("text-sm text-amber-800")

    def _update() -> None:
        n = get_running_threads()
        row.set_visibility(n > 0)
        if n > 1:
            label.set_text(f"Agent is working · {n} tasks")
        else:
            label.set_text("Agent is working")

    _update()
    ui.timer(1.0, _update)


def render_page(
    live_material: LiveMaterial,
    title: str,
    route: str,
    outline: list[OutlineEntry],
    chat_messages: list[dict[str, str]],
    render_kwargs: dict,
    on_chat_send: Callable[[str], str] | None = None,
    on_reset: Callable[[], None] | None = None,
    on_personalize_again: Callable[[], Awaitable[None]] | None = None,
    get_running_threads: Callable[[], int] | None = None,
) -> Callable[..., None]:
    """Build a page of the book: drawer, header with the version bar, sections and chat.

    render_kwargs are the callbacks every section gets, see content_renderer.render_section;
    on_quiz_feedback is added here, since it pushes into this page's chat.

    Returns refresh_all. With version_bar_only=True it refreshes the version bar only, and
    rebuilds the sections when the version on screen changed under the page.
    """
    material = live_material.material
    _setup_styles()

    with _drawer() as drawer:
        render_book_nav(outline, route, _section_toc(material))

    with ui.header().classes("bg-white text-black border-b border-gray-200"):
        ui.button(icon="menu").props("flat dense round color=dark").on("click", drawer.toggle)
        ui.label("QuickLearn").classes("text-xl font-bold")
        ui.label(title).classes("text-xl ml-2")

        @ui.refreshable
        def version_bar() -> None:
            if material.total_versions <= 1:
                return
            viewing = material.viewing_version
            total = material.total_versions
            is_historical = not material.is_at_head

            bg = f"rounded px-3 py-1 {VERSION_BAR_HISTORICAL}" if is_historical else ""
            with ui.row().classes(f"items-center gap-1 {bg}"):
                ui.button(icon="chevron_left").props(
                    "flat dense round size=sm color=dark" + (" disable" if not material.can_go_back else "")
                ).on("click", lambda: _navigate(material.viewing_version - 1))

                ui.button(icon="chevron_right").props(
                    "flat dense round size=sm color=dark" + (" disable" if not material.can_go_forward else "")
                ).on("click", lambda: _navigate(material.viewing_version + 1))

                label_text = f"v{viewing + 1}/{total}"
                if is_historical:
                    label_text += " · an earlier version"
                ui.label(label_text).classes("text-xs text-gray-500 whitespace-nowrap")

                if is_historical:
                    ui.button("Latest", icon="fast_forward").props(
                        f"flat dense size=sm {VERSION_BAR_BACK_BTN}"
                    ).classes("text-xs").on("click", lambda: _navigate(material.total_versions - 1))

        ui.space()
        if get_running_threads:
            _render_agent_activity(get_running_threads)

        version_bar()

        if on_personalize_again:
            ui.button(icon="auto_fix_high", on_click=on_personalize_again).props(
                "flat dense round size=sm color=grey"
            ).tooltip("Personalize again: rewrite the sections the author updated")

        # Reset, behind a confirm dialog since it wipes everything
        if on_reset:
            def handle_reset() -> None:
                reset_dialog.close()
                on_reset()
                _reload_all_pages()

            with ui.dialog() as reset_dialog, ui.card():
                ui.label("Reset everything?").classes("text-lg font-bold")
                ui.label(
                    "This clears what the book knows about you, your answers, the chat and every version."
                ).classes("text-sm")
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Cancel", on_click=reset_dialog.close).props("flat color=grey")
                    ui.button("Reset", icon="restart_alt", on_click=handle_reset).props("color=red")

            ui.button(icon="restart_alt").props(
                "flat dense round size=sm color=grey"
            ).tooltip("Reset everything").on("click", reset_dialog.open)

    def _navigate(index: int) -> None:
        # The buttons read the version when clicked, and a fast second click
        # can land before the bar re-renders, so the index may step past v1.
        index = max(index, 0)
        if index >= material.total_versions - 1:
            material.go_to_head()
        else:
            material.go_to_version(index)
        version_bar.refresh()
        page_ui.rebuild_all(live_material, render_kwargs)

    chat_push: dict[str, Callable[[str], None] | None] = {"fn": None}
    render_kwargs = dict(render_kwargs, on_quiz_feedback=lambda msg: chat_push["fn"] and chat_push["fn"](msg))

    def refresh_all(version_bar_only: bool = False) -> None:
        if not version_bar_only or page_ui.shown_cursor != material.version_cursor:
            # The version changed under this page: a new version opened while the
            # reader browsed an older one, or another browser tab navigated.
            page_ui.rebuild_all(live_material, render_kwargs)
        version_bar.refresh()

    page_ui = PageUI()
    page_ui.render_initial(live_material, render_kwargs)

    chat_push["fn"] = render_chat_widget(
        chat_messages,
        on_send=on_chat_send,
        # Next to the open chat, the 300px TOC covers the text in windows narrower than 2200px
        on_open=lambda: ui.run_javascript(f"if (window.innerWidth < 2200) getElement({drawer.id}).hide()"),
    )

    # Measure actual header height after Vue renders and set CSS variable
    ui.timer(0.5, lambda: ui.run_javascript(
        "const h = document.querySelector('.q-header');"
        "if (h) document.documentElement.style.setProperty('--ql-header-h', h.offsetHeight + 'px');"
    ), once=True)

    return refresh_all


def _reload_all_pages() -> None:
    """Reload every open page, since a reset replaces the state all of them show."""
    for client in list(Client.instances.values()):
        if client.has_socket_connection:
            client.run_javascript("history.go(0)")


def _drawer() -> ui.left_drawer:
    return ui.left_drawer(value=True, elevated=True).props("overlay").classes("bg-white border-r border-gray-200 p-4")


def _section_toc(material: Material) -> list[tuple[str, str]]:
    """The page's sections for the drawer, leaving out quizzes, text inputs and text without a heading."""
    return [
        (f"section-{section.id}", section.title)
        for section in material.sections
        if section.title and not WIDGET_TAG.match(section.content)
    ]
