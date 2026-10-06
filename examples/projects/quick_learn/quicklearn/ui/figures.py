"""Figures and embedded pages of the vault: the route that serves them, and the links to it.

A page links its figures relative to its own folder in the vault, as Obsidian does, so
lectures/lecture_2.md has `![alt](lecture_2/fig.svg)`, `![[lecture_2/fig.svg]]` or
`<iframe src="lecture_2/stepper.html">`. A rewritten section lives in the reader's version folder
but keeps those links, so they resolve against the page's vault folder, never the version folder:
resolve_figures turns them into /vault/lectures/lecture_2/fig.svg, which vault_file serves. It
serves every file of the vault but markdown, hidden files and the reader folders.

A section renders unsanitized only when its only raw HTML is iframes of vault files (trusted_html),
since the browser's sanitizer drops iframes and the rewrites are model output.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from nicegui import ui

from quicklearn.reader.store import PERSONAL_DIR

VAULT_ROUTE = "/vault"
_FOLDER_ATTR = "_quicklearn_page_folder"

_MD_IMAGE = re.compile(r"(!\[[^\]\n]*\]\()\s*(<[^>\n]+>|[^)\s]+)([^)\n]*\))")
IMAGE_SUFFIXES = ("svg", "png", "jpg", "jpeg", "gif", "webp", "avif", "bmp")
# An Obsidian image embed, ![[fig.svg]] or ![[fig.svg|alt]]. vault/chapter.py leaves them to the text.
WIKI_IMAGE = re.compile(
    r"!\[\[([^\[\]|#^\n]+\.(?:" + "|".join(IMAGE_SUFFIXES) + r"))(?:\|([^\[\]\n]*))?\]\]", re.IGNORECASE
)
_HTML_SRC = re.compile(r"(<(?:iframe|img)\b[^>]*?\bsrc\s*=\s*)([\"'])([^\"']*)\2", re.IGNORECASE)
_EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|/|#)", re.IGNORECASE)
_RAW_TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)\b([^>]*)>")
_SAFE_IFRAME_ATTRS = {"src", "title", "style", "width", "height", "loading"}
_ATTR = re.compile(r"""([a-zA-Z-]+)\s*=\s*(?:"[^"]*"|'[^']*'|\S+)""")
# A script URL as a link target, an attribute value or a reference link's target
_SCRIPT_URL = re.compile(
    r"""(?:\]\(\s*<?|=\s*["']?\s*|^\[[^\]\n]+\]:\s*<?)(?:javascript|vbscript|data)\s*:""", re.IGNORECASE | re.MULTILINE
)


def page_folder(target: str) -> str:
    """The vault folder of an outline target.

    lectures/lecture_2 gives lectures, and book/probability/chapter gives book/probability.
    """
    parent = PurePosixPath(target.strip("/")).parent.as_posix()
    return "" if parent == "." else parent


def vault_file(vault: Path, path: str) -> Path | None:
    """The vault file at path, or None for a missing file, markdown, a hidden file or a reader folder."""
    root = vault.resolve()
    file = (root / path).resolve()
    if not file.is_relative_to(root) or not file.is_file() or file.suffix.lower() == ".md":
        return None
    parts = file.relative_to(root).parts
    if parts[0] == PERSONAL_DIR or any(part.startswith(".") for part in parts):
        return None
    return file


def _url(folder: str, link: str) -> str:
    """The route of a relative link in folder, e.g. lecture_2/fig.svg?theme=light in lectures."""
    path, sep, query = link.partition("?")
    parts: list[str] = [p for p in folder.split("/") if p]
    for part in path.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part not in ("", "."):
            parts.append(part)
    return f"{VAULT_ROUTE}/{quote('/'.join(parts))}{sep}{query}"


def resolve_figures(text: str, folder: str | None) -> str:
    """Point the relative figure links and iframe sources of a page in folder at VAULT_ROUTE.

    `![[x.svg|alt]]` becomes `![alt](...)`. With folder None, the text stays as it is.
    """
    if folder is None:
        return text

    def wiki(match: re.Match) -> str:
        alt = (match.group(2) or "").strip()
        return f"![{alt}]({_url(folder, match.group(1).strip())})"

    def image(match: re.Match) -> str:
        link = match.group(2).strip("<>")
        return match.group(0) if _EXTERNAL.match(link) else f"{match.group(1)}{_url(folder, link)}{match.group(3)}"

    def html(match: re.Match) -> str:
        link = match.group(3)
        if _EXTERNAL.match(link):
            return match.group(0)
        return f"{match.group(1)}{match.group(2)}{_url(folder, link)}{match.group(2)}"

    text = WIKI_IMAGE.sub(wiki, text)
    text = _MD_IMAGE.sub(image, text)
    return _HTML_SRC.sub(html, text)


def trusted_html(text: str) -> bool:
    """Whether markdown, after resolve_figures, can render unsanitized: it has an iframe, its only raw
    HTML is iframes of vault files with plain attributes, and it has no script URL anywhere."""
    without_comments = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    tags = _RAW_TAG.findall(without_comments)
    if not any(name.lower() == "iframe" for _, name, _ in tags) or _SCRIPT_URL.search(without_comments):
        return False
    for closing, name, attrs in tags:
        if name.lower() != "iframe":
            return False
        if closing:
            continue
        if not {m.group(1).lower() for m in _ATTR.finditer(attrs)} <= _SAFE_IFRAME_ATTRS:
            return False
        src = re.search(r"""\bsrc\s*=\s*["']([^"']*)["']""", attrs, re.IGNORECASE)
        if src is None or not src.group(1).startswith(f"{VAULT_ROUTE}/"):
            return False
    return True


def set_page_folder(folder: str) -> None:
    """Resolve the figures of every markdown element of this client's page against folder."""
    setattr(ui.context.client, _FOLDER_ATTR, folder)


def client_page_folder(client=None) -> str | None:
    """The folder set_page_folder gave the client, by default the current one, or None outside a page."""
    try:
        client = client or ui.context.client
    except RuntimeError:
        return None
    return getattr(client, _FOLDER_ATTR, None)


def add_vault_route(app: FastAPI, get_vault: Callable[[], Path]) -> None:
    """Serve the vault's figures, embedded pages and other files under VAULT_ROUTE."""

    @app.get(VAULT_ROUTE + "/{path:path}")
    def vault_asset(path: str) -> FileResponse:
        file = vault_file(get_vault(), path)
        if file is None:
            raise HTTPException(404, f"No file {path} in the vault")
        return FileResponse(file)
