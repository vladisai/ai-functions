"""The book outline, `content/outline.md`: the drawer's navigation and the list of pages that exist.

    # Lectures                                         a group
    - [[lectures/lecture_1|Lecture 1]]                 a one-file page
    # Agentic Book
    ## Background                                      a part of the book
    - [[book/probability/chapter|Probability Primer]]  a chapter folder, from its chapter.md
    - Information                                      a chapter without material yet, greyed out

Every linked page is adaptive, see vault/chapter.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from quicklearn.vault.links import route_of, split_target

_ITEM_LINK = re.compile(r"\[\[([^\[\]|]+?)(?:\|([^\[\]]+?))?\]\]")


@dataclass
class OutlineEntry:
    kind: str  # "group", "part" or "chapter"
    title: str
    link: str = ""  # the page's route, e.g. "/book/probability"; empty for a chapter without material yet
    target: str = ""  # the vault file, e.g. "book/probability/chapter"
    line: int = 0

    @property
    def is_chapter(self) -> bool:
        """A link to a chapter folder's chapter.md, rather than to a one-file page."""
        return self.target.endswith("/chapter") or self.target == "chapter"


def parse_outline(path: Path) -> list[OutlineEntry]:
    """Read the outline's groups, parts and chapters in order. Other lines, like comments, are ignored."""
    entries = []
    in_comment = False
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        if in_comment or line.startswith("<!--"):
            in_comment = "-->" not in line
            continue
        if line.startswith("# "):
            entries.append(OutlineEntry("group", line[2:].strip(), line=lineno))
        elif line.startswith("## "):
            entries.append(OutlineEntry("part", line[3:].strip(), line=lineno))
        elif line.startswith("- "):
            item = line[2:].strip()
            match = _ITEM_LINK.fullmatch(item)
            if match:
                target, _ = split_target(match.group(1))
                title = (match.group(2) or target.rsplit("/", 1)[-1]).strip()
                entries.append(OutlineEntry("chapter", title, route_of(target), target, lineno))
            else:
                entries.append(OutlineEntry("chapter", item, line=lineno))
    return entries
