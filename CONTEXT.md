# Starboy — project context

Read this before starting any task. It is the shared background; the task
itself lives in `TASKS.md`.

## What this is

An agentic software factory. A GitHub issue goes in, a planned, implemented,
independently reviewed pull request comes out. It runs unattended on a small
always-on server so issues get worked while the author is elsewhere.

**It never merges.** The factory prepares and verifies a pull request and
stops. The merge decision stays with a person. This is not negotiable and no
task should introduce a merge step.

## What makes it different

Most factories cannot answer the only question that decides whether one is
worth running: is this configuration better than the last one, and how do you
know? Starboy is built so that question is answerable.

Two consequences run through the whole codebase:

**Everything is measured.** Every agent call records its harness, model, token
split, wall clock and outcome. A field not recorded during a run cannot be
recovered afterwards, so when in doubt, record it.

**Two harnesses, deliberately.** Claude Code and Codex, with the builder and
the reviewer on different model families. Numbers from the two must be
directly comparable, which is a constraint on how anything touching them is
written.

## Design rules

**Code owns the loop; agents own the phases.** Sequencing, retries and
acceptance live in Python. An agent works inside one bounded phase and hands
back a result. Context crosses a seam as data, not as conversation.

**Execution facts are not product truth.** A process exiting 0 means a
subprocess succeeded. It is never evidence that the software is correct.

**The reviewer is a different agent from the builder.** Structurally, not by
convention. An author is unreliable about their own work.

**Bounded, always.** Repair loops have a cap, a cost ceiling, and convergence
detection. Stopping and handing back a draft PR is a normal outcome, not a
failure.

**Known invocations are code, not agents.** Running a test suite is a command.
There is no tester agent, and there should never be one.

## Stack

Python 3.12+, uv, src layout, package `starboy`. typer for CLI, pytest, ruff.
Logging is JSONL to a file. No database yet — that is deliberate, revisit when
cross-run queries get painful.

Development happens in Codex. The factory itself drives both Claude Code and
Codex as subprocesses; do not conflate the two.

## Conventions

- Test-first where there is behaviour to test. Write the test, watch it fail
  for the right reason, then implement.
- Expected values in tests are hardcoded literals read from real data. A test
  that recomputes the answer using the implementation's own logic tests
  nothing.
- No abstraction until there are two real cases in hand.
- `uv run pytest` and `uv run ruff check .` must both pass before a task is
  done.

## Landmines

**`input_tokens` means different things in the two CLIs.** Claude reports
cache reads as separate from and additive to its input count. Codex reports a
total with the cached figure already inside it. Normalised names live in
`src/starboy/usage.py` and are deliberately explicit. Never introduce a
variable called `input_tokens`.

**Cache reads dominate.** Coding agents have a huge stable prefix, so most
input tokens are cached and billed at a fraction of full rate. Costing that
ignores the split will be wrong by a large multiple and will still look
plausible.

**The Claude fixture was captured warm.** Its 4 uncached input tokens are not
representative of a real cold run. See the note in `tests/test_usage.py`.

**Unresolved:** whether usage records are per-turn or cumulative across a
session, for either CLI. Marked in `usage.py`. Settle it before anything sums
usage across turns.

**Tool calls are not comparable across harnesses without a folding rule.**
Claude links `tool_use` to `tool_result` by id. Codex emits
`item.started`/`item.completed` pairs and splits one logical action into
separate command and file_change items.

## Scope discipline

The task in front of you is the whole job. Do not build ahead, do not add
configuration for things that have one caller, and do not generalise for a
second case that does not exist yet. If a task seems to require something not
listed in it, say so and stop rather than inventing scope.
