"""The note step: one model call turns an event into reader.md and notes.md, and decides on a rewrite."""

from conftest import FakeLLM
from quicklearn.agents.memory import NoteResult, note_step, parse_reply
from quicklearn.chapter.state import ChapterState
from quicklearn.reader.store import ReaderStore, get_part


def test_parse_reply():
    reply = (
        "Some thinking first.\n<about_reader>\n- Knows calculus.\n</about_reader>\n"
        "<notes>- Mixes up pmf and pdf.</notes>\n<rewrite>Yes, the goals changed.</rewrite>\n"
        "<reason>Wants worked examples.</reason>"
    )
    assert parse_reply(reply) == ("- Knows calculus.", "- Mixes up pmf and pdf.", True, "Wants worked examples.")
    assert parse_reply("<rewrite>no</rewrite>") == (None, None, False, "")
    assert parse_reply("No tags at all.") == (None, None, False, "")


def test_note_step_rewrites_both_parts(chapter: ChapterState, store: ReaderStore, fake_llm: FakeLLM):
    store.record_input("ch", "About you", "Tell us about yourself.", "A physicist.")
    store.add_about("An old fact.")
    fake_llm.replies["memory"] = (
        "<about_reader>- A physicist.</about_reader><notes>- Answered as a physicist.</notes>"
        "<rewrite>yes</rewrite><reason>New background.</reason>"
    )
    assert note_step(store, chapter, "  The reader answered.\n") == NoteResult(True, "New background.")

    assert store.about() == "- A physicist."
    notes = store.notes_md("ch")
    assert get_part(notes, "Notes") == "- Answered as a physicist."
    # The facts the app saved stay
    assert get_part(notes, "Inputs") == "## About you\n\n> Tell us about yourself.\n\nA physicist."
    [request] = fake_llm.requests("memory")
    assert "<reader>\n# About the reader\n\n- An old fact.\n</reader>" in request
    assert "<chapter>\nSmall Chapter\n\n- welcome: Welcome\n- alpha: Alpha (topics: first topic; second topic)\n" in (
        request
    )
    assert request.endswith("<event>\nThe reader answered.\n</event>")


def test_nothing_yet_empties_a_part(chapter: ChapterState, store: ReaderStore, fake_llm: FakeLLM):
    store.add_about("A fact.")
    store.add_note("ch", "A note.")
    fake_llm.replies["memory"] = "<about_reader>Nothing yet.</about_reader><notes>Nothing yet.</notes>"
    assert note_step(store, chapter, "Reset what you know.") == NoteResult(False, "")
    assert store.about() == "" and store.reader_md() == "# About the reader\n\nNothing yet.\n"
    assert get_part(store.notes_md("ch"), "Notes") == ""


def test_a_part_left_out_stays(chapter: ChapterState, store: ReaderStore, fake_llm: FakeLLM):
    store.add_about("A fact.")
    store.add_note("ch", "A note.")
    assert note_step(store, chapter, "Nothing happened.") == NoteResult(False, "Nothing new.")
    assert store.about() == "- A fact."
    assert get_part(store.notes_md("ch"), "Notes") == "- A note."
