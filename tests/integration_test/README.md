# Integration Runner

This starts the real app and throws real F1 telemetry recordings at it, the same way the
actual game would. It is not a pytest suite - pytest never collects this folder. You run it
directly.

## Plain run

```bash
poetry run python -m tests.integration_test.runner
```

This:

1. Downloads the recordings into `test_data/` the first time (cached after that).
2. Starts the full app (backend, web, HUD, everything) as a real subprocess.
3. Opens three browser tabs so the dashboards get exercised too.
4. Replays every recording, one after another, in the same running app.
5. After each recording, hits the HTTP endpoints (`/driver-info`, `/race-info`, etc.) and
   checks they respond.
6. Whenever the app writes a session save, checks that save file for impossible states
   (an invariant checker - things like "a driver can't have negative laps").
7. Prints a stats summary and exits 1 if anything failed.

Nothing here is committed anywhere or reviewed - it is a throwaway check you run locally.

## `--base`: did my change actually change anything?

This is for a different question than "does it work" - it's "did my code change what the
app *outputs*, or only how the code is organized?" That matters when you're refactoring and
want proof you didn't break behavior, not just a feeling that you didn't.

```bash
poetry run python -m tests.integration_test.runner --base <some-commit>
```

What it does, in order:

1. Checks out `<some-commit>` into a **separate, temporary copy** of the repo (a git
   worktree) - your actual working copy is never touched.
2. Runs the full replay (steps 2-5 above) against that old commit's code, but this time it
   also saves a copy of every endpoint response.
3. Deletes the temporary copy.
4. Runs the full replay again, this time against your current code, saving responses the
   same way.
5. Compares the two sets of responses field by field and tells you exactly what's different.

If nothing printed under "DIFF", your change didn't alter any observable output for these
recordings. If something did change, you get the exact field and both values, so you can
judge whether that's the fix you meant to make or something you broke.

**This takes a while - about 30 minutes per side, so ~60 minutes the first time.** The
base-commit side gets cached (keyed by commit), so running `--base` again with the *same*
commit skips straight to just your current code (~30 minutes).

### Splitting it across two sittings

If you don't want to sit through both halves at once:

```bash
# Now: just capture the base commit, then stop
poetry run python -m tests.integration_test.runner --base <some-commit> --base-only

# Later, whenever: this picks up the cached capture and only runs your current code
poetry run python -m tests.integration_test.runner --base <some-commit>
```

Use the *exact same commit* both times (the full hash it prints back to you on the first
run, not a branch name that might move) or the cache won't match and it'll redo both halves.

### Picking a commit to compare against

Any commit works as `--base`, but pick one from **after** `b580463a` (the commit that
unified the live dashboard and save-viewer into one web server) - anything older used a
different set of URLs entirely and the comparison won't mean anything. Also worth a quick
sanity check first:

```bash
git diff --stat <candidate-commit>..HEAD -- pyproject.toml poetry.lock
```

If that's empty, the base commit's dependencies match yours and it'll run cleanly. If it's
not empty, the old code might not even import correctly under your current environment.

### Reading the result

Besides the terminal output, a report file gets written to:

```
test_data/.diff_cache/<commit-hash>.report.txt
```

It's plain text: which commit, whether your code's own checks passed, how many differences
were found, and the full list of what changed. It doesn't get overwritten by an unrelated
test run - only by a `--base` run against that same commit again. This file isn't
committed either; it's local scratch, same as everything else this tool writes.

### Two things worth knowing before you trust a diff

- **Live/instant fields are noisy.** `/stream-overlay-info` and a few fields in
  `/driver-info` (like `car-damage`, `car-status`) reflect whatever packet was *most
  recently processed* the instant the check fired. Since the two runs happen at different
  wall-clock times, tiny differences here (a gear number, a wear percentage by 0.01) are
  usually just that - not a real bug. Don't chase these.
- **A short trailing session at the very end of a recording is unreliable.** If a file ends
  with barely any data after the last session-UID change, don't read much into whatever
  driver validity or classification data does or doesn't show up there - it depends on
  exact timing, not your code.

If a diff still looks suspicious after accounting for both of those, that's the one worth
digging into.

### Adding a new field or endpoint later

You don't need to tell this tool about a new field. It compares whatever JSON the endpoints
actually return, so a new field just gets picked up automatically and diffed like everything
else - that's the normal, wanted case.

The one thing to check: **is the new field's value the same every time you replay the same
recording, or can it change run to run even with identical code?** Things like a wall-clock
timestamp, a random ID, or "time since the app started" are not the same every time. If you
add a field like that, it'll show up as a difference on *every single `--base` run forever*,
even when nothing actually changed - pure noise that trains people to ignore real diffs too.

If you add a field like that, tell this tool to ignore it. Open `diff_utils.py` and add its
key name to `_VOLATILE_KEYS`:

```python
_VOLATILE_KEYS = {"timestamp", "version"}
```

One catch: it matches by field name only, anywhere in the response, not by which endpoint or
which part of the JSON it's in. So don't reuse a name that's already in that list (like
`timestamp`) for a field that *is* meant to be compared - it'll get silently ignored too.
Pick a name that's specific to your new field instead.
