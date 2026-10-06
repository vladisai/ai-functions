# QuickLearn — Project Overview

This is the developer's map of the example. `README.md` is the student's guide to running it.

QuickLearn is an adaptive book. The content is an Obsidian vault of markdown files. The app
rewrites each chapter for its reader as they answer quizzes, tell it about themselves and chat
with a tutor.

## Quick Start

```bash
./run.sh            # http://localhost:8889
./run.sh 8890       # another port
```

Run `uv sync --extra dev` once in this folder. It installs the dependencies, plus the repo's own
`strands-ai-functions` from `../../..` as an editable package. `run.sh` runs `uv run python -m quicklearn.app`.
The model calls go to Bedrock with the usual AWS credentials. The region is
`AWS_DEFAULT_REGION`, or us-west-2 when it is unset. With `ANTHROPIC_API_KEY` set, the calls go to
the Anthropic API instead, which is untested.

| Variable | Default | Meaning |
|---|---|---|
| `QUICKLEARN_CONTENT` | `content/` | the content folder, the vault with outline.md |
| `QUICKLEARN_READER` | `default` | the reader folder in `content/personalization_data/` |
| `QL_FAST_MODEL`, `QL_FAST_EFFORT` | Sonnet 5.5, low | rewrites, quizzes, feedback, the note step |
| `QL_CHAT_MODEL`, `QL_CHAT_EFFORT` | Sonnet 5.5, medium | the chat tutor |
| `TAVILY_API_KEY` | unset | gives the tutor web search |

A reader whose name matches a folder in `demo_readers/` starts as a copy of that folder, so
`QUICKLEARN_READER=physics-undergrad ./run.sh` opens the book as that reader has it after a few
quizzes and a chat. Reset goes back to that copy.

Check the vault for broken links, quizzes and math before a commit to the content:

```bash
uv run python -m quicklearn.check            # errors exit 1
uv run python -m quicklearn.check --strict   # warnings too
```

## The vault

```
content/
  outline.md                       the drawer: groups, parts and wikilinks to the pages
  lectures/
    lecture_1.md                   a one-file page: each heading with text under it is a section
    lecture_1.quiz.md              the page's own quiz: `# Prior`, the background check after the title
    lecture_1.*.quiz.md            quizzes of its sections, e.g. a group's learned quiz in its last section
    lecture_2.md, lecture_3.md     two more one-file pages, with their .quiz.md files
    lecture_2/, lecture_3/         their figures: svg and png, and kv_cache_stepper.html in an iframe
    agent.md                       hints for the tutor and the rewrites of the lectures
  book/preface.md                  a one-file page
  book/probability/                a chapter folder
    chapter.md                     the page: inline sections, `_TEXT_INPUT_:` questions, `![[embeds]]`
    random-variables.md            a section the book rewrites for the reader
    random-variables.quiz.md       its quizzes: `# Prior` before the section, `# Learned` after it
    expectation.md, information-theory.md and their .quiz.md files
    agent.md                       hints for the tutor and the rewrites
    reference.md                   source material the tutor can read
  personalization_data/            the reader folders, git-ignored
demo_readers/
  physics-undergrad/               a reader folder after a text input, a quiz and a chat
  statistics-professor/            a reader folder after a text input and three quizzes
```

Every page in outline.md is adaptive. A link to a `chapter.md` makes a chapter folder. A link to
any other file makes a one-file page, which is read the same way as chapter.md, so embeds and
`_TEXT_INPUT_:` work in it too. In both, an embed is a section. Every heading with text under it
is a section too, named by the slug of its title. A heading with nothing under it and the text
before the first heading stay fixed. A one-file page keeps its quizzes next to it as
`<page>.<name>.quiz.md`. A chapter folder keeps them as `<name>.quiz.md`. The page's own quiz is
`<page>.quiz.md`, or `chapter.quiz.md`. Its Prior shows after the title as "Checking your
background", and its Learned at the page's end. A question ends with tags, the sections it is
about: `[[lecture_2#Stochastic dynamical systems]]` for a heading of the page, `[[random-variables]]`
for an embed. The reader never sees them. The checker fails on a tag that names no section, and
warns on an untagged question of the page's own quiz. The root URL `/` opens the first chapter
folder. The formats are in the docstrings of `vault/outline.py`, `vault/chapter.py` and
`vault/quiz_md.py`.

A page links its figures relative to its own folder, as Obsidian does, so lecture_2.md has
`![alt](lecture_2/fig.svg)`. The forms `![[lecture_2/fig.svg]]` and `<iframe src="lecture_2/x.html">`
work too. `ui/figures.py` turns these links into `/vault/lectures/lecture_2/fig.svg`. A rewritten
section lives in the reader's version folder but still finds its figures in the vault through
these links. `prompts/rewrite.md` tells the rewrites to keep every figure, caption and iframe as it
is. A section's HTML is sanitized unless its only HTML is iframes of `/vault/` files.

| Lecture | Quiz files | Figures |
|---|---|---|
| `lecture_1.md` | 4: a background check of 6 questions and 3 learned quizzes | none |
| `lecture_2.md` | 4: a background check of 6 questions and 3 learned quizzes | 15 svg and the KV cache stepper |
| `lecture_3.md` | 5: a background check of 6 questions and 4 learned quizzes | 24 svg and png |

Every lecture is an adaptive page with one background check and learned quizzes that each cover a
group of sections. A group's learned quiz is in the quiz file of its last section. The probability
chapter has a quiz file for each section instead.

## The reader folder

```
content/personalization_data/<reader>/
  reader.md                        "# About the reader", shared by every chapter
  chat.json                        the chat as shown, and events the tutor has not seen yet
  chat_session/                    the tutor's AI Functions session, its event log
  book/probability/                one folder per page, named by its path without .md
    notes.md                       "# Inputs", "# Quiz results", "# Notes"
    answers.json                   quiz answers and text input answers
    v_0/, v_1/, ..., current       versions: the rewritten sections and quizzes, plus sources.json
  lectures/lecture_1/              the same for a one-file page
```

A version folder holds only what was rewritten. Anything missing falls back to the vault, so a
`git pull` of the content updates every section the reader has not had rewritten. A restart brings
everything back, including the chat and what the tutor remembers. Reset empties the folder.

## Code

```
quicklearn/
  app.py                 NiceGUI entry point: one Book, the pages from the outline, Reset
  book.py                Book: the reader's chapters, rewrites, chat and note steps in one place
  check.py               python -m quicklearn.check, the vault checker
  llm.py                 model setup: the Anthropic SDK for the adapter, strands for the chat
  logging_setup.py       logs/<timestamp>/server.log, logs/latest
  vault/                 reading the vault: outline, chapter.md, quiz.md, wikilinks, front matter
  chapter/
    state.py             ChapterState: one chapter for one reader, the vault with the rewrites on top
    versions.py          the v_N folders and the current link
    live.py              each block of a page watches its file and updates the page
  reader/store.py        ReaderStore: the reader folder, reader.md, notes.md, answers, chat.json
  agents/
    adapter.py           rewrites: Python rules pick the sections, one streamed call writes each
    memory.py            the note step: what to remember after each reader action
    chat.py              ChatAgent: the tutor, an AI Functions thread with tools
    search_tools.py      arXiv search, and Tavily web search with TAVILY_API_KEY
    prompts/             agent.md, rewrite.md, learned_quiz.md, feedback.md, memory.md
  core/                  Material and Section, Quiz, TextInput
  ui/                    layout, drawer, content and quiz renderers, chat panel, math markdown
    figures.py           GET /vault/{path} for figures, and the links to it in a page's text
tests/                   unit tests, no model calls
```

## How a reader action flows

Every action goes through `Book`, so the order of the steps is in one place:

| Action | Facts the app saves | Note step | Rewrites |
|---|---|---|---|
| Text input | answers.json, the answer under "Inputs" | waits for it | every section of the page, if the note step says so |
| Quiz submit | answers.json, the score under "Quiz results" | in the background | at once, by the adapter's rules |
| Chat | chat.json, chat_session/ | in the background, after the answer | through `rewrite_section`, and `add_quiz` writes a quiz |
| Personalize again | | | the rewritten sections whose vault text changed |

The adapter's rules apply to the quizzes of every section, inline or embedded, on every page:

| Reader action | What is rewritten |
|---|---|
| Prior quiz with gaps | the section, around what they missed, and a learned quiz after it |
| Prior quiz all right | the section, condensed, unless it is already compact |
| Page prior with gaps | each section tagged on a missed question, in parallel, and no quiz |
| Page prior all right | nothing |
| Learned quiz with gaps | the tagged sections of the missed questions, else its own, then a fresh learned quiz in the same slot on every section it tags |
| Text input | every section of its page, when the note step says the answer calls for it |
| Chat | the sections the tutor names through rewrite_section |
| Chat, add_quiz | a prior or learned quiz for the section the tutor names, and not its text |

A missed untagged question of the page's own quiz only goes to notes.md. An untagged question of a
section's quiz is about that section. A rewrite opens a new version folder and streams the section
into its file. Each block of the page polls its file every 2 s, so the page starts changing a few
seconds after a submit, without closing an open quiz. Every request carries reader.md and the
chapter's notes.md, so a rewrite of Expectation knows what the reader missed in Random Variables.
Rewrites put `<!-- note: ... -->` markers in the text. The page shows them in the right margin.

### The chat tutor

`agents/chat.py` runs the tutor on the public AI Functions API, the `strands-ai-functions` package:

- The tutor is an `@ai_function` with strands tools: `read_section`, `read_file` for the vault
  outside the reader folders, `rewrite_section`, `add_quiz`, `remember` for reader.md or
  notes.md, `search_arxiv`, and `web_search` with a Tavily key. It has no coordinator tools.
- `add_quiz(name, request, part="learned")` writes a quiz for any section into a new version
  without rewriting its text. With "prior" the quiz goes before the section. With "learned" it
  goes after it. With the page's name, e.g. `add_quiz("lecture_2", ..., part="prior")`, it writes
  the page's own quiz on all its sections. Like `rewrite_section`, it runs in the background and
  returns at once. The quiz appears in its slot when it is written.
- The tutor is spawned once per Book on an `InMemoryCoordinator` with a `LocalWorker`. They live on an
  asyncio loop in a thread of their own, so `ChatAgent.handle(message, chapter)` is a plain
  blocking call, which the chat panel makes through `run.io_bound`. Messages are answered one at a
  time.
- A `config_hook` builds the system prompt for every message from `prompts/agent.md`, the
  chapter's agent.md and sections, reader.md and the chapter's notes.md.
- Quiz submits and text inputs reach the tutor through `handle.notify`. The tutor sees them with
  the next message. They wait in chat.json until then, so a restart does not lose them.
- After each answer, the event log is saved with `FileSessionStore` in `chat_session/`. The next
  start passes it back as `seed_events`, so the tutor remembers the conversation.

## Timings

These timings were measured in Chrome on Sonnet 5.5 on Bedrock:

| Step | Time |
|---|---|
| Quiz feedback in chat | 2-3 s |
| Quiz submit, first section change | 2 s |
| Quiz submit, section and learned quiz done | 20-30 s |
| Chat reply | 2-3 s |
| Chat rewrite request, rewrite started | 4-5 s |
| Chat rewrite request, first section change | 6 s |

## Running Tests

```bash
uv run pytest tests -q
```

The 226 tests take about 3 s. They make no model calls, since `conftest.py` fails any test that
reaches `llm.client`. Its `FakeLLM` answers `llm.stream_text` and `llm.complete` by prompt name. They
work on a tmp vault or a copy of `content/`, never on the real reader folders.

| File | What it covers |
|---|---|
| `test_vault.py`, `test_quiz_md.py`, `test_outline.py` | the vault formats: chapter.md, quizzes, the outline and its links |
| `test_check.py` | the vault checker |
| `test_reader_store.py` | the reader folder, reader.md and notes.md, wipe, the demo readers |
| `test_versions.py`, `test_chapter_state.py` | version folders, stale and empty sections, a reload |
| `test_adapter.py` | the rewrite plans, streaming into one version, stop on Reset |
| `test_page_quiz.py` | the page's own quiz and quiz tags: blocks, tag resolution, plans, a group quiz, a submit |
| `test_note_step.py` | reading the note step's reply |
| `test_book.py` | each reader action on a real Book |
| `test_chat_tools.py` | `read_vault_file`, which keeps the tutor out of the reader folders |
| `test_app.py` | the routes, the `/` redirect, `/debug/material` and Reset |
| `test_live.py` | a change on disk reaches every open page |
| `test_content_renderer.py`, `test_quiz_grading.py`, `test_math_markdown.py` | rendering and grading |
| `test_logging.py` | the log folder and its handlers |
| `test_figures.py` | figure links of a page and of a rewrite, `/vault/` refusing markdown and reader folders, iframes past the sanitizer |

The tutor's AI Functions loop has no unit test. Check it in Chrome with a reply, a rewrite request,
a quiz the tutor knows about, and its memory after a restart.

### Testing in Chrome

A Chrome driven through Playwright, for example from an MCP server, works well for checking the UI. Wait
about 2 s after a page load before interacting. Button labels render uppercase, so match them with
`/check/i`.

| Element | Selector |
|---|---|
| Text input | the textarea in `#section-tell-us-about-yourself`, then its Submit button |
| Quiz | `[id="section-random-variables.prior"]` and its "Take quiz" button, then `.cursor-pointer` options and the Check, Next and "Submit quiz" buttons |
| Section of a one-file page | `#section-<slug>` on its page, e.g. `#section-learning` on `/lectures/lecture_1`, and its quizzes like the one above |
| Chat | the button with the `chat` icon, `textarea[placeholder="Ask a question..."]`, Enter to send |
| Busy indicator | "Agent is working" in the `header` text |
| Personalize again | `header button:has(i:text("auto_fix_high"))` |
| Reset | `header button:has(i:text("restart_alt"))`, then the Reset button in `.q-dialog` |

Letters inside math do not render in headless Chrome, since its fonts lack them. It is not a bug of
the app.

## Debug Endpoints

- `GET /vault/{path}` returns a file of the vault that is not markdown, such as a figure. It
  refuses `.md`, hidden files, `personalization_data/` and paths outside the vault.
- `GET /debug/material?chapter=book/probability` returns the sections, quizzes, text inputs, stale
  sections and running tasks of a loaded chapter.

## Logging

`logs/<timestamp>/server.log` has the quicklearn loggers at DEBUG, and ai_functions and strands at
INFO. `logs/latest` points at the newest folder.
