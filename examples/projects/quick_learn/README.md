# QuickLearn

QuickLearn is a book that rewrites itself for its reader. It runs on your laptop as a small web
app. Before each section it asks a short quiz about what the reader already knows. After the
section, another quiz asks what they learned. Every answer changes what the book knows about them.
The sections are then rewritten around what they know and what they missed. A chat tutor answers
questions about the page, remembers what it learns about the reader, and can rewrite a section or
add a quiz when they ask for it. The book is built with AI Functions, the library in this
repository. The model behind it is Claude.

The book holds the three lectures of the class and the Probability and Statistics Primer:

| Page | What it covers |
|---|---|
| Lecture 1 | learning, induction and transduction, Solomonoff induction |
| Lecture 2: Stochastic Systems and AI Agents | LLMs as dynamical systems, the KV cache, tool calling, with figures and an interactive KV cache stepper |
| Lecture 3: Shannon Information and Inductive Learning | entropy, mutual information, the information bottleneck, with figures |
| Probability and Statistics Primer | random variables, expectation and information theory, in the appendix |

The other chapters of the book's outline are listed in the navigation drawer but greyed out, since
they are not written yet.

## Requirements

| What | Why |
|---|---|
| Python 3.12 or newer | uv downloads it for you if your system Python is older |
| [uv](https://docs.astral.sh/uv/) | installs the dependencies and runs the app |
| git | to clone the repository |
| Access to Claude | through Amazon Bedrock with AWS credentials, or with an Anthropic API key |

Install uv on macOS or Linux with:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows, run `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
and use the Windows Subsystem for Linux for `run.sh`, or start the app with the `uv run` command that `run.sh` contains.

Amazon Bedrock is the tested path. The Anthropic API works the same way in the code, but it has
seen much less use.

## Setup

1. Clone the branch with the example and go to its folder:

   ```bash
   git clone -b examples/quick-learn https://github.com/strands-labs/ai-functions.git
   cd ai-functions/examples/projects/quick_learn
   ```

2. Install the dependencies. This creates a `.venv/` in the folder and installs the AI Functions
   library from the repository itself, so it takes a minute the first time:

   ```bash
   uv sync
   ```

3. Set up your credentials as described in the next section.

4. Start the app and open http://localhost:8889 in your browser:

   ```bash
   ./run.sh
   ```

   To use another port, give it as the argument, for example `./run.sh 8890`. Stop the app with
   Ctrl+C in the terminal.

The pages open without any credentials, so a missing key only shows up once the book calls the
model. That happens the first time you submit a quiz, answer a question or send a chat message.

## Credentials

### Amazon Bedrock

The app uses the usual AWS credential chain, so any of these works:

| Way | How |
|---|---|
| The AWS CLI | run `aws configure` once and enter an access key, a secret key and a region |
| Environment variables | export `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and, for temporary credentials, `AWS_SESSION_TOKEN` |
| A named profile | export `AWS_PROFILE=<name>` to use a profile from `~/.aws/config` |

The region comes from `AWS_DEFAULT_REGION`. When it is unset, `run.sh` sets it to us-west-2. The
account needs access to Claude Sonnet 5.5 in Bedrock in that region. Open the Bedrock console,
go to Model access, and check that Claude Sonnet 5.5 is available. Anthropic models may ask for a
short use-case form the first time. The default model id is
`global.anthropic.claude-sonnet-5-5`, a global inference profile. The IAM user or role needs
permission to invoke it, which `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream`
cover. If you have the AWS CLI, `aws sts get-caller-identity` is a quick check that your
credentials are found.

### Anthropic API key

When `ANTHROPIC_API_KEY` is set, every call goes to the Anthropic API instead of Bedrock. The AWS
settings are then ignored:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
./run.sh
```

## Settings

All settings are environment variables. Set them before `./run.sh` or on the same line, as in
`QUICKLEARN_READER=alice ./run.sh`.

| Variable | Default | Meaning |
|---|---|---|
| `QUICKLEARN_CONTENT` | `content/` | the content folder, an Obsidian vault with `outline.md` |
| `QUICKLEARN_READER` | `default` | the reader's name, which is the folder their data lives in |
| `ANTHROPIC_API_KEY` | unset | use the Anthropic API instead of Bedrock |
| `AWS_DEFAULT_REGION` | `us-west-2` | the Bedrock region |
| `AWS_PROFILE` | unset | the AWS profile to use |
| `QL_FAST_MODEL` | `global.anthropic.claude-sonnet-5-5` on Bedrock, `claude-sonnet-5-5` on the API | the model for rewrites, quizzes, feedback and the notes about the reader |
| `QL_FAST_EFFORT` | `low` | the effort setting of those calls |
| `QL_CHAT_MODEL` | the same as `QL_FAST_MODEL` | the model of the chat tutor |
| `QL_CHAT_EFFORT` | `medium` | the effort setting of the tutor |
| `TAVILY_API_KEY` | unset | gives the tutor web search, besides arXiv search |

On Bedrock a model id carries a prefix such as `global.` or `us.`. Set an effort to `""` for a
model that has no effort setting.

## Using the book

The menu button at the top left opens the drawer with the Preface, the lectures and the outline
of the book. Each page is a list of sections. Most of them have a short quiz before them that asks
what the reader already knows. When they get some of it wrong, the section is rewritten in front
of them around what they missed. A quiz on what they learned then appears after it. When they get
it all right, the section is condensed. A wrong answer on the second quiz rewrites the section
again with a fresh quiz.

Some pages ask the reader about themselves in a text box, for example about their background in
the probability primer. The answer goes into what the book knows about them and shapes the
rewrites of every page.

The round chat button at the bottom right opens the tutor. It knows the page the reader is on,
their quiz results and what the book knows about them. When asked, it can do the following:

| Request | What happens |
|---|---|
| "Explain the KV cache more simply" | it answers in the chat |
| "Rewrite this section with a worked example" | it rewrites the section in the background while it answers |
| "Give me a quiz on expectation" | it adds a quiz to a section, which rewrites the section once submitted |
| "Remember that I know linear algebra well" | it saves a note that every later rewrite and answer uses |
| "Find a paper on the information bottleneck" | it searches arXiv, and the web too when `TAVILY_API_KEY` is set |

The buttons at the top right act on the current page:

| Button | What it does |
|---|---|
| Version bar, `v3/3` with arrows | appears after the first rewrite and steps back through earlier versions of the page, and Latest returns to the newest |
| Wand | Personalize again rewrites the sections whose original text changed since, for example after a `git pull` with new content |
| Circular arrow | Reset, after a confirmation, clears everything the book knows about the reader, their answers, the chat and every version |

## Demo readers

Two prepared readers show how different the same page can become. A reader whose name matches a
folder in `demo_readers/` starts as a copy of that folder:

```bash
QUICKLEARN_READER=physics-undergrad ./run.sh      # after a text input, a quiz and a chat
QUICKLEARN_READER=statistics-professor ./run.sh   # after a text input and three perfect quizzes
```

The tutor remembers the physics undergraduate's chat, since its session is part of the copy. Reset
on a demo reader goes back to the copy rather than to an empty book.

## Your data

Everything the book keeps about a reader is in plain files in
`content/personalization_data/<reader>/`, which git ignores. It holds what the book knows about
them, their answers and quiz results, the chat with the tutor's memory, and every version of each
rewritten page. A restart brings all of it back.

| To | Do |
|---|---|
| Back up a reader | stop the app and copy the folder, `cp -r content/personalization_data/default ~/quicklearn-backup` |
| Restore a backup | stop the app and copy the folder back in place of the current one |
| Start over | press Reset in the app, or stop the app and delete the folder |
| Keep several readers | start with a different `QUICKLEARN_READER` for each one |

## Your own content

The content is an [Obsidian](https://obsidian.md) vault, a folder of markdown files, so you can
write your own book and point the app at it:

```bash
QUICKLEARN_CONTENT=~/my-book ./run.sh
```

The reader data then lives in `~/my-book/personalization_data/`, so add that folder to the
`.gitignore` of your content. To read and edit the vault in Obsidian, install it, choose "Open
folder as vault" and pick the content folder. The format of the pages, sections and quizzes is in
[detailed_overview.md](detailed_overview.md). The easiest start is to copy `content/` and change
it.

Check a vault for broken links, malformed quizzes and math that does not render before you use it:

```bash
uv run python -m quicklearn.check ~/my-book            # errors exit with code 1
uv run python -m quicklearn.check ~/my-book --strict   # warnings fail too
```

Without a path it checks `content/`.

## Changing things

To change the app itself, its prompts, the rules that decide what is rewritten or the tutor's
tools, read [detailed_overview.md](detailed_overview.md). It explains how the code is organized
and how the book uses AI Functions.

## Troubleshooting

Each run writes its log to `logs/<timestamp>/server.log`. The file `logs/latest/server.log` is
always the newest one. Look there first when something does not happen.

| Problem | What to do |
|---|---|
| A quiz or chat does nothing, and the log shows `NoCredentialsError` or `Unable to locate credentials` | the AWS credentials are not found, so run `aws configure` or export them in the same terminal before `./run.sh` |
| The log shows `AccessDeniedException` or a message about model access | the account has no access to Claude Sonnet 5.5 in that region, or the IAM permissions are missing, so check Model access in the Bedrock console and the region in `AWS_DEFAULT_REGION` |
| The log shows `ExpiredToken` | temporary credentials ran out, so refresh them and restart the app |
| The log shows an authentication error with an API key | check `ANTHROPIC_API_KEY`, or unset it to use Bedrock |
| `address already in use` at start | another program has the port, so start on another one with `./run.sh 8890` |
| Math looks odd, with misplaced symbols or wrong spacing | the formulas are rendered as MathML by the browser, which some browsers draw less well, so try a recent Firefox or Chrome |
| `uv: command not found` after installing it | open a new terminal, or run `source $HOME/.local/bin/env`, so the shell finds it |
| `./run.sh: Permission denied` | run `chmod +x run.sh` once, or start it with `bash run.sh` |

## Tests

The tests make no model calls and need no credentials:

```bash
uv sync --extra dev
uv run pytest tests -q
```
