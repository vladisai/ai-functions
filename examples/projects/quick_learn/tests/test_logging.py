"""Session logging: logs/<timestamp>/server.log, the latest link, and which loggers write there."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

import pytest
from quicklearn.logging_setup import setup_session_logging

LOGGERS = ("quicklearn", "ai_functions", "strands")


@pytest.fixture(autouse=True)
def restore_loggers():
    """Take off and close the handlers a test added, and put the levels back."""
    before = {name: (list(logging.getLogger(name).handlers), logging.getLogger(name).level) for name in LOGGERS}
    yield
    for name, (handlers, level) in before.items():
        logger = logging.getLogger(name)
        for handler in logger.handlers:
            if handler not in handlers:
                handler.close()
        logger.handlers, logger.level = handlers, level


def file_handlers(name: str) -> list[logging.FileHandler]:
    return [h for h in logging.getLogger(name).handlers if isinstance(h, logging.FileHandler)]


def flush() -> None:
    for name in LOGGERS:
        for handler in logging.getLogger(name).handlers:
            handler.flush()


def test_session_folder_holds_only_server_log(tmp_path: Path):
    root = tmp_path / "deep" / "logs"
    session_dir = setup_session_logging(logs_root=root)
    assert session_dir.parent == root
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}", session_dir.name)
    assert [p.name for p in session_dir.iterdir()] == ["server.log"]


def test_latest_points_at_the_session(tmp_path: Path):
    session_dir = setup_session_logging(logs_root=tmp_path)
    latest = tmp_path / "latest"
    # Relative, so the logs folder can move
    assert latest.is_symlink() and os.readlink(latest) == session_dir.name
    # A second run in the same second reuses the folder, and moves the link without an error
    again = setup_session_logging(logs_root=tmp_path)
    assert latest.resolve() == again.resolve()


def test_quicklearn_logs_debug_to_the_file_and_info_to_the_console(tmp_path: Path):
    session_dir = setup_session_logging(logs_root=tmp_path)
    logger = logging.getLogger("quicklearn")
    assert logger.level == logging.DEBUG
    file_handler = file_handlers("quicklearn")[-1]
    assert Path(file_handler.baseFilename) == session_dir / "server.log"
    assert file_handler.level == logging.DEBUG
    console = [h for h in logger.handlers if type(h) is logging.StreamHandler]
    assert console and console[-1].level == logging.INFO

    logging.getLogger("quicklearn.test").debug("A debug line")
    flush()
    text = (session_dir / "server.log").read_text()
    assert "Session logging started" in text and "quicklearn.test DEBUG A debug line" in text


def test_the_chat_libraries_log_info_to_the_same_file(tmp_path: Path):
    session_dir = setup_session_logging(logs_root=tmp_path)
    for name in ("ai_functions", "strands"):
        assert logging.getLogger(name).level == logging.INFO
        assert Path(file_handlers(name)[-1].baseFilename) == session_dir / "server.log"
    logging.getLogger("strands.agent").info("A strands line")
    logging.getLogger("strands.agent").debug("Not this one")
    flush()
    text = (session_dir / "server.log").read_text()
    assert "A strands line" in text and "Not this one" not in text
