"""Version folders of a chapter in the reader folder.

    <reader>/<chapter>/v_0/       empty: the chapter as the vault has it
    <reader>/<chapter>/v_1/       after the first rewrite
    <reader>/<chapter>/current → v_1

A version folder holds only what was rewritten for the reader: `<name>.md` with the body of a
section, `<name>.quiz.md` with a `# Learned` part, and sources.json. Anything missing falls back
to the vault, so Reset goes back to the vault, and a git pull updates the sections that were
never rewritten.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

log = logging.getLogger(__name__)

VERSION_PREFIX = "v_"
CURRENT_POINTER = "current"


def create_version(chapter_dir: Path, from_version: int | None = None) -> Path:
    """Create a new version folder in the given tab directory.

    Args:
        chapter_dir: Path to the chapter's folder in the reader folder (e.g. <reader>/book/probability/)
        from_version: If set, copy contents from v_{from_version}/ into the new folder.
                      If None, create an empty folder.

    Returns:
        Path to the newly created version folder.
    """
    chapter_dir.mkdir(parents=True, exist_ok=True)
    existing = list_versions(chapter_dir)
    next_idx = max(existing) + 1 if existing else 0

    new_dir = chapter_dir / f"{VERSION_PREFIX}{next_idx}"

    if from_version is not None:
        src_dir = chapter_dir / f"{VERSION_PREFIX}{from_version}"
        if not src_dir.exists():
            raise FileNotFoundError(f"Source version folder not found: {src_dir}")
        shutil.copytree(src_dir, new_dir)
        log.info("Created version %d from %d in %s", next_idx, from_version, chapter_dir)
    else:
        new_dir.mkdir()
        log.info("Created empty version %d in %s", next_idx, chapter_dir)

    return new_dir


def get_current_version(chapter_dir: Path) -> int | None:
    """Get the current version index from the pointer file/symlink.

    Returns None if no current version is set.
    """
    pointer = chapter_dir / CURRENT_POINTER
    if not pointer.exists():
        return None

    # Handle symlink
    if pointer.is_symlink():
        target = os.readlink(pointer)
        name = Path(target).name
    else:
        # Text file pointer (fallback for systems without symlink support)
        name = pointer.read_text().strip()

    if name.startswith(VERSION_PREFIX):
        try:
            return int(name[len(VERSION_PREFIX):])
        except ValueError:
            pass
    return None


def set_current_version(chapter_dir: Path, version_index: int) -> None:
    """Update the 'current' pointer to a specific version."""
    version_dir = chapter_dir / f"{VERSION_PREFIX}{version_index}"
    if not version_dir.exists():
        raise FileNotFoundError(f"Version folder not found: {version_dir}")

    pointer = chapter_dir / CURRENT_POINTER
    # Remove old pointer
    if pointer.is_symlink() or pointer.exists():
        pointer.unlink()

    # Create relative symlink
    target = f"{VERSION_PREFIX}{version_index}"
    pointer.symlink_to(target)
    log.info("Set current version to %d in %s", version_index, chapter_dir)


def get_current_version_dir(chapter_dir: Path) -> Path | None:
    """Get the path to the current version folder.

    Returns None if no version exists.
    """
    idx = get_current_version(chapter_dir)
    if idx is None:
        return None
    return chapter_dir / f"{VERSION_PREFIX}{idx}"


def list_versions(chapter_dir: Path) -> list[int]:
    """List available version indices, sorted ascending."""
    if not chapter_dir.exists():
        return []

    versions = []
    for child in chapter_dir.iterdir():
        name = child.name
        if child.is_dir() and name.startswith(VERSION_PREFIX) and name != CURRENT_POINTER:
            try:
                versions.append(int(name[len(VERSION_PREFIX):]))
            except ValueError:
                continue
    return sorted(versions)
