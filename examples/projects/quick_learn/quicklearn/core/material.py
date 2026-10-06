from __future__ import annotations

import copy
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class Section:
    id: str  # e.g. "1", "1.1", "quiz", "summary"
    title: str
    content: str  # Markdown with LaTeX. Quizzes inline as <!-- quiz:quiz_id -->
    level: int = 2  # heading level: 2 for ##, 3 for ###, etc.


@dataclass
class Snapshot:
    """A frozen copy of the sections list at a point in time."""

    sections: list[Section]
    description: str = ""


@dataclass
class SectionDiff:
    """A change to apply to a single section."""

    section_id: str
    new_content: str | None = None  # None means no content change
    new_title: str | None = None  # None means no title change


class Material:
    """The content model: a list of sections with linear versioning and cursor-based navigation.

    Timeline: version_stack has N snapshots (indices 0..N-1). The live `sections`
    is version N. Total versions = N+1. Cursor -1 means "at head" (live content).
    """

    def __init__(self, sections: list[Section] | None = None) -> None:
        self.sections: list[Section] = sections or []
        self.version_stack: list[Snapshot] = []
        self.version_cursor: int = -1  # -1 = head, 0..N-1 = historical
        self._head_sections: list[Section] | None = None  # stash of live content when browsing
        self._batch_active: bool = False

    # ── Navigation properties ───────────────────────────────────────

    @property
    def viewing_version(self) -> int:
        """0-based index of the version currently being displayed."""
        if self.version_cursor == -1:
            return len(self.version_stack)
        return self.version_cursor

    @property
    def total_versions(self) -> int:
        return len(self.version_stack) + 1

    @property
    def is_at_head(self) -> bool:
        return self.version_cursor == -1

    @property
    def can_go_back(self) -> bool:
        return self.viewing_version > 0

    @property
    def can_go_forward(self) -> bool:
        return not self.is_at_head

    @property
    def current_version_description(self) -> str:
        if self.is_at_head:
            return "Current"
        snap = self.version_stack[self.version_cursor]
        return snap.description or f"Version {self.version_cursor + 1}"

    # ── Navigation methods ──────────────────────────────────────────

    def go_to_version(self, index: int) -> None:
        """Jump to a specific version. index in [0, total_versions-1]."""
        total = self.total_versions
        if index < 0 or index >= total:
            raise ValueError(f"Version {index} out of range [0, {total - 1}]")
        if index == len(self.version_stack):
            self.go_to_head()
            return
        # Stash the live Section objects themselves: the disk poller keeps
        # updating them while the reader browses, and go_to_head brings them back.
        if self.is_at_head:
            self._head_sections = self.sections
        self.version_cursor = index
        self.sections = copy.deepcopy(self.version_stack[index].sections)

    def go_to_head(self) -> None:
        """Return to the latest live content."""
        if self.is_at_head:
            return
        if self._head_sections is not None:
            self.sections = self._head_sections
            self._head_sections = None
        self.version_cursor = -1

    # ── Section lookup ──────────────────────────────────────────────

    def get_section(self, section_id: str) -> Section:
        for s in self.sections:
            if s.id == section_id:
                return s
        raise KeyError(f"Section '{section_id}' not found")

    def get_section_index(self, section_id: str) -> int:
        for i, s in enumerate(self.sections):
            if s.id == section_id:
                return i
        raise KeyError(f"Section '{section_id}' not found")

    # ── Versioning ──────────────────────────────────────────────────

    def snapshot(self, description: str = "") -> None:
        """Save current state to the version stack.

        If browsing a historical version, auto-returns to head first
        so mutations always apply to the live content.
        Skipped when inside a batch() context (one snapshot taken at batch start).
        """
        if self._batch_active:
            return
        if not self.is_at_head:
            self.go_to_head()
        snap = Snapshot(
            sections=[copy.deepcopy(s) for s in self.sections],
            description=description,
        )
        self.version_stack.append(snap)

    @contextmanager
    def batch(self, description: str = ""):
        """Batch multiple mutations into a single version.

        Takes one snapshot before the batch starts, then suppresses
        per-mutation snapshots until the batch ends.
        """
        self.snapshot(description)
        self._batch_active = True
        try:
            yield
        finally:
            self._batch_active = False

    # ── Mutations (all auto-snapshot before changing) ───────────────

    def apply_diff(self, diff: SectionDiff) -> None:
        """Apply a targeted change to one section. Auto-snapshots before."""
        section = self.get_section(diff.section_id)
        self.snapshot(f"Before diff to '{diff.section_id}'")
        if diff.new_content is not None:
            section.content = diff.new_content
        if diff.new_title is not None:
            section.title = diff.new_title

    def update_section(self, section_id: str, new_content: str) -> None:
        """Replace a section's content. Auto-snapshots before."""
        self.apply_diff(SectionDiff(section_id=section_id, new_content=new_content))

    def add_section(self, after_section_id: str, section: Section) -> None:
        """Insert a new section after the given one. Auto-snapshots before."""
        idx = self.get_section_index(after_section_id)
        self.snapshot(f"Before adding section '{section.id}'")
        self.sections.insert(idx + 1, section)

    def remove_section(self, section_id: str) -> None:
        """Remove a section. Auto-snapshots before."""
        idx = self.get_section_index(section_id)
        self.snapshot(f"Before removing section '{section_id}'")
        self.sections.pop(idx)

    # ── Convenience properties ──────────────────────────────────────

    @property
    def section_ids(self) -> list[str]:
        return [s.id for s in self.sections]

    @property
    def toc(self) -> list[tuple[str, str]]:
        """Return list of (id, title) for table of contents."""
        return [(s.id, s.title) for s in self.sections]
