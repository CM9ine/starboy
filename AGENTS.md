# Starboy

An agentic software factory. GitHub issue in, reviewed pull request out.

## Before doing any work

Read `CONTEXT.md`. It covers what this project is, the design rules that run
through the codebase, and known landmines that will cost you a day if you trip
on them.

Then read `TASKS.md` for the task list and current status.

## Rules

Work only on the task you were given. Do not start the next one, do not
refactor outside its scope, and do not add abstraction or configuration for
cases that do not exist yet.

Test-first where there is behaviour to test: write the test, run it, confirm
it fails for the right reason, then implement.

Both of these must pass before any task is done:

```
uv run pytest
uv run ruff check .
```

Do not edit `TASKS.md`. The author marks tasks done.
