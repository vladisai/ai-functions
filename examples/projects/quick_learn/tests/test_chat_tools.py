"""The chat agent's read_vault_file tool: files of the book, but never the reader folders."""

from pathlib import Path

from quicklearn.agents.chat import _READ_LIMIT, read_vault_file
from quicklearn.reader.store import ReaderStore


def test_reads_a_file_of_the_vault(small_vault: Path):
    assert read_vault_file(small_vault, "ch/agent.md") == "Hints for the rewrites.\n"
    assert read_vault_file(small_vault, " /page.md ") == "# A Page\n\nBack to [[ch/chapter|the chapter]].\n"
    assert read_vault_file(small_vault, "ch/missing.md") == "Error: no file ch/missing.md."


def test_lists_a_folder_without_the_reader_folders(small_vault: Path):
    ReaderStore(small_vault, "tester")
    assert read_vault_file(small_vault, "") == "ch/\noutline.md\npage.md"
    assert read_vault_file(small_vault, "ch") == (
        "agent.md\nalpha.md\nalpha.quiz.md\nbeta.md\nbeta.quiz.md\nchapter.md"
    )


def test_refuses_paths_outside_the_vault(small_vault: Path, tmp_path: Path):
    (tmp_path / "secret.txt").write_text("secret")
    (small_vault / "link.txt").symlink_to(tmp_path / "secret.txt")
    for path in ("../secret.txt", "ch/../../secret.txt", "link.txt"):
        assert read_vault_file(small_vault, path) == f"Error: {path} is not a file of the book.", path
    # An absolute path is read from the vault's root
    absolute = str(tmp_path / "secret.txt")
    assert read_vault_file(small_vault, absolute) == f"Error: no file {absolute}."


def test_refuses_the_reader_folders(small_vault: Path):
    store = ReaderStore(small_vault, "tester")
    store.add_about("Private.")
    for path in ("personalization_data", "personalization_data/tester/reader.md", "ch/../personalization_data"):
        assert read_vault_file(small_vault, path) == f"Error: {path} is not a file of the book.", path


def test_cuts_a_long_file(small_vault: Path):
    (small_vault / "long.md").write_text("x" * (_READ_LIMIT + 10))
    text = read_vault_file(small_vault, "long.md")
    assert text == "x" * _READ_LIMIT + f"\n\n[... cut at {_READ_LIMIT} characters]"
    (small_vault / "exact.md").write_text("x" * _READ_LIMIT)
    assert read_vault_file(small_vault, "exact.md") == "x" * _READ_LIMIT
