"""Logging for one run of the app, in logs/<timestamp>/server.log, with logs/latest pointing at it.

The quicklearn loggers write DEBUG to the file and INFO to the console. The chat agent's libraries,
ai_functions and strands, write INFO to the file.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

LOGS_ROOT = Path(__file__).parent.parent / "logs"


def setup_session_logging(logs_root: Path | None = None) -> Path:
    """Create logs/<timestamp>/ and send the quicklearn loggers there. Returns the folder."""
    root = logs_root or LOGS_ROOT
    root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_dir = root / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)

    latest = root / "latest"
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(timestamp)

    fmt = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(session_dir / "server.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    ql_logger = logging.getLogger("quicklearn")
    ql_logger.setLevel(logging.DEBUG)
    ql_logger.addHandler(file_handler)
    ql_logger.addHandler(console_handler)

    for name in ("ai_functions", "strands"):
        lib_logger = logging.getLogger(name)
        lib_logger.setLevel(logging.INFO)
        lib_logger.addHandler(file_handler)

    ql_logger.info("Session logging started: %s", session_dir)
    return session_dir
