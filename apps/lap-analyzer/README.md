# lap-analyzer

# TODO - fill this after

## Setup

```bash
pnpm install
pnpm sync-segments   # copies assets/track-segments/*.json from the main repo
                      # into src/assets/segments/ (gitignored, regenerate as needed)
```

## Scripts

- `pnpm dev:manual-test` - loads `test-fixtures/sample-session.pngt` through
  `LocalFileProvider` and logs every interface method's output. Throwaway
  smoke test until Phase 4/5 UI exists.
- `pnpm sync-segments` - re-syncs the bundled track-segments asset from the
  main repo. Re-run whenever `assets/track-segments/` changes upstream.
- `pnpm typecheck` - `tsc --noEmit`.
