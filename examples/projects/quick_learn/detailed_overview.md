# QuickLearn in detail

This document is for students who want to understand QuickLearn well enough to change it. The
[README](README.md) explains how to install and use the app. The terse reference for developers is
[docs/project_overview.md](docs/project_overview.md). This document goes through the ideas behind
the code, one reader action from the click to the files on disk, the tutor agent and the content
format. It ends with recipes for common changes.

Paths are relative to this folder, `examples/projects/quick_learn/`. A "reader" is a person who
reads the book in the app. "You" are the person who changes the code.

## 1. The big picture

QuickLearn is an adaptive book. The author writes it as an Obsidian vault of markdown files. The
app shows the book in the browser and rewrites its sections for each reader as they answer
quizzes, tell the book about themselves and chat with a tutor.

### Three kinds of model calls

Everything the model does falls into one of three kinds of calls, each with its own module.

| Call | Code | Model settings | What it gets | What it returns | When it runs |
|---|---|---|---|---|---|
| The tutor | `agents/chat.py`, `ChatAgent`, an AI Functions thread with tools | `QL_CHAT_MODEL` and `QL_CHAT_EFFORT`, medium effort by default | the reader's message, the conversation so far, events from outside the chat, and a system prompt built for the page | a reply, and tool calls that read the book, rewrite sections or add quizzes | on every chat message |
| Rewrites, quizzes and feedback | `agents/adapter.py`, `Adapter`, through `llm.stream_text` and `llm.complete` | `QL_FAST_MODEL` and `QL_FAST_EFFORT`, low effort by default | what the book knows about the reader, the chapter's guide, the reason for the rewrite and the current text | a new section streamed into its file, a quiz in markdown, or a short feedback paragraph | after a quiz or text input, when the tutor asks for it, on "Personalize again", and on a first visit to a page with empty sections |
| The note step | `agents/memory.py`, `note_step` | the fast settings | reader.md, the chapter's notes.md, the chapter's sections and the event | tagged text with the new "About the reader" and "Notes" parts, and whether to rewrite | after every text input, quiz submit and chat exchange |

The tutor is the only agent in the sense of a model that runs in a loop and decides which tools
to call. The other two kinds are single calls with a fixed request and a fixed shape of answer.

### Why the rewrites are rules plus one call

When a reader submits a quiz, the app has to decide what to rewrite and then write it. The
decision follows a few simple rules. A prior quiz with gaps means that the section should be
rewritten around what the reader missed. A perfect prior quiz means that the section can be
condensed. `Adapter.plan_for_quiz` makes this decision in a few lines of Python. Only the writing
goes to the model, as one streamed call per section.

An agent could make the same decision. However, it would cost a model turn before anything
happens, might decide differently each time, and could not be tested without a model. With the
rules in Python, the first change to the page shows about two seconds after a submit. The behavior
is also the same for every reader. `tests/test_adapter.py` checks every rule in milliseconds.

The model does the part that needs judgment, which is writing text for one person. Since the chat
is open-ended, the tutor is an agent. When the tutor wants a section rewritten, it calls
`rewrite_section`, which hands the work to the same adapter.

### Files are the source of truth

The app keeps no state that is not on disk. The vault holds what the author wrote. The app never
writes into it. Everything the app knows about one reader is in their reader folder:

```
content/                                   the vault, written by the author
  outline.md, lectures/, book/ ...
  personalization_data/<reader>/           the reader folder, written by the app
    reader.md                              what is true of the reader everywhere
    chat.json                              the chat as shown, and events the tutor has not seen
    chat_session/                          the tutor's event log, saved by FileSessionStore
    book/probability/                      one folder per page
      notes.md                             "# Inputs", "# Quiz results", "# Notes"
      answers.json                         quiz and text input answers
      v_0/ v_1/ ... current -> v_3         versions: only the rewritten sections and quizzes
```

The objects in memory, such as `ChapterState`, `Material` and `Quiz`, are built from these files
when a page is first opened. The browser follows the files too. Every open page polls the files of
its sections every two seconds and updates a block when its file changed.

This design has a few useful consequences. A restart brings everything back, including what the
tutor remembers. You can open the reader folder to see exactly what the book knows about a reader,
or edit reader.md by hand. A demo reader is just a copied folder. A test can build a book in a
temporary folder and look at the files it wrote.

A version folder holds only what was rewritten. When the app looks for a section, it takes
`v_N/<name>.md` if that file exists and the vault file otherwise. As a result, a `git pull` of the
content updates every section that the reader has not had rewritten.

### How the parts connect

```
 browser tab (NiceGUI page)             browser tab ...
    | clicks, chat messages                ^ every 2 s: poll the files, update changed blocks
    v                                      |
 app.py  chapter_page ------------------> ChapterState.live   (chapter/live.py)
    |                                      ^
    v                                      | reads
 Book  (book.py): one per reader           |
    |-- Adapter     (agents/adapter.py) ---+--> streams v_N/<name>.md, v_N/<name>.quiz.md
    |-- ChatAgent   (agents/chat.py)       |      ^
    |      AI Functions thread, own loop   |      | rewrite_section, add_quiz
    |      tools --------------------------+------+
    |-- note step   (agents/memory.py) ----+--> reader.md, notes.md
    '-- ReaderStore (reader/store.py) -----+--> answers.json, notes.md, chat.json
                                           |
 content/ the vault: outline.md, pages, sections, quizzes, agent.md   (read only)
```

Every reader action goes through `Book`. The order of the steps for each action is therefore in
`book.py`. `app.py` holds one `Book` for the reader named by `QUICKLEARN_READER`. Reset replaces it
with a new one.

## 2. What to learn first

You do not need all of these concepts to make a change. The rows that match the part you want to
touch are enough.

| Concept | Where it shows up | What to read |
|---|---|---|
| AI Functions: `@ai_function`, `.replace`, threads, the coordinator, `notify` | `agents/chat.py` | the sections "Stateful AI Threads" and "A Team of AI Threads" of the repo's top-level README, and the sections "Configuration", "AI Threads: adding state" and "Injecting messages" of `docs/tutorial.md` at the repo root |
| strands tools | `ChatAgent._tools` in `agents/chat.py`, `agents/search_tools.py` | the strands documentation on Python tools, which explains `@tool` and how the docstring's `Args:` become the descriptions of the tool's parameters |
| asyncio and threads | the tutor's loop in `ChatAgent.__init__`, the pools in `Adapter` and `Book`, `run.io_bound` in `app.py` and `ui/chat_widget.py` | the Python documentation of `asyncio.run_coroutine_threadsafe`, event loops and `concurrent.futures.ThreadPoolExecutor` |
| NiceGUI | `app.py` and `ui/` | the NiceGUI documentation of `ui.page`, of building elements inside `with` blocks, of `.classes` and `.props`, and of `ui.timer`, `ui.refreshable` and `run.io_bound` |
| The Anthropic SDK and streaming | `llm.py` | the SDK's documentation of `messages.stream` |
| Obsidian markdown | `content/` and `vault/` | Obsidian's help on internal links, embedded files and properties |
| Prompts | `agents/prompts/*.md`, and the code that builds each request in `adapter.py` and `memory.py` | each prompt next to the function that sends it, since the request supplies the tags the prompt talks about |
| pytest fixtures and `monkeypatch` | `tests/conftest.py` | the pytest documentation of fixtures and monkeypatching |

## 3. One reader action, end to end: a quiz submit

As an example, a reader opens Probability, takes the prior quiz before Random Variables and gets
two of four questions wrong. The steps below run in this order.

**In the browser.** `render_quiz` in `ui/quiz_renderer.py` draws the quiz. The Submit button calls
`handle_submit` inside `_render_active_quiz`. That function copies the answers into the `Quiz`
with `_compile_answers`, marks the quiz completed with `quiz.complete()` and awaits the `on_submit`
callback it was given.

**On the server, at once.** That callback is `on_quiz_submit` in `app.py:chapter_page`. It calls
`Book.submit_quiz(chapter, quiz)`, which does four quick things:

1. `Adapter.plan_for_quiz` splits the quiz id `random-variables.prior` into the section name and
   the part. Since `has_gaps` finds wrong answers, it returns a `Plan` with a sentence for the
   feedback, "The section below is being rewritten around what you missed...", and one
   `Task("random-variables", reason, quiz="learned")`. The reason lists every question with the
   reader's answer and the right one, as `format_answers` writes them.
2. `Adapter.start` sees no other task writing into this page and calls `ChapterState.new_version`.
   That method snapshots the in-memory `Material` for the version bar, copies the current version
   folder, say `v_2`, to `v_3`, points the `current` link at the copy and strips the old change
   notes. `Adapter.start` then submits `Adapter._run` for the task to its thread pool.
3. `ChapterState.save_answers` writes answers.json. The file also holds a fingerprint of the
   questions, which keeps old answers from being restored onto new questions.
4. `ReaderStore.record_quiz` appends a line like "2 of 4 right. Missed: ..." under
   "# Quiz results" in notes.md. `Book._note_later` then queues the note step on the notes pool.

**On the server, the feedback.** `on_quiz_submit` then runs `Book.quiz_feedback` through
`run.io_bound`, which keeps the NiceGUI loop free while it waits. `Adapter.feedback` makes one
`llm.complete` call with `prompts/feedback.md`, which takes 2 to 3 seconds. The feedback goes into
the chat through `ChatAgent.add_assistant_message`. The tutor learns about the quiz through
`ChatAgent.note_event`, which saves the event in chat.json and calls `handle.notify`. Finally the
callback returns the feedback. The quiz card then shows the score, the feedback and "Rewriting the
section for you".

**In the adapter's thread.** `Adapter._run` first takes the lock of this section, which makes two
tasks for the same section run one after the other. `Adapter._rewrite` builds the request from six
parts: `reader_context` with reader.md and notes.md, the chapter's agent.md as `<chapter_guide>`,
the reason, the section's title and heading level, its topics, and its current text. It streams
the reply from `llm.stream_text` with `prompts/rewrite.md`. About once a second it writes the text
so far into `v_3/random-variables.md` with `write_atomic`, cut at the last paragraph break and
followed by "*Rewriting this section for you…*". At the end it writes the whole text and calls
`ChapterState.record_source`, which stores a hash of the vault text in `v_3/sources.json` for
"Personalize again". Since the task asks for a learned quiz, `Adapter._write_quiz` then makes one
call with `prompts/learned_quiz.md`. It parses the reply with `parse_quiz` and writes
`v_3/random-variables.quiz.md`, keeping the prior part that the file may already have.

**In the notes pool.** `memory.note_step` sends the event, reader.md and notes.md to the model with
`prompts/memory.md`. It reads the tags of the reply with `parse_reply` and rewrites the "About the
reader" part of reader.md and the "Notes" part of notes.md.

**Back in the browser.** Every page runs `poll` in `app.py` every two seconds through `ui.timer`.
`poll` calls `LiveMaterial.poll_all`, which asks each block whether its file changed.
`ContentLive.poll` sees the new modification time of `v_3/random-variables.md`, reads the text and
calls the callbacks of every open page. `SectionUI.on_live_change` in `ui/page_ui.py` then updates
the markdown element in place, or rebuilds the block when the text has change notes. When the quiz
file appears, `QuizLive.poll` loads the new questions into the learned quiz and clears its answers.
The page then draws the quiz after the section.

The files change in this order:

| File | Written by | When |
|---|---|---|
| `book/probability/v_3/` and `current` | `ChapterState.new_version` | at the submit |
| `answers.json` | `ChapterState.save_answers` | at the submit |
| `notes.md`, the "# Quiz results" part | `ReaderStore.record_quiz` | at the submit |
| `chat.json` | `ChatAgent.add_assistant_message` and `ChatAgent.note_event` | after the feedback, 2 to 3 s in |
| `v_3/random-variables.md` | `Adapter._rewrite` | streamed, from about 2 s to 20 s in |
| `reader.md` and the "# Notes" part of `notes.md` | `memory.note_step` | a few seconds after the submit |
| `v_3/sources.json` | `ChapterState.record_source` | when the rewrite ends |
| `v_3/random-variables.quiz.md` | `Adapter._write_quiz` | after the rewrite, 20 to 30 s in |
| `chat_session/` | `ChatAgent._save_session` | after the next chat answer |

The other actions follow the same pattern. `book.py` has one method for each of them.
`submit_text_input` waits for the note step and rewrites every section of the page if the note
step asks for it. `personalize_again` rewrites the sections whose vault text changed. `first_visit`
writes the sections that have no text yet.

## 4. The tutor in depth

`agents/chat.py` is the only file that uses AI Functions. It uses a small part of the library,
which is one function spawned once as a thread that keeps its history.

### The AI Function

```python
@ai_function(structured_output=False, coordinator_tools_enabled=False, callback_handler=None)
def tutor(message: str) -> str:
    """{message}"""
```

An AI Function is a Python function whose body is evaluated by an agent. The docstring is the
prompt template, filled in with the call's arguments. The return annotation is the type of the
result. The tutor's template is just the message.

The three options have the following effects. `structured_output=False` makes the reply text the
result, without a structured output tool, which the library allows only for `str`.
`coordinator_tools_enabled=False` leaves out the coordinator tools `list_threads` and
`send_message`, since the tutor has no peers. `callback_handler=None` is passed on to the strands
`Agent` and keeps strands from printing the streamed reply to the console.

The decorator only defines a template. Each `ChatAgent` makes its own variant with `.replace`,
which returns a new AI Function with the given settings merged in:

```python
template = tutor.replace(model=llm.chat_model(), tools=self._tools(), config_hook=self._config_hook)
```

The variant is made per `ChatAgent` because its tools and its hook close over the reader's store
and adapter.

### The thread on a coordinator

`ChatAgent._spawn` creates an `InMemoryCoordinator`, the registry that routes work to threads, and
a `LocalWorker`, which hosts the threads in this process and drives their cycles. It then spawns
the template as a thread named `tutor`:

```python
handle = await self._coordinator.spawn(template, thread_name=THREAD, thread_id=thread_id, seed_events=seed)
```

The app talks to the thread through the returned `ThreadHandle`. A call to
`await handle.run(message=...)` runs one cycle. In a cycle the agent sees the whole conversation so
far, may call tools several times, and ends with its reply. The history stays in the thread. The
next `run` therefore continues the same conversation.

### Tools as closures

`ChatAgent._tools` defines the tools inside the method. Each tool can then use `self` and the
`chapter()` helper without a global variable. The tools are `read_section`, `read_file`,
`rewrite_section`, `add_quiz`, `remember`, `search_arxiv` and, with a Tavily key, `web_search`.
Each one is a plain function under strands' `@tool`, which builds the tool's schema from the
function's name, type hints and docstring. The model reads the docstring and its `Args:` lines,
which makes them part of the prompt.

These tools follow three habits that new tools should keep:

- Every outcome returns a string, including errors like
  `"Error: no section 'foo'. Sections: ..."`. The model can then correct itself instead of the
  cycle failing.
- `rewrite_section` and `add_quiz` do not wait for the work. They build a `Task`, call
  `self.adapter.start` to run it in the background, and at once return a line like "Rewriting
  expectation now. The page updates as the text is written." The tutor thus answers in seconds.
  The page shows the new text as it streams.
- `read_file` goes through `read_vault_file`, a module-level function that refuses paths outside
  the vault and paths inside the reader folders. Since this logic is outside the closure,
  `tests/test_chat_tools.py` can test it without a model.

The tools act on the chapter of the message being answered. `ChatAgent._answer` sets
`self._chapter` before the run. The `chapter()` helper reads it from there. This works because
answers run one at a time under `self._lock`.

### config_hook: a new system prompt for every message

The thread keeps its history across messages. Its system prompt, however, is built again at the
start of every cycle. At that point the library calls the `config_hook` with the cycle's context.
The dict it returns is merged into the thread's settings for that cycle only:

```python
def _config_hook(self, ctx) -> dict:
    return {"system_prompt": self.system_prompt(self._chapter)}
```

`ChatAgent.system_prompt` puts together `prompts/agent.md`, the page's title and file, the page's
agent.md, the list of its sections, and `reader_context` with reader.md and the page's notes.md.
In this way the tutor knows which page the reader is on now and what the note step learned since
the last message, without either being written into the conversation.

Since the hook runs inside the cycle, the library asks that it not block. Reading a few small files
is fine. A model call or a network request does not belong there.

### notify: events from outside the chat

Quiz submits, skipped quizzes and text inputs happen outside the chat. The tutor should still know
about them. `ChatAgent.note_event` does two things with such an event. It appends the event to the
`events` list in chat.json and calls `handle.notify(text)`. A call to `notify` does not start a
cycle. The thread buffers the text. The model sees it at its next turn, ahead of the reader's
next message.

After an answer, `_answer` drops the events that were pending when the message came in. If the app
stops before the next message, `_spawn` notifies the saved events again at the next start. In this
way no event is lost.

### Saving the session

chat.json holds what the chat panel shows. The tutor's own memory is its event log, which also
holds the tool calls, their results and the notified events. After each answer `_save_session`
reads the log with `coordinator.get_events(handle.id)` and saves it with the library's
`FileSessionStore`:

```
chat_session/session.json          the thread's name and id
chat_session/tutor.events.json     its event log
```

At the next start `_spawn` loads the log and passes it as `seed_events`. The new thread thus starts
with the old conversation in its history.

### Why the tutor has its own event loop

NiceGUI runs its own asyncio loop. Everything the browser triggers runs on that loop. The tutor is
also called from other places, such as `run.io_bound` worker threads and `Book` methods that are
plain functions. For this reason `ChatAgent.__init__` starts a second loop in a daemon thread named
`ql-chat`. The coordinator, the worker and the thread all live on that loop. `ChatAgent._call`
runs a coroutine there and waits for its result:

```python
return asyncio.run_coroutine_threadsafe(coro, self._loop).result()
```

As a result, `ChatAgent.handle(message, chapter)` is an ordinary blocking call that works from any
thread. The chat panel calls it through `run.io_bound`. A worker thread then waits for the reply.
Meanwhile, NiceGUI's loop keeps serving every page. On Reset and at shutdown, `Book.stop` calls
`ChatAgent.close`, which closes the worker, cancels what is still running and stops the loop.

## 5. The content format in depth

The docstrings of `vault/outline.py`, `vault/chapter.py` and `vault/quiz_md.py` are the reference
for the format. This section explains the format with the shipped content.

### Pages and the outline

`content/outline.md` defines the drawer's navigation and the list of pages that exist. An excerpt
of it looks like this:

```
- [[book/preface|Preface]]
# Lectures
- [[lectures/lecture_1|Lecture 1]]
# Agentic Book
## Appendix — Background
- [[book/probability/chapter|Probability and Statistics Primer]]
- Information
```

| Line | Meaning |
|---|---|
| `# ` and a name | a group |
| `## ` and a name | a part of the book |
| `- ` and a wikilink | a page |
| `- ` and a title without a link | a chapter still to be written, shown greyed out |

A link to a `chapter.md` is a chapter folder, served at the folder's route, here
`/book/probability`. A link to any other file is a one-file page, served at its path, here
`/lectures/lecture_1`. Both kinds are adaptive and read by the same parser, `parse_page`. The
page's key is `book/probability` or `lectures/lecture_1`. The key also names the page's folder in
the reader folder.

### Blocks: fixed text, sections, quizzes and text inputs

`parse_page` reads a page from top to bottom and turns it into a list of `Block`s:

| On the page | Block | Id |
|---|---|---|
| `![[random-variables]]` alone on a line | an embedded section, the file `random-variables.md` of the page's folder | `random-variables` |
| a heading with text under it, up to the next heading, embed or text input | an inline section | the slug of its title, e.g. `symbols-at-a-glance` |
| `_TEXT_INPUT_: Tell us about yourself`, with the prompt on the lines under it | a text input | `tell-us-about-yourself` |
| the first `# ` heading and the text under it, a heading with no text, or text before any heading | fixed text, which is never rewritten | `fixed-1`, `fixed-2`, ... |

Every section, embedded or inline, gets a prior quiz slot before it and a learned one after it,
with ids like `random-variables.prior`. A slot without questions shows nothing. A section with no
quiz file therefore looks like plain text. If a page has only one heading, as the preface does,
that heading is not taken as a fixed title. The whole page is then one section.

The slug of a section is its title in lower case, with every run of characters other than letters
and digits turned into a dash. For example, the heading "Inductive vs. transductive inference" in
Lecture 1 becomes `inductive-vs-transductive-inference`. If two headings give the same slug, the
second one gets `-2`. The quickest way to find the name for a quiz file is
`/debug/material?chapter=lectures/lecture_1`, which lists the section ids of a page.

The choice between embedded and inline sections is about authoring. An embedded section is a file
of its own, with a `topics` property in its front matter that the rewrite must cover. It can be
opened and edited on its own in Obsidian. An inline section keeps a lecture in one readable file.
The app treats both kinds the same way.

A few details matter when writing content. Headings, embeds and text inputs inside code fences are
plain text. A footnote's definition moves to the block that cites it, since each block renders on
its own. An embed of an image, like `![[lecture_2/fig.svg]]`, is a figure in the text and not a
section.

### Quiz files

A section's quizzes are in one file with a `# Prior` and a `# Learned` part. In a chapter folder
the file is `<name>.quiz.md`, like `book/probability/random-variables.quiz.md`. Next to a one-file
page it is `<page>.<name>.quiz.md`, like `lectures/lecture_1.learning.quiz.md`. A quiz file looks
like this:

```
# Prior

1. Which statement about a density $p(x)$ is right?
   - [ ] $p(x) = \mathbb{P}(X = x)$
   - [x] $\int p(x)\,dx = 1$
2. Evaluate these statements:
   - [T] The marginal is $\int p(x, y)\,dy$.
   - [F] Independence means $p(x, y) = p(x) + p(y)$.

# Learned
```

A numbered item is a question. Options marked `[ ]` and `[x]` make a pick-one question with exactly
one `[x]`. Options marked `[T]` and `[F]` make a set of true-or-false statements. A question without
options takes a free-form answer, which is not graded.

An empty Learned part is normal, since the book writes a learned quiz itself when the prior quiz
shows gaps. The model writes new quizzes in the same format, which `prompts/learned_quiz.md` shows
it. A rewritten quiz goes into the version folder as `<name>.quiz.md` for both kinds of pages.
`ChapterState.quiz_questions` reads each part from there first and from the vault otherwise.

### Text inputs

A line `_TEXT_INPUT_: Title` asks the reader a question in a text box. The non-empty lines right
under it are the prompt. The answer is saved in answers.json and under "# Inputs" in notes.md. The
note step then decides whether the answer calls for a rewrite of the whole page. The probability
chapter opens with a text input, which is how a reader tells the book about their background.

### agent.md and reference.md

The folder of a page may have an `agent.md` with the author's guide to the chapter. It goes into
every rewrite request as `<chapter_guide>` and into the tutor's system prompt. The author sets the
style, depth and prerequisites there. `book/probability/agent.md` has parts like "About this
material", "Pre-conditions", "Post-conditions", "Common misconceptions" and "Style". According to
`rewrite.md`, the Style part sets the default length, depth and tone. The three lectures share
`lectures/agent.md`, since they are in the same folder.

A `reference.md` holds source material. It is not shown on any page. The tutor can read it with
`read_file`, like any other file of the vault.

### Figures

A page links its figures relative to its own folder, as Obsidian does. For example,
`lectures/lecture_2.md` has `![A coding agent session](lecture_2/02_agent_ui.svg)`. Image embeds
like `![[lecture_2/fig.svg]]` and iframes like `<iframe src="lecture_2/kv_cache_stepper.html">`
work too. `resolve_figures` in `ui/figures.py` rewrites these links to
`/vault/lectures/lecture_2/...`. The `/vault/{path}` route serves any file of the vault except
markdown, hidden files and the reader folders. Because the links point at the vault, a rewritten
section in the reader's version folder still finds its figures. `prompts/rewrite.md` also tells the
model to keep every figure, caption and iframe exactly as it is.

The browser's markdown sanitizer would drop iframes. For this reason `trusted_html` turns the
sanitizer off for a section only when its only raw HTML is iframes of vault files. The check is
strict because rewrites are model output.

### Checking the content

`uv run python -m quicklearn.check` reports broken embeds and links, malformed quiz questions, quiz
files without a section, duplicate block ids and math that does not render. It also warns about
embedded sections that have no quiz, since the book cannot adapt them. Authors should run it after
every change to the content.

## 6. Recipes

Each recipe names the files to touch and sketches the change against the real code. After a
change, `uv run pytest tests -q` runs the tests. Section 7 explains how to check the result in the
browser.

### Adding a tool to the tutor

The tools are defined in `ChatAgent._tools` in `agents/chat.py`. The example below adds a tool that
reads a section as an earlier version had it, for a reader who asks what a section said before.
Version folders count from `v_0`, where every section is still the author's text. The version bar
counts from 1.

```python
from quicklearn.chapter.versions import list_versions

        @tool
        def read_earlier_version(name: str, version: int) -> str:
            """The text of one section of this chapter as an earlier version had it.

            Args:
                name: Section name, e.g. random-variables
                version: The version folder's number, 0 for the text as the author wrote it
            """
            if name not in chapter().doc.sections:
                return unknown(name)
            versions = list_versions(chapter().dir)
            if version not in versions:
                return f"Error: no version {version}. Versions: {', '.join(map(str, versions))}"
            return chapter().section_text(name, chapter().dir / f"v_{version}")

        tools = [read_section, read_file, read_earlier_version, rewrite_section, add_quiz, remember,
                 tool(search_tools.search_arxiv)]
```

The tutor learns when to use the tool from a line under "Your tools" in `prompts/agent.md`. The
docstring tells the model what the tool does. The prompt tells it when to use the tool.

A test without a model is easiest when the tool's body is a module-level function that takes the
chapter, as `read_vault_file` is. The `chapter` fixture of `tests/conftest.py` gives such a test a
chapter of the small vault. A tool that starts slow work should return at once, as
`rewrite_section` does. A tool that needs a model call of its own can use `llm.complete`, which the
tests' `FakeLLM` replaces once its prompt is known to the fake, as the prompt recipe below
explains.

### Adding or changing a rule in the adapter

The rules are in `Adapter.plan_for_quiz` in `agents/adapter.py`. A rule returns a `Plan` with the
sentence that the feedback ends with and the tasks to run. A `Task` rewrites a section. With
`quiz="prior"` or `quiz="learned"`, it also writes that quiz. With `rewrite=False`, it writes only
the quiz.

In the example below, a reader who gets every question of a learned quiz right gets a prior quiz
for the next section, when that section has none:

```python
        if part == "learned":
            if not has_gaps(quiz):
                later = names[names.index(name) + 1:]
                if later and not chapter.quizzes[f"{later[0]}.prior"].questions:
                    reason = f"The reader got every question of the quiz after {name} right:\n\n{answers}"
                    return Plan(
                        "You are ready for the next section, and a short quiz before it is on its way.",
                        [Task(later[0], reason, quiz="prior", rewrite=False)],
                    )
                last = not any(chapter.quizzes[f"{n}.{p}"].questions for n in later for p in QUIZ_PARTS)
                return Plan("That completes the chapter." if last else "You are ready for the next section.")
```

A test for the rule belongs next to the others in `tests/test_adapter.py`, which build a quiz with
`answered(...)` and check `plan.tasks`. The small vault's `beta.quiz.md` already has a prior
question. The test should therefore first overwrite that file with an empty quiz,
`"# Prior\n\n# Learned\n"`, and build the `ChapterState` after that. The rule tables in the
docstring of `adapter.py` and in `docs/project_overview.md` should be updated too.

The other plans work the same way. `plan_for_all`, `plan_for_stale` and `plan_for_empty` are the
plans for a text input, for "Personalize again" and for a first visit. `ChapterState.is_compact` is
the test that keeps an expert's section from being condensed twice.

### Changing a prompt

The prompts are the markdown files in `agents/prompts/`, loaded by `load_prompt(name)`:

| Prompt | Sent by | Read from disk |
|---|---|---|
| `agent.md` | `ChatAgent.system_prompt`, for the tutor | on every chat message |
| `rewrite.md` | `Adapter._rewrite` | when a `Book` is made, at start and after Reset |
| `learned_quiz.md` | `Adapter._write_quiz`, for prior and learned quizzes | when a `Book` is made |
| `feedback.md` | `Adapter.feedback` | when a `Book` is made |
| `memory.md` | `memory.note_step` | on every note step |

Each prompt is easiest to read next to the function that builds its request, since the request
supplies the `<reader>`, `<chapter_notes>` and `<chapter_guide>` tags that the prompt refers to.
For example, sections get shorter when the line "Keep the section under 900 words." in `rewrite.md`
asks for fewer words. A length limit should stay well under the `max_tokens` of the call, which is
4000 for a rewrite and 600 for feedback. Otherwise the reply is cut off. The log then warns that
the reply hit `max_tokens`.

Two prompts have a format that the code parses. The note step's reply must keep the tags
`<about_reader>`, `<notes>`, `<rewrite>` and `<reason>`, which `memory.parse_reply` reads. The quiz
format in `learned_quiz.md` must stay what `parse_quiz` reads. A change to either format needs the
same change in the parser and its tests.

For a change to one chapter only, the chapter's agent.md is the better place. The tests' `FakeLLM`
recognizes each call by the exact text of its prompt, loaded when the fixture is made. Edits to the
prompt files therefore need no change to the tests. A new prompt file needs its name in the tuple
that builds `FakeLLM.prompts` and a reply in `FakeLLM.replies`.

### Using another model or effort

All model setup is in `llm.py`. The settings come from the environment, read by
`ModelConfig.from_env`:

```bash
QL_FAST_EFFORT=medium ./run.sh                       # rewrites, quizzes, feedback and the note step
QL_CHAT_MODEL=<model id> ./run.sh                    # the tutor
QL_FAST_MODEL=<model id> QL_FAST_EFFORT= ./run.sh    # a model without an effort setting
```

One kind of call can get a model of its own through a `ModelConfig` passed to `llm.complete` or
`llm.stream_text`. The example below gives the quiz writer in `Adapter._write_quiz` its own
variables, `QL_QUIZ_MODEL` and `QL_QUIZ_EFFORT`:

```python
raw = llm.complete(self._prompts["learned_quiz"], request, max_tokens=3000,
                   config=llm.ModelConfig.from_env("QUIZ", "medium"))
```

The tutor's model is a strands model built in `llm.chat_model`. It is a `BedrockModel`, or an
`AnthropicModel` when `ANTHROPIC_API_KEY` is set. Any strands model provider works there. The
adapter and the note step call the Anthropic SDK directly. Another provider for them means a new
version of `stream_text` and `complete` with that provider's streaming API. Their signatures should
stay the same, so that the rest of the code and the `FakeLLM` still fit.

### Adding a page or a chapter with quizzes

A new page needs no code. A fourth lecture, for example, takes five steps:

1. The page is a new file `content/lectures/lecture_4.md` with a `# Lecture 4` title and `## `
   headings with text under them. Each heading becomes a section.
2. A line `- [[lectures/lecture_4|Lecture 4]]` in `content/outline.md` links the page.
3. Each section that should adapt gets a quiz file `content/lectures/lecture_4.<slug>.quiz.md`
   with a `# Prior` part and an empty `# Learned` part. For a section "Reward and loss", the slug
   is `reward-and-loss`.
4. Figures go into `content/lectures/lecture_4/` and are linked as `![alt](lecture_4/fig.svg)`.
5. `uv run python -m quicklearn.check` checks the result. The page is then at
   `/lectures/lecture_4`. Its section names, listed by `/debug/material?chapter=lectures/lecture_4`,
   should match the names of the quiz files.

A chapter folder takes a few more files. `content/book/<chapter>/chapter.md` has one
`![[<section>]]` line per section. Each section is a `<section>.md` file with a `topics` list in its
front matter and a `# ` heading, next to its `<section>.quiz.md`. The folder also holds an
`agent.md` with the chapter's guide and, optionally, a `reference.md`. The outline links the page
as `book/<chapter>/chapter`. A section file with topics but no text is written for the reader on
their first visit, from its topics.

### Adding a reader action or a kind of block

A reader action is a button or form on the page that leads to a `Book` method. The example below
adds an "Explain more" button under every section, which rewrites the section in more depth. It
touches three files.

In `book.py`, the action follows the same steps as the others. It starts the work, queues the note
step and tells the tutor. `Task` needs to be imported from `quicklearn.agents.adapter`.

```python
    def explain_more(self, chapter: ChapterState, name: str) -> None:
        """The reader asked for more depth in one section."""
        title = chapter.doc.sections[name].title
        reason = "The reader asked for more detail in this section, with a worked example."
        self.adapter.start(chapter, [Task(name, reason)])
        self._note_later(chapter, f"The reader asked for more detail in the section {title}.")
        self.chat.note_event(f"The reader asked for more detail in {name}. Rewriting it for them.")
```

In `ui/content_renderer.py`, `render_section` gets a new keyword and draws the button under the
text of a section. All blocks get the same keywords. Quizzes and text inputs return earlier in the
function. The check of `FIXED_PREFIX` keeps the button off fixed text:

```python
def render_section(..., on_explain_more: Callable | None = None, flash: bool = False):
    ...
        el = _render_chunk_with_notes(content.strip(), bool(NOTE_TAG_PATTERN.search(content)))
        if on_explain_more and not section.id.startswith(FIXED_PREFIX):
            ui.button("Explain more", icon="unfold_more", on_click=lambda: on_explain_more(section.id)).props(
                "flat dense size=sm color=grey")
        return el
```

In `app.py:chapter_page`, the callback goes into `render_kwargs`. It runs the action through
`run.io_bound`, since `note_event` waits for the tutor's loop:

```python
    async def on_explain_more(name: str) -> None:
        await run.io_bound(book.explain_more, chapter, name)
        ui.notify(f"Rewriting {chapter.doc.sections[name].title} with more detail.")

        render_kwargs=dict(..., on_explain_more=on_explain_more),
```

The page needs no new code to show the result, since the poller picks up the new file. A test for
the action fits in `tests/test_book.py`, with `fake_llm` and the `wait(book)` helper there. It can
check that `fake_llm.requests("rewrite")` carries the reason.

A new kind of block goes one level deeper. Text inputs are the example to follow:

| File | Change for a new kind of block |
|---|---|
| `vault/chapter.py` | a pattern like `_TEXT_INPUT` and a branch in `parse_page` that make a new `Block.kind` |
| `chapter/state.py` | an object made in `ChapterState.__init__`, and a tag as the block's content in `ChapterState._section`, like `<!-- text_input:id -->` |
| `chapter/state.py` | `save_answers` and `_restore_answers`, if the answers should survive a restart |
| `ui/content_renderer.py` | a match of the tag in `render_section` that calls a renderer of its own, like `ui/text_input_renderer.py` |
| `app.py` and `book.py` | callbacks in `render_kwargs` that call a new `Book` method, as above |
| `ui/layout.py` | the new tag in `WIDGET_TAG`, which keeps widget blocks out of the drawer's list of sections |
| `check.py` | a check of the new syntax, if authors can get it wrong |

### Changing how a section looks

`render_section` in `ui/content_renderer.py` draws a section. `_render_chunk_with_notes` draws the
change notes in the right margin. The CSS in `ui/layout.py:_setup_styles`, scoped to
`.nicegui-markdown`, sets the typography. Quizzes and text inputs have their own renderers in
`ui/quiz_renderer.py` and `ui/text_input_renderer.py`.

NiceGUI builds the page in Python. An element made inside a `with` block goes inside that element.
The `.classes(...)` method takes Tailwind classes. The `.props(...)` method takes Quasar
properties.

The example below adds a small badge next to the title of a section that was rewritten for the
reader. Such a section is recognized by its change notes:

```python
        if section.title:
            with ui.row().classes("items-center gap-2 mt-6 mb-2"):
                math_markdown(f"{level} {section.title}")
                if NOTE_TAG_PATTERN.search(content):
                    ui.badge("rewritten for you", color="amber-2", text_color="amber-9")
```

Blocks are updated in one of two ways, which matters for anything drawn around the text. When a
block's file changes, `SectionUI.on_live_change` in `ui/page_ui.py` either sets the new text on the
existing markdown element or clears the block and calls `render_section` again. The first is the
fast path for plain text. The second is the slow path for quizzes, sections that had no text, and
text with change notes. Anything drawn around the text is redrawn only on the slow path. The badge
above depends on change notes, which always take the slow path. It therefore appears as soon as the
first note is streamed.

## 7. Testing and debugging

### Tests without model calls

`uv run pytest tests -q` runs the whole suite in a few seconds, without credentials. Two fixtures in
`tests/conftest.py` make this possible:

- `no_model` runs for every test and replaces `llm.client` with a function that fails the test. A
  test that reaches a real model thus fails loudly instead of costing money.
- `fake_llm` replaces `llm.stream_text` and `llm.complete` with a `FakeLLM`. The fake recognizes
  each call by its system prompt, answers from `fake_llm.replies[name]` and records every request in
  `fake_llm.calls`.

```python
def test_a_rewrite_sees_the_reader(book, fake_llm):
    fake_llm.replies["rewrite"] = ["First paragraph.\n\n", "Second paragraph."]
    ...
    assert "<reader>" in fake_llm.requests("rewrite")[0]
```

A reply can be a list of chunks, which are streamed one by one. A chunk can also be a function that
runs between chunks, for example to wait on a `threading.Event` or to look at the half-written file.
`tests/test_adapter.py` uses such functions to test streaming and stopping on Reset.

The tests build their content with `small_vault`, a tiny vault in a temporary folder, or with
`shipped_vault`, a copy of `content/` without the reader folders. They never touch your real reader
folders. Since `Book` methods start background work, `tests/test_book.py` has a `wait(book)` helper
that shuts the pools down and waits for them.

The tutor's AI Functions loop has no unit test, since it needs a real model. Its tools can still be
tested as plain functions. The loop itself is best checked in the browser.

### Logs

Each run writes `logs/<timestamp>/server.log`. The link `logs/latest` points at the newest folder.
The quicklearn loggers write to the file at DEBUG level. The ai_functions and strands loggers write
to it at INFO level. These lines are useful to look for:

| Line | Comes from |
|---|---|
| `book/probability: rewriting ['random-variables'] in v_3` | `Adapter.start` |
| `Rewrote random-variables in 14.2s (612 words)` | `Adapter._run` |
| `Wrote the learned quiz of random-variables in 6.1s` | `Adapter._run` |
| `The learned quiz of random-variables came back without questions` | `Adapter._write_quiz`, when the model's quiz did not parse |
| `Note step for book/probability in 2.1s: rewrite=False (...)` | `memory.note_step` |
| `Chat message on book/probability: ...` | `ChatAgent._answer` |
| `Rewrite failed` or `Note step failed`, with a traceback | the callbacks of the pools |

The failure lines in the last row are the only trace of an exception in a pool's thread.

### Looking at the state

`GET /debug/material?chapter=book/probability` returns the page's sections, its quizzes with their
state and number of answers, its text inputs, the sections that "Personalize again" would rewrite,
and the number of tasks running. The reader folder shows the rest. It holds the current `v_N`, what
the note step wrote in reader.md and notes.md, and what is waiting in chat.json.

Changes are safer to try with a reader other than the usual one, as in
`QUICKLEARN_READER=scratch ./run.sh`. Reset then starts that reader over. A demo reader gives a book
that has already been adapted, as in `QUICKLEARN_READER=physics-undergrad ./run.sh`.

### In the browser

A change to the app is best checked in the browser too. After a submit, the page should start
changing within a few seconds. The "Agent is working" indicator should show while tasks run. A
restart should bring back the chat and the rewritten sections. `docs/project_overview.md` lists
selectors for driving the page from Chrome through Playwright.

## 8. Ideas for projects

- **Spaced repetition.** The date of each learned quiz could go into answers.json. On a later visit,
  the book would then start `Task(name, reason, quiz="learned", rewrite=False)` for the sections
  that are due, which gives the reader a fresh quiz on old material.
- **A teacher dashboard.** A new `@ui.page` could read the notes.md of every reader folder and show,
  per section, how many readers missed which questions. It needs no model, only the files.
- **Several readers at once.** The app holds one `Book`. A `Book` per signed-in reader, kept with
  NiceGUI's user storage, would turn the app into a tool for a whole class.
- **A checked quiz writer.** An AI Function that returns a list of questions could replace the
  `llm.complete` call in `Adapter._write_quiz`. A post-condition that every pick-one question has
  exactly one right answer would make the library ask the model again when a quiz is malformed.
- **A new tool for the tutor.** Possible tools include one that runs a short Python snippet for a
  worked example, one that draws a figure, and one that finds the section of another page that
  covers a concept.
- **A second agent.** A reviewer thread on the same coordinator could read each fresh rewrite and
  check it against the post-conditions in the chapter's agent.md. With coordinator tools enabled,
  the two threads could talk through `send_message`.
- **Your own content.** `QUICKLEARN_CONTENT` can point at a vault of your own course notes. With
  prior quizzes for its sections, the book adapts them like the shipped content.
