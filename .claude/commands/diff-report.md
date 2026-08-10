---
description: Analyze (or run) the integration runner's --base diff mode and summarize what actually changed
allowed-tools: Read, Grep, Glob, Bash
---

Summarize a `--base` differential run of `tests/integration_test/runner.py`. Read
`tests/integration_test/README.md` first if you haven't — it explains what this tool does,
why, and its known noise sources.

## Should you run it, or just analyze an existing report?

A full `--base` run takes ~30-60 minutes (two complete 36-file replays). Default to
**analyzing whatever report already exists** — do not kick off a run unless the user
explicitly asks you to run/kick off/start the diff.

If the user does ask you to run it:
- Resolve their commit with `git rev-parse --verify <ref>^{commit}` first, and tell them the
  full hash.
- Check whether `test_data/.diff_cache/<sha>.json` already exists (cached base capture). If
  not, warn them this is the ~60-minute path, or offer `--base-only` first if they'd rather
  split it across two sittings (see README).
- Run it with `run_in_background: true` — it is long. Do not shorten the corpus or add
  `--pcap`-style filtering to save time; a partial corpus isn't a valid comparison (session
  state carries across files in one continuous replay, per the README).
- Once it completes, proceed to the analysis below.

## Input

Find the report to analyze, in this order:
1. If the user names a commit, resolve it and look for `test_data/.diff_cache/<sha>.report.txt`.
2. Otherwise, glob `test_data/.diff_cache/*.report.txt` and use the most recently modified one.
3. If none exist and the user hasn't asked you to run it, say so and ask whether to run it.

## Analysis

Read the report header first (`base_commit`, `generated_at`, `working_tree_checks_passed`,
`diff_violations`), then parse the `[DIFF] <file> <url>` blocks with their DeepDiff payloads.

**Do not present raw diff dumps as findings.** Categorize every diff before reporting
anything as a regression — this report has produced false leads before that only resolved
after real digging (see the README's "Two things worth knowing" section):

- **Live/instant-snapshot noise** — `/stream-overlay-info`, and live fields inside
  `/driver-info` such as `car-damage`, `car-status`, `g-force`, `motion`,
  `tyre-sets[N].lap-delta-time`. These reflect whatever packet was most recently processed
  at the instant the check fired, which differs by wall-clock timing between the two runs.
  Small numeric differences here are expected noise. Group and count these; don't enumerate
  every value.
- **Trailing-session artifacts** — diffs confined to a file's last session UID, where that
  final session is very short (check how many UID transitions the file had, and how much
  real content landed in the last one — `png.log`/`integration_test.log` from the run, if
  still available, or a fresh isolated replay of just that file if not). Note but don't
  alarm on these without further digging.
- **Structural/schema changes** — a field renamed, added, or removed uniformly across many
  entries usually means the user's changes did that on purpose. Cross-check against
  `git log <base>..HEAD --oneline` before calling it a regression.
- **Everything else** — genuine candidates. This is the part of the report that matters.

For genuine candidates, dig in properly: check the relevant log window for the file/session
involved, read the code path, and if a clean explanation doesn't emerge, replay the specific
file in isolation (fresh app instance, one file, no preceding files) rather than trusting the
full-corpus run's context — cross-file state and full-run timing have both produced
misleading diffs before that a clean isolated replay resolved. Say so explicitly if you're
still uncertain after that; don't assert a regression or a non-issue you haven't verified.

## Output

A short markdown summary, not a wall of raw diff text:

1. **Headline** — base commit (short hash), whether the working tree's own checks passed,
   total diff count.
2. **Breakdown by category** (from above) with counts.
3. **Worth investigating** — the genuine candidates only, each with file/endpoint/field and
   a one-line read on what it might mean. Go deeper only on request.
4. **Recommendation** — clean enough to trust the change, or something to chase first.
