"""The reader folder: its layout, reader.md and notes.md, JSON files, demo readers and reset."""

import json
import os
from pathlib import Path

from quicklearn.chapter.state import ChapterState
from quicklearn.reader.store import ReaderStore, get_part, set_part

REPO = Path(__file__).parent.parent


def test_layout(small_vault: Path):
    store = ReaderStore(small_vault, "ada")
    assert store.dir == small_vault / "personalization_data" / "ada"
    assert store.reader_md() == "# About the reader\n\nNothing yet.\n"
    assert store.about() == ""
    assert store.chapter_dir("book/ch") == store.dir / "book" / "ch" and store.chapter_dir("book/ch").is_dir()
    assert store.notes_path("book/ch") == store.dir / "book" / "ch" / "notes.md"
    assert store.answers_path("book/ch") == store.dir / "book" / "ch" / "answers.json"
    assert store.chat_path == store.dir / "chat.json"


def test_about(store: ReaderStore):
    store.add_about("Knows   calculus.\n")
    store.add_about("Prefers short derivations.")
    assert store.about() == "- Knows calculus.\n- Prefers short derivations."
    assert store.reader_md() == "# About the reader\n\n- Knows calculus.\n- Prefers short derivations.\n"
    store.set_about("")
    assert store.reader_md() == "# About the reader\n\nNothing yet.\n" and store.about() == ""


def test_notes(store: ReaderStore):
    assert store.notes_md("ch") == "# Inputs\n\n# Quiz results\n\n# Notes\n"
    assert not store.notes_path("ch").exists()
    store.add_note("ch", "Mixes up pmf and pdf.")
    store.add_note("ch", "Asked for more examples.")
    assert store.notes_md("ch") == (
        "# Inputs\n\n# Quiz results\n\n# Notes\n\n- Mixes up pmf and pdf.\n- Asked for more examples.\n"
    )
    assert store.notes_md("other") == "# Inputs\n\n# Quiz results\n\n# Notes\n"


def test_record_input_replaces_an_earlier_answer(store: ReaderStore):
    store.record_input("ch", "About you", "Tell us.\nAnything.", "A physicist.")
    store.record_input("ch", "Goals", "", "Learn RL.")
    store.record_input("ch", "About you", "Tell us.\nAnything.", "A chemist.")
    inputs = get_part(store.notes_md("ch"), "Inputs")
    assert inputs == "## About you\n\n> Tell us.\n> Anything.\n\nA chemist.\n\n## Goals\n\nLearn RL."


def test_record_quiz_keeps_every_attempt(store: ReaderStore):
    store.record_quiz("ch", "Alpha, prior knowledge", "1 of 2 right.")
    store.record_quiz("ch", "Alpha, prior knowledge", "2 of 2 right.")
    results = get_part(store.notes_md("ch"), "Quiz results")
    assert results.count("## Alpha, prior knowledge (") == 2
    assert results.index("1 of 2 right.") < results.index("2 of 2 right.")
    # The other parts stay where they were
    assert store.notes_md("ch").startswith("# Inputs\n\n# Quiz results\n\n## Alpha")


def test_parts():
    text = "# A\n\none\n\n## Sub\n\nstill A\n\n# B\n\ntwo\n"
    assert get_part(text, "A") == "one\n\n## Sub\n\nstill A"
    assert get_part(text, "Missing") == ""
    assert set_part(text, "A", "new") == "# A\n\nnew\n\n# B\n\ntwo\n"
    assert set_part(text, "B", "") == "# A\n\none\n\n## Sub\n\nstill A\n\n# B\n"
    assert set_part(text, "C", "three") == text + "\n# C\n\nthree\n"
    assert set_part("", "C", "three") == "# C\n\nthree\n"


def test_json(store: ReaderStore):
    path = store.dir / "data.json"
    assert store.load_json(path, {"empty": True}) == {"empty": True}
    store.save_json(path, {"text": "π ≈ 3.14", "list": [1, 2]})
    assert store.load_json(path, None) == {"text": "π ≈ 3.14", "list": [1, 2]}
    assert "π" in path.read_text()
    assert not path.with_suffix(".json.tmp").exists()


def test_wipe_empties_the_folder(store: ReaderStore):
    store.add_about("Knows calculus.")
    store.add_note("ch", "A note.")
    store.wipe()
    assert sorted(p.name for p in store.dir.iterdir()) == ["reader.md"]
    assert store.about() == ""


def demo_readers(root: Path) -> Path:
    """A demo reader with a rewrite in v_1 and a current symlink."""
    chapter_dir = root / "pat" / "ch"
    (chapter_dir / "v_0").mkdir(parents=True)
    (chapter_dir / "v_1").mkdir()
    (chapter_dir / "v_1" / "alpha.md").write_text("Alpha for Pat.\n")
    (chapter_dir / "current").symlink_to("v_1")
    (root / "pat" / "reader.md").write_text("# About the reader\n\n- Pat.\n")
    return root


def test_a_demo_reader_starts_as_its_copy_and_resets_to_it(small_vault: Path, tmp_path: Path):
    demos = demo_readers(tmp_path / "demo_readers")
    store = ReaderStore(small_vault, "pat", demos)
    assert store.about() == "- Pat."
    current = store.dir / "ch" / "current"
    assert current.is_symlink() and os.readlink(current) == "v_1"
    chapter = ChapterState(small_vault / "ch" / "chapter.md", small_vault, store)
    assert chapter.material.get_section("alpha").content == "Alpha for Pat.\n"

    store.add_about("Learned something.")
    (store.dir / "ch" / "v_1" / "alpha.md").write_text("Changed.\n")
    # An existing folder is not copied over again
    assert ReaderStore(small_vault, "pat", demos).about() == "- Pat.\n- Learned something."
    store.wipe()
    assert store.about() == "- Pat."
    assert (store.dir / "ch" / "v_1" / "alpha.md").read_text() == "Alpha for Pat.\n"
    assert (demos / "pat" / "ch" / "v_1" / "alpha.md").read_text() == "Alpha for Pat.\n"


def test_a_reader_without_a_demo_starts_empty(small_vault: Path, tmp_path: Path):
    demos = demo_readers(tmp_path / "demo_readers")
    assert ReaderStore(small_vault, "sam", demos).demo is None
    assert ReaderStore(small_vault, "pat", None).about() == ""


def test_shipped_demo_readers_load_with_their_answers(shipped_vault: Path):
    for reader in ("physics-undergrad", "statistics-professor"):
        store = ReaderStore(shipped_vault, reader, REPO / "demo_readers")
        chapter = ChapterState(shipped_vault / "book" / "probability" / "chapter.md", shipped_vault, store)
        assert store.about(), reader
        assert chapter.text_inputs["tell-us-about-yourself"].answer, reader
        # The saved answers match the vault's quizzes, or they would not come back
        assert chapter.quizzes["random-variables.prior"].answers, reader
        # Inline sections came in around the embedded ones, which keep their names and versions
        assert {"random-variables", "expectation", "information-theory"} <= set(chapter.section_names), reader
        embedded = ("random-variables", "expectation", "information-theory")
        assert not any(chapter.doc.sections[n].inline for n in embedded), reader
        saved = json.loads(store.answers_path(chapter.key).read_text())
        assert saved["quizzes"] and all(chapter.quizzes[q].answers for q in saved["quizzes"]), reader
        assert all(chapter.text_inputs[t].answer for t in saved["text_inputs"]), reader
        # Every earlier version on disk is in the version bar
        assert len(chapter.material.version_stack) == int(chapter.version_dir.name.removeprefix("v_")) >= 1
