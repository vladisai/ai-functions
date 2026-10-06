"""A question the chapter asks the reader in a text box, from `_TEXT_INPUT_: Title` in chapter.md."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TextInputState(Enum):
    ACTIVE = "active"  # the box is open for an answer
    DONE = "done"  # answered; the reader can still edit and resubmit
    SKIPPED = "skipped"


@dataclass
class TextInput:
    id: str  # a slug of the title, e.g. "tell-us-about-yourself"
    title: str
    prompt: str = ""
    answer: str = ""
    state: TextInputState = TextInputState.ACTIVE
