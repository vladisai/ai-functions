"""Version folders of a chapter in the reader folder: creating, listing and the current pointer."""

from pathlib import Path

import pytest
from quicklearn.chapter.versions import (
    create_version,
    get_current_version,
    get_current_version_dir,
    list_versions,
    set_current_version,
)


@pytest.fixture
def chapter_dir(tmp_path: Path) -> Path:
    path = tmp_path / "tester" / "book" / "ch"
    path.mkdir(parents=True)
    return path


def test_create_empty_and_sequential(chapter_dir: Path):
    assert create_version(chapter_dir) == chapter_dir / "v_0"
    assert create_version(chapter_dir) == chapter_dir / "v_1"
    assert list(chapter_dir.glob("v_*/*")) == []


def test_create_copies_the_source_version(chapter_dir: Path):
    (create_version(chapter_dir) / "alpha.md").write_text("hello")
    v1 = create_version(chapter_dir, from_version=0)
    assert (v1 / "alpha.md").read_text() == "hello"
    with pytest.raises(FileNotFoundError):
        create_version(chapter_dir, from_version=99)


def test_create_makes_the_parent_folders(tmp_path: Path):
    assert create_version(tmp_path / "deep" / "nested").is_dir()


def test_current_pointer(chapter_dir: Path):
    assert get_current_version(chapter_dir) is None and get_current_version_dir(chapter_dir) is None
    create_version(chapter_dir)
    create_version(chapter_dir)
    set_current_version(chapter_dir, 0)
    assert get_current_version(chapter_dir) == 0
    set_current_version(chapter_dir, 1)
    assert get_current_version(chapter_dir) == 1
    assert get_current_version_dir(chapter_dir) == chapter_dir / "v_1"
    # A relative symlink, so a copy of the reader folder keeps working
    assert (chapter_dir / "current").readlink() == Path("v_1")
    with pytest.raises(FileNotFoundError):
        set_current_version(chapter_dir, 42)


def test_text_file_pointer(chapter_dir: Path):
    create_version(chapter_dir)
    (chapter_dir / "current").write_text("v_0\n")
    assert get_current_version(chapter_dir) == 0
    (chapter_dir / "current").write_text("garbage\n")
    assert get_current_version(chapter_dir) is None


def test_list_versions(chapter_dir: Path, tmp_path: Path):
    assert list_versions(tmp_path / "nope") == []
    for _ in range(3):
        create_version(chapter_dir)
    (chapter_dir / "v_x").mkdir()
    (chapter_dir / "other").mkdir()
    (chapter_dir / "v_9").write_text("a file, not a version")
    (chapter_dir / "current").symlink_to("v_2")
    assert list_versions(chapter_dir) == [0, 1, 2]
    for i in (10, 11):
        (chapter_dir / f"v_{i}").mkdir()
    assert list_versions(chapter_dir) == [0, 1, 2, 10, 11]
