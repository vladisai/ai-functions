"""Front matter: the `---` block of YAML at the top of a vault file, which Obsidian shows as properties."""

from __future__ import annotations

import yaml


def split_front_matter(text: str) -> tuple[dict, str]:
    """(properties, the text after the block). A file without the block has no properties."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 3)  # from the opening line's newline, so an empty block ends at once
    if end == -1:
        return {}, text
    properties = yaml.safe_load(text[4:end]) or {}
    rest = text[end + 4:]
    return properties, rest.removeprefix("\n")


def topics_of(properties: dict) -> list[str]:
    """The `topics` property, written as a YAML list or as one comma-separated line."""
    topics = properties.get("topics") or []
    if isinstance(topics, str):
        topics = topics.split(",")
    return [str(t).strip() for t in topics if str(t).strip()]
