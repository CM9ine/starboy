# Per-task prompt

Paste this into a fresh Codex session, filling in the task number. That is the
whole ritual.

---

```
Read CONTEXT.md, then read TASKS.md and find task <N>.

Work only on task <N>. Do not start the next one, do not refactor anything
outside its scope, and do not add configuration or abstraction for cases that
do not exist yet.

Before writing code:
- Tell me your understanding of the task in two or three sentences.
- Flag anything ambiguous, or that conflicts with what you find in the
  codebase. Stop and ask rather than guessing.

Then:
- If the task lists tests, write those first. Run them and show me they fail
  for the right reason before implementing.
- Implement until they pass.
- Run `uv run pytest` and `uv run ruff check .`.

When done, report:
- What you built and where.
- The passing test output.
- Anything you discovered that contradicts CONTEXT.md or TASKS.md, or that
  should change a later task.
- Anything you were unsure about and decided on your own.

Do not update TASKS.md; I will mark it done.
```

---

## Notes on running this

**One task, one session.** The context that matters lives in the two files,
not in the conversation.

**The last two report items are the valuable ones.** Task 2 was worth more for
what it discovered about the two CLIs disagreeing on token accounting than for
the code it produced. Read those sections properly.

**Update CONTEXT.md when a discovery is durable.** The landmines section is
where hard-won facts go. If an agent finds something that would bite a future
task, it belongs there, not in a commit message.

**Only spec tests two or three tasks ahead.** Writing them for task 20 now
means guessing at code that does not exist. Add them as each task comes into
view.

**When a task turns out to be two tasks, split it in TASKS.md** rather than
letting the session sprawl. Task 3.5 got added that way.

**Keep TASKS.md current.** It is the file that goes stale, because updating it
is the step that feels skippable when a task finishes. An agent reading a
stale list will happily redo work.
