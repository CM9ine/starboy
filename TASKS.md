# Starboy — tasks

One task per agent session. Each ends with something runnable and checkable.
Mark tasks done as you go; the agent reads this to know where things stand.

Every task is done only when `uv run pytest` and `uv run ruff check .` both
pass.

---

## Done

### 1. Project skeleton ✅
uv, src layout, package `starboy`, `starboy --version`, single-source version,
pytest and ruff wired up.

### 2. Stream capture ✅
`scripts/capture_stream.py`. Raw JSONL fixtures from both CLIs at
`tests/fixtures/claude_code_stream.jsonl` and `tests/fixtures/codex_stream.jsonl`,
plus a written comparison of their formats.

### 3. Usage parser ✅
`src/starboy/usage.py`. Frozen `Usage` dataclass with explicit field names.
`parse_claude_code_usage` and `parse_codex_usage`, each returning usage plus
session id. Codex requires subtracting its cached figure from its total;
Claude does not.

### 3.5. Two-turn capture ✅
**Why:** the parsers carry an unresolved note about whether usage is per-turn
or cumulative. If cumulative and later summed per turn, totals inflate badly.
Blocks task 4.

Capture two turns in one session, in a **fresh directory** so turn one is
genuinely cold. Determine whether the second usage record includes the first.
Record the answer in `usage.py`, replacing the unknown marker. Commit the
fixture.

**Tests:** this is a measurement, not TDD. One test worth adding: parse the
two-turn fixture and assert turn-two usage against literal values you read
out of it yourself, so the semantics stay pinned even if you misremember.

### 4. Cost function ✅
Pure function: `Usage` plus a model identifier to an API-equivalent dollar
figure. Prices live in one versioned table; every future log line records
which version priced it, so numbers can be recomputed when rates change.

Cache reads and cache writes bill at different rates from uncached input.
Getting this wrong is the single most consequential silent bug in the project.

**Tests, in `tests/test_cost.py`:**
1. Cost of the Claude fixture's usage, asserted against a literal you
   calculated on paper — not with the implementation's own arithmetic.
2. Same for the Codex fixture.
3. For the same token count, cache reads cost less than uncached input.
   Fails loudly if anyone flattens the split.
4. Cache writes price differently from cache reads.
5. Zero usage costs zero.
6. An unknown model identifier raises. A silent zero is how a broken cost
   column survives an entire eval sweep unnoticed.
7. The pricing version is returned alongside the figure so a log line can
   record what priced it.

### 5. `run_agent()` ✅
One function, one harness (Claude Code only). Signature roughly:
`run_agent(harness, model, prompt, cwd) -> (text, Usage, session_id)`.

Two branches inside one function is the whole abstraction. Do not build a
class hierarchy.

Decide and document the tool-call folding rule here: what counts as one tool
call, such that the number means the same thing for both CLIs later.

**Tests:** the subprocess call itself needs a live CLI, so mark that test
`@pytest.mark.integration` and keep it out of the default run. Unit-test the
parts that do not: command construction for a given model and prompt, and
end-to-end parsing of a saved fixture into `(text, Usage, session_id)`.

---

## Next

### 6. JSONL logger
`run_agent()` returns an `AgentResult`; it does not know workflow identifiers
or write logs. A separate logger appends one line per call: run id, nullable
issue, phase, monotonic sequence, requested harness/model, resolved model,
the token counts, cost, pricing version, seconds, and outcome.

`AgentCallContext` owns caller-known workflow and requested-model facts.
`run_agent_logged()` is the thin composition that calls `run_agent()` and then
`log_agent_call()`.

A field not recorded cannot be recovered. Err toward recording.

**Tests:**
1. A written line round-trips through `json.loads` with every expected key
   present.
2. Two calls append rather than overwrite.
3. A `Usage` with zero values still writes all its fields — nothing is
   silently omitted for being falsy.

**Done when:** a `run_agent` call leaves a complete line on disk.

### 7. Worktree isolation
Context manager: branch off main into a scratch git worktree, clean up after.

**Done when:** two concurrent runs do not collide.

### 8. Issue reader
Thin `gh` CLI wrapper. Fetch an issue's title and body.

**Done when:** you can print a real issue.

### 9. Planner phase
Issue in, spec file written to `specs/`, acceptance criteria out.

The planner exists to give the review loop a termination condition. Without
written criteria, "approved" means whatever the reviewer's taste says today,
and taste is unbounded.

**Done when:** a real issue produces a spec you would accept.

### 10. Builder phase
Spec in, code changed in the worktree. No review yet.

**Done when:** a trivial issue produces a working diff.

### 11. Commit and PR
Code performs the commit and opens the PR. The agent proposes the commit
message; it does not run git itself.

**Done when:** a PR appears on GitHub from a real issue.

> **Stop here.** This is the first vertical slice. Run it on several real
> issues before continuing. What breaks decides what comes next, and the
> ordering below is a guess until then.

---

## After the first slice

### 12. Review phase
Second agent, fresh session, different model family from the builder. Returns
`{approved, findings[]}` where each finding has a severity. Log the verdict
and open the PR regardless — no repair yet. The point is to watch it disagree.

### 13. Envelope retry
Reask once on unparseable JSON, then treat as not approved. No correction loop.

### 14.5 Two-turn capture, Claude Code
Same question task 3.5 answered for Codex: is reported usage per-turn or
cumulative across a session? Unknown for Claude Code. The repair loop sends
multiple turns through one session and sums their usage, so summing cumulative
figures would inflate a four-turn run's cost by roughly 2.5x, silently and
plausibly. Capture two turns in a fresh directory, compare output counts
between turns, record the answer in `usage.py` and `CONTEXT.md`.

### 14. Repair loop
Findings back to the builder. Cap of 3. The cap is a failsafe, not the
mechanism.

### 15. Regression guard
Run the test command after each repair. Revert a repair that turns a green
test red. Deterministic code catches regressions more cheaply than an agent.

### 16. Severity gate
Only blockers and majors trigger a repair. Nits go in the PR body. Most of
what a reviewer produces on round two is nits.

### 17. Cost ceiling
Hard per-run stop regardless of round count. One pathological round can
outspend three normal ones and the round counter will not catch it.

### 18. Convergence detection
Stop early if blocker count is not falling or the same file keeps churning.
Diverging is a different failure from needing one more pass.

### 19. Blocked outcome
Draft PR with unresolved findings in the body, issue labelled. Blocked is a
normal outcome — the work is handed back, not thrown away.

### 20. Second harness
Codex branch in `run_agent`, normalised to the same `Usage` shape.

**Done when:** a builder on one family and a reviewer on the other completes
a run.

### 21. Config
Lift hardcoded harness/model pairs into one editable place. Swapping them
becomes a one-line edit, which is the first real experiment.

### 22. Session resume
Optional flag. Now A/B-able against cold starts with real numbers.
