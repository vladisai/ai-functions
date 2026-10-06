"""Obsidian wikilinks in vault text: `[[target]]`, `[[target|label]]` and the embed `![[name]]`."""

from __future__ import annotations

import re
from collections.abc import Callable

WIKILINK = re.compile(r"(!?)\[\[([^\[\]|]+?)(?:\|([^\[\]]+?))?\]\]")
IMAGE_EMBED = re.compile(r".+\.(?:svg|png|jpe?g|gif|webp|avif|bmp)\s*$", re.IGNORECASE)


def split_target(target: str) -> tuple[str, str]:
    """("book/probability/chapter", "heading") from "book/probability/chapter.md#heading"."""
    path, _, anchor = target.strip().partition("#")
    return path.strip().removesuffix(".md"), anchor.strip()


def route_of(path: str) -> str:
    """The page that shows a vault file: book/preface → /book/preface, book/probability/chapter → /book/probability."""
    path = path.strip("/").removesuffix(".md")
    if path == "chapter":
        return "/"
    return "/" + path.removesuffix("/chapter")


def render_links(text: str, resolve: Callable[[str], str | None]) -> str:
    """Turn wikilinks into markdown links. resolve(target path) gives the href, or None for plain text.

    Embeds left in the text, like a heading embed, show as their name, since a chapter embeds whole
    files only and the check command reports the rest.
    """

    def replace(match: re.Match) -> str:
        bang, target, label = match.groups()
        if bang and IMAGE_EMBED.match(target):
            return match.group(0)  # a figure, which ui/figures.py shows
        path, anchor = split_target(target)
        label = (label or (anchor or path.rsplit("/", 1)[-1])).strip()
        href = None if bang else resolve(path)
        if href is None:
            return label
        return f"[{label}]({href}{'#' + anchor if anchor and '#' not in href else ''})"

    return WIKILINK.sub(replace, text)
