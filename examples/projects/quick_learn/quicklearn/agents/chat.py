"""The chat agent: one AI Functions thread per reader, the tutor.

The tutor is an `@ai_function` with tools for reading the book, rewriting a section, adding a quiz
to one, remembering something about the reader and searching. Every section of every page, embedded
or inline, can be rewritten and get a quiz: `rewrite_section` and `add_quiz` start an adapter task
in the background and return at once. It runs on an `InMemoryCoordinator` hosted on an event
loop of its own, in a background thread, so the app calls it like a function from any thread, as
it did with threads-agent's server.

The tutor's event log holds the whole conversation with its tool calls. It is saved after each
message with `FileSessionStore` and passed back as `seed_events` at start, so the tutor
remembers the conversation after a restart:

    personalization_data/<reader>/
      chat.json                         the chat as the panel shows it, and pending events
      chat_session/session.json         the tutor's thread id
      chat_session/tutor.events.json    its event log

The system prompt is built for every message from the page the reader is on, a chapter folder or a
one-file page, through the thread's `config_hook`: prompts/agent.md, the page's agent.md and
sections, reader.md and the page's notes.md. Reader actions outside chat, like quiz submits, reach the tutor through
`notify`, and it sees them with the next message. They also stay in chat.json until then, so a
restart in between does not lose them.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import TYPE_CHECKING

from strands import tool

from ai_functions import FileSessionStore, ai_function
from ai_functions.runtime import InMemoryCoordinator, LocalWorker
from quicklearn import llm
from quicklearn.agents import search_tools
from quicklearn.agents.adapter import QUIZ_PARTS, Adapter, Task, load_prompt, reader_context
from quicklearn.reader.store import PERSONAL_DIR

if TYPE_CHECKING:
    from ai_functions.handle import ThreadHandle
    from quicklearn.chapter.state import ChapterState
    from quicklearn.reader.store import ReaderStore

log = logging.getLogger(__name__)

THREAD = "tutor"  # the thread's name, and its key in the saved session
SESSION_DIR = "chat_session"
_READ_LIMIT = 60_000


@ai_function(structured_output=False, coordinator_tools_enabled=False, callback_handler=None)
def tutor(message: str) -> str:
    """{message}"""


class ChatAgent:
    def __init__(self, store: ReaderStore, adapter: Adapter) -> None:
        self.store = store
        self.adapter = adapter
        data = store.load_json(store.chat_path, {"display": [], "events": []})
        self.display: list[dict[str, str]] = data["display"]
        self._events: list[str] = data.get("events", [])
        self._sessions = FileSessionStore(store.dir)
        # One answer at a time; a second message waits for the first.
        self._lock = threading.Lock()
        self.busy = 0
        # The chapter of the message being answered, for the system prompt and the tools
        self._chapter: ChapterState | None = None
        # Called with (chapter, exchange) after each answer, for the note step
        self.on_exchange: Callable[[ChapterState, str], None] | None = None

        self._closed = False
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, name="ql-chat", daemon=True)
        self._thread.start()
        self._handle: ThreadHandle = self._call(self._spawn())

    def _call[T](self, coro: Coroutine[object, object, T]) -> T:
        """Run a coroutine on the tutor's loop and wait for it."""
        if self._closed:
            coro.close()
            raise RuntimeError("The chat is closed")
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    async def _spawn(self) -> ThreadHandle:
        """Start the tutor, from its saved event log if there is one."""
        self._coordinator = InMemoryCoordinator()
        self._worker = LocalWorker(self._coordinator)
        await self._worker.register()
        template = tutor.replace(model=llm.chat_model(), tools=self._tools(), config_hook=self._config_hook)
        seed, thread_id = None, None
        if self._sessions.exists(SESSION_DIR):
            data = self._sessions.load(SESSION_DIR)
            seed, thread_id = data.threads.get(THREAD), data.thread_ids.get(THREAD)
            log.info("Chat resumed with %d events", len(seed or []))
        handle = await self._coordinator.spawn(template, thread_name=THREAD, thread_id=thread_id, seed_events=seed)
        for event in self._events:
            await handle.notify(event)
        return handle

    def close(self) -> None:
        """Stop the tutor and its loop. A message being answered fails with CancelledError."""
        if self._closed:
            return
        self._closed = True  # before the cancel, so an answer that ends with it does not save
        asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop).result()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        self._loop.close()

    async def _shutdown(self) -> None:
        await self._worker.close()
        others = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        for task in others:
            task.cancel()
        await asyncio.gather(*others, return_exceptions=True)

    def _save(self) -> None:
        self.store.save_json(self.store.chat_path, {"display": self.display, "events": self._events})

    # -- Events and feedback from outside chat --

    def note_event(self, text: str) -> None:
        """Something the reader did outside chat, e.g. a quiz submit. The tutor sees it with the next message."""
        with self.store.lock:
            self._events.append(text)
            self._save()
        self._call(self._handle.notify(text))

    def add_assistant_message(self, text: str) -> None:
        """A message shown in the chat that the tutor did not write, like quiz feedback."""
        with self.store.lock:
            self.display.append({"role": "assistant", "content": text})
            self._save()

    # -- Answering --

    def system_prompt(self, chapter: ChapterState) -> str:
        sections = "\n".join(
            f"- {name}: {chapter.doc.sections[name].title}" for name in chapter.section_names
        )
        stem = chapter.doc.stem
        page_quiz = ""
        if chapter.doc.is_page(stem):
            page_quiz = f"The page's own quiz, on all its sections, is `{stem}` for add_quiz.\n\n"
        return (
            f"{load_prompt('agent').strip()}\n\n"
            f"# The chapter: {chapter.title}\n\nIts file is `{chapter.doc.page.relative_to(chapter.vault)}`.\n\n"
            f"{chapter.doc.agent_notes.strip()}\n\n"
            f"## Sections\n\n{sections}\n\n{page_quiz}"
            f"{reader_context(self.store, chapter)}"
        )

    def _config_hook(self, ctx) -> dict:
        """The system prompt for this message, from the chapter the reader is on."""
        assert self._chapter is not None, "a cycle runs only from handle()"
        return {"system_prompt": self.system_prompt(self._chapter)}

    def handle(self, message: str, chapter: ChapterState) -> str:
        """Answer a chat message. Blocks until the tutor is done, so call it off the UI loop."""
        self.busy += 1
        try:
            with self._lock:
                reply = self._answer(message, chapter)
        finally:
            self.busy -= 1
        if self.on_exchange is not None:
            self.on_exchange(chapter, f"A chat exchange.\n\nThe reader wrote: {message}\n\nThe tutor answered: {reply}")
        return reply

    def _answer(self, message: str, chapter: ChapterState) -> str:
        log.info("Chat message on %s: %s", chapter.key, message[:100])
        self._chapter = chapter
        with self.store.lock:
            self.display.append({"role": "user", "content": message})
            # The events notified so far reach the tutor in this cycle; later ones wait for the next
            seen = len(self._events)
            self._save()
        try:
            reply = (self._call(self._run(message)) or "").strip()
        finally:
            if not self._closed:
                self._call(self._save_session())
        with self.store.lock:
            del self._events[:seen]
            self.display.append({"role": "assistant", "content": reply})
            self._save()
        return reply

    async def _run(self, message: str) -> str:
        return await self._handle.run(message=message)

    async def _save_session(self) -> None:
        events = await self._coordinator.get_events(self._handle.id)
        self._sessions.save(SESSION_DIR, {THREAD: events}, {THREAD: self._handle.id})

    # -- Tools --

    def _tools(self) -> list:
        """The tutor's tools. They act on the chapter of the message being answered."""

        def chapter() -> ChapterState:
            assert self._chapter is not None
            return self._chapter

        def unknown(name: str) -> str:
            return f"Error: no section {name!r}. Sections: {', '.join(chapter().section_names)}"

        @tool
        def read_section(name: str) -> str:
            """The text of one section of this chapter, as the reader sees it now.

            Args:
                name: Section name, e.g. random-variables
            """
            if name not in chapter().doc.sections:
                return unknown(name)
            return chapter().section_text(name)

        @tool
        def read_file(path: str) -> str:
            """Read a file of the book by its path in the content folder, e.g. book/probability/reference.md.
            A folder gives the list of its files.

            Args:
                path: The file's path in the content folder
            """
            return read_vault_file(self.store.vault, path)

        @tool
        def rewrite_section(name: str, request: str, new_quiz: bool = False) -> str:
            """Rewrite one section of this chapter in the background. The page shows the new text
            within seconds. Returns at once. Use it for every change to the text the reader asks for.

            Args:
                name: Section name, e.g. expectation
                request: What to change and why, in enough detail for a writer who sees only this
                    request, the section and the notes about the reader.
                new_quiz: Also write a fresh quiz after the section.
            """
            if name not in chapter().doc.sections:
                return unknown(name)
            task = Task(name, f"The reader asked in chat: {request}", quiz="learned" if new_quiz else "")
            self.adapter.start(chapter(), [task])
            return f"Rewriting {name} now. The page updates as the text is written."

        @tool
        def add_quiz(name: str, request: str, part: str = "learned") -> str:
            """Write a quiz for one section of this chapter, or for the whole page, in the background,
            without changing the text. It replaces that quiz part. Returns at once, and the quiz
            appears on the page when it is written.

            Args:
                name: Section name, e.g. expectation, or the page's name, e.g. lecture_2, for the
                    page's own quiz on all its sections: its prior is the background check after the
                    title, its learned quiz comes at the end of the page.
                request: What the quiz should check and why, in enough detail for a writer who sees
                    only this request, the section and the notes about the reader.
                part: "prior" for a quiz before the section, on what the reader knows already, or
                    "learned" for one after it, on what they understood.
            """
            page = chapter().doc.is_page(name)
            if name not in chapter().doc.sections and not page:
                return unknown(name)
            if part not in QUIZ_PARTS:
                return f"Error: part is one of {', '.join(QUIZ_PARTS)}, not {part!r}."
            covers = chapter().section_names if page else []
            task = Task(name, f"The reader asked in chat: {request}", quiz=part, rewrite=False, covers=covers)
            self.adapter.start(chapter(), [task])
            if page:
                where = "after the title" if part == "prior" else "at the end of the page"
            else:
                where = "before the section" if part == "prior" else "after the section"
            return f"Writing a {part} quiz for {name} now. It appears {where} when it is ready."

        @tool
        def remember(note: str, scope: str) -> str:
            """Keep something learned about the reader in conversation.

            Args:
                note: One short sentence, e.g. "Knows measure theory."
                scope: "reader" for what is true of them everywhere, "chapter" for what they know
                    or miss in this chapter.
            """
            if scope == "chapter":
                self.store.add_note(chapter().key, note)
            else:
                self.store.add_about(note)
            return "Noted."

        tools = [read_section, read_file, rewrite_section, add_quiz, remember, tool(search_tools.search_arxiv)]
        if search_tools.web_search_enabled():
            tools.append(tool(search_tools.web_search))
        return tools


def read_vault_file(vault: Path, path: str) -> str:
    """A file of the vault, but not the reader folders."""
    target = (vault / path.strip().lstrip("/")).resolve()
    if not target.is_relative_to(vault.resolve()) or target.is_relative_to((vault / PERSONAL_DIR).resolve()):
        return f"Error: {path} is not a file of the book."
    if target.is_dir():
        names = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir() if p.name != PERSONAL_DIR)
        return "\n".join(names)
    if not target.is_file():
        return f"Error: no file {path}."
    text = target.read_text(errors="replace")
    if len(text) > _READ_LIMIT:
        text = text[:_READ_LIMIT] + f"\n\n[... cut at {_READ_LIMIT} characters]"
    return text
