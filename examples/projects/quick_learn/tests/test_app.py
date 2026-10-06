"""The web app's routes: the outline's pages, the redirect from /, 404s, /debug/material and reset.

quicklearn.app reads the vault from the environment and starts session logging when it is
imported, so it is imported once, against a small vault, with the logs in a temporary folder.
"""

import importlib
import logging
import sys
from pathlib import Path

import pytest
from conftest import SMALL_VAULT, write
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient
from quicklearn import logging_setup
from quicklearn.vault.chapter import page_key


@pytest.fixture(scope="module")
def app_module(tmp_path_factory: pytest.TempPathFactory):
    assert "quicklearn.app" not in sys.modules, "quicklearn.app reads the environment only on its first import"
    root = tmp_path_factory.mktemp("app")
    vault = write(root / "vault", SMALL_VAULT)
    loggers = [logging.getLogger(name) for name in ("quicklearn", "ai_functions", "strands")]
    before = [(list(logger.handlers), logger.level) for logger in loggers]
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(logging_setup, "LOGS_ROOT", root / "logs")
        mp.setenv("QUICKLEARN_CONTENT", str(vault))
        module = importlib.import_module("quicklearn.app")
    # Take the session's handlers off again, so the other tests log nowhere
    for logger, (handlers, level) in zip(loggers, before, strict=True):
        for handler in logger.handlers:
            if handler not in handlers:
                handler.close()
        logger.handlers, logger.level = handlers, level
    yield module


@pytest.fixture
def app(app_module, small_vault: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The app on a fresh vault, as reader "tester", with no Book yet."""
    monkeypatch.setattr(app_module, "VAULT", small_vault)
    monkeypatch.setattr(app_module, "DEMO_READERS", tmp_path / "no_demo_readers")
    monkeypatch.setattr(app_module, "BOOK", None)
    monkeypatch.setenv("QUICKLEARN_READER", "tester")
    yield app_module
    if app_module.BOOK is not None:
        app_module.BOOK.stop()


def test_import_reads_the_vault_from_the_environment(app_module):
    assert app_module.VAULT.name == "vault" and (app_module.VAULT / "outline.md").is_file()
    assert app_module.SESSION_LOG_DIR.parent.name == "logs"
    assert (app_module.SESSION_LOG_DIR / "server.log").is_file()


def test_the_book_is_for_the_reader_in_the_environment(app, small_vault: Path):
    assert app.running_tasks() == 0
    book = app.get_book()
    assert app.get_book() is book is app.BOOK
    assert book.store.dir == small_vault / "personalization_data" / "tester"


def test_page_key():
    assert page_key("book/probability/chapter") == "book/probability"
    assert page_key("ch/chapter.md") == "ch"
    assert page_key("lectures/lecture_1") == "lectures/lecture_1"
    assert page_key("page.md") == "page"


def test_routes_of_the_outline(app):
    book = app.get_book()
    pages = book.pages()
    assert list(pages) == ["/ch", "/page"]
    assert [e.is_chapter for e in pages.values()] == [True, False]
    assert [book.resolve_link(t) for t in ("ch", "ch/chapter", "page", "nowhere")] == ["/ch", "/ch", "/page", None]


def test_index_redirects_to_the_first_chapter(app, small_vault: Path):
    response = app.index_page()
    assert isinstance(response, RedirectResponse) and response.headers["location"] == "/ch"

    (small_vault / "outline.md").write_text("- [[page|A Page]]\n- [[ch/chapter|Small Chapter]]\n")
    assert app.index_page().headers["location"] == "/ch"
    (small_vault / "outline.md").write_text("- [[page|A Page]]\n")
    assert app.index_page().headers["location"] == "/page"
    (small_vault / "outline.md").write_text("- Not written yet\n")
    with pytest.raises(HTTPException) as error:
        app.index_page()
    assert error.value.status_code == 404


def test_unknown_routes_and_missing_pages_are_404(app, small_vault: Path):
    (small_vault / "outline.md").write_text("- [[ch/chapter|Small Chapter]]\n- [[gone|Gone]]\n")
    for path, detail in (("nope", "No page at /nope"), ("gone/", "gone.md is not in the vault")):
        with pytest.raises(HTTPException) as error:
            app.outline_page(path)
        assert (error.value.status_code, error.value.detail) == (404, detail)


def test_debug_material(app):
    assert app.debug_material() == {"error": "not initialized"}
    app.get_book()
    material = app.debug_material()
    assert app.debug_material("ch") == material
    assert (material["chapter"], material["version"], material["stale"], material["running"]) == ("ch", "v_0", [], 0)
    assert [s["id"] for s in material["sections"]] == [
        "fixed-1", "chapter.prior", "welcome.prior", "welcome", "welcome.learned", "about-you", "alpha.prior", "alpha",
        "alpha.learned", "beta.prior", "beta", "beta.learned", "symbols.prior", "symbols", "symbols.learned",
        "chapter.learned",
    ]
    assert material["sections"][7] == {
        "id": "alpha", "title": "Alpha", "level": 1, "content_len": 600, "start": "alpha " * 13 + "al",
    }
    assert material["quizzes"]["alpha.prior"] == {"n": 1, "state": "active", "answers": 0}
    assert material["quizzes"]["alpha.learned"]["n"] == 0
    assert material["text_inputs"] == {"about-you": {"state": "active", "answer": ""}}


def test_debug_material_over_http(app):
    app.get_book()
    response = TestClient(app.app).get("/debug/material", params={"chapter": "ch"})
    assert response.status_code == 200
    assert response.json()["chapter"] == "ch" and len(response.json()["sections"]) == 16


def test_reset_empties_the_reader_folder(app):
    book = app.get_book()
    book.store.add_about("Knows calculus.")
    book.chapter("ch").new_version()
    app.reset()
    assert app.BOOK is None
    assert sorted(p.name for p in book.store.dir.iterdir()) == ["reader.md"]
    assert app.get_book() is not book and app.BOOK.store.about() == ""
