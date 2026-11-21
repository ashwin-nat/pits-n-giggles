# lap-analyzer

# TODO - fill this after

## Setup

```bash
pnpm install
pnpm sync-segments   # copies assets/track-segments/*.json and assets/track-data/*.npz from the
                      # main repo into src/assets/ (gitignored, regenerate as needed)
```

## Scripts

- `pnpm dev:manual-test` - loads `test-fixtures/sample-session.pngt` through
  `LocalFileProvider` and logs every interface method's output. Throwaway
  smoke test until Phase 4/5 UI exists.
- `pnpm sync-segments` - re-syncs the bundled track-segments and track-geometry
  assets from the main repo. Re-run whenever `assets/track-segments/` or
  `assets/track-data/` changes upstream.
- `pnpm test:chart-math` - the pure-logic tests (`tsx --test`).
- `pnpm typecheck` - `tsc --noEmit`.

## Track map and markers

The map panel draws the track from `assets/track-data/c<circuit>.npz` and the
segment files. Everything on it comes from the bundled files; no backend change
is needed.

- **Marks per formula** are decided by `src/lib/formulas.ts`, a table keyed by the
  session's `formula` string. F1 26 shows active aero and overtake, every other
  formula shows DRS, and the speed trap shows for all. The same table gives the
  display names used for the game ("F1 2025", "F1 26").
- **`src/lib/trackMarkers.ts`** builds the markers (zones, points, brake boards) from
  a track's segment file and the formula rules. The map and the section strip
  both draw from it. The **Markers** button in the header hides them on both.
- **Brake boards and point labels** appear only when the map is zoomed in far
  enough to fit them.
- **Corner badges** show the turn number; hovering one shows its name and span.
