"""PageUI: UI counterpart to LiveMaterial — tracks rendered elements per section.

On initial render, creates containers and wires each SectionUI to its
corresponding LiveSection via bind(). When a LiveSection detects a file change,
the bound SectionUI updates the DOM surgically:
- Content sections: set .content on the ui.markdown element (no DOM destruction)
- Quiz/structural changes: clear container + re-render that section only
"""

from __future__ import annotations

from dataclasses import dataclass, field

from nicegui import ui

from quicklearn.chapter.live import ContentLive, LiveMaterial, LiveSection
from quicklearn.core.material import Material, Section
from quicklearn.core.quiz import Quiz
from quicklearn.ui.content_renderer import NOTE_TAG_PATTERN, render_section
from quicklearn.ui.math_markdown import update_math_markdown


@dataclass
class SectionUI:
    """UI binding target for one section.

    Stores a reference to the section's container and (for content sections)
    the ui.markdown element for in-place text updates.
    """

    section_id: str
    container: ui.column
    material: Material
    content_el: ui.markdown | None = None
    # Stored at bind time by PageUI for use in on_live_change callback
    _quizzes: dict[str, Quiz] = field(default_factory=dict, repr=False)
    _render_kwargs: dict = field(default_factory=dict, repr=False)

    def set_content(self, text: str, flash: bool = False) -> None:
        """Fast path: update markdown text in-place. Zero DOM destruction."""
        if self.content_el is None:
            return
        update_math_markdown(self.content_el, NOTE_TAG_PATTERN.sub("", text))
        if flash:
            # Remove then re-add to retrigger CSS animation
            self.container.classes(remove="section-flash")
            self.container.classes(add="section-flash")

    def rebuild(self, section: Section, quizzes: dict[str, Quiz],
                render_kwargs: dict, **extra) -> None:
        """Slow path: clear + re-render. For structural changes."""
        self.container.clear()
        self.content_el = None
        with self.container:
            self.content_el = render_section(section, quizzes, **render_kwargs, **extra)

    def on_live_change(self, live_section: LiveSection) -> None:
        """Callback wired to LiveSection.bind(). Routes to fast or slow path."""
        if not self.material.is_at_head:
            return  # the page shows an older version; returning to the latest rebuilds every section
        section = live_section.section
        has_notes = bool(NOTE_TAG_PATTERN.search(section.content))
        # Fast path: content section with existing markdown element, no notes
        if (isinstance(live_section, ContentLive)
                and self.content_el is not None
                and section.content.strip()
                and not has_notes):
            self.set_content(section.content, flash=True)
        else:
            # Slow path: a quiz, a section that had no text, or change notes
            self.rebuild(section, self._quizzes, self._render_kwargs, flash=True)


class PageUI:
    """UI counterpart to LiveMaterial. Tracks rendered elements per section.

    On initial render, creates containers and wires each SectionUI
    to its corresponding LiveSection via bind().
    """

    def __init__(self) -> None:
        self.sections: dict[str, SectionUI] = {}
        # Material.version_cursor of the version on screen, -1 for the latest
        self.shown_cursor = -1

    def render_initial(self, live_material: LiveMaterial,
                       render_kwargs: dict) -> None:
        """First render: create containers, render sections, wire bindings."""
        with ui.column().classes("w-full max-w-4xl mx-auto p-8"):
            for ls in live_material.live_sections:
                container = ui.column().classes("w-full")
                sui = SectionUI(
                    section_id=ls.section.id,
                    container=container,
                    material=live_material.material,
                    _quizzes=live_material.quizzes,
                    _render_kwargs=render_kwargs,
                )
                self.sections[ls.section.id] = sui
                with container:
                    sui.content_el = render_section(
                        ls.section, live_material.quizzes, **render_kwargs,
                    )
                # Wire binding: LiveSection change → SectionUI update
                ls.bind(sui.on_live_change)
                ui.context.client.on_delete(lambda ls=ls, sui=sui: ls.unbind(sui.on_live_change))
        self.shown_cursor = live_material.material.version_cursor

    def rebuild_all(self, live_material: LiveMaterial,
                    render_kwargs: dict) -> None:
        """Full rebuild: version navigation, content adaptation.
        Clears and re-renders every section.

        Uses material.sections (which reflects the navigated-to version)
        rather than LiveSection.section (which always points at head content).
        """
        sections_by_id = {s.id: s for s in live_material.material.sections}
        for ls in live_material.live_sections:
            section = sections_by_id.get(ls.section.id)
            sui = self.sections.get(ls.section.id)
            if sui and section:
                sui.rebuild(section, live_material.quizzes, render_kwargs)
        self.shown_cursor = live_material.material.version_cursor
